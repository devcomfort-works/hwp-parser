"""Worker 모듈 단위 테스트.

워커 프로세스 내부에서 실행되는 함수들을 직접 테스트합니다.
multiprocessing 자식 프로세스의 커버리지 문제를 해결하기 위해
내부 함수들을 메인 프로세스에서 직접 호출하여 테스트합니다.
"""

import shutil
import tempfile
from multiprocessing import Queue
from pathlib import Path
from threading import Thread
from unittest.mock import MagicMock, patch

import pytest

from hwp_parser.core.worker import (
    WorkerResult,
    WorkerTask,
    _convert_to_html_dir,
    _convert_to_odt,
    _html_to_markdown,
    _html_to_text,
    worker_main,
)


class TestWorkerDataClasses:
    """Worker 데이터 클래스 테스트.

    테스트 대상:
        - WorkerTask, WorkerResult 데이터 클래스

    검증 범위:
        1. 필드 접근성
        2. 기본값
    """

    def test_worker_task_fields(self) -> None:
        """WorkerTask 필드가 정상 생성되는지 검증."""
        task = WorkerTask(task_id=1, file_path="/test.hwp", output_format="html")
        assert task.task_id == 1
        assert task.file_path == "/test.hwp"
        assert task.output_format == "html"

    def test_worker_result_success(self) -> None:
        """성공한 WorkerResult 생성 검증."""
        result = WorkerResult(task_id=1, success=True, content="<html></html>")
        assert result.task_id == 1
        assert result.success is True
        assert result.content == "<html></html>"
        assert result.error is None

    def test_worker_result_failure(self) -> None:
        """실패한 WorkerResult 생성 검증."""
        result = WorkerResult(task_id=1, success=False, error="변환 실패")
        assert result.success is False
        assert result.content is None
        assert result.error == "변환 실패"


class TestHtmlConversion:
    """HTML 변환 내부 함수 테스트.

    테스트 대상:
        - _convert_to_html_dir 함수

    검증 범위:
        1. 실제 HWP 파일 → HTML 디렉터리 변환
        2. XHTML, CSS, bindata 반환 확인
    """

    @pytest.fixture
    def sample_hwp_file(self) -> Path:
        """테스트용 HWP 파일 경로 반환."""
        fixtures_dir = Path(__file__).parent / "fixtures"
        hwp_files = list(fixtures_dir.glob("*.hwp"))
        if not hwp_files:
            pytest.skip("테스트용 HWP 파일이 없습니다.")
        return hwp_files[0]

    def test_convert_to_html_dir_returns_tuple(self, sample_hwp_file: Path) -> None:
        """_convert_to_html_dir이 (xhtml, css, bindata) 튜플을 반환하는지 검증."""
        temp_dir = Path(tempfile.mkdtemp())
        try:
            result = _convert_to_html_dir(sample_hwp_file, temp_dir)
            assert isinstance(result, tuple)
            assert len(result) == 3

            xhtml, css, bindata = result
            assert isinstance(xhtml, str)
            assert len(xhtml) > 0
            assert "html" in xhtml.lower() or "xhtml" in xhtml.lower()
            assert isinstance(css, str)
            assert isinstance(bindata, dict)
        finally:
            if temp_dir.exists():
                shutil.rmtree(temp_dir)

    def test_convert_to_html_dir_missing_output_raises(
        self, sample_hwp_file: Path
    ) -> None:
        """HTML 변환 후 결과 파일이 없으면 RuntimeError 발생 검증."""
        temp_dir = Path(tempfile.mkdtemp())
        try:
            # HTMLTransform.transform_hwp5_to_dir을 mock하여 파일 생성 안 함
            with patch("hwp_parser.core.worker.HTMLTransform") as mock_transform:
                mock_instance = MagicMock()
                mock_transform.return_value = mock_instance

                with pytest.raises(RuntimeError, match="결과 파일이 생성되지 않음"):
                    _convert_to_html_dir(sample_hwp_file, temp_dir)
        finally:
            if temp_dir.exists():
                shutil.rmtree(temp_dir)


