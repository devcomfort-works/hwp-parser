"""
Python API (HWPConverter) 테스트
"""

from __future__ import annotations

from pathlib import Path

import pytest

from hwp_parser.core import ConversionResult, HWPConverter

# === 핵심 케이스 ===


class TestHWPConverterInit:
    """HWPConverter 초기화 테스트"""

    def test_create_converter(self) -> None:
        """컨버터 인스턴스 생성 검증.

        Notes
        -----
        - 목적: HWPConverter 생성 가능 여부 확인.
        - 로직: 인스턴스 생성 후 None 여부 검사.
        - 데이터: 없음.
        """
        converter = HWPConverter()
        assert converter is not None

    def test_supported_formats(self) -> None:
        """지원 포맷 상수 검증.

        Notes
        -----
        - 목적: SUPPORTED_FORMATS 값 확인.
        - 로직: 튜플 내용 비교.
        - 데이터: 클래스 상수.
        """
        assert HWPConverter.SUPPORTED_FORMATS == ("txt", "html", "markdown", "odt")


class TestFileValidation:
    """파일 검증 테스트"""

    def test_validate_existing_file(
        self, converter: HWPConverter, sample_hwp_file: Path
    ) -> None:
        """존재하는 파일 경로 검증.

        Parameters
        ----------
        converter : HWPConverter
            변환기 fixture.
        sample_hwp_file : Path
            샘플 HWP 파일.

        Notes
        -----
        - 목적: 유효한 파일 경로 통과 여부 확인.
        - 로직: 반환 Path가 입력과 동일한지 검사.
        - 데이터: fixtures `converter`, `sample_hwp_file`.
        """
        result = converter._validate_file(sample_hwp_file)
        assert result == sample_hwp_file

    def test_validate_nonexistent_file(
        self, converter: HWPConverter, nonexistent_file: Path
    ) -> None:
        """존재하지 않는 파일 경로 예외 검증.

        Parameters
        ----------
        converter : HWPConverter
            변환기 fixture.
        nonexistent_file : Path
            존재하지 않는 파일 경로.

        Notes
        -----
        - 목적: FileNotFoundError 발생 확인.
        - 로직: pytest.raises로 예외 체크.
        - 데이터: fixtures `converter`, `nonexistent_file`.
        """
        with pytest.raises(FileNotFoundError):
            converter._validate_file(nonexistent_file)

    def test_validate_directory_raises_error(
        self, converter: HWPConverter, temp_directory: Path
    ) -> None:
        """디렉토리 경로 입력 시 ValueError 검증.

        Parameters
        ----------
        converter : HWPConverter
            변환기 fixture.
        temp_directory : Path
            임시 디렉터리 경로.

        Notes
        -----
        - 목적: 디렉터리 입력 차단 동작 확인.
        - 로직: ValueError 및 메시지 패턴 검사.
        - 데이터: fixtures `converter`, `temp_directory`.
        """
        with pytest.raises(ValueError, match="디렉토리가 입력되었습니다"):
            converter._validate_file(temp_directory)

    def test_validate_string_path(
        self, converter: HWPConverter, sample_hwp_file: Path
    ) -> None:
        """문자열 경로 입력 처리 검증.

        Parameters
        ----------
        converter : HWPConverter
            변환기 fixture.
        sample_hwp_file : Path
            샘플 HWP 파일.

        Notes
        -----
        - 목적: 문자열 경로가 Path로 변환되는지 확인.
        - 로직: 반환 타입 검사.
        - 데이터: fixtures `converter`, `sample_hwp_file`.
        """
        result = converter._validate_file(str(sample_hwp_file))  # type: ignore
        assert isinstance(result, Path)


