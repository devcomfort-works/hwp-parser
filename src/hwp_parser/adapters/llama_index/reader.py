"""
LlamaIndex HWPReader - BaseReader 구현

LlamaIndex의 BaseReader 인터페이스를 구현하여
HWP 파일을 Document 객체로 변환합니다.
"""

from __future__ import annotations

import base64
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal, cast

# 런타임 import
try:
    from llama_index.core.readers.base import BaseReader
    from llama_index.core.schema import Document

    LLAMA_INDEX_AVAILABLE = True
except ImportError:
    LLAMA_INDEX_AVAILABLE = False
    BaseReader = object  # type: ignore[misc, assignment]
    Document = None  # type: ignore[misc, assignment]

from hwp_parser.core import HWPConverter

# TYPE_CHECKING 블록에서 타입 별칭 정의
if TYPE_CHECKING:
    from llama_index.core.schema import Document as DocumentType

    DocumentList = list[DocumentType]
else:
    DocumentList = list

OutputFormat = Literal["txt", "html", "markdown", "odt"]


class HWPReader(BaseReader):  # type: ignore[misc]
    """
    LlamaIndex용 HWP 파일 리더

    pyhwp CLI 도구를 사용하여 HWP 파일을 여러 포맷으로 변환하고
    LlamaIndex Document 객체로 반환합니다.

    지원 포맷:
    - txt: 순수 텍스트
    - html: XHTML 형식
    - markdown: Markdown 형식 (기본값)
    - odt: ODT 형식 (base64 인코딩)

    Example:
        reader = HWPReader()

        # Markdown으로 변환 (기본값)
        docs = reader.load_data(Path("document.hwp"))

        # 텍스트로 변환
        docs = reader.load_data(Path("document.hwp"), output_format="txt")

        # 추가 메타데이터 포함
        docs = reader.load_data(
            Path("document.hwp"),
            extra_info={"category": "manual"}
        )
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        HWPReader 초기화

        Raises:
            ImportError: llama-index-core가 설치되지 않은 경우
        """
        if not LLAMA_INDEX_AVAILABLE:
            raise ImportError(
                "llama-index-core가 필요합니다. "
                "다음 명령으로 설치하세요: pip install hwp-parser[llama-index]"
            )

        super().__init__(*args, **kwargs)
        self._converter = HWPConverter()

    def load_data(
        self,
        file: Path | str,
        extra_info: dict[str, Any] | None = None,
        output_format: OutputFormat = "markdown",
    ) -> DocumentList:
        """
        HWP 파일을 LlamaIndex Document로 변환

        Args:
            file: HWP 파일 경로
            extra_info: Document 메타데이터에 추가할 정보
            output_format: 출력 포맷 (기본값: markdown)

        Returns:
            Document 리스트 (항상 1개)

        Raises:
            ValueError: 지원하지 않는 포맷 또는 디렉토리 경로
            FileNotFoundError: 파일이 존재하지 않는 경우
            RuntimeError: 변환 실패
        """
        if not isinstance(file, Path):
            file = Path(file)

        # Core 변환기로 변환
        result = self._converter.convert(file, output_format)

        # ODT는 바이너리이므로 base64 인코딩
        if result.is_binary:
            content = base64.b64encode(cast(bytes, result.content)).decode("utf-8")
        else:
            content = cast(str, result.content)

        # 메타데이터 구성
        metadata: dict[str, Any] = {
            "file_name": result.source_name,
            "file_path": str(result.source_path.absolute()),
            "format": result.output_format,
            "source": "hwp-parser",
            "conversion_pipeline": result.pipeline,
        }

        if extra_info:
            metadata.update(extra_info)

        document = Document(text=content, metadata=metadata)  # type: ignore[misc]

        return [document]  # type: ignore[return-value]
