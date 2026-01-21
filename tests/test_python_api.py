"""Python API (HWPConverter) 테스트."""

from __future__ import annotations

from pathlib import Path

import pytest

from hwp_parser.core import ConversionResult, HWPConverter


# === 핵심 케이스 ===


class TestHWPConverterInit:
    """HWPConverter 초기화 테스트 스위트.

    테스트 대상:
        - HWPConverter 인스턴스 생성
        - SUPPORTED_FORMATS 클래스 상수

    검증 범위:
        1. 인스턴스 생성 성공 여부
        2. 지원 포맷 목록 정확성

    관련 테스트:
        - TestConvert: 실제 변환 동작 테스트
    """

    def test_create_converter(self) -> None:
        """HWPConverter 인스턴스가 정상적으로 생성되는지 검증.

        시나리오:
            기본 생성자로 HWPConverter를 생성하면
            None이 아닌 유효한 인스턴스가 반환되어야 한다.

        의존성:
            - 모듈: hwp_parser.core.HWPConverter
        """
        converter = HWPConverter()
        assert converter is not None

    def test_supported_formats(self) -> None:
        """지원 포맷 상수가 올바르게 정의되어 있는지 검증.

        시나리오:
            SUPPORTED_FORMATS 클래스 상수는 convert() 메서드에서
            포맷 검증에 사용된다. 지원하는 4가지 포맷이 정확히 정의되어야 한다.

        의존성:
            - 모듈: hwp_parser.core.HWPConverter.SUPPORTED_FORMATS

        관련 테스트:
            - TestConvert.test_convert_unsupported_format: 미지원 포맷 검증
        """
        assert HWPConverter.SUPPORTED_FORMATS == ("txt", "html", "markdown", "odt")


class TestFileValidation:
    """파일 경로 검증 테스트 스위트.

    테스트 대상:
        - HWPConverter._validate_file() 내부 메서드

    검증 범위:
        1. 존재하는 파일 → Path 반환
        2. 존재하지 않는 파일 → FileNotFoundError
        3. 디렉터리 입력 → ValueError
        4. 문자열 경로 → Path 변환

    비즈니스 컨텍스트:
        모든 변환 메서드는 내부적으로 _validate_file()을 호출하여
        입력 파일을 검증한다. 잘못된 입력은 조기에 거부해야 한다.

    관련 테스트:
        - TestConverterErrorPaths: 변환 중 발생하는 에러 처리
    """

    def test_validate_existing_file(
        self, converter: HWPConverter, sample_hwp_file: Path
    ) -> None:
        """존재하는 파일 → 경로 반환.

        Given: 유효한 HWP 파일 경로
        When: _validate_file 호출
        Then: 동일한 Path 반환
        """
        result = converter._validate_file(sample_hwp_file)
        assert result == sample_hwp_file

    def test_validate_nonexistent_file(
        self, converter: HWPConverter, nonexistent_file: Path
    ) -> None:
        """존재하지 않는 파일 → FileNotFoundError.

        Given: 존재하지 않는 파일 경로
        When: _validate_file 호출
        Then: FileNotFoundError 발생
        """
        with pytest.raises(FileNotFoundError):
            converter._validate_file(nonexistent_file)

    def test_validate_directory_raises_error(
        self, converter: HWPConverter, temp_directory: Path
    ) -> None:
        """디렉터리 입력 → ValueError.

        Given: 디렉터리 경로
        When: _validate_file 호출
        Then: ValueError("디렉토리가 입력되었습니다") 발생

        파일만 허용, 디렉터리 입력은 명시적 거부.
        """
        with pytest.raises(ValueError, match="디렉토리가 입력되었습니다"):
            converter._validate_file(temp_directory)

    def test_validate_string_path(
        self, converter: HWPConverter, sample_hwp_file: Path
    ) -> None:
        """문자열 경로 → Path로 변환.

        Given: 문자열 형태의 파일 경로
        When: _validate_file 호출
        Then: Path 객체 반환
        """
        result = converter._validate_file(str(sample_hwp_file))  # type: ignore
        assert isinstance(result, Path)