class TestToHtml:
    """HTML 변환 테스트"""

    def test_to_html_returns_result(
        self, converter: HWPConverter, sample_hwp_file: Path
    ) -> None:
        """HTML 변환 결과 검증.

        Parameters
        ----------
        converter : HWPConverter
            변환기 fixture.
        sample_hwp_file : Path
            샘플 HWP 파일.

        Notes
        -----
        - 목적: ConversionResult 기본 속성 확인.
        - 로직: 타입/포맷/파이프라인 검사.
        - 데이터: fixtures `converter`, `sample_hwp_file`.
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
        """HTML 태그 포함 여부 검증.

        Parameters
        ----------
        converter : HWPConverter
            변환기 fixture.
        sample_hwp_file : Path
            샘플 HWP 파일.

        Notes
        -----
        - 목적: 결과 문자열에 HTML/DOCTYPE 포함 확인.
        - 로직: 문자열 포함 검사.
        - 데이터: fixtures `converter`, `sample_hwp_file`.
        """
        result = converter.to_html(sample_hwp_file)
        content = result.content
        assert isinstance(content, str)
        assert "<html" in content.lower() or "<!doctype" in content.lower()


class TestToText:
    """텍스트 변환 테스트"""

    def test_to_text_returns_result(
        self, converter: HWPConverter, sample_hwp_file: Path
    ) -> None:
        """텍스트 변환 결과 검증.

        Parameters
        ----------
        converter : HWPConverter
            변환기 fixture.
        sample_hwp_file : Path
            샘플 HWP 파일.

        Notes
        -----
        - 목적: ConversionResult 속성 및 포맷 확인.
        - 로직: 타입/파이프라인 검사.
        - 데이터: fixtures `converter`, `sample_hwp_file`.
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
        """텍스트 결과에 HTML 태그 제거 검증.

        Parameters
        ----------
        converter : HWPConverter
            변환기 fixture.
        sample_hwp_file : Path
            샘플 HWP 파일.

        Notes
        -----
        - 목적: 텍스트 변환 시 HTML 태그 제거 확인.
        - 로직: <html>/<body> 미포함 검사.
        - 데이터: fixtures `converter`, `sample_hwp_file`.
        """
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
        """Markdown 변환 결과 검증.

        Parameters
        ----------
        converter : HWPConverter
            변환기 fixture.
        sample_hwp_file : Path
            샘플 HWP 파일.

        Notes
        -----
        - 목적: Markdown 결과의 포맷/파이프라인 확인.
        - 로직: output_format/pipeline/type 검사.
        - 데이터: fixtures `converter`, `sample_hwp_file`.
        """
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
        """ODT 바이너리 반환 검증.

        Parameters
        ----------
        converter : HWPConverter
            변환기 fixture.
        sample_hwp_file : Path
            샘플 HWP 파일.

        Notes
        -----
        - 목적: ODT 결과가 bytes인지 확인.
        - 로직: output_format/is_binary/type 검사.
        - 데이터: fixtures `converter`, `sample_hwp_file`.
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
        """ODT ZIP 시그니처 검증.

        Parameters
        ----------
        converter : HWPConverter
            변환기 fixture.
        sample_hwp_file : Path
            샘플 HWP 파일.

        Notes
        -----
        - 목적: ODT 결과가 ZIP 형식임을 확인.
        - 로직: 바이너리 첫 2바이트("PK") 검사.
        - 데이터: fixtures `converter`, `sample_hwp_file`.
        """
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
        """지원 포맷별 변환 결과 검증.

        Parameters
        ----------
        converter : HWPConverter
            변환기 fixture.
        sample_hwp_file : Path
            샘플 HWP 파일.
        output_format : str
            테스트 대상 포맷.

        Notes
        -----
        - 목적: convert가 지정 포맷을 반영하는지 확인.
        - 로직: output_format 비교.
        - 데이터: fixtures `converter`, `sample_hwp_file` 및 parametrize 값.
        """
        result = converter.convert(sample_hwp_file, output_format)  # type: ignore
        assert result.output_format == output_format

    def test_convert_unsupported_format(
        self, converter: HWPConverter, sample_hwp_file: Path
    ) -> None:
        """지원하지 않는 포맷 입력 오류 검증.

        Parameters
        ----------
        converter : HWPConverter
            변환기 fixture.
        sample_hwp_file : Path
            샘플 HWP 파일.

        Notes
        -----
        - 목적: ValueError 발생 확인.
        - 로직: pytest.raises로 예외 확인.
        - 데이터: fixtures `converter`, `sample_hwp_file`.
        """
        with pytest.raises(ValueError, match="지원하지 않는 포맷"):
            converter.convert(sample_hwp_file, "pdf")  # type: ignore

    def test_convert_default_format_is_markdown(
        self, converter: HWPConverter, sample_hwp_file: Path
    ) -> None:
        """기본 변환 포맷 검증.

        Parameters
        ----------
        converter : HWPConverter
            변환기 fixture.
        sample_hwp_file : Path
            샘플 HWP 파일.

        Notes
        -----
        - 목적: 기본 output_format이 markdown인지 확인.
        - 로직: 결과 output_format 검사.
        - 데이터: fixtures `converter`, `sample_hwp_file`.
        """
        result = converter.convert(sample_hwp_file)
        assert result.output_format == "markdown"


class TestConversionResult:
    """ConversionResult 테스트"""

    def test_result_properties(
        self, converter: HWPConverter, sample_hwp_file: Path
    ) -> None:
        """ConversionResult 속성 검증.

        Parameters
        ----------
        converter : HWPConverter
            변환기 fixture.
        sample_hwp_file : Path
            샘플 HWP 파일.

        Notes
        -----
        - 목적: source_path/source_name/converted_at 확인.
        - 로직: 속성 값 비교 및 None 여부 검사.
        - 데이터: fixtures `converter`, `sample_hwp_file`.
        """
        result = converter.to_text(sample_hwp_file)

        assert result.source_path == sample_hwp_file
        assert result.source_name == sample_hwp_file.name
        assert result.converted_at is not None

    def test_result_to_dict(
        self, converter: HWPConverter, sample_hwp_file: Path
    ) -> None:
        """ConversionResult to_dict 검증.

        Parameters
        ----------
        converter : HWPConverter
            변환기 fixture.
        sample_hwp_file : Path
            샘플 HWP 파일.

        Notes
        -----
        - 목적: to_dict 필수 키 존재 확인.
        - 로직: dict 키 포함 검사.
        - 데이터: fixtures `converter`, `sample_hwp_file`.
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
    """여러 파일 변환 테스트"""

    def test_convert_multiple_files_to_text(
        self, converter: HWPConverter, small_hwp_files: list[Path]
    ) -> None:
        """여러 파일 텍스트 변환 검증.

        Parameters
        ----------
        converter : HWPConverter
            변환기 fixture.
        small_hwp_files : list[Path]
            작은 HWP 파일 목록.

        Notes
        -----
        - 목적: 배치 변환 결과 포맷/콘텐츠 확인.
        - 로직: 각 파일 변환 결과 검사.
        - 데이터: fixtures `converter`, `small_hwp_files`.
        """
        for hwp_file in small_hwp_files:
            result = converter.to_text(hwp_file)
            assert result.output_format == "txt"
            assert len(result.content) > 0

    def test_convert_multiple_files_to_markdown(
        self, converter: HWPConverter, small_hwp_files: list[Path]
    ) -> None:
        """여러 파일 마크다운 변환 검증.

        Parameters
        ----------
        converter : HWPConverter
            변환기 fixture.
        small_hwp_files : list[Path]
            작은 HWP 파일 목록.

        Notes
        -----
        - 목적: 배치 마크다운 변환 결과 확인.
        - 로직: 각 파일 변환 결과 검사.
        - 데이터: fixtures `converter`, `small_hwp_files`.
        """
        for hwp_file in small_hwp_files:
            result = converter.to_markdown(hwp_file)
            assert result.output_format == "markdown"
            assert len(result.content) > 0


