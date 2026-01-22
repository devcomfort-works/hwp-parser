"""
HWP 파일 변환기 - 메인 클래스

pyhwp를 사용하여 HWP 파일을 다양한 포맷으로 변환합니다.
"""

from __future__ import annotations

import html
import io
import multiprocessing
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile
from dataclasses import dataclass, field
from datetime import datetime
from multiprocessing import Process, Queue
from pathlib import Path
from typing import TYPE_CHECKING, Literal, cast

# Fork 경고 방지: spawn 모드 사용 (멀티스레드 환경에서 안전)
try:
    multiprocessing.set_start_method("spawn", force=False)
except RuntimeError:  # pragma: no cover
    pass  # 이미 설정된 경우 무시

from loguru import logger

if TYPE_CHECKING:
    from hwp_parser.core.worker import WorkerResult

OutputFormat = Literal["txt", "html", "markdown", "odt"]


@dataclass
class ConversionResult:
    """
    HWP 변환 결과를 담는 데이터 클래스

    Attributes:
        content: 변환된 콘텐츠 (텍스트 또는 바이너리)
        source_path: 원본 HWP 파일 경로
        output_format: 변환된 포맷
        pipeline: 변환 파이프라인 설명
        converted_at: 변환 시각
    """

    content: str | bytes
    source_path: Path
    output_format: OutputFormat
    pipeline: str
    converted_at: datetime = field(default_factory=datetime.now)

    @property
    def source_name(self) -> str:
        """원본 파일 이름"""
        return self.source_path.name

    @property
    def is_binary(self) -> bool:
        """바이너리 콘텐츠 여부"""
        return isinstance(self.content, bytes)

    def to_dict(self) -> dict:
        """딕셔너리로 변환"""
        return {
            "source_name": self.source_name,
            "source_path": str(self.source_path),
            "output_format": self.output_format,
            "pipeline": self.pipeline,
            "converted_at": self.converted_at.isoformat(),
            "content_length": len(self.content),
            "is_binary": self.is_binary,
        }


@dataclass
class HTMLDirResult:
    """
    HTML 디렉터리 변환 결과를 담는 데이터 클래스

    hwp5html은 단일 파일이 아닌 디렉터리 구조를 생성합니다:
    - index.xhtml: 메인 HTML 문서
    - styles.css: 스타일시트
    - bindata/: 이미지 등 바이너리 데이터 (선택적)

    Attributes:
        xhtml_content: index.xhtml 내용
        css_content: styles.css 내용
        bindata: 바이너리 데이터 딕셔너리 {파일명: bytes}
        source_path: 원본 HWP 파일 경로
        converted_at: 변환 시각
    """

    xhtml_content: str
    css_content: str
    bindata: dict[str, bytes]
    source_path: Path
    converted_at: datetime = field(default_factory=datetime.now)

    @property
    def output_format(self) -> str:
        """출력 포맷 (항상 'html')"""
        return "html"

    @property
    def is_binary(self) -> bool:
        """바이너리 콘텐츠 여부 (HTML은 항상 False)"""
        return False

    @property
    def source_name(self) -> str:
        """원본 파일 이름"""
        return self.source_path.name

    def to_zip_bytes(self) -> bytes:
        """결과를 ZIP 파일 바이트로 변환"""
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("index.xhtml", self.xhtml_content.encode("utf-8"))
            zf.writestr("styles.css", self.css_content.encode("utf-8"))
            for name, data in self.bindata.items():
                zf.writestr(f"bindata/{name}", data)
        return buffer.getvalue()

    def get_preview_html(self) -> str:
        """미리보기용 완전한 HTML 생성 (CSS 인라인 포함)"""
        # CSS를 style 태그로 인라인 삽입
        css_tag = f"<style>\n{self.css_content}\n</style>"

        # </head> 앞에 CSS 삽입
        if "</head>" in self.xhtml_content:
            return self.xhtml_content.replace("</head>", f"{css_tag}\n</head>")
        else:  # pragma: no cover
            # head가 없으면 맨 앞에 추가 (pyhwp는 항상 head를 생성하므로 발생하지 않음)
            return f"{css_tag}\n{self.xhtml_content}"