class TestToHtml:
    """HTML 변환 테스트 스위트.

    테스트 대상:
        - HWPConverter.to_html() 메서드

    검증 범위:
        1. 반환값이 ConversionResult 타입
        2. output_format="html", pipeline="hwp→xhtml"
        3. 결과에 HTML 태그 포함

    변환 파이프라인:
        HWP → pyhwp(hwp5html) → XHTML

    관론 테스트:
        - TestToText: HTML을 텍스트로 추가 변환
        - TestToMarkdown: HTML을 마크다운으로 추가 변환
    """

    def test_to_html_returns_result(
        self, converter: HWPConverter, sample_hwp_file: Path
    ) -> None:
        """HWP → HTML 변환 결과.

        Given: 유효한 HWP 파일
        When: to_html 호출
        Then: ConversionResult(output_format="html", pipeline="hwp→xhtml")
        """
        result = converter.to_html(sample_hwp_file)
        assert isinstance(result, ConversionResult)
        assert result.output_format == "html"
        assert result.pipeline == "hwp→xhtml"
        assert isinstance(result.content, str)
        assert not result.is_binary

    def test_to_html_contains_html_tags(
        self, converter: HWPConverter, sample_hwp_file: Path
    ) -> None:
        """HTML 결과에 태그 포함 확인.

        Given: 유효한 HWP 파일
        When: to_html 호출
        Then: 결과에 <html> 또는 <!doctype> 포함
        """
        result = converter.to_html(sample_hwp_file)
        content = result.content
        assert isinstance(content, str)
        assert "<html" in content.lower() or "<!doctype" in content.lower()


class TestToText:
    """텍스트 변환 테스트 스위트.

    테스트 대상:
        - HWPConverter.to_text() 메서드

    검증 범위:
        1. 반환값이 ConversionResult 타입
        2. output_format="txt", pipeline="hwp→xhtml→txt"
        3. 결과에 HTML 태그 제거됨

    변환 파이프라인:
        HWP → pyhwp(hwp5html) → XHTML → html2text → TXT

    관련 테스트:
        - TestToHtml: HTML 변환 (중간 단계)
    """

    def test_to_text_returns_result(
        self, converter: HWPConverter, sample_hwp_file: Path
    ) -> None:
        """HWP → TXT 변환 결과.

        Given: 유효한 HWP 파일
        When: to_text 호출
        Then: ConversionResult(output_format="txt", pipeline="hwp→xhtml→txt")
        """
        result = converter.to_text(sample_hwp_file)
        assert isinstance(result, ConversionResult)
        assert result.output_format == "txt"
        assert result.pipeline == "hwp→xhtml→txt"
        assert isinstance(result.content, str)
        assert not result.is_binary

    def test_to_text_no_html_tags(
        self, converter: HWPConverter, sample_hwp_file: Path
    ) -> None:
        """텍스트 결과에 HTML 태그 제거 확인.

        Given: 유효한 HWP 파일
        When: to_text 호출
        Then: <html>, <body> 태그 미포함
        """
        result = converter.to_text(sample_hwp_file)
        content = result.content
        assert isinstance(content, str)
        assert "<html" not in content.lower()
        assert "<body" not in content.lower()


class TestToMarkdown:
    """Markdown 변환 테스트 스위트.

    테스트 대상:
        - HWPConverter.to_markdown() 메서드

    검증 범위:
        1. 반환값이 ConversionResult 타입
        2. output_format="markdown", pipeline="hwp→xhtml→markdown"

    변환 파이프라인:
        HWP → pyhwp(hwp5html) → XHTML → html-to-markdown → Markdown

    의존성:
        - 외부 라이브러리: html-to-markdown

    관련 테스트:
        - TestMarkdownImportError: html-to-markdown 미설치 시 동작
    """

    def test_to_markdown_returns_result(
        self, converter: HWPConverter, sample_hwp_file: Path
    ) -> None:
        """HWP → Markdown 변환 결과.

        Given: 유효한 HWP 파일
        When: to_markdown 호출
        Then: ConversionResult(output_format="markdown", pipeline="hwp→xhtml→markdown")
        """
        result = converter.to_markdown(sample_hwp_file)
        assert isinstance(result, ConversionResult)
        assert result.output_format == "markdown"
        assert result.pipeline == "hwp→xhtml→markdown"
        assert isinstance(result.content, str)
        assert not result.is_binary


