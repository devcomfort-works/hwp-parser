"""설정 모듈 테스트."""

from __future__ import annotations

import os
from pathlib import Path
from unittest import mock


# === 핵심 케이스 ===
class TestConfigLoading:
    """설정 로드 핵심 동작 테스트 스위트.

    테스트 대상:
        - config 모듈의 _get_* 헬퍼 함수들 (_get_str, _get_int, _get_float, _get_bool)
        - ServiceConfig 인스턴스 (모듈 임포트 시 자동 생성)

    검증 범위:
        1. 환경변수 미설정 시 기본값 반환
        2. 환경변수 설정 시 해당 값 정확히 반환 (타입 변환 포함)
        3. config 인스턴스의 필수 필드가 유효한 범위 내 값 보유

    비즈니스 컨텍스트:
        BentoML 서비스는 시작 시점에 config 모듈을 임포트한다.
        이때 설정값이 잘못되면 서비스 시작 자체가 실패하므로,
        기본값과 환경변수 처리가 정확해야 한다.

    관련 테스트:
        - TestConfigHelpers: 에지 케이스 (파싱 실패, 비표준 입력 등)
        - TestConfigTypeValidation: default 파라미터 타입 검증
    """

    def test_default_config_values(self) -> None:
        """환경변수 미설정 시 _get_* 헬퍼가 기본값을 반환하는지 검증.

        시나리오:
            서비스 배포 시 모든 환경변수를 명시적으로 설정하지 않는 경우,
            _get_* 헬퍼 함수들은 지정된 기본값을 반환해야 한다.

        의존성:
            - 테스트 데이터: "__NONEXISTENT_VAR__" (존재하지 않는 키)
            - 모듈: hwp_parser.adapters.api.config (_get_str, _get_int, _get_float, _get_bool)

        관련 테스트:
            - test_config_from_env: 환경변수 설정 시 동작 검증 (반대 케이스)
            - TestConfigHelpers.test_get_*_with_invalid_value: 파싱 실패 시 기본값 반환
        """
        from hwp_parser.adapters.api.config import (
            _get_bool,
            _get_float,
            _get_int,
            _get_str,
        )

        # 존재하지 않는 키 → 각각 지정한 기본값 반환
        assert _get_str("__NONEXISTENT_VAR__", "default") == "default"
        assert _get_int("__NONEXISTENT_VAR__", 42) == 42
        assert _get_float("__NONEXISTENT_VAR__", 3.14) == 3.14
        assert _get_bool("__NONEXISTENT_VAR__", True) is True
        assert _get_bool("__NONEXISTENT_VAR__", False) is False

    def test_config_instance_created(self) -> None:
        """config 인스턴스가 유효한 필드값으로 생성되는지 검증.

        시나리오:
            config 모듈 임포트 시 ServiceConfig 인스턴스가 자동 생성된다.
            각 필드는 BentoML @bentoml.service 데코레이터에 전달되므로,
            잘못된 값(음수 포트, 0 워커 등)이 들어가면 서비스 시작이 실패한다.

        의존성:
            - 모듈: hwp_parser.adapters.api.config (config 인스턴스)
            - 데이터클래스: ServiceConfig (name, workers, timeout, port 필드)

        검증 항목:
            - name: 빈 문자열이 아닌 서비스 이름
            - workers: 1 이상의 워커 수
            - timeout: 0보다 큰 타임아웃 (초)
            - port: 0보다 큰 HTTP 포트
        """
        from hwp_parser.adapters.api.config import config

        # 필수 필드들이 유효한 범위 내 값 보유
        assert isinstance(config.name, str) and len(config.name) >= 1  # 서비스 이름
        assert config.workers >= 1  # 워커 수
        assert config.timeout > 0  # 타임아웃 (초)
        assert config.port > 0  # HTTP 포트

    def test_config_from_env(self) -> None:
        """환경변수 설정 시 _get_* 헬퍼가 해당 값을 반환하는지 검증.

        시나리오:
            운영 환경에서 HWP_SERVICE_* 환경변수로 서비스를 구성한다.
            문자열 "4"는 정수 4로, "true"는 불리언 True로 정확히 변환되어야 한다.

        의존성:
            - 테스트 데이터: HWP_SERVICE_NAME, HWP_SERVICE_WORKERS 등 환경변수
            - 모듈: hwp_parser.adapters.api.config (_get_str, _get_int, _get_float, _get_bool)
            - mock: os.environ 패치 (unittest.mock.patch.dict)

        관련 테스트:
            - test_default_config_values: 환경변수 미설정 시 동작 (반대 케이스)
            - TestConfigHelpers.test_get_bool_variations: 다양한 truthy/falsy 표현
        """
        # Given: HWP_SERVICE_* 환경변수들 설정
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

            # Then: 환경변수 값이 정확히 반환
            assert _get_str("HWP_SERVICE_NAME", "default") == "test-service"
            assert _get_int("HWP_SERVICE_WORKERS", 1) == 4
            assert _get_float("HWP_SERVICE_TIMEOUT", 300.0) == 600.5
            assert _get_int("HWP_SERVICE_PORT", 3000) == 8080
            assert _get_bool("HWP_SERVICE_CORS_ENABLED", False) is True


