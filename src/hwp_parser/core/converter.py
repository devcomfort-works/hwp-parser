"""
HWP 파일 변환기 - 메인 클래스

pyhwp CLI 도구를 사용하여 HWP 파일을 다양한 포맷으로 변환합니다.
"""

from __future__ import annotations

import html
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Literal, cast

from loguru import logger

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


class HWPConverter:
    """
    HWP 파일 변환기

    pyhwp CLI 도구를 사용하여 HWP 파일을 다양한 포맷으로 변환합니다.

    지원 포맷:
    - txt: 순수 텍스트 (hwp→html→txt 파이프라인)
    - html: XHTML 형식 (hwp5html 명령)
    - markdown: Markdown 형식 (hwp→html→markdown 파이프라인)
    - odt: Open Document Text (hwp5odt 명령)

    Example:
        converter = HWPConverter()
        result = converter.to_text(Path("document.hwp"))
        print(result.content)
    """

    SUPPORTED_FORMATS: tuple[OutputFormat, ...] = ("txt", "html", "markdown", "odt")
    _logger_configured: bool = False

    def __init__(self, verbose: bool = False) -> None:
        """HWPConverter 초기화"""
        self.verbose = verbose
        if self.verbose:
            self._configure_logger()

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

    def to_html(self, file_path: Path) -> ConversionResult:
        """
        HWP 파일을 XHTML로 변환

        pyhwp의 hwp5html 명령을 사용합니다.

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
        self._log_start(file_path, "html")
        started_at = time.perf_counter()

        temp_dir = Path(tempfile.mkdtemp())
        output_dir = temp_dir / file_path.stem

        try:
            command = ["hwp5html", f"--output={output_dir}", str(file_path)]
            result = subprocess.run(
                command,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            if result.returncode != 0:
                raise RuntimeError(f"HTML 변환 실패: {file_path.name}\n{result.stderr}")

            xhtml_file = output_dir / "index.xhtml"
            if not xhtml_file.exists():
                raise RuntimeError(
                    f"HTML 변환 실패: 결과 파일이 생성되지 않음 - {file_path.name}"
                )

            content = xhtml_file.read_text(encoding="utf-8")

            result = ConversionResult(
                content=content,
                source_path=file_path,
                output_format="html",
                pipeline="hwp→xhtml",
            )

            self._log_finish(
                file_path,
                "html",
                result.pipeline,
                result.content,
                started_at,
            )

            return result

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
        import html2text

        file_path = self._validate_file(file_path)
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

        # to_html()은 항상 str을 반환함
        text_content = h.handle(cast(str, html_result.content))

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
        try:
            from html_to_markdown import ConversionOptions, convert
        except ImportError:
            raise ImportError(
                "html-to-markdown 라이브러리가 필요합니다: pip install html-to-markdown"
            )

        file_path = self._validate_file(file_path)
        self._log_start(file_path, "markdown")
        started_at = time.perf_counter()

        # 1단계: HTML 변환
        html_result = self.to_html(file_path)

        # 2단계: HTML → Markdown (to_html()은 항상 str을 반환)
        options = ConversionOptions(escape_misc=False)
        markdown_content = convert(cast(str, html_result.content), options)
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
