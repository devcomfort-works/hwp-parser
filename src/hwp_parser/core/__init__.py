"""
HWP Parser Core - HWP 파싱 로직

pyhwp를 사용하여 HWP 파일을 다양한 포맷으로 변환합니다.

지원 포맷:
- txt: 순수 텍스트 (HTML → html2text 파이프라인)
- html: XHTML 형식
- markdown: Markdown 형식 (HTML → markdown 파이프라인)
- odt: Open Document Text 형식

변환 모드:
- num_workers=None (기본): subprocess 기반 변환
- num_workers>0: Persistent Worker 사용 (pyhwp 직접 호출, ~64% 빠름)

Usage:
    from pathlib import Path
    from hwp_parser.core import HWPConverter

    # 방식 1: 기본 사용 (subprocess)
    converter = HWPConverter()
    result = converter.to_text(Path("document.hwp"))

    # 방식 2: 고성능 모드 (Worker Pool)
    with HWPConverter(num_workers=4) as converter:
        result = converter.to_markdown("document.hwp")
"""

from hwp_parser.core.converter import ConversionResult, HTMLDirResult, HWPConverter

__all__ = ["HWPConverter", "ConversionResult", "HTMLDirResult"]
