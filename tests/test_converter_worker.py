"""HWPConverter 워커 모드 테스트."""

from pathlib import Path

import pytest

from hwp_parser.core import HWPConverter


class TestWorkerModeInit:
    """HWPConverter 워커 모드 초기화 테스트.

    테스트 대상:
        - HWPConverter의 num_workers 파라미터

    검증 범위:
        1. num_workers=None → subprocess 모드
        2. num_workers>0 → 워커 모드
        3. 초기 상태에서 워커가 시작되지 않음
    """

    def test_default_is_subprocess_mode(self) -> None:
        """기본값이 subprocess 모드인지 검증."""
        converter = HWPConverter()
        assert converter.num_workers is None
        assert converter._use_worker() is False

    def test_worker_mode_enabled(self) -> None:
        """num_workers 설정 시 워커 모드가 활성화되는지 검증."""
        converter = HWPConverter(num_workers=2)
        assert converter.num_workers == 2
        assert converter._use_worker() is True

    def test_workers_not_started_on_init(self) -> None:
        """초기화 시 워커가 바로 시작되지 않는지 검증."""
        converter = HWPConverter(num_workers=2)
        assert converter._worker_started is False
        assert len(converter._workers) == 0


class TestWorkerModeLifecycle:
    """HWPConverter 워커 모드 생명주기 테스트.

    테스트 대상:
        - context manager를 통한 워커 시작/종료
        - _start_workers, _shutdown_workers 메서드

    검증 범위:
        1. context manager 진입 시 워커 시작
        2. context manager 종료 시 워커 정리
        3. 다중 시작 시 중복 생성 방지
        4. 시작 없이 종료해도 에러 없음
    """

    def test_context_manager_starts_workers(self) -> None:
        """context manager 진입 시 워커가 시작되는지 검증."""
        with HWPConverter(num_workers=1) as converter:
            assert converter._worker_started is True
            assert len(converter._workers) == 1
            for worker in converter._workers:
                assert worker.is_alive()

    def test_context_manager_stops_workers(self) -> None:
        """context manager 종료 시 워커가 정리되는지 검증."""
        with HWPConverter(num_workers=1) as converter:
            pass  # context manager 종료

        assert converter._worker_started is False
        assert len(converter._workers) == 0

    def test_start_workers_idempotent(self) -> None:
        """_start_workers를 여러 번 호출해도 워커가 중복 생성되지 않는지 검증."""
        converter = HWPConverter(num_workers=1)
        try:
            converter._start_workers()
            converter._start_workers()  # 두 번째 호출
            assert len(converter._workers) == 1
        finally:
            converter._shutdown_workers()

    def test_shutdown_without_start(self) -> None:
        """시작 없이 종료 호출해도 에러가 없는지 검증."""
        converter = HWPConverter(num_workers=1)
        converter._shutdown_workers()  # 에러 없이 통과해야 함
        assert converter._worker_started is False

    def test_subprocess_mode_context_manager(self) -> None:
        """subprocess 모드에서 context manager가 정상 동작하는지 검증."""
        with HWPConverter() as converter:
            # subprocess 모드이므로 워커 시작 안 함
            assert converter._worker_started is False


class TestWorkerModeIntegration:
    """HWPConverter 워커 모드 통합 테스트 (실제 HWP 파일 사용).

    테스트 대상:
        - 워커 모드에서의 실제 HWP 파일 변환

    검증 범위:
        1. HTML, 텍스트, Markdown, ODT 변환
        2. 파이프라인 문자열에 "worker" 포함 확인
        3. 여러 파일 연속 변환
    """

    @pytest.fixture
    def sample_hwp_file(self) -> Path:
        """테스트용 HWP 파일 경로 반환."""
        fixtures_dir = Path(__file__).parent / "fixtures"
        hwp_files = list(fixtures_dir.glob("*.hwp"))
        if not hwp_files:
            pytest.skip("테스트용 HWP 파일이 없습니다.")
        return hwp_files[0]

    def test_convert_to_html(self, sample_hwp_file: Path) -> None:
        """워커 모드 HTML 변환 테스트."""
        from hwp_parser.core import HTMLDirResult

        with HWPConverter(num_workers=1) as converter:
            result = converter.to_html(sample_hwp_file)

            assert isinstance(result, HTMLDirResult)
            assert result.output_format == "html"
            assert result.source_path == sample_hwp_file
            assert isinstance(result.xhtml_content, str)
            assert len(result.xhtml_content) > 0
            assert isinstance(result.css_content, str)
            assert isinstance(result.bindata, dict)

    def test_convert_to_text(self, sample_hwp_file: Path) -> None:
        """워커 모드 텍스트 변환 테스트."""
        with HWPConverter(num_workers=1) as converter:
            result = converter.to_text(sample_hwp_file)

            assert result.output_format == "txt"
            assert "worker" in result.pipeline
            assert isinstance(result.content, str)

    def test_convert_to_markdown(self, sample_hwp_file: Path) -> None:
        """워커 모드 Markdown 변환 테스트."""
        with HWPConverter(num_workers=1) as converter:
            result = converter.to_markdown(sample_hwp_file)

            assert result.output_format == "markdown"
            assert "worker" in result.pipeline
            assert isinstance(result.content, str)

    def test_convert_to_odt(self, sample_hwp_file: Path) -> None:
        """워커 모드 ODT 변환 테스트."""
        with HWPConverter(num_workers=1) as converter:
            result = converter.to_odt(sample_hwp_file)

            assert result.output_format == "odt"
            assert "worker" in result.pipeline
            assert isinstance(result.content, bytes)
            assert len(result.content) > 0

    def test_multiple_conversions(self, sample_hwp_file: Path) -> None:
        """여러 파일 연속 변환 테스트."""
        with HWPConverter(num_workers=2) as converter:
            results = []
            for _ in range(3):
                result = converter.to_text(sample_hwp_file)
                results.append(result)

            assert len(results) == 3
            for result in results:
                assert result.output_format == "txt"
                assert isinstance(result.content, str)


