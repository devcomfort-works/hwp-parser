"""
BentoML 서비스 설정

환경변수 또는 .env 파일로 설정을 관리합니다.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


def _load_dotenv() -> None:
    """프로젝트 루트의 .env 파일 로드 (python-dotenv 없이)"""
    # 프로젝트 루트 찾기 (pyproject.toml 기준)
    current = Path(__file__).resolve()
    for parent in current.parents:
        env_file = parent / ".env"
        if env_file.exists():
            _parse_env_file(env_file)
            break
        # pyproject.toml이 있으면 프로젝트 루트로 간주하고 탐색 중단
        if (parent / "pyproject.toml").exists():
            break


def _parse_env_file(env_path: Path) -> None:
    """간단한 .env 파일 파서"""
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            # 빈 줄, 주석 무시
            if not line or line.startswith("#"):
                continue
            # KEY=VALUE 파싱
            if "=" in line:
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip()
                # 따옴표 제거
                if (value.startswith('"') and value.endswith('"')) or (
                    value.startswith("'") and value.endswith("'")
                ):
                    value = value[1:-1]
                # 환경변수가 이미 설정되어 있으면 덮어쓰지 않음
                if key not in os.environ:
                    os.environ[key] = value


# .env 파일 로드
_load_dotenv()


def _get_int(key: str, default: int) -> int:
    """환경변수에서 정수 값 가져오기"""
    if not isinstance(default, int):
        raise TypeError(f"default must be int, got {type(default).__name__}")
    value = os.environ.get(key)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _get_float(key: str, default: float) -> float:
    """환경변수에서 실수 값 가져오기"""
    if not isinstance(default, (int, float)):
        raise TypeError(f"default must be float, got {type(default).__name__}")
    value = os.environ.get(key)
    if value is None:
        return float(default)
    try:
        return float(value)
    except ValueError:
        return float(default)


def _get_str(key: str, default: str) -> str:
    """환경변수에서 문자열 값 가져오기"""
    if not isinstance(default, str):
        raise TypeError(f"default must be str, got {type(default).__name__}")
    return os.environ.get(key, default)


def _get_bool(key: str, default: bool) -> bool:
    """환경변수에서 불리언 값 가져오기"""
    if not isinstance(default, bool):
        raise TypeError(f"default must be bool, got {type(default).__name__}")
    value = os.environ.get(key)
    if value is None:
        return default
    return value.lower() in ("true", "1", "yes", "on")


def _get_list(key: str, default: list[str]) -> list[str]:
    """환경변수에서 콤마로 구분된 리스트 가져오기"""
    if not isinstance(default, list):
        raise TypeError(f"default must be list, got {type(default).__name__}")
    value = os.environ.get(key)
    if value is None:
        return default
    return [item.strip() for item in value.split(",") if item.strip()]


@dataclass(frozen=True)
class ServiceConfig:
    """서비스 설정"""

    # 서비스 이름
    name: str = _get_str("HWP_SERVICE_NAME", "hwp-parser")

    # 워커 수 (프로세스 병렬화)
    workers: int = _get_int("HWP_SERVICE_WORKERS", 1)

    # 요청 타임아웃 (초, 실수 허용)
    timeout: float = _get_float("HWP_SERVICE_TIMEOUT", 300.0)

    # 최대 동시 요청 수
    max_concurrency: int = _get_int("HWP_SERVICE_MAX_CONCURRENCY", 50)

    # HTTP 서버 설정
    port: int = _get_int("HWP_SERVICE_PORT", 3000)

    # CORS 설정
    cors_enabled: bool = _get_bool("HWP_SERVICE_CORS_ENABLED", False)
    cors_origins: list[str] = field(
        default_factory=lambda: _get_list("HWP_SERVICE_CORS_ORIGINS", ["*"])
    )


# 전역 설정 인스턴스
config = ServiceConfig()
