"""
Persistent Worker - pyhwp 직접 호출 워커

subprocess 오버헤드 없이 pyhwp를 직접 사용하여 HWP 변환을 수행합니다.
별도 프로세스에서 실행되며, 한 번 초기화 후 재사용됩니다.

Note:
    이 모듈은 pyhwp(AGPL v3)를 직접 import합니다.
    따라서 이 라이브러리(hwp-parser)도 AGPL v3 라이선스가 적용됩니다.
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from multiprocessing import Queue
from pathlib import Path
from typing import Literal

# pyhwp 직접 import (AGPL v3)
from hwp5.hwp5html import HTMLTransform
from hwp5.xmlmodel import Hwp5File

OutputFormat = Literal["txt", "html", "markdown", "odt"]


@dataclass
class WorkerTask:
    """워커에게 전달되는 작업"""

    task_id: int
    file_path: str
    output_format: OutputFormat


@dataclass
class WorkerResult:
    """워커가 반환하는 결과"""

    task_id: int
    success: bool
    content: str | bytes | None = None
    # HTML 변환 시 추가 데이터
    css_content: str | None = None
    bindata: dict[str, bytes] | None = None
    error: str | None = None


def _convert_to_html_dir(
    file_path: Path, temp_dir: Path
) -> tuple[str, str, dict[str, bytes]]:
    """HWP를 HTML 디렉터리 구조로 변환 (pyhwp 직접 호출)

    Returns:
        tuple[xhtml_content, css_content, bindata]
    """
    output_dir = temp_dir / file_path.stem
    output_dir.mkdir(parents=True, exist_ok=True)

    hwp5file = Hwp5File(str(file_path))
    try:
        transform = HTMLTransform()
        transform.transform_hwp5_to_dir(hwp5file, str(output_dir))

        xhtml_file = output_dir / "index.xhtml"
        css_file = output_dir / "styles.css"

        if not xhtml_file.exists():
            raise RuntimeError(
                f"HTML 변환 실패: 결과 파일이 생성되지 않음 - {file_path.name}"
            )

        xhtml_content = xhtml_file.read_text(encoding="utf-8")
        css_content = css_file.read_text(encoding="utf-8") if css_file.exists() else ""

        # bindata 디렉터리 읽기
        bindata: dict[str, bytes] = {}
        bindata_dir = output_dir / "bindata"
        if bindata_dir.exists() and bindata_dir.is_dir():
            for file in bindata_dir.iterdir():
                # pyhwp(hwp5html)는 bindata에 파일만 생성하고 서브디렉터리는 생성하지 않음.
                # is_file() 체크는 미래 변경이나 파일시스템 이상에 대비한 방어 코드.
                if file.is_file():  # pragma: no branch
                    bindata[file.name] = file.read_bytes()

        return xhtml_content, css_content, bindata
    finally:
        hwp5file.wrapped.close()


def _convert_to_odt(file_path: Path, temp_dir: Path) -> bytes:
    """HWP를 ODT로 변환 (hwp5odt CLI 사용 - 내부 API가 복잡하여 CLI 유지)"""
    output_file = temp_dir / f"{file_path.stem}.odt"

    command = ["hwp5odt", f"--output={output_file}", str(file_path)]
    result = subprocess.run(
        command,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(f"ODT 변환 실패: {file_path.name}\n{result.stderr}")

    if not output_file.exists():
        raise RuntimeError(
            f"ODT 변환 실패: 결과 파일이 생성되지 않음 - {file_path.name}"
        )

    return output_file.read_bytes()


def _html_to_text(html_content: str) -> str:
    """HTML을 텍스트로 변환"""
    import html2text

    converter = html2text.HTML2Text()
    converter.ignore_links = True
    converter.ignore_images = True
    converter.ignore_emphasis = True
    converter.body_width = 0  # 줄바꿈 비활성화

    return converter.handle(html_content).strip()


def _html_to_markdown(html_content: str) -> str:
    """HTML을 Markdown으로 변환"""
    from html_to_markdown import convert

    return convert(html_content).strip()


def worker_main(input_queue: Queue, output_queue: Queue) -> None:
    """
    워커 프로세스 메인 루프

    input_queue에서 작업을 받아 처리하고 output_queue로 결과를 전송합니다.
    None을 받으면 종료합니다.

    Args:
        input_queue: 작업을 받는 큐
        output_queue: 결과를 전송하는 큐
    """
    while True:
        task: WorkerTask | None = input_queue.get()

        # 종료 신호
        if task is None:
            break

        temp_dir = Path(tempfile.mkdtemp())
        try:
            file_path = Path(task.file_path)

            if task.output_format == "html":
                xhtml, css, bindata = _convert_to_html_dir(file_path, temp_dir)
                output_queue.put(
                    WorkerResult(
                        task_id=task.task_id,
                        success=True,
                        content=xhtml,
                        css_content=css,
                        bindata=bindata,
                    )
                )
            elif task.output_format == "txt":
                xhtml, _, _ = _convert_to_html_dir(file_path, temp_dir)
                content = _html_to_text(xhtml)
                output_queue.put(
                    WorkerResult(
                        task_id=task.task_id,
                        success=True,
                        content=content,
                    )
                )
            elif task.output_format == "markdown":
                xhtml, _, _ = _convert_to_html_dir(file_path, temp_dir)
                content = _html_to_markdown(xhtml)
                output_queue.put(
                    WorkerResult(
                        task_id=task.task_id,
                        success=True,
                        content=content,
                    )
                )
            elif task.output_format == "odt":
                content = _convert_to_odt(file_path, temp_dir)
                output_queue.put(
                    WorkerResult(
                        task_id=task.task_id,
                        success=True,
                        content=content,
                    )
                )
            else:
                raise ValueError(f"지원하지 않는 포맷: {task.output_format}")

        except Exception as e:
            output_queue.put(
                WorkerResult(
                    task_id=task.task_id,
                    success=False,
                    error=str(e),
                )
            )

        finally:
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
