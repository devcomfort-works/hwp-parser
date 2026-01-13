"""
HWP Parser Core - 순수 HWP 파싱 로직

pyhwp CLI 도구를 래핑하여 HWP 파일을 다양한 포맷으로 변환합니다.
외부 프레임워크 의존성 없이 독립적으로 사용할 수 있습니다.

지원 포맷:
- txt: 순수 텍스트 (HTML → html2text 파이프라인)
- html: XHTML 형식
- markdown: Markdown 형식 (HTML → markdown 파이프라인)
- odt: Open Document Text 형식

Usage:
    from pathlib import Path
    from hwp_parser.core import HWPConverter

    converter = HWPConverter()

    # 텍스트로 변환
    result = converter.to_text(Path("document.hwp"))
    print(result.content)

    # HTML로 변환
    result = converter.to_html(Path("document.hwp"))

    # Markdown으로 변환
    result = converter.to_markdown(Path("document.hwp"))
"""

from hwp_parser.core.converter import HWPConverter, ConversionResult

__all__ = ["HWPConverter", "ConversionResult"]
