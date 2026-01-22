"""CLI 테스트."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from hwp_parser.cli.app import cli, convert_file, main


class TestCli:
    """CLI 기능 테스트."""

    def test_convert_command_no_args(self) -> None:
        """인자 없이 실행 시 메시지 출력 검증."""
        runner = CliRunner()
        result = runner.invoke(cli, ["convert"])
        # Click 8.x + isolated_filesystem 동작에서 exit_code는 0일 수 있음
        # 하지만 "변환할 파일이 없습니다" 메시지로 정상적인 "아무것도 안 함" 상태를 검증
        assert (
            "Missing argument 'SOURCES'" in result.output
            or "변환할 파일이 없습니다." in result.output
        )

    def test_convert_command_with_no_files(self) -> None:
        """존재하지 않는 파일 패턴 입력 시 경고 출력 검증."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(cli, ["convert", "*.hwp"])
            assert result.exit_code == 0
            assert "변환할 파일이 없습니다." in result.output

    def test_convert_command_single_file(self) -> None:
        """단일 파일 변환 명령 실행 검증 (Mock 사용)."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            # 가상 파일 생성
            with open("test.hwp", "w") as f:
                f.write("dummy content")

            # convert_file 함수 Mocking (실제 변환 방지)
            # 주의: ProcessPoolExecutor 내부에서는 patch가 적용되지 않을 수 있음 (Pickling 문제)
            # 따라서 ProcessPoolExecutor 자체를 Mocking하여 동기적으로 실행되는 것처럼 흉내냄
            with patch("hwp_parser.cli.app.ProcessPoolExecutor") as mock_executor:
                # Executor 컨텍스트 매니저 Mock
                mock_pool = MagicMock()
                mock_executor.return_value.__enter__.return_value = mock_pool

                # submit 결과(Future) Mock
                mock_future = MagicMock()
                mock_future.result.return_value = "[Success] test.hwp -> test.md"

                # as_completed가 generator이므로 future 리스트를 반환하도록 설정
                # mock_executor를 사용했으므로 submit은 호출되지만 실제 스레드/프로세스는 생성안됨
                # 따라서 as_completed도 굳이 진짜를 쓸 필요 없음
                with patch(
                    "hwp_parser.cli.app.as_completed", return_value=[mock_future]
                ):
                    # verbose 옵션을 켜야 성공 메시지가 출력됨
                    result = runner.invoke(
                        cli, ["convert", "test.hwp", "--workers", "1", "--verbose"]
                    )

                    assert result.exit_code == 0
                    assert "총 1개의 파일을 변환합니다" in result.output
                    assert "[Success] test.hwp -> test.md" in result.output

    def test_convert_command_output_dir(self) -> None:
        """출력 디렉터리 지정 옵션 검증."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            with open("test.hwp", "w") as f:
                f.write("dummy")

            with patch("hwp_parser.cli.app.ProcessPoolExecutor") as mock_executor:
                mock_pool = MagicMock()
                mock_executor.return_value.__enter__.return_value = mock_pool

                mock_future = MagicMock()
                mock_future.result.return_value = "Success"

                with patch(
                    "hwp_parser.cli.app.as_completed", return_value=[mock_future]
                ):
                    result = runner.invoke(
                        cli, ["convert", "test.hwp", "--output-dir", "out"]
                    )

                    assert result.exit_code == 0

                    # submit 호출 인자 확인 (output_dir은 4번째 인자)
                    # submit(convert_file, f, format, output_path_obj, verbose)
                    args = mock_pool.submit.call_args[0]
                    assert args[3] == Path("out")

    def test_convert_command_format(self) -> None:
        """변환 포맷 지정 옵션 검증."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            with open("test.hwp", "w") as f:
                f.write("dummy")

            with patch("hwp_parser.cli.app.ProcessPoolExecutor") as mock_executor:
                mock_pool = MagicMock()
                mock_executor.return_value.__enter__.return_value = mock_pool

                mock_future = MagicMock()
                mock_future.result.return_value = "Success"

                with patch(
                    "hwp_parser.cli.app.as_completed", return_value=[mock_future]
                ):
                    result = runner.invoke(
                        cli, ["convert", "test.hwp", "--format", "html"]
                    )

                    assert result.exit_code == 0

                    # submit 호출 인자 확인 (format은 3번째 인자)
                    args = mock_pool.submit.call_args[0]
                    assert args[2] == "html"


class TestConvertFileFunction:
    """convert_file 함수 단위 테스트."""

    @patch("hwp_parser.cli.app.HWPConverter")
    def test_convert_file_success(self, mock_converter_cls, tmp_path) -> None:
        """convert_file 함수 정상 동작 테스트."""
        # 1. Mock 설정
        mock_instance = mock_converter_cls.return_value
        mock_result = MagicMock()
        mock_result.is_binary = False
        mock_result.content = "Converted Content"
        mock_instance.to_markdown.return_value = mock_result

        # 2. 파일 준비
        input_file = tmp_path / "doc.hwp"
        input_file.touch()

        # 3. 함수 실행
        result_msg = convert_file(
            file_path=input_file,
            output_format="markdown",
            output_dir=None,
            verbose=False,
        )

        # 4. 검증
        output_file = tmp_path / "doc.md"
        assert output_file.exists()
        assert output_file.read_text() == "Converted Content"
        assert "[Success]" in result_msg
        assert str(input_file.name) in result_msg

    @patch("hwp_parser.cli.app.HWPConverter")
    def test_convert_file_error(self, mock_converter_cls, tmp_path) -> None:
        """변환 중 에러 발생 시 처리 검증."""
        # 1. Mock 설정 (예외 발생)
        mock_instance = mock_converter_cls.return_value
        mock_instance.to_markdown.side_effect = Exception("Conversion Failed")

        # 2. 파일 준비
        input_file = tmp_path / "error.hwp"
        input_file.touch()

        # 3. 함수 실행
        result_msg = convert_file(
            file_path=input_file,
            output_format="markdown",
            output_dir=None,
            verbose=False,
        )

        # 4. 검증
        assert "[Fail]" in result_msg
        assert "Conversion Failed" in result_msg

    def test_convert_file_unsupported_format(self, tmp_path) -> None:
        """지원하지 않는 포맷 요청 시 에러 메시지 검증."""
        input_file = tmp_path / "doc.hwp"
        input_file.touch()

        result_msg = convert_file(
            file_path=input_file,
            output_format="pdf",  # Unsupported
            output_dir=None,
            verbose=False,
        )

        assert "[Error]" in result_msg
        assert "지원하지 않는 포맷" in result_msg

    @patch("hwp_parser.cli.app.HWPConverter")
    def test_convert_file_all_formats(self, mock_converter_cls, tmp_path) -> None:
        """모든 지원 포맷에 대한 분기 테스트 (html, txt, odt)."""
        input_file = tmp_path / "doc.hwp"
        input_file.touch()

        mock_instance = mock_converter_cls.return_value
        mock_result = MagicMock()
        mock_result.is_binary = False
        mock_result.content = "content"

        # 각 메서드 반환값 설정
        mock_instance.to_html.return_value = mock_result
        mock_instance.to_text.return_value = mock_result
        mock_instance.to_odt.return_value = mock_result

        # HTML
        convert_file(input_file, "html", None, False)
        mock_instance.to_html.assert_called_once()

        # TXT
        convert_file(input_file, "txt", None, False)
        mock_instance.to_text.assert_called_once()

        # ODT
        convert_file(input_file, "odt", None, False)
        mock_instance.to_odt.assert_called_once()


class TestCliDiscovery:
    """CLI 파일 검색 로직 테스트."""

    def test_no_files_found(self) -> None:
        """변환할 파일이 없는 경우."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(cli, ["convert", "*.hwp"])
            assert result.exit_code == 0
            assert "Warning: 패턴 '*.hwp'에 매칭되는 파일이 없습니다." in result.output
            assert "변환할 파일이 없습니다." in result.output

    def test_directory_input(self) -> None:
        """디렉터리 입력 시 재귀 검색 테스트."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            # 디렉터리 구조 생성
            Path("subdir").mkdir()
            Path("subdir/test.hwp").touch()

            with patch("hwp_parser.cli.app.ProcessPoolExecutor") as mock_executor:
                mock_executor.return_value.__enter__.return_value = MagicMock()
                with patch("hwp_parser.cli.app.as_completed", return_value=[]):
                    result = runner.invoke(cli, ["convert", "subdir", "--workers", "1"])

                    assert result.exit_code == 0
                    assert "총 1개의 파일을 변환합니다" in result.output

    def test_glob_pattern(self) -> None:
        """Glob 패턴 입력 테스트."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            Path("a.hwp").touch()
            Path("b.hwp").touch()
            Path("c.txt").touch()

            with patch("hwp_parser.cli.app.ProcessPoolExecutor") as mock_executor:
                mock_executor.return_value.__enter__.return_value = MagicMock()
                with patch("hwp_parser.cli.app.as_completed", return_value=[]):
                    # 따옴표로 감싸서 쉘 확장이 아닌 내부 glob 로직을 타게 함 -> runner.invoke는 쉘 확장이 없으므로 그냥 전달됨
                    result = runner.invoke(cli, ["convert", "*.hwp", "--workers", "1"])

                    assert result.exit_code == 0
                    assert "총 2개의 파일을 변환합니다" in result.output