class TestToOdt:
    """ODT 변환 테스트 스위트.

    테스트 대상:
        - HWPConverter.to_odt() 메서드

    검증 범위:
        1. 반환값이 ConversionResult 타입, is_binary=True
        2. output_format="odt", pipeline="hwp→odt"
        3. 결과가 유효한 ZIP 파일 (ODT는 ZIP 형식)

    변환 파이프라인:
        HWP → pyhwp(hwp5odt) → ODT

    관련 테스트:
        - TestConverterErrorPaths.test_to_odt_*: ODT 변환 에러 처리
    """

    def test_to_odt_returns_binary(
        self, converter: HWPConverter, sample_hwp_file: Path
    ) -> None:
        """HWP → ODT 바이너리 결과.

        Given: 유효한 HWP 파일
        When: to_odt 호출
        Then: ConversionResult(is_binary=True, content=bytes)
        """
        result = converter.to_odt(sample_hwp_file)
        assert isinstance(result, ConversionResult)
        assert result.output_format == "odt"
        assert result.pipeline == "hwp→odt"
        assert isinstance(result.content, bytes)
        assert result.is_binary

    def test_to_odt_is_valid_zip(
        self, converter: HWPConverter, sample_hwp_file: Path
    ) -> None:
        """ODT 결과가 ZIP 형식.

        Given: 유효한 HWP 파일
        When: to_odt 호출
        Then: 결과 바이너리가 "PK" 시그니처로 시작

        ODT는 내부적으로 ZIP 압축 형식 사용.
        """
        result = converter.to_odt(sample_hwp_file)
        content = result.content
        assert isinstance(content, bytes)
        assert content[:2] == b"PK"


class TestConvert:
    """범용 convert() 메서드 테스트 스위트.

    테스트 대상:
        - HWPConverter.convert(file, output_format) 메서드

    검증 범위:
        1. 모든 지원 포맷(txt, html, markdown, odt)으로 변환
        2. 미지원 포맷 입력 시 ValueError
        3. 포맷 미지정 시 기본값(markdown) 적용

    비즈니스 컨텍스트:
        convert()는 내부적으로 to_text(), to_html(), to_markdown(), to_odt()를
        호출하는 통합 진입점이다. 포맷 검증 후 적절한 메서드로 라우팅한다.

    관련 테스트:
        - TestHWPConverterInit.test_supported_formats: 지원 포맷 상수
    """

    @pytest.mark.parametrize("output_format", ["txt", "html", "markdown", "odt"])
    def test_convert_all_formats(
        self, converter: HWPConverter, sample_hwp_file: Path, output_format: str
    ) -> None:
        """모든 지원 포맷 변환.

        Given: 유효한 HWP 파일, 지원 포맷
        When: convert(file, format) 호출
        Then: output_format이 지정값과 일치
        """
        result = converter.convert(sample_hwp_file, output_format)  # type: ignore
        assert result.output_format == output_format

    def test_convert_unsupported_format(
        self, converter: HWPConverter, sample_hwp_file: Path
    ) -> None:
        """미지원 포맷 → ValueError.

        Given: 유효한 HWP 파일, 미지원 포맷 "pdf"
        When: convert 호출
        Then: ValueError("지원하지 않는 포맷") 발생
        """
        with pytest.raises(ValueError, match="지원하지 않는 포맷"):
            converter.convert(sample_hwp_file, "pdf")  # type: ignore

    def test_convert_default_format_is_markdown(
        self, converter: HWPConverter, sample_hwp_file: Path
    ) -> None:
        """기본 변환 포맷 = markdown.

        Given: 유효한 HWP 파일
        When: convert(file) 호출 (포맷 미지정)
        Then: output_format == "markdown"
        """
        result = converter.convert(sample_hwp_file)
        assert result.output_format == "markdown"


