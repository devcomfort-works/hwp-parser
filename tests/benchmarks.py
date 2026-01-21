"""
HWP 변환 성능 벤치마크

pytest-benchmark를 사용하여 변환 성능을 측정합니다.

실행 방법:
    # 벤치마크만 실행
    rye run pytest tests/benchmarks.py -v

    # 상세 통계 포함
    rye run pytest tests/benchmarks.py -v --benchmark-verbose

    # 결과 저장
    rye run pytest tests/benchmarks.py --benchmark-save=baseline

    # 이전 결과와 비교
    rye run pytest tests/benchmarks.py --benchmark-compare=baseline
"""

from __future__ import annotations

import json
import os
import uuid
from pathlib import Path
from typing import Callable
from urllib.error import URLError
from urllib.request import Request, urlopen

import pytest

from hwp_parser.adapters.llama_index import HWPReader
from hwp_parser.core import HWPConverter


# === 핵심 케이스 ===
class TestConverterBenchmark:
    """HWPConverter 벤치마크"""

    @pytest.fixture
    def converter(self) -> HWPConverter:
        """HWPConverter 인스턴스"""
        return HWPConverter()

    def test_benchmark_to_html(
        self,
        benchmark: Callable,
        converter: HWPConverter,
        sample_hwp_file: Path,
    ) -> None:
        """HTML 변환 벤치마크"""
        result = benchmark(converter.to_html, sample_hwp_file)
        assert result.output_format == "html"

    def test_benchmark_to_text(
        self,
        benchmark: Callable,
        converter: HWPConverter,
        sample_hwp_file: Path,
    ) -> None:
        """텍스트 변환 벤치마크"""
        result = benchmark(converter.to_text, sample_hwp_file)
        assert result.output_format == "txt"

    def test_benchmark_to_markdown(
        self,
        benchmark: Callable,
        converter: HWPConverter,
        sample_hwp_file: Path,
    ) -> None:
        """Markdown 변환 벤치마크"""
        result = benchmark(converter.to_markdown, sample_hwp_file)
        assert result.output_format == "markdown"

    def test_benchmark_to_odt(
        self,
        benchmark: Callable,
        converter: HWPConverter,
        sample_hwp_file: Path,
    ) -> None:
        """ODT 변환 벤치마크"""
        result = benchmark(converter.to_odt, sample_hwp_file)
        assert result.output_format == "odt"


class TestMultiFileBenchmark:
    """여러 파일 변환 벤치마크"""

    @pytest.fixture
    def converter(self) -> HWPConverter:
        """HWPConverter 인스턴스"""
        return HWPConverter()

    def test_benchmark_batch_text_conversion(
        self,
        benchmark: Callable,
        converter: HWPConverter,
        small_hwp_files: list[Path],
    ) -> None:
        """여러 파일 텍스트 변환 벤치마크"""

        def convert_all() -> list:
            return [converter.to_text(f) for f in small_hwp_files]

        results = benchmark(convert_all)
        assert len(results) == len(small_hwp_files)

    def test_benchmark_batch_markdown_conversion(
        self,
        benchmark: Callable,
        converter: HWPConverter,
        small_hwp_files: list[Path],
    ) -> None:
        """여러 파일 Markdown 변환 벤치마크"""

        def convert_all() -> list:
            return [converter.to_markdown(f) for f in small_hwp_files]

        results = benchmark(convert_all)
        assert len(results) == len(small_hwp_files)


class TestPipelineBenchmark:
    """변환 파이프라인별 벤치마크"""

    @pytest.fixture
    def converter(self) -> HWPConverter:
        """HWPConverter 인스턴스"""
        return HWPConverter()

    @pytest.mark.parametrize(
        "output_format,expected_pipeline",
        [
            ("txt", "hwp→xhtml→txt"),
            ("html", "hwp→xhtml"),
            ("markdown", "hwp→xhtml→markdown"),
            ("odt", "hwp→odt"),
        ],
    )
    def test_benchmark_pipeline(
        self,
        benchmark: Callable,
        converter: HWPConverter,
        sample_hwp_file: Path,
        output_format: str,
        expected_pipeline: str,
    ) -> None:
        """파이프라인별 벤치마크"""
        result = benchmark(converter.convert, sample_hwp_file, output_format)
        assert result.pipeline == expected_pipeline


class TestLargeFileBenchmark:
    """큰 파일 변환 벤치마크"""

    @pytest.fixture
    def converter(self) -> HWPConverter:
        """HWPConverter 인스턴스"""
        return HWPConverter()

    @pytest.fixture
    def large_hwp_file(self, all_hwp_files: list[Path]) -> Path:
        """가장 큰 HWP 파일"""
        return max(all_hwp_files, key=lambda f: f.stat().st_size)

    def test_benchmark_large_file_to_text(
        self,
        benchmark: Callable,
        converter: HWPConverter,
        large_hwp_file: Path,
    ) -> None:
        """큰 파일 텍스트 변환 벤치마크"""
        result = benchmark(converter.to_text, large_hwp_file)
        assert result.output_format == "txt"

    def test_benchmark_large_file_to_markdown(
        self,
        benchmark: Callable,
        converter: HWPConverter,
        large_hwp_file: Path,
    ) -> None:
        """큰 파일 Markdown 변환 벤치마크"""
        result = benchmark(converter.to_markdown, large_hwp_file)
        assert result.output_format == "markdown"


# === 에지 케이스 ===
def _post_hwp(url: str, file_path: Path) -> dict:
    boundary = uuid.uuid4().hex
    mime = "application/octet-stream"
    file_bytes = file_path.read_bytes()

    header = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{file_path.name}"\r\n'
        f"Content-Type: {mime}\r\n\r\n"
    ).encode("utf-8")
    footer = f"\r\n--{boundary}--\r\n".encode("utf-8")
    body = header + file_bytes + footer

    request = Request(url, data=body, method="POST")
    request.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
    request.add_header("Content-Length", str(len(body)))

    with urlopen(request, timeout=30) as response:
        payload = response.read().decode("utf-8")
    return json.loads(payload)


def _rest_api_available(api_url: str) -> bool:
    health_url = api_url.replace("/convert/markdown", "/health")
    try:
        with urlopen(health_url, timeout=2) as response:
            return response.status == 200
    except URLError:
        return False


class TestInterfaceBenchmark:
    """인터페이스별 처리 시간 벤치마크"""

    @pytest.fixture
    def converter(self) -> HWPConverter:
        return HWPConverter()

    def test_python_api_latency(
        self,
        benchmark: Callable,
        converter: HWPConverter,
        sample_hwp_file: Path,
    ) -> None:
        """Python API 처리 시간"""
        result = benchmark(converter.to_markdown, sample_hwp_file)
        assert result.output_format == "markdown"

    def test_llama_index_latency(
        self,
        benchmark: Callable,
        sample_hwp_file: Path,
    ) -> None:
        """LlamaIndex HWPReader 처리 시간"""
        reader = HWPReader()
        docs = benchmark(reader.load_data, sample_hwp_file)
        assert len(docs) == 1

    def test_rest_api_latency(
        self,
        benchmark: Callable,
        sample_hwp_file: Path,
    ) -> None:
        """REST API 엔드투엔드 지연 시간"""
        api_url = os.environ.get(
            "HWP_BENCHMARK_API_URL", "http://localhost:3000/convert/markdown"
        )
        if not _rest_api_available(api_url):
            pytest.skip("REST API 서버가 실행 중이 아닙니다.")

        response = benchmark(_post_hwp, api_url, sample_hwp_file)
        assert response.get("output_format") == "markdown"
