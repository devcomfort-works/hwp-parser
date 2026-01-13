"""
HWP Parser - HWP 파일 파싱 라이브러리

pyhwp CLI 도구를 사용하여 HWP 파일을 다양한 포맷으로 변환하는 라이브러리입니다.

구성:
- core: 순수 HWP 파싱 로직 (pyhwp CLI 래퍼)
- adapters.llama_index: LlamaIndex BaseReader 어댑터 (선택적)

Usage:
    # Core 사용
    from hwp_parser.core import HWPConverter

    converter = HWPConverter()
    text = converter.to_text(Path("document.hwp"))
    html = converter.to_html(Path("document.hwp"))
    markdown = converter.to_markdown(Path("document.hwp"))

    # LlamaIndex 어댑터 사용 (llama-index 설치 필요)
    from hwp_parser.adapters.llama_index import HWPReader

    reader = HWPReader()
    documents = reader.load_data(Path("document.hwp"))
"""

from hwp_parser.core import HWPConverter, ConversionResult

__version__ = "0.1.0"
__all__ = ["HWPConverter", "ConversionResult"]
