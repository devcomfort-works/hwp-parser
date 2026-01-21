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
    """HWPService 테스트."""

    @pytest.fixture
    def service(self) -> ServiceInstance:
        """HWPService 인스턴스."""
        return HWPService()

    def test_service_init(self, service: ServiceInstance) -> None:
        """서비스 초기화 → converter 주입.

        Given: 없음
        When: HWPService() 생성
        Then: converter 속성에 HWPConverter 인스턴스 존재
        """
        assert service.converter is not None
        assert isinstance(service.converter, HWPConverter)

    def test_health_endpoint(self, service: ServiceInstance) -> None:
        """헬스 체크 엔드포인트.

        Given: HWPService 인스턴스
        When: health() 호출
        Then: {"status": "healthy", "service": "hwp-parser"}
        """
        result = service.health()
        assert result["status"] == "healthy"
        assert result["service"] == "hwp-parser"

    def test_formats_endpoint(self, service: ServiceInstance) -> None:
        """지원 포맷 엔드포인트.

        Given: HWPService 인스턴스
        When: formats() 호출
        Then: supported_formats에 txt/html/markdown/odt 포함
        """
        result = service.formats()
        assert "supported_formats" in result
        assert "txt" in result["supported_formats"]
        assert "html" in result["supported_formats"]
        assert "markdown" in result["supported_formats"]
        assert "odt" in result["supported_formats"]


class TestApiServe:
    """API 실행 래퍼 테스트."""

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
    """ConversionResponse 테스트."""

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
    """_result_to_response 함수 테스트."""

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
    """서비스 변환 테스트."""

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
    """HTTP 설정 에지 케이스 테스트."""

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