# === 에지 케이스 ===
class TestConfigHelpers:
    """_get_* 헬퍼 함수의 에지 케이스 처리 테스트 스위트.

    테스트 대상:
        - _get_int, _get_float: 파싱 불가능한 값 처리
        - _get_bool: 다양한 truthy/falsy 문자열 인식
        - _get_list: 콤마 구분, 공백 처리, 빈 값 vs 미설정 구분

    검증 범위:
        1. 파싱 실패 시 예외 대신 기본값 fallback (서비스 안정성)
        2. 다양한 truthy/falsy 표현 허용 (사용자 편의)
        3. 빈 문자열과 미설정의 의미 구분 (명확한 시맨틱)

    비즈니스 컨텍스트:
        운영 환경에서 환경변수에 예상치 못한 값이 들어올 수 있다.
        HWP_SERVICE_WORKERS="auto"처럼 파싱 불가능한 값이나,
        HWP_SERVICE_CORS_ENABLED="yes"처럼 비표준 표현이 사용될 수 있다.
        이 경우 서비스가 중단되지 않고 합리적으로 동작해야 한다.

    관련 테스트:
        - TestConfigLoading: 정상 케이스 (기본값, 환경변수 설정)
        - TestConfigTypeValidation: default 파라미터 타입 검증
    """

    def test_get_int_with_invalid_value(self) -> None:
        """정수로 파싱 불가능한 환경변수 값에 대해 기본값을 반환하는지 검증.

        시나리오:
            환경변수 값이 "not_a_number"처럼 정수로 변환할 수 없는 경우,
            ValueError를 발생시키면 서비스 시작이 실패한다.
            대신 기본값을 반환하여 서비스 안정성을 보장한다.

        의존성:
            - 테스트 데이터: TEST_INT="not_a_number" (파싱 불가능한 값)
            - 모듈: hwp_parser.adapters.api.config (_get_int)
            - mock: os.environ 패치

        관련 테스트:
            - TestConfigLoading.test_default_config_values: 미설정 시 기본값
            - test_get_float_with_invalid_value: float 버전의 동일한 테스트
        """
        from hwp_parser.adapters.api.config import _get_int

        with mock.patch.dict(os.environ, {"TEST_INT": "not_a_number"}):
            result = _get_int("TEST_INT", 42)
            assert result == 42

    def test_get_float_with_valid_values(self) -> None:
        """유효한 실수 문자열이 float으로 정확히 변환되는지 검증.

        시나리오:
            타임아웃 같은 설정은 실수값이 필요하다.
            "3.14"는 물론이고 "42"처럼 정수 형태의 문자열도 실수로 변환 가능해야 한다.

        의존성:
            - 테스트 데이터: TEST_FLOAT="3.14", TEST_FLOAT="42"
            - 모듈: hwp_parser.adapters.api.config (_get_float)
            - mock: os.environ 패치

        관련 테스트:
            - test_get_float_with_invalid_value: 파싱 실패 시 기본값 반환
            - TestConfigTypeValidation.test_get_float_accepts_int_default: int 기본값 허용
        """
        from hwp_parser.adapters.api.config import _get_float

        # "3.14" → 3.14
        with mock.patch.dict(os.environ, {"TEST_FLOAT": "3.14"}):
            assert _get_float("TEST_FLOAT", 0.0) == 3.14

        # "42" (정수 문자열) → 42.0 (실수로 변환 가능)
        with mock.patch.dict(os.environ, {"TEST_FLOAT": "42"}):
            assert _get_float("TEST_FLOAT", 0.0) == 42.0

    def test_get_float_with_invalid_value(self) -> None:
        """실수로 파싱 불가능한 환경변수 값에 대해 기본값을 반환하는지 검증.

        시나리오:
            _get_int와 동일한 fallback 전략을 사용한다.
            파싱 실패 시 예외 대신 기본값을 반환하여 서비스 안정성을 보장한다.

        의존성:
            - 테스트 데이터: TEST_FLOAT="not_a_number" (파싱 불가능한 값)
            - 모듈: hwp_parser.adapters.api.config (_get_float)
            - mock: os.environ 패치

        관련 테스트:
            - test_get_int_with_invalid_value: int 버전의 동일한 테스트
            - test_get_float_with_valid_values: 정상 파싱 케이스
        """
        from hwp_parser.adapters.api.config import _get_float

        with mock.patch.dict(os.environ, {"TEST_FLOAT": "not_a_number"}):
            result = _get_float("TEST_FLOAT", 3.14)
            assert result == 3.14

    def test_get_bool_variations(self) -> None:
        """다양한 truthy/falsy 문자열이 불리언으로 정확히 변환되는지 검증.

        시나리오:
            사용자마다 불리언 값을 표현하는 방식이 다르다.
            "true", "1", "yes", "on" 등은 True로,
            "false", "0", "no", "off", "" 등은 False로 인식해야 한다.
            대소문자는 무시하여 사용자 편의를 높인다.

        의존성:
            - 테스트 데이터: true_values, false_values 리스트 (다양한 표현)
            - 모듈: hwp_parser.adapters.api.config (_get_bool)
            - mock: os.environ 패치

        관련 테스트:
            - TestConfigLoading.test_config_from_env: 실제 환경변수 사용 예시
            - TestConfigTypeValidation.test_get_bool_rejects_*: 타입 검증
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
        """콤마로 구분된 문자열이 리스트로 파싱되는지 검증.

        시나리오:
            CORS origins처럼 여러 값을 받아야 하는 설정이 있다.
            환경변수는 문자열만 지원하므로 "http://a.com,http://b.com" 형태로
            입력받아 리스트로 변환해야 한다.

        의존성:
            - 테스트 데이터: TEST_LIST="http://localhost,https://example.com"
            - 모듈: hwp_parser.adapters.api.config (_get_list)
            - mock: os.environ 패치

        관련 테스트:
            - test_get_list_with_spaces: 공백 포함 입력 처리
            - test_get_list_empty: 빈 문자열 vs 미설정 구분
        """
        from hwp_parser.adapters.api.config import _get_list

        with mock.patch.dict(
            os.environ, {"TEST_LIST": "http://localhost,https://example.com"}
        ):
            result = _get_list("TEST_LIST", ["*"])
            assert result == ["http://localhost", "https://example.com"]

    def test_get_list_with_spaces(self) -> None:
        """공백이 포함된 리스트 값에서 각 항목의 공백이 trim되는지 검증.

        시나리오:
            사용자가 " http://a.com , http://b.com " 처럼 공백을 포함하여 입력할 수 있다.
            이를 그대로 사용하면 " http://b.com"처럼 앞에 공백이 붙어 URL 오류가 발생한다.
            각 항목의 앞뒤 공백을 자동으로 제거하여 사용자 실수를 보정한다.

        의존성:
            - 테스트 데이터: TEST_LIST=" http://localhost , https://example.com "
            - 모듈: hwp_parser.adapters.api.config (_get_list)
            - mock: os.environ 패치

        관련 테스트:
            - test_get_list: 정상 입력 (공백 없음)
        """
        from hwp_parser.adapters.api.config import _get_list

        with mock.patch.dict(
            os.environ, {"TEST_LIST": " http://localhost , https://example.com "}
        ):
            result = _get_list("TEST_LIST", ["*"])
            assert result == ["http://localhost", "https://example.com"]

    def test_get_list_empty(self) -> None:
        """빈 문자열("")이 빈 리스트([])로 변환되는지 검증.

        시나리오:
            환경변수가 ""(빈 문자열)로 설정된 경우는 미설정과 다르다.
            빈 문자열은 "명시적으로 비어있음"을 의미하므로 기본값 대신 []를 반환한다.
            이를 통해 사용자가 의도적으로 목록을 비울 수 있다 (예: CORS 비활성화).

        의존성:
            - 테스트 데이터: TEST_LIST="" (빈 문자열)
            - 모듈: hwp_parser.adapters.api.config (_get_list)
            - mock: os.environ 패치

        관련 테스트:
            - test_get_list_default_when_missing: 미설정 시 기본값 반환 (반대 케이스)
        """
        from hwp_parser.adapters.api.config import _get_list

        with mock.patch.dict(os.environ, {"TEST_LIST": ""}):
            result = _get_list("TEST_LIST", ["default"])
            assert result == []

    def test_get_list_default_when_missing(self) -> None:
        """환경변수 미설정 시 기본값이 반환되는지 검증.

        시나리오:
            환경변수가 아예 설정되지 않은 경우(os.environ에 키 없음)는
            빈 문자열("")과 다르게 처리해야 한다. 이 경우 지정된 기본값을 반환한다.

        의존성:
            - 테스트 데이터: TEST_LIST 키 없음 (clear=True로 환경 초기화)
            - 모듈: hwp_parser.adapters.api.config (_get_list)
            - mock: os.environ 패치 (clear=True)

        관련 테스트:
            - test_get_list_empty: 빈 문자열 시 [] 반환 (반대 케이스)
        """
        from hwp_parser.adapters.api.config import _get_list

        with mock.patch.dict(os.environ, {}, clear=True):
            result = _get_list("TEST_LIST", ["default"])
            assert result == ["default"]


class TestLoadDotenv:
    """_load_dotenv 함수의 .env 파일 탐색 및 로드 테스트 스위트.

    테스트 대상:
        - _load_dotenv(): 프로젝트 루트에서 .env 파일 탐색
        - _parse_env_file(): .env 파일 파싱 및 환경변수 설정

    검증 범위:
        1. config.py 위치에서 상위 디렉터리 순회하며 .env 파일 탐색
        2. pyproject.toml을 프로젝트 루트 마커로 사용하여 탐색 중단
        3. .env 파일 형식 파싱 (KEY=VALUE, 주석, 따옴표 등)
        4. 기존 환경변수 보존 (런타임 환경변수 > .env)

    비즈니스 컨텍스트:
        로컬 개발 환경에서는 .env 파일로 환경변수를 관리하는 것이 일반적이다.
        _load_dotenv()는 python-dotenv 의존성 없이 이 기능을 제공한다.

    테스트 전략:
        실제 파일 I/O를 테스트하기 위해 tmp_path에 가상 디렉터리 구조를 만들고,
        config 모듈의 __file__을 monkeypatch로 조작하여 탐색 시작점을 변경한다.
        이를 통해 mocking 없이 실제 파일 탐색 로직을 검증할 수 있다.

    관련 테스트:
        - TestConfigLoading: _get_* 헬퍼 함수 동작 (.env 로드 후 사용)
        - TestConfigHelpers: 헬퍼 함수 에지 케이스
    """

    def test_load_dotenv_loads_env_file(self, tmp_path, monkeypatch) -> None:
        """프로젝트 루트에 .env 파일이 있으면 환경변수로 로드한다.

        시나리오:
            가장 기본적인 사용 패턴 - config.py와 같은 디렉터리에 .env가 있으면
            해당 파일을 파싱하여 환경변수에 설정해야 한다.

        의존성:
            - pytest fixture: tmp_path (임시 디렉터리), monkeypatch (__file__ 조작)
            - 테스트 데이터: .env 파일 (TEST_LOAD_DOTENV_VAR=hello)
            - 모듈: hwp_parser.adapters.api.config (_load_dotenv, __file__)
            - mock: os.environ 패치 (clear=True)

        관련 테스트:
            - test_load_dotenv_finds_env_at_project_root: 상위 디렉터리에서 탐색
            - test_parse_env_file: .env 파일 파싱 세부 동작
        """
        from hwp_parser.adapters.api import config as cfg

        # 테스트 구조:
        # tmp_path/
        # └── .env  (TEST_LOAD_DOTENV_VAR=hello)
        env_file = tmp_path / ".env"
        env_file.write_text("TEST_LOAD_DOTENV_VAR=hello\n", encoding="utf-8")

        # __file__을 tmp_path 내 파일로 변경 → tmp_path/.env를 찾게 됨
        fake_config_path = tmp_path / "config.py"
        monkeypatch.setattr(cfg, "__file__", str(fake_config_path))

        with mock.patch.dict(os.environ, {}, clear=True):
            cfg._load_dotenv()
            assert os.environ.get("TEST_LOAD_DOTENV_VAR") == "hello"

    def test_load_dotenv_skips_when_no_env(self, tmp_path, monkeypatch) -> None:
        """pyproject.toml은 있지만 .env가 없으면 환경변수를 변경하지 않는다.

        시나리오:
            pyproject.toml이 있으면 해당 디렉터리를 프로젝트 루트로 간주하고 탐색을 중단한다.
            이때 .env가 없어도 에러 없이 정상 종료해야 한다.
            이는 .env 파일이 선택적이라는 것을 의미한다.

        의존성:
            - pytest fixture: tmp_path, monkeypatch
            - 테스트 데이터: pyproject.toml (빈 파일), .env 없음
            - 모듈: hwp_parser.adapters.api.config (_load_dotenv, __file__)
            - mock: os.environ 패치 (clear=True)

        관련 테스트:
            - test_load_dotenv_loads_env_file: .env 존재 시 로드 (성공 케이스)
        """
        from hwp_parser.adapters.api import config as cfg

        # 테스트 구조:
        # tmp_path/
        # ├── pyproject.toml  (탐색 중단점)
        # └── src/
        #     └── config.py  (가상 시작점)
        (tmp_path / "pyproject.toml").touch()

        subdir = tmp_path / "src"
        subdir.mkdir()
        fake_config_path = subdir / "config.py"
        monkeypatch.setattr(cfg, "__file__", str(fake_config_path))

        # .env 없으므로 환경변수 변경 없음
        with mock.patch.dict(os.environ, {}, clear=True):
            cfg._load_dotenv()
            assert "TEST_LOAD_DOTENV_VAR" not in os.environ

    def test_load_dotenv_finds_env_at_project_root(self, tmp_path, monkeypatch) -> None:
        """하위 디렉터리에서 시작해도 상위의 .env를 찾아 로드한다.

        시나리오:
            실제 프로젝트에서 config.py는 src/hwp_parser/adapters/api/ 하위에 있고,
            .env는 프로젝트 루트에 있다. _load_dotenv()는 상위 디렉터리를
            순회하며 .env를 찾아야 한다.

        의존성:
            - pytest fixture: tmp_path, monkeypatch
            - 테스트 데이터: pyproject.toml, .env (PROJECT_ROOT_VAR=found), src/ 하위 구조
            - 모듈: hwp_parser.adapters.api.config (_load_dotenv, __file__)
            - mock: os.environ 패치 (clear=True)

        관련 테스트:
            - test_load_dotenv_loads_env_file: 같은 디렉터리에서 탐색
        """
        from hwp_parser.adapters.api import config as cfg

        # 테스트 구조:
        # tmp_path/
        # ├── pyproject.toml
        # ├── .env  (PROJECT_ROOT_VAR=found)
        # └── src/
        #     └── config.py  (가상 시작점)
        (tmp_path / "pyproject.toml").touch()
        (tmp_path / ".env").write_text("PROJECT_ROOT_VAR=found\n", encoding="utf-8")

        src_dir = tmp_path / "src"
        src_dir.mkdir()
        fake_config_path = src_dir / "config.py"
        monkeypatch.setattr(cfg, "__file__", str(fake_config_path))

        # src/에서 시작 → 상위 tmp_path/.env 발견
        with mock.patch.dict(os.environ, {}, clear=True):
            cfg._load_dotenv()
            assert os.environ.get("PROJECT_ROOT_VAR") == "found"

    def test_load_dotenv_no_parents(self, tmp_path, monkeypatch) -> None:
        """Path.parents가 비어있는 특수 케이스에서도 에러 없이 종료한다.

        시나리오:
            이론적으로 루트 디렉터리에서 실행되면 parents가 비어있을 수 있다.
            이 경우 for 루프가 실행되지 않고 함수가 종료되는데,
            예외 없이 정상 종료해야 한다.

        의존성:
            - pytest fixture: tmp_path, monkeypatch
            - 모듈: hwp_parser.adapters.api.config (_load_dotenv), pathlib.Path
            - mock: Path.resolve() 메서드를 가짜 객체로 대체

        커버리지 목적:
            config.py Line 18 분기 (for parent in current.parents: 루프 skip)
        """
        from hwp_parser.adapters.api import config as cfg

        # config.py Line 18 분기 커버:
        # for parent in current.parents:  ← parents=[]이면 루프 skip
        class _FakePath:
            """parents가 빈 리스트인 가짜 Path 객체."""

            parents: list[Path] = []

        monkeypatch.setattr(Path, "resolve", lambda self: _FakePath())

        # 에러 없이 종료되어야 함
        cfg._load_dotenv()

    def test_parse_env_file(self, tmp_path) -> None:
        """_parse_env_file이 .env 파일의 다양한 형식을 올바르게 파싱하는지 검증.

        시나리오:
            .env 파일은 다양한 형식을 지원해야 한다:
            - KEY=VALUE 기본 형식
            - # 주석 무시
            - 따옴표로 감싼 값 ("value" → value)
            - KEY = VALUE 처럼 공백 포함

        의존성:
            - pytest fixture: tmp_path
            - 테스트 데이터: .env 파일 (다양한 형식의 키-값 쌍)
            - 모듈: hwp_parser.adapters.api.config (_parse_env_file)
            - mock: os.environ 패치 (clear=True)

        관련 테스트:
            - test_parse_env_file_ignores_invalid_line: 잘못된 형식 처리
            - test_parse_env_file_preserves_existing: 기존 환경변수 보존
        """
        from hwp_parser.adapters.api.config import _parse_env_file

        # 주석(#)은 무시, 따옴표는 제거, 공백은 trim
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
        """KEY=VALUE 형식이 아닌 라인은 무시하고 계속 진행한다.

        시나리오:
            .env 파일에 "INVALIDLINE"처럼 '='가 없는 라인이 있을 수 있다.
            이를 에러로 처리하면 서비스 시작이 실패하므로,
            조용히 무시하고 다음 라인을 처리해야 한다.

        의존성:
            - pytest fixture: tmp_path
            - 테스트 데이터: .env 파일 ("INVALIDLINE" - 잘못된 형식)
            - 모듈: hwp_parser.adapters.api.config (_parse_env_file)
            - mock: os.environ 패치 (clear=True)

        관련 테스트:
            - test_parse_env_file: 정상 형식 파싱
        """
        from hwp_parser.adapters.api.config import _parse_env_file

        # 잘못된 형식은 조용히 스킵 → 서비스 중단 방지
        env_file = tmp_path / ".env"
        env_file.write_text("INVALIDLINE\n", encoding="utf-8")

        with mock.patch.dict(os.environ, {}, clear=True):
            _parse_env_file(env_file)
            assert "INVALIDLINE" not in os.environ

    def test_parse_env_file_preserves_existing(self, tmp_path: Path) -> None:
        """이미 설정된 환경변수는 .env 값으로 덮어쓰지 않는다.

        시나리오:
            런타임에서 명시적으로 설정한 환경변수(export, docker -e 등)가
            .env 파일보다 우선해야 한다. .env는 기본값 역할이며,
            런타임 환경변수가 있으면 그 값을 유지해야 한다.

        의존성:
            - pytest fixture: tmp_path
            - 테스트 데이터: .env 파일 (TEST_ENV_EXISTING=override)
            - 모듈: hwp_parser.adapters.api.config (_parse_env_file)
            - mock: os.environ 패치 ({"TEST_ENV_EXISTING": "original"}, clear=True)

        관련 테스트:
            - test_parse_env_file: 정상 형식 파싱
        """
        from hwp_parser.adapters.api.config import _parse_env_file

        # 런타임 환경변수가 .env보다 우선
        env_file = tmp_path / ".env"
        env_file.write_text("TEST_ENV_EXISTING=override", encoding="utf-8")

        with mock.patch.dict(os.environ, {"TEST_ENV_EXISTING": "original"}, clear=True):
            _parse_env_file(env_file)
            # .env의 "override"가 아닌 기존 "original" 유지
            assert os.environ["TEST_ENV_EXISTING"] == "original"


# === 타입 검사 테스트 ===
class TestConfigTypeValidation:
    """_get_* 헬퍼 함수의 default 파라미터 타입 검증 테스트 스위트.

    테스트 대상:
        - _get_int: int 타입 기본값만 허용 (float, str 거부)
        - _get_float: float 또는 int 기본값 허용 (str 거부)
        - _get_str: str 타입 기본값만 허용 (int 거부)
        - _get_bool: bool 타입 기본값만 허용 (int, str 거부)
        - _get_list: list 타입 기본값만 허용 (str, tuple 거부)

    검증 범위:
        1. 잘못된 타입의 default 파라미터 전달 시 TypeError 발생
        2. 런타임 타입 검사로 개발 중 실수 조기 발견

    비즈니스 컨텍스트:
        _get_* 헬퍼 함수는 환경변수 문자열을 특정 타입으로 변환한다.
        default 파라미터의 타입이 잘못되면 예상치 못한 동작이 발생한다:
        - _get_int("KEY", "42") → 문자열 "42"가 기본값이 되어 타입 불일치
        런타임 검증은 정적 타입 검사(mypy)를 보완하여 개발 중 즉시 오류를 발생시킨다.
        이를 통해 잘못된 기본값이 프로덕션까지 전파되는 것을 방지한다 (fail-fast 원칙).

    관련 테스트:
        - TestConfigLoading: _get_* 함수 정상 동작
        - TestConfigHelpers: 에지 케이스 처리
    """

    def test_get_int_rejects_float_default(self) -> None:
        """_get_int에 float 기본값을 전달하면 TypeError가 발생한다.

        시나리오:
            3.14는 float이므로 int 기본값으로 적합하지 않다.
            타입 혼동은 예상치 못한 동작을 유발할 수 있으므로 즉시 거부한다.

        의존성:
            - 모듈: hwp_parser.adapters.api.config (_get_int), pytest (raises)
            - 테스트 데이터: 3.14 (float 기본값)

        관련 테스트:
            - test_get_int_rejects_str_default: str 기본값 거부
            - TestConfigHelpers.test_get_int_with_invalid_value: 환경변수 파싱 실패 (다른 케이스)
        """
        import pytest

        from hwp_parser.adapters.api.config import _get_int

        # 타입 불일치 조기 감지 → 버그 방지
        with pytest.raises(TypeError, match="default must be int"):
            _get_int("__TEST__", 3.14)  # type: ignore[arg-type]

    def test_get_int_rejects_str_default(self) -> None:
        """_get_int에 str 기본값을 전달하면 TypeError가 발생한다.

        시나리오:
            "42"는 정수처럼 보이지만 문자열이다. _get_int는 환경변수 문자열을
            정수로 변환하는 함수이므로, 기본값까지 문자열이면 타입 혼동이 발생한다.

        의존성:
            - 모듈: hwp_parser.adapters.api.config (_get_int), pytest (raises)
            - 테스트 데이터: "42" (str 기본값)

        관련 테스트:
            - test_get_int_rejects_float_default: float 기본값 거부
        """
        import pytest

        from hwp_parser.adapters.api.config import _get_int

        # "42"는 문자열이므로 int 기본값으로 부적절
        with pytest.raises(TypeError, match="default must be int"):
            _get_int("__TEST__", "42")  # type: ignore[arg-type]

    def test_get_float_rejects_str_default(self) -> None:
        """_get_float에 str 기본값을 전달하면 TypeError가 발생한다.

        시나리오:
            "3.14"는 실수처럼 보이지만 문자열이다.
            타입 실수를 방지하기 위해 즉시 거부한다.

        의존성:
            - 모듈: hwp_parser.adapters.api.config (_get_float), pytest (raises)
            - 테스트 데이터: "3.14" (str 기본값)

        관련 테스트:
            - test_get_float_accepts_int_default: int 기본값 허용
        """
        import pytest

        from hwp_parser.adapters.api.config import _get_float

        # "3.14"는 문자열이므로 float 기본값으로 부적절
        with pytest.raises(TypeError, match="default must be float"):
            _get_float("__TEST__", "3.14")  # type: ignore[arg-type]

    def test_get_float_accepts_int_default(self) -> None:
        """_get_float에 int 기본값은 허용한다.

        시나리오:
            Python에서 int는 float의 부분집합으로 취급된다.
            isinstance(42, (int, float))는 True이므로, _get_float은 int 기본값을 허용한다.
            단, 반환값은 float으로 변환된다.

        의존성:
            - 모듈: hwp_parser.adapters.api.config (_get_float)
            - 테스트 데이터: 42 (int 기본값)

        관련 테스트:
            - test_get_float_rejects_str_default: str 기본값 거부
        """
        from hwp_parser.adapters.api.config import _get_float

        # Python에서 int는 float의 subset으로 간주
        # isinstance(42, (int, float)) == True
        result = _get_float("__NONEXISTENT__", 42)
        assert result == 42.0
        assert isinstance(result, float)

    def test_get_str_rejects_int_default(self) -> None:
        """_get_str에 int 기본값을 전달하면 TypeError가 발생한다.

        시나리오:
            42는 정수이므로 str 기본값으로 적합하지 않다.
            타입 실수를 방지하기 위해 즉시 거부한다.

        의존성:
            - 모듈: hwp_parser.adapters.api.config (_get_str), pytest (raises)
            - 테스트 데이터: 42 (int 기본값)
        """
        import pytest

        from hwp_parser.adapters.api.config import _get_str

        # 42는 int이므로 str 기본값으로 부적절
        with pytest.raises(TypeError, match="default must be str"):
            _get_str("__TEST__", 42)  # type: ignore[arg-type]

    def test_get_bool_rejects_int_default(self) -> None:
        """_get_bool에 int 기본값을 전달하면 TypeError가 발생한다.

        시나리오:
            Python에서 bool은 int의 subclass이지만, 1을 True로 쓰는 것은 가독성을 해친다.
            명시적인 bool 값(True/False)만 허용하여 코드 명확성을 보장한다.

        의존성:
            - 모듈: hwp_parser.adapters.api.config (_get_bool), pytest (raises)
            - 테스트 데이터: 1 (int 기본값)

        관련 테스트:
            - test_get_bool_rejects_str_default: str 기본값 거부
            - TestConfigHelpers.test_get_bool_variations: 환경변수 문자열 파싱
        """
        import pytest

        from hwp_parser.adapters.api.config import _get_bool

        # bool은 int의 subclass이지만, 명시적 bool 요구
        with pytest.raises(TypeError, match="default must be bool"):
            _get_bool("__TEST__", 1)  # type: ignore[arg-type]

    def test_get_bool_rejects_str_default(self) -> None:
        """_get_bool에 str 기본값을 전달하면 TypeError가 발생한다.

        시나리오:
            "true"는 불리언처럼 보이지만 문자열이다. _get_bool은 환경변수 문자열을
            불리언으로 변환하는 함수이므로, 기본값까지 문자열이면 타입 혼동이 발생한다.

        의존성:
            - 모듈: hwp_parser.adapters.api.config (_get_bool), pytest (raises)
            - 테스트 데이터: "true" (str 기본값)

        관련 테스트:
            - test_get_bool_rejects_int_default: int 기본값 거부
        """
        import pytest

        from hwp_parser.adapters.api.config import _get_bool

        # "true"는 문자열이므로 bool 기본값으로 부적절
        with pytest.raises(TypeError, match="default must be bool"):
            _get_bool("__TEST__", "true")  # type: ignore[arg-type]

    def test_get_list_rejects_str_default(self) -> None:
        """_get_list에 str 기본값을 전달하면 TypeError가 발생한다.

        시나리오:
            "a,b,c"는 리스트처럼 보이지만 문자열이다. _get_list는 환경변수 문자열을
            리스트로 변환하는 함수이므로, 기본값까지 문자열이면 타입 혼동이 발생한다.

        의존성:
            - 모듈: hwp_parser.adapters.api.config (_get_list), pytest (raises)
            - 테스트 데이터: "a,b,c" (str 기본값)

        관련 테스트:
            - test_get_list_rejects_tuple_default: tuple 기본값 거부
            - TestConfigHelpers.test_get_list: 환경변수 문자열 파싱
        """
        import pytest

        from hwp_parser.adapters.api.config import _get_list

        # "a,b,c"는 문자열이므로 list 기본값으로 부적절
        with pytest.raises(TypeError, match="default must be list"):
            _get_list("__TEST__", "a,b,c")  # type: ignore[arg-type]

    def test_get_list_rejects_tuple_default(self) -> None:
        """_get_list에 tuple 기본값을 전달하면 TypeError가 발생한다.

        시나리오:
            ("a", "b")는 리스트와 비슷하지만 tuple이다.
            tuple과 list는 다른 타입으로 엄격히 구분하여 예상치 못한 동작을 방지한다.

        의존성:
            - 모듈: hwp_parser.adapters.api.config (_get_list), pytest (raises)
            - 테스트 데이터: ("a", "b") (tuple 기본값)

        관련 테스트:
            - test_get_list_rejects_str_default: str 기본값 거부
        """
        import pytest

        from hwp_parser.adapters.api.config import _get_list

        # tuple과 list는 다른 타입으로 엄격히 구분
        with pytest.raises(TypeError, match="default must be list"):
            _get_list("__TEST__", ("a", "b"))  # type: ignore[arg-type]
