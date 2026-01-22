"""
pytest 공통 fixtures
"""

from __future__ import annotations

from pathlib import Path

import pytest

from hwp_parser.core import HWPConverter

# 테스트 fixtures 디렉토리
FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def converter() -> HWPConverter:
    """HWPConverter 인스턴스"""
    return HWPConverter()


@pytest.fixture
def sample_hwp_file() -> Path:
    """샘플 HWP 파일 (가장 작은 파일)"""
    return FIXTURES_DIR / "_5_문서상태아이콘_ori.hwp"


@pytest.fixture
def hwp_file_with_bindata() -> Path:
    """bindata(이미지)가 포함된 HWP 파일"""
    return FIXTURES_DIR / "_4_문서정보구분[대외문서_협조문_내부기안_보안문서]_ori.hwp"


@pytest.fixture
def all_hwp_files() -> list[Path]:
    """모든 HWP fixture 파일"""
    return list(FIXTURES_DIR.glob("*.hwp"))


@pytest.fixture
def small_hwp_files() -> list[Path]:
    """작은 HWP 파일들 (빠른 테스트용)"""
    files = list(FIXTURES_DIR.glob("*.hwp"))
    # 파일 크기 기준 정렬 후 상위 3개
    return sorted(files, key=lambda f: f.stat().st_size)[:3]


@pytest.fixture
def temp_dir(tmp_path: Path) -> Path:
    """임시 디렉토리"""
    return tmp_path


@pytest.fixture
def nonexistent_file(tmp_path: Path) -> Path:
    """존재하지 않는 파일 경로"""
    return tmp_path / "nonexistent.hwp"


@pytest.fixture
def temp_directory(tmp_path: Path) -> Path:
    """임시 디렉토리 (디렉토리 검증 테스트용)"""
    d = tmp_path / "test_dir"
    d.mkdir()
    return d