class HWPConverter:
    """
    HWP 파일 변환기

    pyhwp를 사용하여 HWP 파일을 다양한 포맷으로 변환합니다.


    지원 포맷:
    - txt: 순수 텍스트 (hwp→html→txt 파이프라인)
    - html: XHTML 형식 (hwp5html 명령)
    - markdown: Markdown 형식 (hwp→html→markdown 파이프라인)
    - odt: Open Document Text (hwp5odt 명령)

    변환 모드:
    - num_workers=None (기본): subprocess 기반 변환
    - num_workers>0: Persistent Worker 사용 (pyhwp 직접 호출, ~64% 빠름)

    Example:
        # 기본 사용 (subprocess)
        converter = HWPConverter()
        result = converter.to_text(Path("document.hwp"))
        print(result.content)

        # 고성능 모드 (Worker Pool)
        with HWPConverter(num_workers=4) as converter:
            result = converter.to_markdown("document.hwp")
    """

    SUPPORTED_FORMATS: tuple[OutputFormat, ...] = ("txt", "html", "markdown", "odt")
    _logger_configured: bool = False

    def __init__(self, verbose: bool = False, num_workers: int | None = None) -> None:
        """
        HWPConverter 초기화

        Args:
            verbose: 상세 로깅 활성화
            num_workers: 워커 프로세스 수. None이면 subprocess 모드, 양수면 Worker Pool 모드.
        """
        self.verbose = verbose
        self.num_workers = num_workers

        # Worker Pool 관련 상태
        self._workers: list[Process] = []
        self._input_queue: Queue | None = None
        self._output_queue: Queue | None = None
        self._task_counter = 0
        self._worker_started = False

        if self.verbose:
            self._configure_logger()

    # ========== Worker Pool 관리 ==========

    def _start_workers(self) -> None:
        """워커 프로세스 시작 (내부 API)"""
        if self._worker_started or self.num_workers is None or self.num_workers <= 0:
            return

        from hwp_parser.core.worker import worker_main

        self._input_queue = Queue()
        self._output_queue = Queue()

        for _ in range(self.num_workers):
            p = Process(
                target=worker_main,
                args=(self._input_queue, self._output_queue),
                daemon=True,
            )
            p.start()
            self._workers.append(p)

        self._worker_started = True

    def _shutdown_workers(self, timeout: float = 5.0) -> None:
        """워커 프로세스 종료 (내부 API)"""
        if not self._worker_started:
            return

        # 종료 신호 전송
        for _ in self._workers:
            if self._input_queue:
                self._input_queue.put(None)

        # 워커 종료 대기
        for worker in self._workers:
            worker.join(timeout=timeout)
            if worker.is_alive():  # pragma: no cover
                worker.terminate()

        self._workers.clear()
        self._input_queue = None
        self._output_queue = None
        self._worker_started = False

    def _convert_via_worker(
        self, file_path: Path, output_format: OutputFormat
    ) -> ConversionResult:
        """워커를 통한 변환 (내부 API)"""
        from hwp_parser.core.worker import WorkerTask

        if not self._worker_started:
            self._start_workers()

        self._task_counter += 1
        task = WorkerTask(
            task_id=self._task_counter,
            file_path=str(file_path.absolute()),
            output_format=output_format,
        )
        self._input_queue.put(task)  # type: ignore

        result: WorkerResult = self._output_queue.get()  # type: ignore

        if not result.success:
            raise RuntimeError(f"변환 실패: {result.error}")

        # 파이프라인 문자열 생성
        if output_format == "txt":
            pipeline = "hwp→xhtml→txt (worker)"
        elif output_format == "markdown":
            pipeline = "hwp→xhtml→markdown (worker)"
        elif output_format == "odt":
            pipeline = "hwp→odt (worker)"
        else:  # pragma: no cover
            pipeline = f"hwp→{output_format} (worker)"

        return ConversionResult(
            content=cast("str | bytes", result.content),
            source_path=file_path,
            output_format=output_format,
            pipeline=pipeline,
        )

    def _convert_html_via_worker(self, file_path: Path) -> HTMLDirResult:
        """워커를 통한 HTML 디렉터리 변환 (내부 API)"""
        from hwp_parser.core.worker import WorkerTask

        if not self._worker_started:
            self._start_workers()

        self._task_counter += 1
        task = WorkerTask(
            task_id=self._task_counter,
            file_path=str(file_path.absolute()),
            output_format="html",
        )
        self._input_queue.put(task)  # type: ignore

        result: WorkerResult = self._output_queue.get()  # type: ignore

        if not result.success:
            raise RuntimeError(f"HTML 변환 실패: {result.error}")

        return HTMLDirResult(
            xhtml_content=cast("str", result.content),
            css_content=result.css_content or "",
            bindata=result.bindata or {},
            source_path=file_path,
        )

    def __enter__(self) -> "HWPConverter":
        """Context manager 진입 - 워커 자동 시작"""
        if self.num_workers and self.num_workers > 0:
            self._start_workers()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager 종료 - 워커 자동 정리"""
        self._shutdown_workers()

    # ========== 로깅 ==========

    @classmethod
    def _configure_logger(cls) -> None:
        if cls._logger_configured:
            return
        logger.remove()
        logger.add(
            sys.stderr,
            level="INFO",
            colorize=True,
            format=(
                "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
                "<level>{level: <8}</level> | {message}"
            ),
        )
        cls._logger_configured = True

    def _log_start(self, file_path: Path, output_format: OutputFormat) -> None:
        if not self.verbose:
            return
        input_size = file_path.stat().st_size if file_path.exists() else 0
        logger.info(
            "HWP 변환 시작 | {name} | 입력 {size} bytes | 포맷 {fmt}",
            name=file_path.name,
            size=input_size,
            fmt=output_format,
        )

    def _log_finish(
        self,
        file_path: Path,
        output_format: OutputFormat,
        pipeline: str,
        content: str | bytes,
        started_at: float,
    ) -> None:
        if not self.verbose:
            return
        input_size = file_path.stat().st_size if file_path.exists() else 0
        output_size = len(content)
        elapsed = time.perf_counter() - started_at
        logger.info(
            "HWP 변환 완료 | {name} | 입력 {in_size} bytes | 출력 {out_size} bytes | "
            "포맷 {fmt} | 파이프라인 {pipeline} | 소요 {elapsed:.3f}s",
            name=file_path.name,
            in_size=input_size,
            out_size=output_size,
            fmt=output_format,
            pipeline=pipeline,
            elapsed=elapsed,
        )

    def _validate_file(self, file_path: Path) -> Path:
        """
        파일 경로 유효성 검증

        Args:
            file_path: 검증할 파일 경로

        Returns:
            검증된 Path 객체

        Raises:
            ValueError: 디렉토리 경로가 전달된 경우
            FileNotFoundError: 파일이 존재하지 않는 경우
        """
        if not isinstance(file_path, Path):
            file_path = Path(file_path)

        if file_path.is_dir():
            raise ValueError(
                f"디렉토리가 입력되었습니다: {file_path}\n"
                f"HWP 파일 경로를 지정해야 합니다."
            )

        if not file_path.exists():
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")

        return file_path

    def _use_worker(self) -> bool:
        """워커 모드 사용 여부 확인"""
        return self.num_workers is not None and self.num_workers > 0

    def to_html(self, file_path: Path) -> HTMLDirResult:
        """
        HWP 파일을 HTML 디렉터리 구조로 변환

        hwp5html이 생성하는 전체 디렉터리 구조를 반환합니다:
        - index.xhtml: 메인 HTML 문서
        - styles.css: 스타일시트
        - bindata/: 이미지 등 바이너리 데이터 (선택적)

        Args:
            file_path: 변환할 HWP 파일 경로

        Returns:
            HTMLDirResult: 디렉터리 구조를 담은 결과 객체

        Raises:
            ValueError: 디렉토리 경로가 전달된 경우
            FileNotFoundError: 파일이 존재하지 않는 경우
            RuntimeError: 변환 실패
        """
        file_path = self._validate_file(file_path)

        # 워커 모드
        if self._use_worker():
            self._log_start(file_path, "html")
            started_at = time.perf_counter()
            result = self._convert_html_via_worker(file_path)
            elapsed = time.perf_counter() - started_at
            if self.verbose:
                logger.info(
                    "HTML 디렉터리 변환 완료 | {name} | xhtml={xhtml_size} css={css_size} bindata={bindata_count}개 | {elapsed:.3f}s",
                    name=file_path.name,
                    xhtml_size=len(result.xhtml_content),
                    css_size=len(result.css_content),
                    bindata_count=len(result.bindata),
                    elapsed=elapsed,
                )
            return result

        # subprocess 모드
        self._log_start(file_path, "html")
        started_at = time.perf_counter()

        temp_dir = Path(tempfile.mkdtemp())
        output_dir = temp_dir / file_path.stem

        try:
            command = ["hwp5html", f"--output={output_dir}", str(file_path)]
            proc_result = subprocess.run(
                command,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            if proc_result.returncode != 0:
                raise RuntimeError(
                    f"HTML 변환 실패: {file_path.name}\n{proc_result.stderr}"
                )

            xhtml_file = output_dir / "index.xhtml"
            css_file = output_dir / "styles.css"

            if not xhtml_file.exists():
                raise RuntimeError(
                    f"HTML 변환 실패: 결과 파일이 생성되지 않음 - {file_path.name}"
                )

            xhtml_content = xhtml_file.read_text(encoding="utf-8")
            css_content = (
                css_file.read_text(encoding="utf-8") if css_file.exists() else ""
            )

            # bindata 디렉터리 읽기
            bindata: dict[str, bytes] = {}
            bindata_dir = output_dir / "bindata"
            if bindata_dir.exists() and bindata_dir.is_dir():
                for file in bindata_dir.iterdir():
                    # pyhwp(hwp5html)는 bindata에 파일만 생성하고 서브디렉터리는 생성하지 않음.
                    # is_file() 체크는 미래 변경이나 파일시스템 이상에 대비한 방어 코드.
                    if file.is_file():  # pragma: no branch
                        bindata[file.name] = file.read_bytes()

            html_result = HTMLDirResult(
                xhtml_content=xhtml_content,
                css_content=css_content,
                bindata=bindata,
                source_path=file_path,
            )

            elapsed = time.perf_counter() - started_at
            if self.verbose:
                logger.info(
                    "HTML 디렉터리 변환 완료 | {name} | xhtml={xhtml_size} css={css_size} bindata={bindata_count}개 | {elapsed:.3f}s",
                    name=file_path.name,
                    xhtml_size=len(xhtml_content),
                    css_size=len(css_content),
                    bindata_count=len(bindata),
                    elapsed=elapsed,
                )

            return html_result

        finally:
            if temp_dir.exists():
                shutil.rmtree(temp_dir)

    def to_text(self, file_path: Path) -> ConversionResult:
        """
        HWP 파일을 순수 텍스트로 변환

        hwp→html→txt 파이프라인을 사용합니다.

        Args:
            file_path: 변환할 HWP 파일 경로

        Returns:
            ConversionResult: 변환 결과

        Raises:
            ValueError: 디렉토리 경로가 전달된 경우
            FileNotFoundError: 파일이 존재하지 않는 경우
            RuntimeError: 변환 실패
        """
        file_path = self._validate_file(file_path)

        # 워커 모드
        if self._use_worker():
            self._log_start(file_path, "txt")
            started_at = time.perf_counter()
            result = self._convert_via_worker(file_path, "txt")
            self._log_finish(
                file_path, "txt", result.pipeline, result.content, started_at
            )
            return result

        # subprocess 모드
        import html2text

        self._log_start(file_path, "txt")
        started_at = time.perf_counter()

        # 1단계: HTML 변환
        html_result = self.to_html(file_path)

        # 2단계: HTML → 텍스트
        h = html2text.HTML2Text()
        h.ignore_links = False
        h.ignore_images = True
        h.ignore_emphasis = False
        h.body_width = 0
        h.unicode_snob = True
        h.escape_snob = True
        h.bypass_tables = False

        # to_html()은 HTMLDirResult를 반환
        text_content = h.handle(html_result.xhtml_content)

        # HTML 엔티티 언이스케이프
        text_content = html.unescape(text_content)

        # Markdown 이스케이프 제거
        markdown_escapes = [r"\(", r"\)", r"\[", r"\]", r"\.", r"\*", r"\_", r"\#"]
        for escape in markdown_escapes:
            text_content = text_content.replace(escape, escape[1:])

        result = ConversionResult(
            content=text_content,
            source_path=file_path,
            output_format="txt",
            pipeline="hwp→xhtml→txt",
        )

        self._log_finish(
            file_path,
            "txt",
            result.pipeline,
            result.content,
            started_at,
        )

        return result

    def to_markdown(self, file_path: Path) -> ConversionResult:
        """
        HWP 파일을 Markdown으로 변환

        hwp→html→markdown 파이프라인을 사용합니다.

        Args:
            file_path: 변환할 HWP 파일 경로

        Returns:
            ConversionResult: 변환 결과

        Raises:
            ValueError: 디렉토리 경로가 전달된 경우
            FileNotFoundError: 파일이 존재하지 않는 경우
            RuntimeError: 변환 실패
            ImportError: html-to-markdown이 설치되지 않은 경우
        """
        file_path = self._validate_file(file_path)

        # 워커 모드
        if self._use_worker():
            self._log_start(file_path, "markdown")
            started_at = time.perf_counter()
            result = self._convert_via_worker(file_path, "markdown")
            self._log_finish(
                file_path, "markdown", result.pipeline, result.content, started_at
            )
            return result

        # subprocess 모드
        try:
            from html_to_markdown import ConversionOptions, convert
        except ImportError:
            raise ImportError(
                "html-to-markdown 라이브러리가 필요합니다: pip install html-to-markdown"
            )

        self._log_start(file_path, "markdown")
        started_at = time.perf_counter()

        # 1단계: HTML 변환
        html_result = self.to_html(file_path)

        # 2단계: HTML → Markdown (to_html()은 HTMLDirResult를 반환)
        options = ConversionOptions(escape_misc=False)
        markdown_content = convert(html_result.xhtml_content, options)
        markdown_content = html.unescape(markdown_content)

        result = ConversionResult(
            content=markdown_content,
            source_path=file_path,
            output_format="markdown",
            pipeline="hwp→xhtml→markdown",
        )

        self._log_finish(
            file_path,
            "markdown",
            result.pipeline,
            result.content,
            started_at,
        )

        return result

    def to_odt(self, file_path: Path) -> ConversionResult:
        """
        HWP 파일을 ODT(Open Document Text)로 변환

        pyhwp의 hwp5odt 명령을 사용합니다.

        ⚠️ 일부 복잡한 서식의 HWP는 RelaxNG 검증 오류가 발생할 수 있습니다.

        Args:
            file_path: 변환할 HWP 파일 경로

        Returns:
            ConversionResult: 변환 결과 (바이너리)

        Raises:
            ValueError: 디렉토리 경로가 전달된 경우
            FileNotFoundError: 파일이 존재하지 않는 경우
            RuntimeError: 변환 실패
        """
        file_path = self._validate_file(file_path)

        # 워커 모드
        if self._use_worker():
            self._log_start(file_path, "odt")
            started_at = time.perf_counter()
            result = self._convert_via_worker(file_path, "odt")
            self._log_finish(
                file_path, "odt", result.pipeline, result.content, started_at
            )
            return result

        # subprocess 모드
        self._log_start(file_path, "odt")
        started_at = time.perf_counter()

        temp_dir = Path(tempfile.mkdtemp())
        output_file = temp_dir / f"{file_path.stem}.odt"

        try:
            command = ["hwp5odt", f"--output={output_file}", str(file_path)]
            result = subprocess.run(
                command,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            if result.returncode != 0:
                stderr = result.stderr.strip()
                if "RelaxNG" in stderr or "ValidationFailed" in stderr:
                    raise RuntimeError(
                        f"ODT 변환 실패 (RelaxNG 검증 오류): {file_path.name}\n"
                        f"복잡한 서식으로 인해 ODT 변환이 불가합니다. "
                        f"HTML 또는 Markdown 사용을 권장합니다."
                    )
                raise RuntimeError(f"ODT 변환 실패: {file_path.name}\n{stderr}")

            if not output_file.exists():
                raise RuntimeError(
                    f"ODT 변환 실패: 결과 파일이 생성되지 않음 - {file_path.name}"
                )

            content = output_file.read_bytes()

            result = ConversionResult(
                content=content,
                source_path=file_path,
                output_format="odt",
                pipeline="hwp→odt",
            )

            self._log_finish(
                file_path,
                "odt",
                result.pipeline,
                result.content,
                started_at,
            )

            return result

        finally:
            if temp_dir.exists():
                shutil.rmtree(temp_dir)

    def convert(
        self, file_path: Path, output_format: OutputFormat = "markdown"
    ) -> ConversionResult:
        """
        HWP 파일을 지정된 포맷으로 변환

        Args:
            file_path: 변환할 HWP 파일 경로
            output_format: 출력 포맷 (txt, html, markdown, odt)

        Returns:
            ConversionResult: 변환 결과

        Raises:
            ValueError: 지원하지 않는 포맷인 경우
        """
        if output_format not in self.SUPPORTED_FORMATS:
            raise ValueError(
                f"지원하지 않는 포맷: {output_format}. "
                f"사용 가능: {', '.join(self.SUPPORTED_FORMATS)}"
            )

        converters = {
            "txt": self.to_text,
            "html": self.to_html,
            "markdown": self.to_markdown,
            "odt": self.to_odt,
        }

        return converters[output_format](file_path)