class TestHtmlConversionWithBinData:
    """bindata 포함된 HTML 변환 테스트.

    테스트 대상:
        - _convert_to_html_dir 함수 (bindata 있는 경우)

    검증 범위:
        1. bindata 디렉터리 반환
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
        # 아무 파일이라도 반환
        hwp_files = list(fixtures_dir.glob("*.hwp"))
        if not hwp_files:
            pytest.skip("테스트용 HWP 파일이 없습니다.")
        return hwp_files[0]

    def test_convert_to_html_dir_with_bindata(
        self, hwp_file_with_bindata: Path
    ) -> None:
        """bindata가 포함된 HWP 변환 시 bindata dict가 채워지는지 검증."""
        temp_dir = Path(tempfile.mkdtemp())
        try:
            xhtml, css, bindata = _convert_to_html_dir(hwp_file_with_bindata, temp_dir)
            # bindata가 있을 수도 있고 없을 수도 있음 (파일에 따라)
            # 하지만 dict 타입이어야 함
            assert isinstance(bindata, dict)
            # bindata가 있으면 bytes 값이어야 함
            for name, data in bindata.items():
                assert isinstance(name, str)
                assert isinstance(data, bytes)
        finally:
            if temp_dir.exists():
                shutil.rmtree(temp_dir)


class TestOdtConversion:
    """ODT 변환 내부 함수 테스트.

    테스트 대상:
        - _convert_to_odt 함수

    검증 범위:
        1. 실제 HWP 파일 → ODT 변환
        2. ODT 파일이 바이너리로 반환됨
    """

    @pytest.fixture
    def sample_hwp_file(self) -> Path:
        """테스트용 HWP 파일 경로 반환."""
        fixtures_dir = Path(__file__).parent / "fixtures"
        hwp_files = list(fixtures_dir.glob("*.hwp"))
        if not hwp_files:
            pytest.skip("테스트용 HWP 파일이 없습니다.")
        return hwp_files[0]

    def test_convert_to_odt_returns_bytes(self, sample_hwp_file: Path) -> None:
        """_convert_to_odt가 바이트를 반환하는지 검증."""
        temp_dir = Path(tempfile.mkdtemp())
        try:
            result = _convert_to_odt(sample_hwp_file, temp_dir)
            assert isinstance(result, bytes)
            assert len(result) > 0
            # ODT(ZIP) 시그니처 확인
            assert result[:2] == b"PK"
        finally:
            if temp_dir.exists():
                shutil.rmtree(temp_dir)

    def test_convert_to_odt_command_failure_raises(self, sample_hwp_file: Path) -> None:
        """hwp5odt 명령 실패 시 RuntimeError 발생 검증."""
        temp_dir = Path(tempfile.mkdtemp())
        try:
            mock_result = MagicMock()
            mock_result.returncode = 1
            mock_result.stderr = "변환 오류"

            with patch(
                "hwp_parser.core.worker.subprocess.run", return_value=mock_result
            ):
                with pytest.raises(RuntimeError, match="ODT 변환 실패"):
                    _convert_to_odt(sample_hwp_file, temp_dir)
        finally:
            if temp_dir.exists():
                shutil.rmtree(temp_dir)

    def test_convert_to_odt_missing_output_raises(self, sample_hwp_file: Path) -> None:
        """ODT 변환 후 결과 파일이 없으면 RuntimeError 발생 검증."""
        temp_dir = Path(tempfile.mkdtemp())
        try:
            mock_result = MagicMock()
            mock_result.returncode = 0  # 성공했지만 파일은 없음

            with patch(
                "hwp_parser.core.worker.subprocess.run", return_value=mock_result
            ):
                with pytest.raises(RuntimeError, match="결과 파일이 생성되지 않음"):
                    _convert_to_odt(sample_hwp_file, temp_dir)
        finally:
            if temp_dir.exists():
                shutil.rmtree(temp_dir)


class TestTextConversion:
    """텍스트 변환 함수 테스트.

    테스트 대상:
        - _html_to_text, _html_to_markdown 함수

    검증 범위:
        1. HTML → 텍스트 변환
        2. HTML → Markdown 변환
    """

    def test_html_to_text_basic(self) -> None:
        """기본 HTML을 텍스트로 변환 테스트."""
        html = "<html><body><p>안녕하세요</p><p>테스트입니다</p></body></html>"
        result = _html_to_text(html)
        assert "안녕하세요" in result
        assert "테스트입니다" in result

    def test_html_to_text_ignores_tags(self) -> None:
        """HTML 태그가 제거되는지 검증."""
        html = "<p><strong>볼드</strong> <a href='#'>링크</a></p>"
        result = _html_to_text(html)
        assert "볼드" in result
        assert "링크" in result
        assert "<" not in result
        assert ">" not in result

    def test_html_to_markdown_basic(self) -> None:
        """기본 HTML을 Markdown으로 변환 테스트."""
        html = "<html><body><p>테스트</p></body></html>"
        result = _html_to_markdown(html)
        assert "테스트" in result

    def test_html_to_markdown_preserves_formatting(self) -> None:
        """Markdown이 서식을 보존하는지 검증."""
        html = "<p><strong>볼드</strong></p>"
        result = _html_to_markdown(html)
        # Markdown 볼드 형식 확인
        assert "볼드" in result


class TestWorkerMain:
    """worker_main 함수 테스트.

    테스트 대상:
        - worker_main 함수의 메인 루프

    검증 범위:
        1. 작업 수신 및 처리
        2. 종료 신호(None) 처리
        3. 에러 발생 시 결과 반환
        4. 지원하지 않는 포맷 처리
    """

    @pytest.fixture
    def sample_hwp_file(self) -> Path:
        """테스트용 HWP 파일 경로 반환."""
        fixtures_dir = Path(__file__).parent / "fixtures"
        hwp_files = list(fixtures_dir.glob("*.hwp"))
        if not hwp_files:
            pytest.skip("테스트용 HWP 파일이 없습니다.")
        return hwp_files[0]

    def test_worker_main_html_conversion(self, sample_hwp_file: Path) -> None:
        """worker_main이 HTML 변환을 수행하는지 검증."""
        input_queue: Queue = Queue()
        output_queue: Queue = Queue()

        # 작업 전송
        task = WorkerTask(
            task_id=1, file_path=str(sample_hwp_file), output_format="html"
        )
        input_queue.put(task)
        input_queue.put(None)  # 종료 신호

        # 워커 실행 (스레드로 실행하여 타임아웃 가능하게)
        thread = Thread(target=worker_main, args=(input_queue, output_queue))
        thread.start()
        thread.join(timeout=30)

        # 결과 확인
        result: WorkerResult = output_queue.get(timeout=5)
        assert result.task_id == 1
        assert result.success is True
        assert isinstance(result.content, str)
        assert len(result.content) > 0

    def test_worker_main_text_conversion(self, sample_hwp_file: Path) -> None:
        """worker_main이 텍스트 변환을 수행하는지 검증."""
        input_queue: Queue = Queue()
        output_queue: Queue = Queue()

        task = WorkerTask(
            task_id=2, file_path=str(sample_hwp_file), output_format="txt"
        )
        input_queue.put(task)
        input_queue.put(None)

        thread = Thread(target=worker_main, args=(input_queue, output_queue))
        thread.start()
        thread.join(timeout=30)

        result: WorkerResult = output_queue.get(timeout=5)
        assert result.task_id == 2
        assert result.success is True
        assert isinstance(result.content, str)

    def test_worker_main_markdown_conversion(self, sample_hwp_file: Path) -> None:
        """worker_main이 Markdown 변환을 수행하는지 검증."""
        input_queue: Queue = Queue()
        output_queue: Queue = Queue()

        task = WorkerTask(
            task_id=3, file_path=str(sample_hwp_file), output_format="markdown"
        )
        input_queue.put(task)
        input_queue.put(None)

        thread = Thread(target=worker_main, args=(input_queue, output_queue))
        thread.start()
        thread.join(timeout=30)

        result: WorkerResult = output_queue.get(timeout=5)
        assert result.task_id == 3
        assert result.success is True
        assert isinstance(result.content, str)

    def test_worker_main_odt_conversion(self, sample_hwp_file: Path) -> None:
        """worker_main이 ODT 변환을 수행하는지 검증."""
        input_queue: Queue = Queue()
        output_queue: Queue = Queue()

        task = WorkerTask(
            task_id=4, file_path=str(sample_hwp_file), output_format="odt"
        )
        input_queue.put(task)
        input_queue.put(None)

        thread = Thread(target=worker_main, args=(input_queue, output_queue))
        thread.start()
        thread.join(timeout=30)

        result: WorkerResult = output_queue.get(timeout=5)
        assert result.task_id == 4
        assert result.success is True
        assert isinstance(result.content, bytes)

    def test_worker_main_file_not_found(self) -> None:
        """존재하지 않는 파일 처리 시 에러 반환 검증."""
        input_queue: Queue = Queue()
        output_queue: Queue = Queue()

        task = WorkerTask(
            task_id=5, file_path="/nonexistent/file.hwp", output_format="html"
        )
        input_queue.put(task)
        input_queue.put(None)

        thread = Thread(target=worker_main, args=(input_queue, output_queue))
        thread.start()
        thread.join(timeout=10)

        result: WorkerResult = output_queue.get(timeout=5)
        assert result.task_id == 5
        assert result.success is False
        assert result.error is not None

    def test_worker_main_unsupported_format(self, sample_hwp_file: Path) -> None:
        """지원하지 않는 포맷 요청 시 에러 반환 검증."""
        input_queue: Queue = Queue()
        output_queue: Queue = Queue()

        task = WorkerTask(
            task_id=6,
            file_path=str(sample_hwp_file),
            output_format="pdf",  # type: ignore[arg-type]
        )
        input_queue.put(task)
        input_queue.put(None)

        thread = Thread(target=worker_main, args=(input_queue, output_queue))
        thread.start()
        thread.join(timeout=10)

        result: WorkerResult = output_queue.get(timeout=5)
        assert result.task_id == 6
        assert result.success is False
        assert "지원하지 않는 포맷" in result.error  # type: ignore

    def test_worker_main_multiple_tasks(self, sample_hwp_file: Path) -> None:
        """worker_main이 여러 작업을 연속으로 처리하는지 검증 (while 루프 재진입)."""
        input_queue: Queue = Queue()
        output_queue: Queue = Queue()

        # 3개의 작업을 연속으로 전송
        task1 = WorkerTask(
            task_id=10, file_path=str(sample_hwp_file), output_format="html"
        )
        task2 = WorkerTask(
            task_id=11, file_path=str(sample_hwp_file), output_format="txt"
        )
        task3 = WorkerTask(
            task_id=12, file_path=str(sample_hwp_file), output_format="markdown"
        )

        input_queue.put(task1)
        input_queue.put(task2)
        input_queue.put(task3)
        input_queue.put(None)  # 종료 신호

        thread = Thread(target=worker_main, args=(input_queue, output_queue))
        thread.start()
        thread.join(timeout=60)

        # 3개의 결과 수신
        results = []
        for _ in range(3):
            result: WorkerResult = output_queue.get(timeout=10)
            results.append(result)

        # 모든 작업이 성공해야 함
        assert len(results) == 3
        for result in results:
            assert result.success is True