class TestWorkerModeHtmlWithBinData:
    """워커 모드 bindata 포함 HTML 변환 테스트.

    테스트 대상:
        - 워커 모드에서 bindata 포함 HTML 변환

    검증 범위:
        1. bindata dict 반환
    """

    @pytest.fixture
    def hwp_file_with_bindata(self) -> Path:
        """bindata(이미지) 포함된 HWP 파일 경로 반환."""
        fixtures_dir = Path(__file__).parent / "fixtures"
        # 실제로 bindata가 있는 파일
        candidate_files = [
            "_5_문서상태아이콘_ori.hwp",
            "_4_문서정보구분[대외문서_협조문_내부기안_보안문서]_ori.hwp",
            "ER31107_교원퇴직절차에관한지침_ori.hwp",
        ]
        for name in candidate_files:
            path = fixtures_dir / name
            if path.exists():
                return path
        hwp_files = list(fixtures_dir.glob("*.hwp"))
        if not hwp_files:
            pytest.skip("테스트용 HWP 파일이 없습니다.")
        return hwp_files[0]

    def test_worker_html_conversion_with_bindata(
        self, hwp_file_with_bindata: Path
    ) -> None:
        """워커 모드에서 bindata 포함 HTML 변환 시 bindata dict 반환 검증."""
        from hwp_parser.core import HTMLDirResult

        with HWPConverter(num_workers=1) as converter:
            result = converter.to_html(hwp_file_with_bindata)

            assert isinstance(result, HTMLDirResult)
            assert isinstance(result.bindata, dict)
            # bindata가 있으면 bytes 값이어야 함
            for name, data in result.bindata.items():
                assert isinstance(name, str)
                assert isinstance(data, bytes)


class TestWorkerModeErrorHandling:
    """HWPConverter 워커 모드 에러 처리 테스트.

    테스트 대상:
        - 워커 모드에서의 에러 핸들링

    검증 범위:
        1. 존재하지 않는 파일 처리
        2. 디렉터리 경로 처리
    """

    def test_file_not_found_raises(self) -> None:
        """존재하지 않는 파일 변환 시 FileNotFoundError 발생 검증."""
        with HWPConverter(num_workers=1) as converter:
            with pytest.raises(FileNotFoundError, match="파일을 찾을 수 없습니다"):
                converter.to_markdown(Path("nonexistent.hwp"))

    def test_directory_raises(self, tmp_path: Path) -> None:
        """디렉터리 경로로 변환 시 ValueError 발생 검증."""
        with HWPConverter(num_workers=1) as converter:
            with pytest.raises(ValueError, match="디렉토리가 입력되었습니다"):
                converter.to_markdown(tmp_path)


class TestWorkerModeVerbose:
    """HWPConverter 워커 모드 verbose 테스트.

    테스트 대상:
        - verbose=True 옵션과 워커 모드 조합

    검증 범위:
        1. verbose 모드에서 로깅이 정상 동작
        2. 변환 완료 후 로그 출력
    """

    @pytest.fixture
    def sample_hwp_file(self) -> Path:
        """테스트용 HWP 파일 경로 반환."""
        fixtures_dir = Path(__file__).parent / "fixtures"
        hwp_files = list(fixtures_dir.glob("*.hwp"))
        if not hwp_files:
            pytest.skip("테스트용 HWP 파일이 없습니다.")
        return hwp_files[0]

    def test_verbose_mode_html(self, sample_hwp_file: Path) -> None:
        """verbose 모드 HTML 변환 테스트."""
        with HWPConverter(num_workers=1, verbose=True) as converter:
            result = converter.to_html(sample_hwp_file)
            assert result.output_format == "html"

    def test_verbose_mode_text(self, sample_hwp_file: Path) -> None:
        """verbose 모드 텍스트 변환 테스트."""
        with HWPConverter(num_workers=1, verbose=True) as converter:
            result = converter.to_text(sample_hwp_file)
            assert result.output_format == "txt"

    def test_verbose_mode_markdown(self, sample_hwp_file: Path) -> None:
        """verbose 모드 Markdown 변환 테스트."""
        with HWPConverter(num_workers=1, verbose=True) as converter:
            result = converter.to_markdown(sample_hwp_file)
            assert result.output_format == "markdown"

    def test_verbose_mode_odt(self, sample_hwp_file: Path) -> None:
        """verbose 모드 ODT 변환 테스트."""
        with HWPConverter(num_workers=1, verbose=True) as converter:
            result = converter.to_odt(sample_hwp_file)
            assert result.output_format == "odt"


