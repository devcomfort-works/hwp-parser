"""
LlamaIndex Adapter - HWP 파일을 LlamaIndex Document로 변환

LlamaIndex의 BaseReader 인터페이스를 구현하여
HWP 파일을 LlamaIndex 생태계에서 사용할 수 있게 합니다.

설치:
    pip install hwp-parser[llama-index]

Usage:
    from pathlib import Path
    from hwp_parser.adapters.llama_index import HWPReader

    reader = HWPReader()

    # Markdown으로 변환 (기본값)
    documents = reader.load_data(Path("document.hwp"))

    # 텍스트로 변환
    documents = reader.load_data(Path("document.hwp"), output_format="txt")

    # 추가 메타데이터 포함
    documents = reader.load_data(
        Path("document.hwp"),
        extra_info={"category": "regulation"}
    )
"""

from hwp_parser.adapters.llama_index.reader import HWPReader

__all__ = ["HWPReader"]
