"""설정 모듈 테스트."""

from __future__ import annotations

import os
from pathlib import Path
from unittest import mock


# === 핵심 케이스 ===
class TestConfigLoading:
    """설정 로드 테스트."""

    def test_default_config_values(self) -> None:
        """미설정 환경변수 → 기본값 반환.

        Given: 존재하지 않는 환경변수 키
        When: _get_str, _get_int, _get_float, _get_bool 호출
        Then: 각각 지정한 기본값 반환
        """
        from hwp_parser.adapters.api.config import (
            _get_bool,
            _get_float,
            _get_int,
            _get_str,
        )

        assert _get_str("__NONEXISTENT_VAR__", "default") == "default"
        assert _get_int("__NONEXISTENT_VAR__", 42) == 42
        assert _get_float("__NONEXISTENT_VAR__", 3.14) == 3.14
        assert _get_bool("__NONEXISTENT_VAR__", True) is True
        assert _get_bool("__NONEXISTENT_VAR__", False) is False

    def test_config_instance_created(self) -> None:
        """config 인스턴스 정상 생성.

        Given: 모듈 임포트
        When: config 인스턴스 접근
        Then: 필수 필드들이 유효한 범위 내 값 보유
        """
        # load config data as an instance.
        from hwp_parser.adapters.api.config import config

        assert config.name is not None  # 서비스 이름
        assert config.workers >= 1  # 한글 변환 시, 병렬화에 사용할 워커 수
        assert config.timeout > 0  # 요청 타임아웃 (초 단위, 실수 허용)
        assert config.port > 0  # HTTP 포트

    def test_config_from_env(self) -> None:
        """환경변수 설정 → 헬퍼 함수 반영.

        Given: HWP_SERVICE_* 환경변수들 설정
        When: _get_str, _get_int, _get_float, _get_bool 호출
        Then: 환경변수 값이 정확히 반환
        """
        with mock.patch.dict(
            os.environ,
            {
                "HWP_SERVICE_NAME": "test-service",
                "HWP_SERVICE_WORKERS": "4",
                "HWP_SERVICE_TIMEOUT": "600.5",
                "HWP_SERVICE_PORT": "8080",
                "HWP_SERVICE_CORS_ENABLED": "true",
            },
        ):
            from hwp_parser.adapters.api.config import (
                _get_bool,
                _get_float,
                _get_int,
                _get_str,
            )

            assert _get_str("HWP_SERVICE_NAME", "default") == "test-service"
            assert _get_int("HWP_SERVICE_WORKERS", 1) == 4
            assert _get_float("HWP_SERVICE_TIMEOUT", 300.0) == 600.5
            assert _get_int("HWP_SERVICE_PORT", 3000) == 8080
            assert _get_bool("HWP_SERVICE_CORS_ENABLED", False) is True