class TestWorkerModeEdgeCases:
    """HWPConverter 워커 모드 엣지 케이스 테스트.

    테스트 대상:
        - 워커 강제 종료
        - 자동 워커 시작
        - 변환 실패 처리

    검증 범위:
        1. 워커가 응답하지 않을 때 강제 종료
        2. context manager 없이 변환 시 워커 자동 시작
        3. 워커에서 변환 실패 시 RuntimeError
    """

    @pytest.fixture
    def sample_hwp_file(self) -> Path:
        """테스트용 HWP 파일 경로 반환."""
        fixtures_dir = Path(__file__).parent / "fixtures"
        hwp_files = list(fixtures_dir.glob("*.hwp"))
        if not hwp_files:
            pytest.skip("테스트용 HWP 파일이 없습니다.")
        return hwp_files[0]

    def test_auto_start_workers_without_context_manager(
        self, sample_hwp_file: Path
    ) -> None:
        """context manager 없이 변환 시 워커가 자동 시작되는지 검증."""
        converter = HWPConverter(num_workers=1)
        try:
            # context manager 없이 직접 호출
            assert converter._worker_started is False
            result = converter.to_text(sample_hwp_file)
            assert converter._worker_started is True
            assert result.output_format == "txt"
        finally:
            converter._shutdown_workers()

    def test_auto_start_workers_for_html_without_context_manager(
        self, sample_hwp_file: Path
    ) -> None:
        """HTML 변환 시 context manager 없이 워커가 자동 시작되는지 검증."""
        from hwp_parser.core import HTMLDirResult

        converter = HWPConverter(num_workers=1)
        try:
            # context manager 없이 직접 호출
            assert converter._worker_started is False
            result = converter.to_html(sample_hwp_file)
            assert converter._worker_started is True
            assert isinstance(result, HTMLDirResult)
        finally:
            converter._shutdown_workers()

    def test_worker_conversion_failure_raises_runtime_error(
        self, sample_hwp_file: Path
    ) -> None:
        """워커에서 변환 실패 시 RuntimeError 발생 검증."""
        from hwp_parser.core.worker import WorkerResult

        converter = HWPConverter(num_workers=1)
        try:
            converter._start_workers()

            # 실패 결과를 반환하도록 output_queue mock
            mock_result = WorkerResult(task_id=1, success=False, error="테스트 에러")

            def mock_get(*args, **kwargs):
                return mock_result

            assert converter._output_queue is not None
            converter._output_queue.get = mock_get  # type: ignore[method-assign]

            with pytest.raises(RuntimeError, match="변환 실패: 테스트 에러"):
                converter._convert_via_worker(sample_hwp_file, "txt")
        finally:
            converter._shutdown_workers()

    def test_worker_html_conversion_failure_raises_runtime_error(
        self, sample_hwp_file: Path
    ) -> None:
        """워커에서 HTML 변환 실패 시 RuntimeError 발생 검증."""
        from hwp_parser.core.worker import WorkerResult

        converter = HWPConverter(num_workers=1)
        try:
            converter._start_workers()

            # 실패 결과를 반환하도록 output_queue mock
            mock_result = WorkerResult(
                task_id=1, success=False, error="HTML 테스트 에러"
            )

            def mock_get(*args, **kwargs):
                return mock_result

            assert converter._output_queue is not None
            converter._output_queue.get = mock_get  # type: ignore[method-assign]

            with pytest.raises(RuntimeError, match="HTML 변환 실패: HTML 테스트 에러"):
                converter._convert_html_via_worker(sample_hwp_file)
        finally:
            converter._shutdown_workers()

    def test_shutdown_with_none_input_queue(self) -> None:
        """input_queue가 None일 때 shutdown이 정상 동작하는지 검증."""
        converter = HWPConverter(num_workers=1)
        converter._start_workers()

        # 강제로 input_queue를 None으로 설정
        converter._input_queue = None

        # shutdown 호출 시 에러 없어야 함
        converter._shutdown_workers()
        assert converter._worker_started is False
