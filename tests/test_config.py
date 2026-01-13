"""
설정 모듈 테스트
"""

from __future__ import annotations

import os
from unittest import mock


class TestConfigLoading:
    """설정 로드 테스트"""

    def test_default_config_values(self) -> None:
        """기본 설정 값 확인 (헬퍼 함수 테스트)"""
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
        """설정 인스턴스 생성 확인"""
        from hwp_parser.adapters.api.config import config

        # 인스턴스가 생성되었는지만 확인 (값은 환경변수에 따라 다를 수 있음)
        assert config.name is not None
        assert config.workers >= 1
        assert config.timeout > 0
        assert config.port > 0

    def test_config_from_env(self) -> None:
        """환경변수에서 설정 로드"""
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


class TestConfigHelpers:
    """설정 헬퍼 함수 테스트"""

    def test_get_int_with_invalid_value(self) -> None:
        """잘못된 정수 값 처리"""
        from hwp_parser.adapters.api.config import _get_int

        with mock.patch.dict(os.environ, {"TEST_INT": "not_a_number"}):
            result = _get_int("TEST_INT", 42)
            assert result == 42  # 기본값 반환

    def test_get_bool_variations(self) -> None:
        """다양한 불리언 값 처리"""
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
        """리스트 값 처리"""
        from hwp_parser.adapters.api.config import _get_list

        with mock.patch.dict(
            os.environ, {"TEST_LIST": "http://localhost,https://example.com"}
        ):
            result = _get_list("TEST_LIST", ["*"])
            assert result == ["http://localhost", "https://example.com"]

    def test_get_list_with_spaces(self) -> None:
        """공백 포함 리스트 처리"""
        from hwp_parser.adapters.api.config import _get_list

        with mock.patch.dict(
            os.environ, {"TEST_LIST": " http://localhost , https://example.com "}
        ):
            result = _get_list("TEST_LIST", ["*"])
            assert result == ["http://localhost", "https://example.com"]

    def test_get_list_empty(self) -> None:
        """빈 리스트 처리"""
        from hwp_parser.adapters.api.config import _get_list

        with mock.patch.dict(os.environ, {"TEST_LIST": ""}):
            result = _get_list("TEST_LIST", ["default"])
            assert result == []
