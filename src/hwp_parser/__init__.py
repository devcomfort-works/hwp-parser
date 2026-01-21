"""
HWP Parser - HWP 파일 파싱 라이브러리

pyhwp CLI 도구를 사용하여 HWP 파일을 다양한 포맷으로 변환하는 라이브러리입니다.

구성:
- core: 순수 HWP 파싱 로직 (pyhwp CLI 래퍼)
- adapters.llama_index: LlamaIndex BaseReader 어댑터 (선택적)
- adapters.api: BentoML REST API 서비스 (선택적)

Usage:
    # Core 사용 (기본)
    from hwp_parser import HWPConverter, ConversionResult

    converter = HWPConverter()
    result = converter.to_markdown("document.hwp")
    print(result.content)

    # LlamaIndex 어댑터 사용 (llama-index 설치 필요)
    from hwp_parser import HWPReader

    reader = HWPReader()
    documents = reader.load_data("document.hwp")

    # REST API 서버 실행 (bentoml 설치 필요)
    from hwp_parser import HWPService, serve
    serve()  # 또는 bentoml serve hwp_parser:HWPService
"""

from typing import TYPE_CHECKING

from hwp_parser.core import ConversionResult, HWPConverter

if TYPE_CHECKING:
    from hwp_parser.adapters.api import HWPService, serve
    from hwp_parser.adapters.llama_index import HWPReader

__version__ = "0.1.0"

# Lazy imports for optional dependencies
_HWPReader = None
_HWPService = None
_serve = None


def __getattr__(name: str):
    """Lazy import for optional dependencies."""
    global _HWPReader, _HWPService, _serve

    if name == "HWPReader":
        if _HWPReader is None:
            from hwp_parser.adapters.llama_index import HWPReader as _HWPReader
        return _HWPReader

    if name == "HWPService":
        if _HWPService is None:
            from hwp_parser.adapters.api import HWPService as _HWPService
        return _HWPService

    if name == "serve":
        if _serve is None:
            from hwp_parser.adapters.api import serve as _serve
        return _serve

    raise AttributeError(f"module 'hwp_parser' has no attribute '{name}'")


__all__ = [
    # Core (always available)
    "HWPConverter",
    "ConversionResult",
    # LlamaIndex adapter (optional: pip install hwp-parser[llama-index])
    "HWPReader",
    # API adapter (optional: pip install hwp-parser[bentoml])
    "HWPService",
    "serve",
]
