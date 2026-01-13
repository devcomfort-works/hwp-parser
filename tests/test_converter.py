"""
HWPConverter 단위 테스트
"""

from __future__ import annotations

from pathlib import Path

import pytest

from hwp_parser.core import ConversionResult, HWPConverter


class TestHWPConverterInit:
    """HWPConverter 초기화 테스트"""

    def test_create_converter(self) -> None:
        """컨버터 인스턴스 생성"""
        converter = HWPConverter()
        assert converter is not None

    def test_supported_formats(self) -> None:
        """지원 포맷 확인"""
        assert HWPConverter.SUPPORTED_FORMATS == ("txt", "html", "markdown", "odt")


class TestFileValidation:
    """파일 검증 테스트"""

    def test_validate_existing_file(
        self, converter: HWPConverter, sample_hwp_file: Path
    ) -> None:
        """존재하는 파일 검증"""
        result = converter._validate_file(sample_hwp_file)
        assert result == sample_hwp_file

    def test_validate_nonexistent_file(
        self, converter: HWPConverter, nonexistent_file: Path
    ) -> None:
        """존재하지 않는 파일 검증 실패"""
        with pytest.raises(FileNotFoundError):
            converter._validate_file(nonexistent_file)

    def test_validate_directory_raises_error(
        self, converter: HWPConverter, temp_directory: Path
    ) -> None:
        """디렉토리 경로 입력 시 ValueError 발생"""
        with pytest.raises(ValueError, match="디렉토리가 입력되었습니다"):
            converter._validate_file(temp_directory)

    def test_validate_string_path(
        self, converter: HWPConverter, sample_hwp_file: Path
    ) -> None:
        """문자열 경로도 처리 가능"""
        result = converter._validate_file(str(sample_hwp_file))  # type: ignore
        assert isinstance(result, Path)


class TestToHtml:
    """HTML 변환 테스트"""

    def test_to_html_returns_result(
        self, converter: HWPConverter, sample_hwp_file: Path
    ) -> None:
        """HTML 변환 결과 반환"""
        result = converter.to_html(sample_hwp_file)
        assert isinstance(result, ConversionResult)
        assert result.output_format == "html"
        assert result.pipeline == "hwp→xhtml"
        assert isinstance(result.content, str)
        assert not result.is_binary

    def test_to_html_contains_html_tags(
        self, converter: HWPConverter, sample_hwp_file: Path
    ) -> None:
        """HTML 결과에 HTML 태그 포함"""
        result = converter.to_html(sample_hwp_file)
        content = result.content
        assert isinstance(content, str)
        assert "<html" in content.lower() or "<!doctype" in content.lower()


class TestToText:
    """텍스트 변환 테스트"""

    def test_to_text_returns_result(
        self, converter: HWPConverter, sample_hwp_file: Path
    ) -> None:
        """텍스트 변환 결과 반환"""
        result = converter.to_text(sample_hwp_file)
        assert isinstance(result, ConversionResult)
        assert result.output_format == "txt"
        assert result.pipeline == "hwp→xhtml→txt"
        assert isinstance(result.content, str)
        assert not result.is_binary

    def test_to_text_no_html_tags(
        self, converter: HWPConverter, sample_hwp_file: Path
    ) -> None:
        """텍스트 결과에 HTML 태그 없음"""
        result = converter.to_text(sample_hwp_file)
        content = result.content
        assert isinstance(content, str)
        # HTML 태그가 제거되었는지 확인
        assert "<html" not in content.lower()
        assert "<body" not in content.lower()


class TestToMarkdown:
    """Markdown 변환 테스트"""

    def test_to_markdown_returns_result(
        self, converter: HWPConverter, sample_hwp_file: Path
    ) -> None:
        """Markdown 변환 결과 반환"""
        result = converter.to_markdown(sample_hwp_file)
        assert isinstance(result, ConversionResult)
        assert result.output_format == "markdown"
        assert result.pipeline == "hwp→xhtml→markdown"
        assert isinstance(result.content, str)
        assert not result.is_binary


class TestToOdt:
    """ODT 변환 테스트"""

    def test_to_odt_returns_binary(
        self, converter: HWPConverter, sample_hwp_file: Path
    ) -> None:
        """ODT 변환은 바이너리 반환"""
        result = converter.to_odt(sample_hwp_file)
        assert isinstance(result, ConversionResult)
        assert result.output_format == "odt"
        assert result.pipeline == "hwp→odt"
        assert isinstance(result.content, bytes)
        assert result.is_binary

    def test_to_odt_is_valid_zip(
        self, converter: HWPConverter, sample_hwp_file: Path
    ) -> None:
        """ODT 파일은 유효한 ZIP 형식"""
        result = converter.to_odt(sample_hwp_file)
        content = result.content
        assert isinstance(content, bytes)
        # ODT는 ZIP 형식이므로 PK 시그니처로 시작
        assert content[:2] == b"PK"


class TestConvert:
    """범용 convert 메서드 테스트"""

    @pytest.mark.parametrize("output_format", ["txt", "html", "markdown", "odt"])
    def test_convert_all_formats(
        self, converter: HWPConverter, sample_hwp_file: Path, output_format: str
    ) -> None:
        """모든 지원 포맷 변환"""
        result = converter.convert(sample_hwp_file, output_format)  # type: ignore
        assert result.output_format == output_format

    def test_convert_unsupported_format(
        self, converter: HWPConverter, sample_hwp_file: Path
    ) -> None:
        """지원하지 않는 포맷 오류"""
        with pytest.raises(ValueError, match="지원하지 않는 포맷"):
            converter.convert(sample_hwp_file, "pdf")  # type: ignore

    def test_convert_default_format_is_markdown(
        self, converter: HWPConverter, sample_hwp_file: Path
    ) -> None:
        """기본 변환 포맷은 markdown"""
        result = converter.convert(sample_hwp_file)
        assert result.output_format == "markdown"


class TestConversionResult:
    """ConversionResult 테스트"""

    def test_result_properties(
        self, converter: HWPConverter, sample_hwp_file: Path
    ) -> None:
        """결과 객체 속성 확인"""
        result = converter.to_text(sample_hwp_file)

        assert result.source_path == sample_hwp_file
        assert result.source_name == sample_hwp_file.name
        assert result.converted_at is not None

    def test_result_to_dict(
        self, converter: HWPConverter, sample_hwp_file: Path
    ) -> None:
        """결과를 딕셔너리로 변환"""
        result = converter.to_text(sample_hwp_file)
        d = result.to_dict()

        assert "source_name" in d
        assert "output_format" in d
        assert "pipeline" in d
        assert "converted_at" in d
        assert "content_length" in d
        assert "is_binary" in d


class TestMultipleFiles:
    """여러 파일 변환 테스트"""

    def test_convert_multiple_files_to_text(
        self, converter: HWPConverter, small_hwp_files: list[Path]
    ) -> None:
        """여러 파일 텍스트 변환"""
        for hwp_file in small_hwp_files:
            result = converter.to_text(hwp_file)
            assert result.output_format == "txt"
            assert len(result.content) > 0

    def test_convert_multiple_files_to_markdown(
        self, converter: HWPConverter, small_hwp_files: list[Path]
    ) -> None:
        """여러 파일 마크다운 변환"""
        for hwp_file in small_hwp_files:
            result = converter.to_markdown(hwp_file)
            assert result.output_format == "markdown"
            assert len(result.content) > 0