class TestConversionResult:
    """ConversionResult 데이터클래스 테스트 스위트.

    테스트 대상:
        - ConversionResult 속성 (source_path, source_name, converted_at 등)
        - ConversionResult.to_dict() 메서드

    검증 범위:
        1. 변환 결과 객체의 속성 접근 가능 여부
        2. to_dict() 직렬화 결과에 필수 키 포함

    비즈니스 컨텍스트:
        ConversionResult는 모든 변환 메서드의 반환 타입이다.
        REST API에서는 to_dict()를 통해 JSON 응답으로 변환된다.
    """

    def test_result_properties(
        self, converter: HWPConverter, sample_hwp_file: Path
    ) -> None:
        """결과 객체 속성 확인.

        Given: 변환 완료된 ConversionResult
        When: 속성 접근
        Then: source_path, source_name, converted_at 존재
        """
        result = converter.to_text(sample_hwp_file)

        assert result.source_path == sample_hwp_file
        assert result.source_name == sample_hwp_file.name
        assert result.converted_at is not None

    def test_result_to_dict(
        self, converter: HWPConverter, sample_hwp_file: Path
    ) -> None:
        """to_dict() 직렬화 확인.

        Given: 변환 완료된 ConversionResult
        When: to_dict() 호출
        Then: 필수 키 모두 포함
        """
        result = converter.to_text(sample_hwp_file)
        d = result.to_dict()

        assert "source_name" in d
        assert "output_format" in d
        assert "pipeline" in d
        assert "converted_at" in d
        assert "content_length" in d
        assert "is_binary" in d


class TestMultipleFiles:
    """여러 파일 변환 테스트 스위트.

    테스트 대상:
        - 다양한 크기의 HWP 파일들에 대한 변환

    검증 범위:
        1. 큰 파일에 대한 변환 성공 여부
        2. 여러 파일 순차 변환 성공 여부

    비즈니스 컨텍스트:
        실제 운영 환경에서는 다양한 크기의 HWP 파일을 처리해야 한다.
        tests/fixtures/에 있는 실제 파일로 테스트하여 신뢰성을 보장한다.

    의존성:
        - pytest fixture: all_hwp_files, small_hwp_files (conftest.py)
        - 테스트 데이터: tests/fixtures/*.hwp
    """

    def test_convert_large_file_to_markdown(
        self, converter: HWPConverter, all_hwp_files: list[Path]
    ) -> None:
        """큰 파일 Markdown 변환.

        Given: 가장 큰 HWP 파일
        When: to_markdown 호출
        Then: 정상 변환, 비어있지 않은 콘텐츠
        """
        large_file = max(all_hwp_files, key=lambda f: f.stat().st_size)
        result = converter.to_markdown(large_file)
        assert result.output_format == "markdown"
        assert len(result.content) > 0

    def test_convert_multiple_files_to_text(
        self, converter: HWPConverter, small_hwp_files: list[Path]
    ) -> None:
        """여러 파일 TXT 변환.

        Given: 작은 HWP 파일 목록
        When: 각 파일에 to_text 호출
        Then: 모든 파일 정상 변환
        """
        for hwp_file in small_hwp_files:
            result = converter.to_text(hwp_file)
            assert result.output_format == "txt"
            assert len(result.content) > 0

    def test_convert_multiple_files_to_markdown(
        self, converter: HWPConverter, small_hwp_files: list[Path]
    ) -> None:
        """여러 파일 Markdown 변환.

        Given: 작은 HWP 파일 목록
        When: 각 파일에 to_markdown 호출
        Then: 모든 파일 정상 변환
        """
        for hwp_file in small_hwp_files:
            result = converter.to_markdown(hwp_file)
            assert result.output_format == "markdown"
            assert len(result.content) > 0


# === 에지 케이스 ===