# === 에지 케이스 ===


class TestConverterErrorPaths:
    """변환기 예외 경로 테스트"""

    def test_to_html_subprocess_failure(self, tmp_path: Path) -> None:
        """hwp5html 실패 시 RuntimeError 검증.

        Notes
        -----
        - 목적: subprocess 실패 분기 커버.
        - 로직: returncode!=0인 결과를 주입.
        - 데이터: 임시 HWP 파일.
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
        """결과 파일 미생성 시 RuntimeError 검증.

        Notes
        -----
        - 목적: index.xhtml 미존재 분기 커버.
        - 로직: subprocess 성공 처리 후 파일 생성하지 않음.
        - 데이터: 임시 HWP 파일.
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
        """RelaxNG 오류 분기 검증.

        Notes
        -----
        - 목적: RelaxNG 오류 메시지 분기 커버.
        - 로직: stderr에 RelaxNG 포함된 실패 결과 주입.
        - 데이터: 임시 HWP 파일.
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
        """ODT 결과 파일 미생성 분기 검증.

        Notes
        -----
        - 목적: output_file 미존재 분기 커버.
        - 로직: subprocess 성공 처리 후 파일 생성하지 않음.
        - 데이터: 임시 HWP 파일.
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
        """ODT 일반 실패 분기 검증.

        Notes
        -----
        - 목적: RelaxNG 외 일반 오류 분기 커버.
        - 로직: stderr에 다른 메시지를 포함한 실패 결과 주입.
        - 데이터: 임시 HWP 파일.
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
    """로깅 초기화 경로 테스트"""

    def test_verbose_configures_logger(self) -> None:
        """verbose=True 시 로거 설정 경로 검증.

        Notes
        -----
        - 목적: _configure_logger가 호출되어 플래그가 켜지는지 확인.
        - 로직: 클래스 플래그 초기화 후 인스턴스 생성.
        - 데이터: 없음.
        """
        HWPConverter._logger_configured = False
        converter = HWPConverter(verbose=True)
        assert converter.verbose is True
        assert HWPConverter._logger_configured is True

    def test_configure_logger_idempotent(self) -> None:
        """로거 설정 재호출 시 조기 반환 검증.

        Notes
        -----
        - 목적: _configure_logger의 조기 반환 분기 커버.
        - 로직: 플래그를 True로 설정 후 재호출.
        - 데이터: 없음.
        """
        HWPConverter._logger_configured = True
        HWPConverter._configure_logger()
        assert HWPConverter._logger_configured is True

    def test_log_start_with_missing_file(self, tmp_path: Path) -> None:
        """_log_start에서 파일 미존재 분기 검증.

        Notes
        -----
        - 목적: exists False 분기 커버.
        - 로직: 존재하지 않는 경로로 _log_start 직접 호출.
        - 데이터: 임시 경로.
        """
        converter = HWPConverter(verbose=True)
        missing_file = tmp_path / "missing.hwp"
        converter._log_start(missing_file, "markdown")

    def test_log_finish_with_missing_file(self, tmp_path: Path) -> None:
        """_log_finish에서 파일 미존재 분기 검증.

        Notes
        -----
        - 목적: exists False 분기 커버.
        - 로직: 존재하지 않는 경로로 _log_finish 호출.
        - 데이터: 임시 경로.
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
    """Markdown 변환 ImportError 경로 테스트"""

    def test_to_markdown_import_error(self, tmp_path: Path, monkeypatch) -> None:
        """html_to_markdown 미설치 시 ImportError 검증.

        Notes
        -----
        - 목적: to_markdown import 예외 경로 커버.
        - 로직: html_to_markdown import를 강제 실패.
        - 데이터: 임시 HWP 파일.
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