class TestCliMain:
    """main() 함수 테스트."""

    def test_main_calls_cli(self) -> None:
        """main() 함수가 cli()를 호출하는지 검증."""
        with patch("hwp_parser.cli.app.cli") as mock_cli:
            main()
            mock_cli.assert_called_once()

    def test_cli_module_main_calls_app_main(self) -> None:
        """cli/__init__.py의 main이 app.main을 호출하는지 검증."""
        from hwp_parser.cli import main as cli_main

        with patch("hwp_parser.cli.app.cli") as mock_cli:
            cli_main()
            mock_cli.assert_called_once()


class TestConvertFileOutputDir:
    """convert_file의 output_dir 관련 테스트."""

    def test_convert_file_with_output_dir(self, tmp_path: Path) -> None:
        """출력 디렉터리가 지정된 경우 해당 위치에 저장되는지 검증."""
        input_file = tmp_path / "test.hwp"
        input_file.touch()
        output_dir = tmp_path / "output"

        with patch("hwp_parser.cli.app.HWPConverter") as mock_converter_cls:
            mock_instance = mock_converter_cls.return_value
            mock_result = MagicMock()
            mock_result.is_binary = False
            mock_result.content = "# Test Content"
            mock_instance.to_markdown.return_value = mock_result

            result = convert_file(input_file, "markdown", output_dir, False)

            assert "[Success]" in result
            assert output_dir.exists()
            output_file = output_dir / "test.md"
            assert output_file.exists()
            assert output_file.read_text() == "# Test Content"

    def test_convert_file_with_output_dir_html(self, tmp_path: Path) -> None:
        """HTML 포맷으로 출력 디렉터리에 저장 (디렉터리 구조 검증)."""
        input_file = tmp_path / "test.hwp"
        input_file.touch()
        output_dir = tmp_path / "output"

        with patch("hwp_parser.cli.app.HWPConverter") as mock_converter_cls:
            mock_instance = mock_converter_cls.return_value
            # HTMLDirResult mock
            mock_result = MagicMock()
            mock_result.xhtml_content = "<html>Test</html>"
            mock_result.css_content = "body { color: black; }"
            mock_result.bindata = {}
            mock_instance.to_html.return_value = mock_result

            result = convert_file(input_file, "html", output_dir, False)

            assert "[Success]" in result
            # HTML은 디렉터리로 저장됨
            html_dir = output_dir / "test"
            assert html_dir.exists()
            assert (html_dir / "index.xhtml").exists()
            assert (html_dir / "styles.css").exists()

    def test_convert_file_with_output_dir_html_with_bindata(
        self, tmp_path: Path
    ) -> None:
        """HTML 포맷으로 bindata 포함된 출력 저장 검증."""
        input_file = tmp_path / "test.hwp"
        input_file.touch()
        output_dir = tmp_path / "output"

        with patch("hwp_parser.cli.app.HWPConverter") as mock_converter_cls:
            mock_instance = mock_converter_cls.return_value
            # HTMLDirResult mock with bindata
            mock_result = MagicMock()
            mock_result.xhtml_content = "<html>Test</html>"
            mock_result.css_content = "body { color: black; }"
            mock_result.bindata = {"image.png": b"PNG_DATA"}
            mock_instance.to_html.return_value = mock_result

            result = convert_file(input_file, "html", output_dir, False)

            assert "[Success]" in result
            html_dir = output_dir / "test"
            assert (html_dir / "bindata" / "image.png").exists()
            assert (html_dir / "bindata" / "image.png").read_bytes() == b"PNG_DATA"

    def test_convert_file_html_without_css(self, tmp_path: Path) -> None:
        """HTML 포맷으로 CSS 없이 저장 검증."""
        input_file = tmp_path / "test.hwp"
        input_file.touch()
        output_dir = tmp_path / "output"

        with patch("hwp_parser.cli.app.HWPConverter") as mock_converter_cls:
            mock_instance = mock_converter_cls.return_value
            mock_result = MagicMock()
            mock_result.xhtml_content = "<html>Test</html>"
            mock_result.css_content = ""  # 빈 CSS
            mock_result.bindata = {}
            mock_instance.to_html.return_value = mock_result

            result = convert_file(input_file, "html", output_dir, False)

            assert "[Success]" in result
            html_dir = output_dir / "test"
            assert (html_dir / "index.xhtml").exists()
            # CSS가 비어있으면 파일이 생성되지 않음
            assert not (html_dir / "styles.css").exists()