class TestConverterErrorPaths:
    """변환기 예외 경로 테스트 스위트.

    테스트 대상:
        - to_html(), to_odt() 메서드의 에러 처리 로직

    검증 범위:
        1. pyhwp CLI 실패 (returncode != 0) → RuntimeError
        2. 결과 파일 미생성 → RuntimeError
        3. RelaxNG 검증 실패 → 명확한 에러 메시지

    비즈니스 컨텍스트:
        HWPConverter는 내부적으로 pyhwp CLI(hwp5html, hwp5odt)를
        subprocess로 호출한다. 외부 도구 실패 시 명확한 예외를 전달해야 한다.

    테스트 전략:
        subprocess.run을 mocking하여 실패 시나리오를 재현한다.
        실제 pyhwp CLI 실패은 재현하기 어려우므로 mocking 사용.

    관련 테스트:
        - TestFileValidation: 입력 파일 검증
    """

    def test_to_html_subprocess_failure(self, tmp_path: Path) -> None:
        """hwp5html 실패 → RuntimeError.

        Given: subprocess가 returncode=1 반환하도록 mocking
        When: to_html 호출
        Then: RuntimeError("HTML 변환 실패") 발생

        외부 CLI 도구 실패 시 명확한 예외 전달.
        """
        hwp_file = tmp_path / "sample.hwp"
        hwp_file.write_bytes(b"dummy")

        def _fake_run(*_args: object, **_kwargs: object):
            class Result:
                returncode = 1
                stderr = "boom"

            return Result()

        converter = HWPConverter()
        import subprocess

        original_run = subprocess.run
        subprocess.run = _fake_run  # type: ignore[assignment]
        try:
            with pytest.raises(RuntimeError, match="HTML 변환 실패"):
                converter.to_html(hwp_file)
        finally:
            subprocess.run = original_run  # type: ignore[assignment]

    def test_to_html_missing_output(self, tmp_path: Path) -> None:
        """결과 파일 미생성 → RuntimeError.

        Given: subprocess 성공하지만 index.xhtml 미생성
        When: to_html 호출
        Then: RuntimeError("결과 파일이 생성되지 않음") 발생
        """
        hwp_file = tmp_path / "sample.hwp"
        hwp_file.write_bytes(b"dummy")

        def _fake_run(*_args: object, **_kwargs: object):
            class Result:
                returncode = 0
                stderr = ""

            return Result()

        converter = HWPConverter()
        import subprocess

        original_run = subprocess.run
        subprocess.run = _fake_run  # type: ignore[assignment]
        try:
            with pytest.raises(RuntimeError, match="결과 파일이 생성되지 않음"):
                converter.to_html(hwp_file)
        finally:
            subprocess.run = original_run  # type: ignore[assignment]

    def test_to_odt_relaxng_error(self, tmp_path: Path) -> None:
        """RelaxNG 검증 실패 → RuntimeError.

        Given: stderr에 "RelaxNG" 포함된 실패
        When: to_odt 호출
        Then: RuntimeError("RelaxNG") 발생

        HWP 문서 구조 검증 실패를 명확히 전달.
        """
        hwp_file = tmp_path / "sample.hwp"
        hwp_file.write_bytes(b"dummy")

        def _fake_run(*_args: object, **_kwargs: object):
            class Result:
                returncode = 1
                stderr = "RelaxNG ValidationFailed"

            return Result()

        converter = HWPConverter()
        import subprocess

        original_run = subprocess.run
        subprocess.run = _fake_run  # type: ignore[assignment]
        try:
            with pytest.raises(RuntimeError, match="RelaxNG"):
                converter.to_odt(hwp_file)
        finally:
            subprocess.run = original_run  # type: ignore[assignment]

    def test_to_odt_missing_output(self, tmp_path: Path) -> None:
        """ODT 결과 파일 미생성 → RuntimeError.

        Given: subprocess 성공하지만 ODT 미생성
        When: to_odt 호출
        Then: RuntimeError("결과 파일이 생성되지 않음") 발생
        """
        hwp_file = tmp_path / "sample.hwp"
        hwp_file.write_bytes(b"dummy")

        def _fake_run(*_args: object, **_kwargs: object):
            class Result:
                returncode = 0
                stderr = ""

            return Result()

        converter = HWPConverter()
        import subprocess

        original_run = subprocess.run
        subprocess.run = _fake_run  # type: ignore[assignment]
        try:
            with pytest.raises(RuntimeError, match="결과 파일이 생성되지 않음"):
                converter.to_odt(hwp_file)
        finally:
            subprocess.run = original_run  # type: ignore[assignment]

    def test_to_odt_generic_error(self, tmp_path: Path) -> None:
        """ODT 일반 실패 → RuntimeError.

        Given: RelaxNG 외 다른 오류로 실패
        When: to_odt 호출
        Then: RuntimeError("ODT 변환 실패") 발생
        """
        hwp_file = tmp_path / "sample.hwp"
        hwp_file.write_bytes(b"dummy")

        def _fake_run(*_args: object, **_kwargs: object):
            class Result:
                returncode = 1
                stderr = "Unexpected failure"

            return Result()

        converter = HWPConverter()
        import subprocess

        original_run = subprocess.run
        subprocess.run = _fake_run  # type: ignore[assignment]
        try:
            with pytest.raises(RuntimeError, match="ODT 변환 실패"):
                converter.to_odt(hwp_file)
        finally:
            subprocess.run = original_run  # type: ignore[assignment]


