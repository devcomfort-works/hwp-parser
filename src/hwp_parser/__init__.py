"""
HWP Parser - HWP 파일 파싱 라이브러리

pyhwp를 사용하여 HWP 파일을 다양한 포맷으로 변환하는 라이브러리입니다.

구성:
- core: HWP 파싱 로직 (HWPConverter)
- adapters.llama_index: LlamaIndex BaseReader 어댑터 (선택적)

Usage:
    # Core 사용 (기본)
    from hwp_parser import HWPConverter, ConversionResult

    converter = HWPConverter()
    result = converter.to_markdown("document.hwp")
    print(result.content)

    # 고성능 모드 (Worker Pool)
    with HWPConverter(num_workers=4) as converter:
        result = converter.to_markdown("document.hwp")
        print(result.content)

    # LlamaIndex 어댑터 사용 (llama-index 설치 필요)
    from hwp_parser import HWPReader

    reader = HWPReader()
    documents = reader.load_data("document.hwp")
"""

from typing import TYPE_CHECKING

from hwp_parser.core import ConversionResult, HWPConverter

if TYPE_CHECKING:
    from hwp_parser.adapters.llama_index import HWPReader

__version__ = "0.1.0"

# Lazy imports for optional dependencies
_HWPReader = None


def __getattr__(name: str):
    """Lazy import for optional dependencies."""
    global _HWPReader

    if name == "HWPReader":
        if _HWPReader is None:
            from hwp_parser.adapters.llama_index import HWPReader as _HWPReader
        return _HWPReader

    raise AttributeError(f"module 'hwp_parser' has no attribute '{name}'")


__all__ = [
    # Core (always available)
    "HWPConverter",
    "ConversionResult",
    # LlamaIndex adapter (optional: pip install hwp-parser[llama-index])
    "HWPReader",
]