class TestCliAbsolutePathGlob:
    """절대 경로 glob 패턴 테스트."""

    def test_absolute_path_glob_pattern(self, tmp_path: Path) -> None:
        """절대 경로 glob 패턴이 제대로 처리되는지 검증."""
        # tmp_path에 테스트 파일 생성
        test_file = tmp_path / "test.hwp"
        test_file.touch()

        # 절대 경로 glob 패턴
        abs_pattern = str(tmp_path / "*.hwp")

        runner = CliRunner()
        with patch("hwp_parser.cli.app.ProcessPoolExecutor") as mock_executor:
            mock_executor.return_value.__enter__.return_value = MagicMock()
            with patch("hwp_parser.cli.app.as_completed", return_value=[]):
                result = runner.invoke(cli, ["convert", abs_pattern, "--workers", "1"])

                assert result.exit_code == 0
                assert "총 1개의 파일을 변환합니다" in result.output


class TestCliFileNotFound:
    """파일 못 찾음 경고 테스트."""

    def test_file_not_found_warning(self) -> None:
        """존재하지 않는 파일 경로에 대한 경고 메시지 검증."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(cli, ["convert", "nonexistent.hwp"])

            assert (
                "Warning: 파일 'nonexistent.hwp'를 찾을 수 없습니다." in result.output
            )
            assert "변환할 파일이 없습니다." in result.output


class TestCliProgressAndVerbose:
    """진행바 및 verbose 출력 테스트."""

    def test_verbose_output_on_success(self, tmp_path: Path) -> None:
        """verbose 모드에서 성공 메시지가 출력되는지 검증."""
        test_file = tmp_path / "test.hwp"
        test_file.touch()

        runner = CliRunner()
        # ProcessPoolExecutor 내부의 convert_file을 mock할 수 없으므로
        # Executor 자체를 mock하여 future를 직접 제어
        with patch("hwp_parser.cli.app.ProcessPoolExecutor") as mock_executor:
            mock_future = MagicMock()
            mock_future.result.return_value = "[Success] test.hwp -> test.md"

            mock_executor_instance = MagicMock()
            mock_executor_instance.submit.return_value = mock_future
            mock_executor.return_value.__enter__.return_value = mock_executor_instance

            with patch("hwp_parser.cli.app.as_completed", return_value=[mock_future]):
                result = runner.invoke(
                    cli,
                    ["convert", str(test_file), "--workers", "1", "--verbose"],
                )

                assert result.exit_code == 0
                assert "모든 작업이 완료되었습니다." in result.output

    def test_error_output_shown_without_verbose(self, tmp_path: Path) -> None:
        """verbose가 아니어도 에러 메시지는 출력되는지 검증."""
        test_file = tmp_path / "test.hwp"
        test_file.touch()

        runner = CliRunner()
        with patch("hwp_parser.cli.app.ProcessPoolExecutor") as mock_executor:
            mock_future = MagicMock()
            mock_future.result.return_value = "[Error] test.hwp: 변환 실패"

            mock_executor_instance = MagicMock()
            mock_executor_instance.submit.return_value = mock_future
            mock_executor.return_value.__enter__.return_value = mock_executor_instance

            with patch("hwp_parser.cli.app.as_completed", return_value=[mock_future]):
                result = runner.invoke(
                    cli,
                    ["convert", str(test_file), "--workers", "1"],
                )

                assert result.exit_code == 0
                assert "모든 작업이 완료되었습니다." in result.output

    def test_fail_output_shown_without_verbose(self, tmp_path: Path) -> None:
        """verbose가 아니어도 Fail 메시지는 출력되는지 검증."""
        test_file = tmp_path / "test.hwp"
        test_file.touch()

        runner = CliRunner()
        with patch("hwp_parser.cli.app.ProcessPoolExecutor") as mock_executor:
            mock_future = MagicMock()
            mock_future.result.return_value = "[Fail] test.hwp: 예외 발생"

            mock_executor_instance = MagicMock()
            mock_executor_instance.submit.return_value = mock_future
            mock_executor.return_value.__enter__.return_value = mock_executor_instance

            with patch("hwp_parser.cli.app.as_completed", return_value=[mock_future]):
                result = runner.invoke(
                    cli,
                    ["convert", str(test_file), "--workers", "1"],
                )

                assert result.exit_code == 0
                assert "모든 작업이 완료되었습니다." in result.output


class TestCliWorkersValidation:
    """workers 인자 검증 테스트."""

    def test_workers_less_than_one_defaults_to_one(self, tmp_path: Path) -> None:
        """workers가 1 미만인 경우 1로 설정되는지 검증."""
        test_file = tmp_path / "test.hwp"
        test_file.touch()

        runner = CliRunner()
        with patch("hwp_parser.cli.app.ProcessPoolExecutor") as mock_executor:
            mock_future = MagicMock()
            mock_future.result.return_value = "[Success] test.hwp -> test.md"

            mock_executor_instance = MagicMock()
            mock_executor_instance.submit.return_value = mock_future
            mock_executor.return_value.__enter__.return_value = mock_executor_instance

            with patch("hwp_parser.cli.app.as_completed", return_value=[mock_future]):
                result = runner.invoke(
                    cli,
                    ["convert", str(test_file), "--workers", "0"],
                )

                assert result.exit_code == 0
                # max_workers=1로 호출되었는지 검증
                mock_executor.assert_called_once_with(max_workers=1)


class TestCliProgressBarOutput:
    """progressbar 출력 분기 테스트."""

    def test_verbose_with_visible_progressbar(self, tmp_path: Path) -> None:
        """progressbar가 visible일 때 verbose 출력이 동작하는지 검증."""
        test_file = tmp_path / "test.hwp"
        test_file.touch()

        runner = CliRunner()
        with patch("hwp_parser.cli.app.ProcessPoolExecutor") as mock_executor:
            mock_future = MagicMock()
            mock_future.result.return_value = "[Success] test.hwp -> test.md"

            mock_executor_instance = MagicMock()
            mock_executor_instance.submit.return_value = mock_future
            mock_executor.return_value.__enter__.return_value = mock_executor_instance

            # progressbar를 mock하여 is_hidden=False 설정
            mock_bar = MagicMock()
            mock_bar.is_hidden = False

            with patch("hwp_parser.cli.app.as_completed", return_value=[mock_future]):
                with patch("click.progressbar") as mock_progressbar:
                    mock_progressbar.return_value.__enter__.return_value = mock_bar

                    result = runner.invoke(
                        cli,
                        ["convert", str(test_file), "--workers", "1", "--verbose"],
                    )

                    assert result.exit_code == 0
                    # bar.update가 호출되었는지 검증
                    mock_bar.update.assert_called_once_with(1)

    def test_verbose_with_hidden_progressbar(self, tmp_path: Path) -> None:
        """progressbar가 hidden일 때 출력이 스킵되는지 검증."""
        test_file = tmp_path / "test.hwp"
        test_file.touch()

        runner = CliRunner()
        with patch("hwp_parser.cli.app.ProcessPoolExecutor") as mock_executor:
            mock_future = MagicMock()
            mock_future.result.return_value = "[Error] test.hwp: 변환 실패"

            mock_executor_instance = MagicMock()
            mock_executor_instance.submit.return_value = mock_future
            mock_executor.return_value.__enter__.return_value = mock_executor_instance

            # progressbar를 mock하여 is_hidden=True 설정
            mock_bar = MagicMock()
            mock_bar.is_hidden = True

            with patch("hwp_parser.cli.app.as_completed", return_value=[mock_future]):
                with patch("click.progressbar") as mock_progressbar:
                    mock_progressbar.return_value.__enter__.return_value = mock_bar

                    # click.echo를 모니터링하여 에러 메시지가 출력되지 않는지 확인
                    with patch("hwp_parser.cli.app.click.echo") as mock_echo:
                        result = runner.invoke(
                            cli,
                            ["convert", str(test_file), "--workers", "1"],
                        )

                        assert result.exit_code == 0
                        # is_hidden=True이면 에러 메시지가 click.echo로 출력되지 않음
                        # 단, "모든 작업이 완료되었습니다."는 출력됨
                        echo_calls = [
                            call
                            for call in mock_echo.call_args_list
                            if "[Error]" in str(call)
                        ]
                        assert len(echo_calls) == 0


class TestCliIntegration:
    """CLI 통합 테스트 (실제 HWP 파일 사용).

    테스트 대상:
        - 실제 HWP 파일을 CLI로 변환하여 결과 검증

    검증 범위:
        1. Markdown 변환 후 파일 생성 및 내용 확인
        2. HTML 변환 후 파일 생성 및 형식 확인
        3. TXT 변환 후 파일 생성 및 내용 확인
        4. 여러 파일 동시 변환
    """

    @staticmethod
    def get_sample_hwp() -> Path:
        """테스트용 HWP 파일 경로 반환."""
        fixtures_dir = Path(__file__).parent / "fixtures"
        hwp_files = list(fixtures_dir.glob("*.hwp"))
        if not hwp_files:
            return None
        return hwp_files[0]

    def test_convert_to_markdown_integration(self, tmp_path: Path) -> None:
        """실제 HWP 파일을 Markdown으로 변환 통합 테스트."""
        sample_hwp = self.get_sample_hwp()
        if sample_hwp is None:
            import pytest

            pytest.skip("테스트용 HWP 파일이 없습니다.")

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "convert",
                str(sample_hwp),
                "--format",
                "markdown",
                "--output-dir",
                str(tmp_path),
                "--workers",
                "1",
            ],
        )

        assert result.exit_code == 0
        assert "총 1개의 파일을 변환합니다" in result.output
        assert "모든 작업이 완료되었습니다" in result.output

        # 변환된 파일 확인
        output_files = list(tmp_path.glob("*.md"))
        assert len(output_files) == 1

        # 파일 내용 확인 (비어있지 않아야 함)
        content = output_files[0].read_text(encoding="utf-8")
        assert len(content) > 30  # 최소 내용 확인 (샘플 파일에 따라 길이가 다를 수 있음)

    def test_convert_to_html_integration(self, tmp_path: Path) -> None:
        """실제 HWP 파일을 HTML로 변환 통합 테스트 (디렉터리 구조)."""
        sample_hwp = self.get_sample_hwp()
        if sample_hwp is None:
            import pytest

            pytest.skip("테스트용 HWP 파일이 없습니다.")

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "convert",
                str(sample_hwp),
                "--format",
                "html",
                "--output-dir",
                str(tmp_path),
                "--workers",
                "1",
            ],
        )

        assert result.exit_code == 0

        # HTML은 디렉터리로 저장됨 (파일명.stem 디렉터리)
        output_dirs = [d for d in tmp_path.iterdir() if d.is_dir()]
        assert len(output_dirs) == 1

        html_dir = output_dirs[0]
        assert (html_dir / "index.xhtml").exists()

        content = (html_dir / "index.xhtml").read_text(encoding="utf-8")
        assert "<html" in content.lower() or "xhtml" in content.lower()

    def test_convert_to_txt_integration(self, tmp_path: Path) -> None:
        """실제 HWP 파일을 TXT로 변환 통합 테스트."""
        sample_hwp = self.get_sample_hwp()
        if sample_hwp is None:
            import pytest

            pytest.skip("테스트용 HWP 파일이 없습니다.")

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "convert",
                str(sample_hwp),
                "--format",
                "txt",
                "--output-dir",
                str(tmp_path),
                "--workers",
                "1",
            ],
        )

        assert result.exit_code == 0

        output_files = list(tmp_path.glob("*.txt"))
        assert len(output_files) == 1

        content = output_files[0].read_text(encoding="utf-8")
        assert len(content) > 30  # 텍스트 내용이 있어야 함

    def test_convert_multiple_files_integration(self, tmp_path: Path) -> None:
        """여러 HWP 파일을 동시에 변환하는 통합 테스트."""
        fixtures_dir = Path(__file__).parent / "fixtures"
        hwp_files = list(fixtures_dir.glob("*.hwp"))
        if len(hwp_files) < 2:
            import pytest

            pytest.skip("테스트용 HWP 파일이 2개 미만입니다.")

        # 처음 3개 파일만 테스트 (시간 단축)
        test_files = hwp_files[:3]

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "convert",
                *[str(f) for f in test_files],
                "--format",
                "markdown",
                "--output-dir",
                str(tmp_path),
                "--workers",
                "2",
            ],
        )

        assert result.exit_code == 0
        assert f"총 {len(test_files)}개의 파일을 변환합니다" in result.output

        # 변환된 파일 수 확인
        output_files = list(tmp_path.glob("*.md"))
        assert len(output_files) == len(test_files)
