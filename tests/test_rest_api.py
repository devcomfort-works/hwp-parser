"""REST API (BentoML) 테스트."""

from __future__ import annotations

import base64
import importlib
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest

from hwp_parser.adapters.api.service import (
    ConversionResponse,
    HWPService,
    _result_to_response,
)
from hwp_parser.core import HWPConverter

# === 핵심 케이스 ===

if TYPE_CHECKING:
    ServiceInstance = Any


class TestHWPService:
    """HWPService 초기화 및 기본 엔드포인트 테스트 스위트.

    테스트 대상:
        - HWPService 인스턴스 생성 및 converter 주입
        - health(), formats() 엔드포인트

    검증 범위:
        1. 서비스 생성 시 HWPConverter 인스턴스 자동 주입
        2. health 엔드포인트 응답 형식
        3. formats 엔드포인트 응답 형식

    비즈니스 컨텍스트:
        HWPService는 BentoML @bentoml.service 데코레이터로 정의된 REST API 서비스다.
        health는 로드밸런서/쿠버네티스 헬스체크에 사용된다.

    관련 테스트:
        - TestServiceConversion: 실제 변환 엔드포인트 테스트
    """

    @pytest.fixture
    def service(self) -> ServiceInstance:
        """HWPService 인스턴스."""
        return HWPService()

    def test_service_init(self, service: ServiceInstance) -> None:
        """서비스 초기화 시 HWPConverter가 자동 주입되는지 검증.

        시나리오:
            HWPService는 생성 시 내부적으로 HWPConverter 인스턴스를
            생성하여 converter 속성에 저장한다.

        의존성:
            - pytest fixture: service (HWPService 인스턴스)
            - 모듈: hwp_parser.core.HWPConverter
        """
        assert service.converter is not None
        assert isinstance(service.converter, HWPConverter)

    def test_health_endpoint(self, service: ServiceInstance) -> None:
        """헬스 체크 엔드포인트 응답 형식 검증.

        시나리오:
            GET /health 엔드포인트는 서비스 상태를 반환한다.
            쿠버네티스 liveness/readiness probe에 사용된다.

        의존성:
            - pytest fixture: service
        """
        result = service.health()
        assert result["status"] == "healthy"
        assert result["service"] == "hwp-parser"

    def test_formats_endpoint(self, service: ServiceInstance) -> None:
        """지원 포맷 엔드포인트 응답 형식 검증.

        시나리오:
            GET /formats 엔드포인트는 지원하는 변환 포맷 목록을 반환한다.
            클라이언트가 사용 가능한 포맷을 조회할 수 있다.

        의존성:
            - pytest fixture: service

        관련 테스트:
            - test_python_api.TestHWPConverterInit.test_supported_formats: 동일한 포맷 목록
        """
        result = service.formats()
        assert "supported_formats" in result
        assert "txt" in result["supported_formats"]
        assert "html" in result["supported_formats"]
        assert "markdown" in result["supported_formats"]
        assert "odt" in result["supported_formats"]


