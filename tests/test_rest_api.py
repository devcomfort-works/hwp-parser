"""
REST API (BentoML) 테스트
"""

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
    # 테스트에서는 실제 인스턴스 타입을 사용
    ServiceInstance = Any


class TestHWPService:
    """HWPService 테스트"""

    @pytest.fixture
    def service(self) -> ServiceInstance:
        """HWPService 인스턴스.

        Notes
        -----
        - 목적: REST API 서비스 테스트에 사용할 인스턴스 제공.
        - 로직: HWPService를 직접 생성해 반환.
        - 데이터: 없음.
        """
        return HWPService()

    def test_service_init(self, service: ServiceInstance) -> None:
        """서비스 초기화 검증.

        Parameters
        ----------
        service : ServiceInstance
            HWPService fixture.

        Notes
        -----
        - 목적: 서비스 생성 시 converter가 주입되는지 확인.
        - 로직: converter 존재 여부와 타입 검사.
        - 데이터: fixture `service`.
        """
        assert service.converter is not None
        assert isinstance(service.converter, HWPConverter)

    def test_health_endpoint(self, service: ServiceInstance) -> None:
        """헬스 체크 엔드포인트 검증.

        Parameters
        ----------
        service : ServiceInstance
            HWPService fixture.

        Notes
        -----
        - 목적: health 응답의 상태/서비스명 확인.
        - 로직: 반환 dict의 key/value 검사.
        - 데이터: fixture `service`.
        """
        result = service.health()
        assert result["status"] == "healthy"
        assert result["service"] == "hwp-parser"

    def test_formats_endpoint(self, service: ServiceInstance) -> None:
        """지원 포맷 엔드포인트 검증.

        Parameters
        ----------
        service : ServiceInstance
            HWPService fixture.

        Notes
        -----
        - 목적: 지원 포맷 목록에 핵심 포맷 포함 여부 확인.
        - 로직: supported_formats 존재 및 값 포함 검사.
        - 데이터: fixture `service`.
        """
        result = service.formats()
        assert "supported_formats" in result
        assert "txt" in result["supported_formats"]
        assert "html" in result["supported_formats"]
        assert "markdown" in result["supported_formats"]
        assert "odt" in result["supported_formats"]