# === 에지 케이스 ===
class TestConfigHelpers:
    """설정 헬퍼 함수 테스트."""

    def test_get_int_with_invalid_value(self) -> None:
        """파싱 불가 정수 → 기본값 fallback.

        Given: TEST_INT="not_a_number" (파싱 불가)
        When: _get_int("TEST_INT", 42) 호출
        Then: 예외 없이 기본값 42 반환

        서비스 안정성을 위해 설정 오류 시 fallback 전략 사용.
        """
        from hwp_parser.adapters.api.config import _get_int

        with mock.patch.dict(os.environ, {"TEST_INT": "not_a_number"}):
            result = _get_int("TEST_INT", 42)
            assert result == 42

    def test_get_float_with_valid_values(self) -> None:
        """실수 문자열 → float 변환.

        Given: TEST_FLOAT="3.14" 또는 "42"
        When: _get_float 호출
        Then: 실수로 파싱된 값 반환

        정수 문자열도 실수로 변환 가능.
        """
        from hwp_parser.adapters.api.config import _get_float

        with mock.patch.dict(os.environ, {"TEST_FLOAT": "3.14"}):
            assert _get_float("TEST_FLOAT", 0.0) == 3.14

        with mock.patch.dict(os.environ, {"TEST_FLOAT": "42"}):
            assert _get_float("TEST_FLOAT", 0.0) == 42.0

    def test_get_float_with_invalid_value(self) -> None:
        """파싱 불가 실수 → 기본값 fallback.

        Given: TEST_FLOAT="not_a_number" (파싱 불가)
        When: _get_float("TEST_FLOAT", 3.14) 호출
        Then: 예외 없이 기본값 3.14 반환
        """
        from hwp_parser.adapters.api.config import _get_float

        with mock.patch.dict(os.environ, {"TEST_FLOAT": "not_a_number"}):
            result = _get_float("TEST_FLOAT", 3.14)
            assert result == 3.14

    def test_get_bool_variations(self) -> None:
        """다양한 truthy/falsy 문자열 → 불리언 변환.

        Given: "true", "1", "yes", "on" 등 truthy 값
               "false", "0", "no", "off", "" 등 falsy 값
        When: _get_bool 호출
        Then: 각각 True/False 반환

        대소문자 무관하게 일반적인 truthy/falsy 표현 모두 지원.
        """
        from hwp_parser.adapters.api.config import _get_bool

        true_values = ["true", "True", "TRUE", "1", "yes", "YES", "on", "ON"]
        false_values = ["false", "False", "0", "no", "off", ""]

        for val in true_values:
            with mock.patch.dict(os.environ, {"TEST_BOOL": val}):
                assert _get_bool("TEST_BOOL", False) is True, f"Failed for: {val}"

        for val in false_values:
            with mock.patch.dict(os.environ, {"TEST_BOOL": val}):
                assert _get_bool("TEST_BOOL", True) is False, f"Failed for: {val}"

    def test_get_list(self) -> None:
        """콤마 구분 문자열 → 리스트 파싱.

        Given: TEST_LIST="http://localhost,https://example.com"
        When: _get_list 호출
        Then: ["http://localhost", "https://example.com"] 반환
        """
        from hwp_parser.adapters.api.config import _get_list

        with mock.patch.dict(
            os.environ, {"TEST_LIST": "http://localhost,https://example.com"}
        ):
            result = _get_list("TEST_LIST", ["*"])
            assert result == ["http://localhost", "https://example.com"]

    def test_get_list_with_spaces(self) -> None:
        """공백 포함 리스트 → trim 후 파싱.

        Given: TEST_LIST=" http://localhost , https://example.com "
        When: _get_list 호출
        Then: 공백 제거된 리스트 반환

        사용자 입력 실수(공백)를 자동 보정.
        """
        from hwp_parser.adapters.api.config import _get_list

        with mock.patch.dict(
            os.environ, {"TEST_LIST": " http://localhost , https://example.com "}
        ):
            result = _get_list("TEST_LIST", ["*"])
            assert result == ["http://localhost", "https://example.com"]

    def test_get_list_empty(self) -> None:
        """빈 문자열 → 빈 리스트.

        Given: TEST_LIST=""
        When: _get_list 호출
        Then: [] 반환 (기본값 무시)

        명시적 빈 값은 "비어있음"으로 해석.
        """
        from hwp_parser.adapters.api.config import _get_list

        with mock.patch.dict(os.environ, {"TEST_LIST": ""}):
            result = _get_list("TEST_LIST", ["default"])
            assert result == []

    def test_get_list_default_when_missing(self) -> None:
        """환경변수 미설정 → 기본값 반환.

        Given: TEST_LIST 환경변수 미설정
        When: _get_list("TEST_LIST", ["default"]) 호출
        Then: ["default"] 반환
        """
        from hwp_parser.adapters.api.config import _get_list

        with mock.patch.dict(os.environ, {}, clear=True):
            result = _get_list("TEST_LIST", ["default"])
            assert result == ["default"]

    def test_load_dotenv_calls_parser(self, monkeypatch) -> None:
        """.env 파일 존재 → 파서 호출.

        Given: .env 파일이 존재하는 상황 (mocked)
        When: _load_dotenv() 호출
        Then: _parse_env_file 함수 호출됨
        """
        from hwp_parser.adapters.api import config as cfg

        called: dict[str, bool] = {"called": False}

        def _fake_parse(_path):
            called["called"] = True

        def _fake_exists(self) -> bool:
            return self.name == ".env"

        monkeypatch.setattr(cfg, "_parse_env_file", _fake_parse)
        monkeypatch.setattr(Path, "exists", _fake_exists, raising=False)

        cfg._load_dotenv()
        assert called["called"] is True

    def test_parse_env_file(self, tmp_path) -> None:
        """.env 파일 파싱 → 환경변수 설정.

        Given: 주석, 따옴표, 공백이 포함된 .env 파일
        When: _parse_env_file 호출
        Then: 유효한 KEY=VALUE만 환경변수에 반영

        주석(#)은 무시, 따옴표는 제거, 공백은 trim.
        """
        from hwp_parser.adapters.api.config import _parse_env_file

        env_file = tmp_path / ".env"
        env_file.write_text(
            """
            # comment
            TEST_ENV_SIMPLE=value
            TEST_ENV_QUOTED="quoted value"
            TEST_ENV_SPACES = spaced
            """,
            encoding="utf-8",
        )

        with mock.patch.dict(os.environ, {}, clear=True):
            _parse_env_file(env_file)
            assert os.environ["TEST_ENV_SIMPLE"] == "value"
            assert os.environ["TEST_ENV_QUOTED"] == "quoted value"
            assert os.environ["TEST_ENV_SPACES"] == "spaced"

    def test_parse_env_file_ignores_invalid_line(self, tmp_path: Path) -> None:
        """'=' 없는 라인 → 무시.

        Given: .env 파일에 "INVALIDLINE" (= 없음)
        When: _parse_env_file 호출
        Then: 해당 라인 무시, 환경변수 미설정

        잘못된 형식은 조용히 스킵하여 서비스 중단 방지.
        """
        from hwp_parser.adapters.api.config import _parse_env_file

        env_file = tmp_path / ".env"
        env_file.write_text("INVALIDLINE\n", encoding="utf-8")

        with mock.patch.dict(os.environ, {}, clear=True):
            _parse_env_file(env_file)
            assert "INVALIDLINE" not in os.environ

    def test_parse_env_file_preserves_existing(self, tmp_path: Path) -> None:
        """기존 환경변수 → 덮어쓰기 방지.

        Given: TEST_ENV_EXISTING="original" 이미 설정
               .env에 TEST_ENV_EXISTING=override
        When: _parse_env_file 호출
        Then: 기존 값 "original" 유지

        런타임 환경변수가 .env보다 우선.
        """
        from hwp_parser.adapters.api.config import _parse_env_file

        env_file = tmp_path / ".env"
        env_file.write_text("TEST_ENV_EXISTING=override", encoding="utf-8")

        with mock.patch.dict(os.environ, {"TEST_ENV_EXISTING": "original"}, clear=True):
            _parse_env_file(env_file)
            assert os.environ["TEST_ENV_EXISTING"] == "original"

    def test_load_dotenv_skips_when_no_env(self, monkeypatch) -> None:
        """.env 미존재 + pyproject.toml 발견 → 탐색 중단.

        Given: .env 없음, pyproject.toml 존재
        When: _load_dotenv() 호출
        Then: 파서 미호출, 루프 종료

        프로젝트 루트 감지 시 상위 디렉터리 탐색 중단.
        """
        from hwp_parser.adapters.api import config as cfg

        called: dict[str, bool] = {"called": False}

        def _fake_parse(_path):
            called["called"] = True

        def _fake_exists(self) -> bool:
            if self.name == ".env":
                return False
            if self.name == "pyproject.toml":
                return True
            return False

        monkeypatch.setattr(cfg, "_parse_env_file", _fake_parse)
        monkeypatch.setattr(Path, "exists", _fake_exists, raising=False)

        cfg._load_dotenv()
        assert called["called"] is False

    def test_load_dotenv_env_found_in_pyproject_branch(self, monkeypatch) -> None:
        """pyproject.toml 디렉터리에서 .env 발견 → 파서 호출.

        Given: 첫 번째 .env 체크 False, pyproject.toml True,
               이후 .env 체크 True
        When: _load_dotenv() 호출
        Then: 파서 호출됨

        pyproject.toml 옆의 .env 파일도 탐지.
        """
        from hwp_parser.adapters.api import config as cfg

        called: dict[str, bool] = {"called": False}
        counter = {"env_calls": 0}

        def _fake_parse(_path):
            called["called"] = True

        def _fake_exists(self) -> bool:
            if self.name == ".env":
                counter["env_calls"] += 1
                return counter["env_calls"] > 1
            if self.name == "pyproject.toml":
                return True
            return False

        monkeypatch.setattr(cfg, "_parse_env_file", _fake_parse)
        monkeypatch.setattr(Path, "exists", _fake_exists, raising=False)

        cfg._load_dotenv()
        assert called["called"] is True

    def test_load_dotenv_no_parents(self, monkeypatch) -> None:
        """parents 비어있음 → 루프 미진입.

        Given: Path.resolve()가 parents=[]인 객체 반환
        When: _load_dotenv() 호출
        Then: for-loop 미진입, 정상 종료

        루트 디렉터리 등 특수 케이스 처리.
        """
        from hwp_parser.adapters.api import config as cfg

        class _DummyPath:
            parents: list[Path] = []

        monkeypatch.setattr(Path, "resolve", lambda self: _DummyPath())

        cfg._load_dotenv()
