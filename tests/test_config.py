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


class TestLoadDotenv:
    """_load_dotenv 테스트 (임시 파일 기반).

    테스트 전략:
        1. tmp_path에 실제 디렉터리 구조와 .env 파일 생성
        2. cfg.__file__을 tmp_path 내 경로로 변경 (탐색 시작점 조작)
        3. _load_dotenv() 실행 후 환경변수가 실제로 설정되었는지 확인

    이 방식의 장점:
        - 실제 파일 I/O를 테스트하므로 더 현실적
        - 복잡한 모킹 없이 _load_dotenv의 전체 흐름 검증 가능

    _load_dotenv() 동작 원리:
        1. Path(__file__).resolve().parents 를 순회하며
        2. 각 디렉터리에서 .env 파일이 존재하는지 확인
        3. 존재하면 _parse_env_file()을 호출하여 환경변수 로드
        4. pyproject.toml을 발견하면 프로젝트 루트로 인식하고 탐색 중단
    """

    def test_load_dotenv_loads_env_file(self, tmp_path, monkeypatch) -> None:
        """.env 파일 존재 → 환경변수 로드.

        Given: tmp_path에 .env 파일 존재 (TEST_VAR=hello)
        When: _load_dotenv() 호출 (탐색 시작점을 tmp_path로 변경)
        Then: 환경변수 TEST_VAR=hello가 설정됨

        테스트 구조::

            tmp_path/
            └── .env  (TEST_LOAD_DOTENV_VAR=hello)

        왜 __file__을 변경하는가?
            _load_dotenv()는 Path(__file__).resolve().parents를 순회하므로,
            __file__을 tmp_path 내 파일로 변경하면 tmp_path/.env를 찾게 됨.
        """
        from hwp_parser.adapters.api import config as cfg

        env_file = tmp_path / ".env"
        env_file.write_text("TEST_LOAD_DOTENV_VAR=hello\n", encoding="utf-8")

        fake_config_path = tmp_path / "config.py"
        monkeypatch.setattr(cfg, "__file__", str(fake_config_path))

        with mock.patch.dict(os.environ, {}, clear=True):
            cfg._load_dotenv()
            assert os.environ.get("TEST_LOAD_DOTENV_VAR") == "hello"

    def test_load_dotenv_skips_when_no_env(self, tmp_path, monkeypatch) -> None:
        """.env 미존재 → 환경변수 변경 없음.

        Given: tmp_path에 .env 파일 없음, pyproject.toml만 존재
        When: _load_dotenv() 호출
        Then: 환경변수 변경 없음, 에러 없이 종료

        테스트 구조::

            tmp_path/
            ├── pyproject.toml  (탐색 중단점 역할)
            └── src/
                └── config.py  (가상 시작점)

        pyproject.toml이 있으면 프로젝트 루트로 인식하고 탐색 중단.
        .env가 없으므로 환경변수는 변경되지 않음.
        """
        from hwp_parser.adapters.api import config as cfg

        (tmp_path / "pyproject.toml").touch()

        subdir = tmp_path / "src"
        subdir.mkdir()
        fake_config_path = subdir / "config.py"
        monkeypatch.setattr(cfg, "__file__", str(fake_config_path))

        with mock.patch.dict(os.environ, {}, clear=True):
            cfg._load_dotenv()
            assert "TEST_LOAD_DOTENV_VAR" not in os.environ

    def test_load_dotenv_finds_env_at_project_root(self, tmp_path, monkeypatch) -> None:
        """pyproject.toml 옆의 .env 발견 → 환경변수 로드.

        Given: tmp_path에 pyproject.toml과 .env 모두 존재
               하위 디렉터리(src/)에서 탐색 시작
        When: _load_dotenv() 호출
        Then: 상위의 .env가 로드됨

        테스트 구조::

            tmp_path/
            ├── pyproject.toml
            ├── .env  (PROJECT_ROOT_VAR=found)
            └── src/
                └── config.py  (가상 시작점)

        src/config.py 위치에서 시작하여 상위로 탐색하면
        tmp_path/.env를 발견하고 환경변수를 로드해야 함.
        """
        from hwp_parser.adapters.api import config as cfg

        (tmp_path / "pyproject.toml").touch()
        (tmp_path / ".env").write_text("PROJECT_ROOT_VAR=found\n", encoding="utf-8")

        src_dir = tmp_path / "src"
        src_dir.mkdir()
        fake_config_path = src_dir / "config.py"
        monkeypatch.setattr(cfg, "__file__", str(fake_config_path))

        with mock.patch.dict(os.environ, {}, clear=True):
            cfg._load_dotenv()
            assert os.environ.get("PROJECT_ROOT_VAR") == "found"

    def test_load_dotenv_no_parents(self, tmp_path, monkeypatch) -> None:
        """parents 비어있음 → 루프 미진입 (Line 18→exit 커버).

        Given: Path(__file__).resolve().parents가 빈 리스트
        When: _load_dotenv() 호출
        Then: for 루프 미진입, 에러 없이 종료

        이 테스트는 config.py Line 18 분기를 커버:
            for parent in current.parents:  # ← parents=[]이면 루프 skip

        루트 디렉터리 등 부모가 없는 특수 케이스 처리 검증.
        """
        from hwp_parser.adapters.api import config as cfg

        class _FakePath:
            """parents가 빈 리스트인 가짜 Path 객체."""

            parents: list[Path] = []

        monkeypatch.setattr(Path, "resolve", lambda self: _FakePath())

        cfg._load_dotenv()  # 에러 없이 종료되어야 함

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