class TestApiServe:
    """serve() 함수 테스트 스위트.

    테스트 대상:
        - hwp_parser.adapters.api.serve() 함수

    검증 범위:
        1. bentoml serve 명령어 정확히 실행

    비즈니스 컨텍스트:
        serve()는 CLI 진입점으로, pyproject.toml의 hwp-serve 스크립트에서 호출된다.
        내부적으로 subprocess.run으로 bentoml serve를 실행한다.

    테스트 전략:
        subprocess.run을 mocking하여 실제 서버 실행 없이 검증한다.
    """

    def test_serve_invokes_bentoml(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """serve() → bentoml serve 호출.

        Given: subprocess.run mocked
        When: serve() 호출
        Then: bentoml serve hwp_parser.adapters.api:HWPService 실행
        """
        captured: dict[str, object] = {}

        def _fake_run(args: list[str], check: bool) -> None:
            captured["args"] = args
            captured["check"] = check

        monkeypatch.setattr("subprocess.run", _fake_run)

        from hwp_parser.adapters.api import serve

        serve()
        assert captured["check"] is True
        args = captured["args"]
        assert isinstance(args, list)
        assert args[1:] == [
            "-m",
            "bentoml",
            "serve",
            "hwp_parser.adapters.api:HWPService",
        ]


class TestConversionResponse:
    """ConversionResponse Pydantic 모델 테스트 스위트.

    테스트 대상:
        - ConversionResponse 데이터 모델

    검증 범위:
        1. 모델 생성 시 필드 정상 설정

    비즈니스 컨텍스트:
        ConversionResponse는 REST API 응답의 JSON 스키마를 정의한다.
        Pydantic 모델로 정의되어 자동 검증 및 직렬화를 제공한다.
    """

    def test_response_model(self) -> None:
        """응답 모델 생성.

        Given: 테스트 데이터
        When: ConversionResponse 생성
        Then: 모든 필드 정상 설정
        """
        response = ConversionResponse(
            content="test content",
            source_name="test.hwp",
            output_format="txt",
            pipeline="hwp→txt",
            is_binary=False,
            content_length=12,
        )
        assert response.content == "test content"
        assert response.source_name == "test.hwp"
        assert response.output_format == "txt"


class TestResultToResponse:
    """_result_to_response() 변환 함수 테스트 스위트.

    테스트 대상:
        - _result_to_response(ConversionResult) → ConversionResponse 변환

    검증 범위:
        1. 텍스트 결과 → 문자열 응답 (is_binary=False)
        2. 바이너리 결과 → base64 인코딩 응답 (is_binary=True)

    비즈니스 컨텍스트:
        HWPConverter의 ConversionResult를 REST API 응답으로 변환한다.
        ODT 같은 바이너리 데이터는 JSON 직렬화를 위해 base64로 인코딩된다.

    관련 테스트:
        - test_python_api.TestConversionResult: ConversionResult 속성
    """

    def test_text_result_to_response(
        self, converter: HWPConverter, sample_hwp_file: Path
    ) -> None:
        """텍스트 결과 → API 응답 변환.

        Given: to_text() 결과
        When: _result_to_response 호출
        Then: ConversionResponse(is_binary=False) 반환
        """
        result = converter.to_text(sample_hwp_file)
        response = _result_to_response(result)

        assert isinstance(response, ConversionResponse)
        assert response.output_format == "txt"
        assert response.is_binary is False
        assert isinstance(response.content, str)

    def test_binary_result_to_response(
        self, converter: HWPConverter, sample_hwp_file: Path
    ) -> None:
        """바이너리 결과 → base64 응답 변환.

        Given: to_odt() 결과 (바이너리)
        When: _result_to_response 호출
        Then: base64 인코딩된 문자열 반환

        바이너리 데이터는 JSON 직렬화를 위해 base64 인코딩.
        """
        result = converter.to_odt(sample_hwp_file)
        response = _result_to_response(result)

        assert isinstance(response, ConversionResponse)
        assert response.output_format == "odt"
        assert response.is_binary is True
        decoded = base64.b64decode(response.content)
        assert decoded[:2] == b"PK"


class TestServiceConversion:
    """서비스 변환 엔드포인트 테스트 스위트.

    테스트 대상:
        - convert_to_text(), convert_to_html(), convert_to_markdown(), convert_to_odt()
        - convert(file, output_format) 범용 메서드

    검증 범위:
        1. 각 포맷별 변환 엔드포인트 정상 동작
        2. 큰 파일 변환
        3. 베크 파일 변환

    비즈니스 컨텍스트:
        각 엔드포인트는 POST /convert/{format} HTTP 요청을 처리한다.
        내부적으로 HWPConverter의 해당 메서드를 호출한다.

    의존성:
        - pytest fixture: sample_hwp_file, all_hwp_files, small_hwp_files (conftest.py)
        - 테스트 데이터: tests/fixtures/*.hwp

    관련 테스트:
        - test_python_api.TestConvert: HWPConverter.convert() 테스트
    """

    @pytest.fixture
    def service(self) -> ServiceInstance:
        """HWPService 인스턴스."""
        return HWPService()

    def test_convert_to_text(
        self, service: ServiceInstance, sample_hwp_file: Path
    ) -> None:
        """REST API 텍스트 변환.

        Given: 유효한 HWP 파일
        When: convert_to_text 호출
        Then: output_format="txt", is_binary=False
        """
        response = service.convert_to_text(sample_hwp_file)
        assert response.output_format == "txt"
        assert response.is_binary is False

    def test_convert_to_html(
        self, service: ServiceInstance, sample_hwp_file: Path
    ) -> None:
        """REST API HTML 변환.

        Given: 유효한 HWP 파일
        When: convert_to_html 호출
        Then: output_format="html", is_binary=False
        """
        response = service.convert_to_html(sample_hwp_file)
        assert response.output_format == "html"
        assert response.is_binary is False

    def test_convert_to_markdown(
        self, service: ServiceInstance, sample_hwp_file: Path
    ) -> None:
        """REST API Markdown 변환.

        Given: 유효한 HWP 파일
        When: convert_to_markdown 호출
        Then: output_format="markdown", is_binary=False
        """
        response = service.convert_to_markdown(sample_hwp_file)
        assert response.output_format == "markdown"
        assert response.is_binary is False

    def test_convert_to_odt(
        self, service: ServiceInstance, sample_hwp_file: Path
    ) -> None:
        """REST API ODT 변환.

        Given: 유효한 HWP 파일
        When: convert_to_odt 호출
        Then: output_format="odt", is_binary=True
        """
        response = service.convert_to_odt(sample_hwp_file)
        assert response.output_format == "odt"
        assert response.is_binary is True

    def test_convert_with_format(
        self, service: ServiceInstance, sample_hwp_file: Path
    ) -> None:
        """포맷 지정 변환.

        Given: 유효한 HWP 파일, output_format="html"
        When: convert 호출
        Then: output_format="html"
        """
        response = service.convert(sample_hwp_file, output_format="html")
        assert response.output_format == "html"

    def test_convert_large_file(
        self, service: ServiceInstance, all_hwp_files: list[Path]
    ) -> None:
        """큰 파일 변환.

        Given: 가장 큰 HWP 파일
        When: convert_to_markdown 호출
        Then: 정상 변환
        """
        large_file = max(all_hwp_files, key=lambda f: f.stat().st_size)
        response = service.convert_to_markdown(large_file)
        assert response.output_format == "markdown"
        assert response.is_binary is False

    def test_convert_bulk_files(
        self, service: ServiceInstance, small_hwp_files: list[Path]
    ) -> None:
        """벌크 파일 변환.

        Given: 작은 HWP 파일 목록
        When: 각 파일에 convert_to_text 호출
        Then: 모든 파일 정상 변환
        """
        results = [service.convert_to_text(f) for f in small_hwp_files]
        assert len(results) == len(small_hwp_files)
        assert all(r.output_format == "txt" for r in results)


# === 에지 케이스 ===


class TestServiceHttpConfig:
    """HTTP 설정 에지 케이스 테스트 스위트.

    테스트 대상:
        - _http_config 모듈 변수 (CORS 설정)

    검증 범위:
        1. HWP_SERVICE_CORS_ENABLED=true 시 CORS 설정 포함
        2. HWP_SERVICE_CORS_ORIGINS 환경변수 반영

    비즈니스 컨텍스트:
        BentoML 서비스는 _http_config를 통해 CORS 정책을 설정한다.
        환경변수로 CORS를 활성화/비활성화하고 허용 도메인을 지정할 수 있다.

    테스트 전략:
        환경변수 설정 후 모듈을 reload하여 설정 변경을 반영한다.

    관련 테스트:
        - test_config.TestConfigHelpers: _get_bool, _get_list 헬퍼
    """

    def test_http_config_includes_cors(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """CORS 설정 → HTTP config 반영.

        Given: HWP_SERVICE_CORS_ENABLED=true
        When: 모듈 리로드
        Then: _http_config에 cors 설정 포함

        환경변수로 CORS 정책 제어 가능.
        """
        import hwp_parser.adapters.api.config as cfg_module
        import hwp_parser.adapters.api.service as service_module

        monkeypatch.setenv("HWP_SERVICE_CORS_ENABLED", "true")
        monkeypatch.setenv(
            "HWP_SERVICE_CORS_ORIGINS",
            "http://example.com,https://example.com",
        )

        cfg_module = importlib.reload(cfg_module)
        service_module = importlib.reload(service_module)

        assert "cors" in service_module._http_config
        cors = service_module._http_config["cors"]
        assert cors["enabled"] is True
        assert cors["access_control_allow_origins"] == [
            "http://example.com",
            "https://example.com",
        ]

        monkeypatch.delenv("HWP_SERVICE_CORS_ENABLED", raising=False)
        monkeypatch.delenv("HWP_SERVICE_CORS_ORIGINS", raising=False)
        importlib.reload(cfg_module)
        importlib.reload(service_module)
