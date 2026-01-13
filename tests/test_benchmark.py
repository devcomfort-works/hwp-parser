"""
HWP 변환 성능 벤치마크

pytest-benchmark를 사용하여 변환 성능을 측정합니다.

실행 방법:
    # 벤치마크만 실행
    rye run pytest tests/test_benchmark.py -v

    # 상세 통계 포함
    rye run pytest tests/test_benchmark.py -v --benchmark-verbose

    # 결과 저장
    rye run pytest tests/test_benchmark.py --benchmark-save=baseline

    # 이전 결과와 비교
    rye run pytest tests/test_benchmark.py --benchmark-compare=baseline
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import pytest

from hwp_parser.core import HWPConverter


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