# === 타입 검사 테스트 ===
class TestConfigTypeValidation:
    """설정 헬퍼 타입 검사 테스트 (fail-fast)."""

    def test_get_int_rejects_float_default(self) -> None:
        """_get_int에 float 기본값 → TypeError.

        Given: _get_int 호출 시 float 기본값 전달
        When: _get_int("KEY", 3.14) 호출
        Then: TypeError 발생

        타입 불일치를 조기에 감지하여 버그 방지.
        """
        import pytest

        from hwp_parser.adapters.api.config import _get_int

        with pytest.raises(TypeError, match="default must be int"):
            _get_int("__TEST__", 3.14)  # type: ignore[arg-type]

    def test_get_int_rejects_str_default(self) -> None:
        """_get_int에 str 기본값 → TypeError.

        Given: _get_int 호출 시 str 기본값 전달
        When: _get_int("KEY", "42") 호출
        Then: TypeError 발생
        """
        import pytest

        from hwp_parser.adapters.api.config import _get_int

        with pytest.raises(TypeError, match="default must be int"):
            _get_int("__TEST__", "42")  # type: ignore[arg-type]

    def test_get_float_rejects_str_default(self) -> None:
        """_get_float에 str 기본값 → TypeError.

        Given: _get_float 호출 시 str 기본값 전달
        When: _get_float("KEY", "3.14") 호출
        Then: TypeError 발생
        """
        import pytest

        from hwp_parser.adapters.api.config import _get_float

        with pytest.raises(TypeError, match="default must be float"):
            _get_float("__TEST__", "3.14")  # type: ignore[arg-type]

    def test_get_float_accepts_int_default(self) -> None:
        """_get_float에 int 기본값 → 허용 (float로 변환).

        Given: _get_float 호출 시 int 기본값 전달
        When: _get_float("KEY", 42) 호출
        Then: 42.0 반환 (int → float 변환)

        Python에서 int는 float의 subset으로 간주.
        """
        from hwp_parser.adapters.api.config import _get_float

        result = _get_float("__NONEXISTENT__", 42)
        assert result == 42.0
        assert isinstance(result, float)

    def test_get_str_rejects_int_default(self) -> None:
        """_get_str에 int 기본값 → TypeError.

        Given: _get_str 호출 시 int 기본값 전달
        When: _get_str("KEY", 42) 호출
        Then: TypeError 발생
        """
        import pytest

        from hwp_parser.adapters.api.config import _get_str

        with pytest.raises(TypeError, match="default must be str"):
            _get_str("__TEST__", 42)  # type: ignore[arg-type]

    def test_get_bool_rejects_int_default(self) -> None:
        """_get_bool에 int 기본값 → TypeError.

        Given: _get_bool 호출 시 int 기본값 전달 (1 또는 0)
        When: _get_bool("KEY", 1) 호출
        Then: TypeError 발생

        Python에서 bool은 int의 subclass이지만, 명시적 bool 요구.
        """
        import pytest

        from hwp_parser.adapters.api.config import _get_bool

        with pytest.raises(TypeError, match="default must be bool"):
            _get_bool("__TEST__", 1)  # type: ignore[arg-type]

    def test_get_bool_rejects_str_default(self) -> None:
        """_get_bool에 str 기본값 → TypeError.

        Given: _get_bool 호출 시 str 기본값 전달
        When: _get_bool("KEY", "true") 호출
        Then: TypeError 발생
        """
        import pytest

        from hwp_parser.adapters.api.config import _get_bool

        with pytest.raises(TypeError, match="default must be bool"):
            _get_bool("__TEST__", "true")  # type: ignore[arg-type]

    def test_get_list_rejects_str_default(self) -> None:
        """_get_list에 str 기본값 → TypeError.

        Given: _get_list 호출 시 str 기본값 전달
        When: _get_list("KEY", "a,b,c") 호출
        Then: TypeError 발생
        """
        import pytest

        from hwp_parser.adapters.api.config import _get_list

        with pytest.raises(TypeError, match="default must be list"):
            _get_list("__TEST__", "a,b,c")  # type: ignore[arg-type]

    def test_get_list_rejects_tuple_default(self) -> None:
        """_get_list에 tuple 기본값 → TypeError.

        Given: _get_list 호출 시 tuple 기본값 전달
        When: _get_list("KEY", ("a", "b")) 호출
        Then: TypeError 발생

        tuple과 list는 다른 타입으로 엄격히 구분.
        """
        import pytest

        from hwp_parser.adapters.api.config import _get_list

        with pytest.raises(TypeError, match="default must be list"):
            _get_list("__TEST__", ("a", "b"))  # type: ignore[arg-type]
