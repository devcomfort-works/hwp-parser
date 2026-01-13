"""
BentoML HWP 변환 서비스

HWP 파일을 다양한 포맷으로 변환하는 REST API를 제공합니다.
"""

from __future__ import annotations

import base64
from pathlib import Path
from typing import Annotated, Any, Literal, cast

import bentoml
from pydantic import BaseModel, Field

from hwp_parser.adapters.api.config import config
from hwp_parser.core import ConversionResult, HWPConverter

OutputFormat = Literal["txt", "html", "markdown", "odt"]


class ConversionResponse(BaseModel):
    """변환 결과 응답 모델"""

    content: str = Field(description="변환된 콘텐츠 (ODT의 경우 base64 인코딩)")
    source_name: str = Field(description="원본 파일명")
    output_format: OutputFormat = Field(description="출력 포맷")
    pipeline: str = Field(description="변환 파이프라인")
    is_binary: bool = Field(description="바이너리 콘텐츠 여부")
    content_length: int = Field(description="콘텐츠 길이")


class ErrorResponse(BaseModel):
    """에러 응답 모델"""

    error: str = Field(description="에러 메시지")
    detail: str | None = Field(default=None, description="상세 에러 정보")


def _result_to_response(result: ConversionResult) -> ConversionResponse:
    """ConversionResult를 API 응답으로 변환"""
    if result.is_binary:
        content = base64.b64encode(cast(bytes, result.content)).decode("utf-8")
    else:
        content = cast(str, result.content)

    return ConversionResponse(
        content=content,
        source_name=result.source_name,
        output_format=result.output_format,
        pipeline=result.pipeline,
        is_binary=result.is_binary,
        content_length=len(result.content),
    )


# CORS 설정 구성
_http_config: dict[str, Any] = {"port": config.port}
if config.cors_enabled:
    _http_config["cors"] = {
        "enabled": True,
        "access_control_allow_origins": config.cors_origins,
        "access_control_allow_methods": ["GET", "POST", "OPTIONS"],
        "access_control_allow_headers": ["*"],
    }


@bentoml.service(
    name=config.name,
    workers=config.workers,
    traffic={
        "timeout": config.timeout,
        "max_concurrency": config.max_concurrency,
    },
    http=_http_config,  # type: ignore[arg-type]
)
class HWPService:
    """
    HWP 파일 변환 BentoML 서비스

    HWP 파일을 텍스트, HTML, Markdown, ODT 포맷으로 변환합니다.

    Endpoints:
        POST /health - 헬스 체크
        POST /formats - 지원 포맷 목록
        POST /convert - 범용 변환
        POST /convert/text - 텍스트로 변환
        POST /convert/html - HTML로 변환
        POST /convert/markdown - Markdown으로 변환
        POST /convert/odt - ODT로 변환
    """

    def __init__(self) -> None:
        """서비스 초기화"""
        self.converter = HWPConverter()

    @bentoml.api
    def health(self) -> dict[str, str]:
        """헬스 체크 엔드포인트"""
        return {"status": "healthy", "service": "hwp-parser"}

    @bentoml.api
    def formats(self) -> dict[str, list[str]]:
        """지원 포맷 목록 반환"""
        return {"supported_formats": list(HWPConverter.SUPPORTED_FORMATS)}

    @bentoml.api(route="/convert/text")
    def convert_to_text(
        self,
        file: Annotated[
            Path, bentoml.validators.ContentType("application/octet-stream")
        ] = Field(description="변환할 HWP 파일"),
    ) -> ConversionResponse:
        """
        HWP 파일을 텍스트로 변환

        Args:
            file: HWP 파일

        Returns:
            변환된 텍스트 콘텐츠
        """
        return self._convert_file(file, "txt")

    @bentoml.api(route="/convert/html")
    def convert_to_html(
        self,
        file: Annotated[
            Path, bentoml.validators.ContentType("application/octet-stream")
        ] = Field(description="변환할 HWP 파일"),
    ) -> ConversionResponse:
        """
        HWP 파일을 HTML로 변환

        Args:
            file: HWP 파일

        Returns:
            변환된 HTML 콘텐츠
        """
        return self._convert_file(file, "html")

    @bentoml.api(route="/convert/markdown")
    def convert_to_markdown(
        self,
        file: Annotated[
            Path, bentoml.validators.ContentType("application/octet-stream")
        ] = Field(description="변환할 HWP 파일"),
    ) -> ConversionResponse:
        """
        HWP 파일을 Markdown으로 변환

        Args:
            file: HWP 파일

        Returns:
            변환된 Markdown 콘텐츠
        """
        return self._convert_file(file, "markdown")

    @bentoml.api(route="/convert/odt")
    def convert_to_odt(
        self,
        file: Annotated[
            Path, bentoml.validators.ContentType("application/octet-stream")
        ] = Field(description="변환할 HWP 파일"),
    ) -> ConversionResponse:
        """
        HWP 파일을 ODT로 변환

        Args:
            file: HWP 파일

        Returns:
            변환된 ODT 콘텐츠 (base64 인코딩)
        """
        return self._convert_file(file, "odt")

    @bentoml.api(route="/convert")
    def convert(
        self,
        file: Annotated[
            Path, bentoml.validators.ContentType("application/octet-stream")
        ] = Field(description="변환할 HWP 파일"),
        output_format: OutputFormat = Field(
            default="markdown",
            description="출력 포맷 (txt, html, markdown, odt)",
        ),
    ) -> ConversionResponse:
        """
        HWP 파일을 지정된 포맷으로 변환

        Args:
            file: HWP 파일
            output_format: 출력 포맷 (txt, html, markdown, odt)

        Returns:
            변환된 콘텐츠
        """
        return self._convert_file(file, output_format)

    def _convert_file(
        self, file: Path, output_format: OutputFormat
    ) -> ConversionResponse:
        """
        파일 변환 내부 메서드

        BentoML이 업로드된 파일을 임시 경로에 저장하므로,
        해당 경로를 그대로 사용하여 변환합니다.

        Args:
            file: 업로드된 파일 경로
            output_format: 출력 포맷

        Returns:
            변환 결과 응답
        """
        # BentoML이 제공하는 임시 파일 경로 사용
        result = self.converter.convert(file, output_format)
        return _result_to_response(result)
