"""
BentoML API 서비스 테스트
"""

from __future__ import annotations

import base64
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest

from hwp_parser.adapters.api.service import (
    ConversionResponse,
    HWPService,
    _result_to_response,
)
from hwp_parser.core import HWPConverter

if TYPE_CHECKING:
    # 테스트에서는 실제 인스턴스 타입을 사용
    ServiceInstance = Any


class TestHWPService:
    """HWPService 테스트"""

    @pytest.fixture
    def service(self) -> ServiceInstance:
        """HWPService 인스턴스"""
        return HWPService()

    def test_service_init(self, service: ServiceInstance) -> None:
        """서비스 초기화"""
        assert service.converter is not None
        assert isinstance(service.converter, HWPConverter)

    def test_health_endpoint(self, service: ServiceInstance) -> None:
        """헬스 체크 엔드포인트"""
        result = service.health()
        assert result["status"] == "healthy"
        assert result["service"] == "hwp-parser"

    def test_formats_endpoint(self, service: ServiceInstance) -> None:
        """지원 포맷 엔드포인트"""
        result = service.formats()
        assert "supported_formats" in result
        assert "txt" in result["supported_formats"]
        assert "html" in result["supported_formats"]
        assert "markdown" in result["supported_formats"]
        assert "odt" in result["supported_formats"]


class TestConversionResponse:
    """ConversionResponse 테스트"""

    def test_response_model(self) -> None:
        """응답 모델 생성"""
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
        """텍스트 결과를 응답으로 변환"""
        result = converter.to_text(sample_hwp_file)
        response = _result_to_response(result)

        assert isinstance(response, ConversionResponse)
        assert response.output_format == "txt"
        assert response.is_binary is False
        assert isinstance(response.content, str)

    def test_binary_result_to_response(
        self, converter: HWPConverter, sample_hwp_file: Path
    ) -> None:
        """바이너리 결과를 응답으로 변환 (base64 인코딩)"""
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
        """HWPService 인스턴스"""
        return HWPService()

    def test_convert_to_text(
        self, service: ServiceInstance, sample_hwp_file: Path
    ) -> None:
        """텍스트 변환"""
        response = service.convert_to_text(sample_hwp_file)
        assert response.output_format == "txt"
        assert response.is_binary is False

    def test_convert_to_html(
        self, service: ServiceInstance, sample_hwp_file: Path
    ) -> None:
        """HTML 변환"""
        response = service.convert_to_html(sample_hwp_file)
        assert response.output_format == "html"
        assert response.is_binary is False

    def test_convert_to_markdown(
        self, service: ServiceInstance, sample_hwp_file: Path
    ) -> None:
        """Markdown 변환"""
        response = service.convert_to_markdown(sample_hwp_file)
        assert response.output_format == "markdown"
        assert response.is_binary is False

    def test_convert_to_odt(
        self, service: ServiceInstance, sample_hwp_file: Path
    ) -> None:
        """ODT 변환"""
        response = service.convert_to_odt(sample_hwp_file)
        assert response.output_format == "odt"
        assert response.is_binary is True

    def test_convert_with_format(
        self, service: ServiceInstance, sample_hwp_file: Path
    ) -> None:
        """포맷 지정 변환"""
        response = service.convert(sample_hwp_file, output_format="html")
        assert response.output_format == "html"
