"""
설정 모듈 테스트
"""

from __future__ import annotations

import os
from pathlib import Path
from unittest import mock


# === 핵심 케이스 ===
class TestConfigLoading:
    """설정 로드 테스트"""

    def test_default_config_values(self) -> None:
        """기본 설정 값 확인.

        Notes
        -----
        - 목적: 헬퍼 함수가 기본값을 반환하는지 검증.
        - 로직: 미설정 환경변수에 대해 반환값 비교.
        - 데이터: 하드코딩된 기본값.
        """
        from hwp_parser.adapters.api.config import (
            _get_bool,
            _get_int,
            _get_str,
        )

        # 설정되지 않은 환경변수에서 기본값 반환 확인
        assert _get_str("__NONEXISTENT_VAR__", "default") == "default"
        assert _get_int("__NONEXISTENT_VAR__", 42) == 42
        assert _get_bool("__NONEXISTENT_VAR__", True) is True
        assert _get_bool("__NONEXISTENT_VAR__", False) is False

    def test_config_instance_created(self) -> None:
        """설정 인스턴스 생성 확인.

        Notes
        -----
        - 목적: config 인스턴스가 생성되었는지 확인.
        - 로직: 필드 기본 범위 검사.
        - 데이터: 환경변수에 따라 달라질 수 있음.
        """
        from hwp_parser.adapters.api.config import config

        # 인스턴스가 생성되었는지만 확인 (값은 환경변수에 따라 다를 수 있음)
        assert config.name is not None
        assert config.workers >= 1
        assert config.timeout > 0
        assert config.port > 0

    def test_config_from_env(self) -> None:
        """환경변수에서 설정 로드 검증.

        Notes
        -----
        - 목적: 환경변수 값이 헬퍼 함수에 반영되는지 확인.
        - 로직: mock.patch.dict로 환경변수 주입 후 반환값 비교.
        - 데이터: 테스트용 환경변수 값.
        """
        with mock.patch.dict(
            os.environ,
            {
                "HWP_SERVICE_NAME": "test-service",
                "HWP_SERVICE_WORKERS": "4",
                "HWP_SERVICE_TIMEOUT": "600",
                "HWP_SERVICE_PORT": "8080",
                "HWP_SERVICE_CORS_ENABLED": "true",
            },
        ):
            # 환경변수 설정 후 헬퍼 함수 직접 테스트
            from hwp_parser.adapters.api.config import (
                _get_bool,
                _get_int,
                _get_str,
            )

            assert _get_str("HWP_SERVICE_NAME", "default") == "test-service"
            assert _get_int("HWP_SERVICE_WORKERS", 1) == 4
            assert _get_int("HWP_SERVICE_TIMEOUT", 300) == 600
            assert _get_int("HWP_SERVICE_PORT", 3000) == 8080
            assert _get_bool("HWP_SERVICE_CORS_ENABLED", False) is True