class TestConverterLogging:
    """로깅 초기화 경로 테스트 스위트.

    테스트 대상:
        - HWPConverter._configure_logger() 클래스 메서드
        - HWPConverter._log_start(), _log_finish() 메서드

    검증 범위:
        1. verbose=True 시 로거 설정
        2. 로거 재설정 시 조기 반환 (멱등성)
        3. 존재하지 않는 파일에 대한 로깅 정상 처리

    비즈니스 컨텍스트:
        loguru를 사용한 로깅은 디버깅 목적이다.
        _logger_configured 플래그로 중복 설정을 방지한다.
    """

    def test_verbose_configures_logger(self) -> None:
        """verbose=True → 로거 설정.

        Given: _logger_configured=False
        When: HWPConverter(verbose=True) 생성
        Then: _logger_configured=True
        """
        HWPConverter._logger_configured = False
        converter = HWPConverter(verbose=True)
        assert converter.verbose is True
        assert HWPConverter._logger_configured is True

    def test_configure_logger_idempotent(self) -> None:
        """로거 재설정 → 조기 반환.

        Given: _logger_configured=True
        When: _configure_logger() 재호출
        Then: 플래그 유지 (중복 설정 방지)
        """
        HWPConverter._logger_configured = True
        HWPConverter._configure_logger()
        assert HWPConverter._logger_configured is True

    def test_log_start_with_missing_file(self, tmp_path: Path) -> None:
        """존재하지 않는 파일 로깅 → 정상 처리.

        Given: 존재하지 않는 파일 경로
        When: _log_start 호출
        Then: 예외 없이 완료 (exists=False 분기)
        """
        converter = HWPConverter(verbose=True)
        missing_file = tmp_path / "missing.hwp"
        converter._log_start(missing_file, "markdown")

    def test_log_finish_with_missing_file(self, tmp_path: Path) -> None:
        """존재하지 않는 파일 로깅 → 정상 처리.

        Given: 존재하지 않는 파일 경로
        When: _log_finish 호출
        Then: 예외 없이 완료
        """
        converter = HWPConverter(verbose=True)
        missing_file = tmp_path / "missing.hwp"
        converter._log_finish(
            missing_file,
            "markdown",
            "hwp→xhtml→markdown",
            "content",
            0.0,
        )


class TestMarkdownImportError:
    """Markdown 변환 ImportError 경로 테스트 스위트.

    테스트 대상:
        - to_markdown()에서 html-to-markdown import 실패 시 동작

    검증 범위:
        1. html_to_markdown import 실패 → ImportError("html-to-markdown")

    비즈니스 컨텍스트:
        html-to-markdown은 선택적 의존성이다.
        미설치 시 명확한 에러 메시지를 제공해야 한다.

    테스트 전략:
        builtins.__import__를 mocking하여 import 실패을 재현한다.

    관련 테스트:
        - TestToMarkdown: 정상 Markdown 변환
    """

    def test_to_markdown_import_error(self, tmp_path: Path, monkeypatch) -> None:
        """html_to_markdown 미설치 → ImportError.

        Given: html_to_markdown import 실패하도록 mocking
        When: to_markdown 호출
        Then: ImportError("html-to-markdown") 발생

        의존성 누락 시 명확한 에러 메시지 제공.
        """
        hwp_file = tmp_path / "sample.hwp"
        hwp_file.write_bytes(b"dummy")

        import builtins

        original_import = builtins.__import__

        def _fake_import(name, *args, **kwargs):
            if name == "html_to_markdown":
                raise ImportError("missing")
            return original_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", _fake_import)

        converter = HWPConverter()
        with pytest.raises(ImportError, match="html-to-markdown"):
            converter.to_markdown(hwp_file)
