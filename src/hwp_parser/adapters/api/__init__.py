"""
API Adapter - HWP 파일 변환 REST API 서비스

BentoML을 사용하여 HWP 파일 변환 기능을 REST API로 제공합니다.

설치:
    pip install hwp-parser[bentoml]

Usage:
    # 서비스 실행
    rye run serve

    # 또는 직접 실행
    bentoml serve hwp_parser.adapters.api:HWPService

    # API 호출 예시
    curl -X POST http://localhost:3000/convert/markdown \\
        -F "file=@document.hwp"
"""

from hwp_parser.adapters.api.service import HWPService


def serve() -> None:
    """BentoML 서버 실행"""
    import subprocess
    import sys

    subprocess.run(
        [
            sys.executable,
            "-m",
            "bentoml",
            "serve",
            "hwp_parser.adapters.api:HWPService",
        ],
        check=True,
    )


__all__ = ["HWPService", "serve"]