# === 에지 케이스 ===
class TestConfigHelpers:
    """설정 헬퍼 함수 테스트"""

    def test_get_int_with_invalid_value(self) -> None:
        """잘못된 정수 값 처리 검증.

        Notes
        -----
        - 목적: 숫자 파싱 실패 시 기본값 반환 확인.
        - 로직: 잘못된 값 설정 후 반환값 비교.
        - 데이터: TEST_INT=not_a_number.
        """
        from hwp_parser.adapters.api.config import _get_int

        with mock.patch.dict(os.environ, {"TEST_INT": "not_a_number"}):
            result = _get_int("TEST_INT", 42)
            assert result == 42  # 기본값 반환

    def test_get_bool_variations(self) -> None:
        """다양한 불리언 값 처리 검증.

        Notes
        -----
        - 목적: truthy/falsey 문자열 처리 확인.
        - 로직: 다양한 값으로 _get_bool 결과 비교.
        - 데이터: true_values/false_values 리스트.
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
        """리스트 값 처리 검증.

        Notes
        -----
        - 목적: 콤마 분리 리스트 파싱 확인.
        - 로직: TEST_LIST 설정 후 반환값 비교.
        - 데이터: "http://localhost,https://example.com".
        """
        from hwp_parser.adapters.api.config import _get_list

        with mock.patch.dict(
            os.environ, {"TEST_LIST": "http://localhost,https://example.com"}
        ):
            result = _get_list("TEST_LIST", ["*"])
            assert result == ["http://localhost", "https://example.com"]

    def test_get_list_with_spaces(self) -> None:
        """공백 포함 리스트 처리 검증.

        Notes
        -----
        - 목적: 공백이 포함된 리스트 파싱 확인.
        - 로직: 공백 포함 값 설정 후 반환값 비교.
        - 데이터: " http://localhost , https://example.com ".
        """
        from hwp_parser.adapters.api.config import _get_list

        with mock.patch.dict(
            os.environ, {"TEST_LIST": " http://localhost , https://example.com "}
        ):
            result = _get_list("TEST_LIST", ["*"])
            assert result == ["http://localhost", "https://example.com"]

    def test_get_list_empty(self) -> None:
        """빈 리스트 처리 검증.

        Notes
        -----
        - 목적: 빈 문자열 입력 시 빈 리스트 반환 확인.
        - 로직: TEST_LIST="" 설정 후 반환값 비교.
        - 데이터: 빈 문자열.
        """
        from hwp_parser.adapters.api.config import _get_list

        with mock.patch.dict(os.environ, {"TEST_LIST": ""}):
            result = _get_list("TEST_LIST", ["default"])
            assert result == []

    def test_get_list_default_when_missing(self) -> None:
        """환경변수 미설정 시 기본값 반환 검증.

        Notes
        -----
        - 목적: _get_list가 default를 반환하는 분기 커버.
        - 로직: 환경변수 미설정 상태에서 호출.
        - 데이터: default 리스트.
        """
        from hwp_parser.adapters.api.config import _get_list

        with mock.patch.dict(os.environ, {}, clear=True):
            result = _get_list("TEST_LIST", ["default"])
            assert result == ["default"]

    def test_load_dotenv_calls_parser(self, monkeypatch) -> None:
        """_load_dotenv이 .env 파서를 호출하는지 검증.

        Notes
        -----
        - 목적: .env 존재 분기 커버.
        - 로직: Path.exists를 조작해 .env 존재로 가정.
        - 데이터: 가짜 .env 경로.
        """
        from hwp_parser.adapters.api import config as cfg

        called: dict[str, bool] = {"called": False}

        def _fake_parse(_path):
            called["called"] = True

        def _fake_exists(self) -> bool:  # type: ignore[override]
            return self.name == ".env"

        monkeypatch.setattr(cfg, "_parse_env_file", _fake_parse)
        monkeypatch.setattr(Path, "exists", _fake_exists, raising=False)

        cfg._load_dotenv()
        assert called["called"] is True

    def test_parse_env_file(self, tmp_path) -> None:
        """.env 파서 동작 검증.

        Notes
        -----
        - 목적: _parse_env_file이 주석/공백/따옴표를 처리하는지 확인.
        - 로직: 임시 .env 파일 작성 후 환경변수 반영 여부 확인.
        - 데이터: 임시 파일의 KEY=VALUE 라인.
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
        """'=' 없는 라인 무시 분기 검증.

        Notes
        -----
        - 목적: KEY=VALUE가 아닌 라인 스킵 분기 커버.
        - 로직: 잘못된 라인 포함 후 환경변수 미설정 확인.
        - 데이터: INVALIDLINE.
        """
        from hwp_parser.adapters.api.config import _parse_env_file

        env_file = tmp_path / ".env"
        env_file.write_text("INVALIDLINE\n", encoding="utf-8")

        with mock.patch.dict(os.environ, {}, clear=True):
            _parse_env_file(env_file)
            assert "INVALIDLINE" not in os.environ

    def test_parse_env_file_preserves_existing(self, tmp_path: Path) -> None:
        """기존 환경변수 값 보존 검증.

        Notes
        -----
        - 목적: 이미 설정된 키는 덮어쓰지 않는 분기 커버.
        - 로직: 기존 값 설정 후 .env 파싱 결과 확인.
        - 데이터: TEST_ENV_EXISTING.
        """
        from hwp_parser.adapters.api.config import _parse_env_file

        env_file = tmp_path / ".env"
        env_file.write_text("TEST_ENV_EXISTING=override", encoding="utf-8")

        with mock.patch.dict(os.environ, {"TEST_ENV_EXISTING": "original"}, clear=True):
            _parse_env_file(env_file)
            assert os.environ["TEST_ENV_EXISTING"] == "original"

    def test_load_dotenv_skips_when_no_env(self, monkeypatch) -> None:
        """.env 파일이 없을 때 파서 미호출 검증.

        Notes
        -----
        - 목적: pyproject.toml 발견 시 break 분기 커버.
        - 로직: .env는 False, pyproject.toml은 True로 설정.
        - 데이터: 없음.
        """
        from hwp_parser.adapters.api import config as cfg

        called: dict[str, bool] = {"called": False}

        def _fake_parse(_path):
            called["called"] = True

        def _fake_exists(self) -> bool:  # type: ignore[override]
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
        """pyproject 분기에서 .env 발견 경로 검증.

        Notes
        -----
        - 목적: 2차 env_file.exists True 분기 커버.
        - 로직: .env exists 첫 호출 False, 두 번째 True로 조작.
        - 데이터: 없음.
        """
        from hwp_parser.adapters.api import config as cfg

        called: dict[str, bool] = {"called": False}
        counter = {"env_calls": 0}

        def _fake_parse(_path):
            called["called"] = True

        def _fake_exists(self) -> bool:  # type: ignore[override]
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
        """parents가 비어있는 경우 루프 종료 분기 검증.

        Notes
        -----
        - 목적: for-loop 미진입 분기 커버.
        - 로직: Path.resolve()가 parents=[]인 객체 반환.
        - 데이터: 없음.
        """
        from hwp_parser.adapters.api import config as cfg

        class _DummyPath:
            parents: list[Path] = []

        monkeypatch.setattr(Path, "resolve", lambda self: _DummyPath())

        cfg._load_dotenv()