class TestApiServe:
    """API 실행 래퍼 테스트"""

    def test_serve_invokes_bentoml(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """serve()가 bentoml serve를 호출하는지 검증.

        Parameters
        ----------
        monkeypatch : pytest.MonkeyPatch
            subprocess.run 패치에 사용.

        Notes
        -----
        - 목적: CLI 래퍼 호출 경로 확인.
        - 로직: subprocess.run 호출 인자를 캡처해 비교.
        - 데이터: 없음.
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
    """ConversionResponse 테스트"""

    def test_response_model(self) -> None:
        """응답 모델 생성 검증.

        Notes
        -----
        - 목적: ConversionResponse 기본 필드가 정상 생성되는지 확인.
        - 로직: 생성 후 필드 값 비교.
        - 데이터: 하드코딩된 테스트 값.
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
    """_result_to_response 함수 테스트"""

    def test_text_result_to_response(
        self, converter: HWPConverter, sample_hwp_file: Path
    ) -> None:
        """텍스트 결과를 API 응답으로 변환 검증.

        Parameters
        ----------
        converter : HWPConverter
            변환기 fixture.
        sample_hwp_file : Path
            샘플 HWP 파일.

        Notes
        -----
        - 목적: 텍스트 결과가 문자열로 직렬화되는지 확인.
        - 로직: output_format/is_binary/content 타입 검사.
        - 데이터: fixtures `converter`, `sample_hwp_file`.
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
        """바이너리 결과를 base64 응답으로 변환 검증.

        Parameters
        ----------
        converter : HWPConverter
            변환기 fixture.
        sample_hwp_file : Path
            샘플 HWP 파일.

        Notes
        -----
        - 목적: ODT 결과가 base64로 인코딩되는지 확인.
        - 로직: is_binary/포맷 검사 후 base64 디코딩으로 ZIP 시그니처 확인.
        - 데이터: fixtures `converter`, `sample_hwp_file`.
        """
        result = converter.to_odt(sample_hwp_file)
        response = _result_to_response(result)

        assert isinstance(response, ConversionResponse)
        assert response.output_format == "odt"
        assert response.is_binary is True
        # base64로 디코딩 가능해야 함
        decoded = base64.b64decode(response.content)
        assert decoded[:2] == b"PK"  # ZIP 시그니처


class TestServiceConversion:
    """서비스 변환 테스트"""

    @pytest.fixture
    def service(self) -> ServiceInstance:
        """HWPService 인스턴스.

        Notes
        -----
        - 목적: 변환 API 테스트용 서비스 인스턴스 제공.
        - 로직: HWPService 직접 생성.
        - 데이터: 없음.
        """
        return HWPService()

    def test_convert_to_text(
        self, service: ServiceInstance, sample_hwp_file: Path
    ) -> None:
        """REST API 텍스트 변환 검증.

        Parameters
        ----------
        service : ServiceInstance
            HWPService fixture.
        sample_hwp_file : Path
            샘플 HWP 파일.

        Notes
        -----
        - 목적: convert_to_text가 텍스트 응답을 반환하는지 확인.
        - 로직: output_format/is_binary 검사.
        - 데이터: fixtures `service`, `sample_hwp_file`.
        """
        response = service.convert_to_text(sample_hwp_file)
        assert response.output_format == "txt"
        assert response.is_binary is False

    def test_convert_to_html(
        self, service: ServiceInstance, sample_hwp_file: Path
    ) -> None:
        """REST API HTML 변환 검증.

        Parameters
        ----------
        service : ServiceInstance
            HWPService fixture.
        sample_hwp_file : Path
            샘플 HWP 파일.

        Notes
        -----
        - 목적: convert_to_html 결과 포맷 확인.
        - 로직: output_format/is_binary 검사.
        - 데이터: fixtures `service`, `sample_hwp_file`.
        """
        response = service.convert_to_html(sample_hwp_file)
        assert response.output_format == "html"
        assert response.is_binary is False

    def test_convert_to_markdown(
        self, service: ServiceInstance, sample_hwp_file: Path
    ) -> None:
        """REST API Markdown 변환 검증.

        Parameters
        ----------
        service : ServiceInstance
            HWPService fixture.
        sample_hwp_file : Path
            샘플 HWP 파일.

        Notes
        -----
        - 목적: convert_to_markdown 결과 포맷 확인.
        - 로직: output_format/is_binary 검사.
        - 데이터: fixtures `service`, `sample_hwp_file`.
        """
        response = service.convert_to_markdown(sample_hwp_file)
        assert response.output_format == "markdown"
        assert response.is_binary is False

    def test_convert_to_odt(
        self, service: ServiceInstance, sample_hwp_file: Path
    ) -> None:
        """REST API ODT 변환 검증.

        Parameters
        ----------
        service : ServiceInstance
            HWPService fixture.
        sample_hwp_file : Path
            샘플 HWP 파일.

        Notes
        -----
        - 목적: convert_to_odt가 바이너리 응답을 반환하는지 확인.
        - 로직: output_format/is_binary 검사.
        - 데이터: fixtures `service`, `sample_hwp_file`.
        """
        response = service.convert_to_odt(sample_hwp_file)
        assert response.output_format == "odt"
        assert response.is_binary is True

    def test_convert_with_format(
        self, service: ServiceInstance, sample_hwp_file: Path
    ) -> None:
        """포맷 지정 변환 검증.

        Parameters
        ----------
        service : ServiceInstance
            HWPService fixture.
        sample_hwp_file : Path
            샘플 HWP 파일.

        Notes
        -----
        - 목적: convert에 output_format을 전달했을 때 포맷 반영 확인.
        - 로직: output_format 값 검사.
        - 데이터: fixtures `service`, `sample_hwp_file`.
        """
        response = service.convert(sample_hwp_file, output_format="html")
        assert response.output_format == "html"

    def test_convert_large_file(
        self, service: ServiceInstance, all_hwp_files: list[Path]
    ) -> None:
        """큰 파일 변환 검증.

        Parameters
        ----------
        service : ServiceInstance
            HWPService fixture.
        all_hwp_files : list[Path]
            전체 HWP 파일 목록.

        Notes
        -----
        - 목적: 가장 큰 파일 변환 결과 확인.
        - 로직: max(size) 파일을 convert_to_markdown로 변환.
        - 데이터: fixture `all_hwp_files`.
        """
        large_file = max(all_hwp_files, key=lambda f: f.stat().st_size)
        response = service.convert_to_markdown(large_file)
        assert response.output_format == "markdown"
        assert response.is_binary is False

    def test_convert_bulk_files(
        self, service: ServiceInstance, small_hwp_files: list[Path]
    ) -> None:
        """벌크 파일 변환 검증.

        Parameters
        ----------
        service : ServiceInstance
            HWPService fixture.
        small_hwp_files : list[Path]
            작은 HWP 파일 목록.

        Notes
        -----
        - 목적: 여러 파일 변환 결과 개수 확인.
        - 로직: 각 파일을 convert_to_text로 변환.
        - 데이터: fixture `small_hwp_files`.
        """
        results = [service.convert_to_text(f) for f in small_hwp_files]
        assert len(results) == len(small_hwp_files)
        assert all(r.output_format == "txt" for r in results)


# === 에지 케이스 ===


class TestServiceHttpConfig:
    """HTTP 설정 에지 케이스 테스트"""

    def test_http_config_includes_cors(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """CORS 설정이 HTTP config에 반영되는지 검증.

        Notes
        -----
        - 목적: CORS 활성화 시 _http_config 분기 커버.
        - 로직: 환경변수 설정 후 모듈 리로드로 config 재평가.
        - 데이터: 테스트용 CORS 설정.
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
