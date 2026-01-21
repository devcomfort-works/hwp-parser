"""LlamaIndex API (HWPReader) 테스트."""

from __future__ import annotations

import builtins
import importlib
from pathlib import Path
from typing import Literal

import pytest

from hwp_parser.adapters.llama_index import HWPReader


# === 핵심 케이스 ===


def _load_docs(reader: HWPReader, file_path: Path) -> list:
    """HWPReader 로드 헬퍼."""
    return reader.load_data(file_path)


class TestHWPReaderCompatibility:
    """HWPReader 호환성 테스트."""

    def test_load_data_returns_document(self, sample_hwp_file: Path) -> None:
        """HWP 파일 로드 → Document 반환.

        Given: 유효한 HWP 파일
        When: load_data 호출
        Then: Document 1개 반환, text/metadata 존재
        """
        reader = HWPReader()
        docs = _load_docs(reader, sample_hwp_file)
        assert len(docs) == 1
        doc = docs[0]
        assert hasattr(doc, "text")
        assert hasattr(doc, "metadata")
        assert isinstance(doc.text, str)
        assert doc.text

        metadata = doc.metadata
        assert metadata.get("file_name") == sample_hwp_file.name
        assert metadata.get("format") == "markdown"
        assert metadata.get("source") == "hwp-parser"
        assert metadata.get("conversion_pipeline") == "hwp→xhtml→markdown"

    def test_load_data_multiple_files(self, all_hwp_files: list[Path]) -> None:
        """여러 파일 로드 → 파일 수만큼 Document.

        Given: 여러 HWP 파일
        When: 각 파일에 load_data 호출
        Then: 파일 수 == Document 수
        """
        reader = HWPReader()
        docs = []
        for file_path in all_hwp_files:
            docs.extend(_load_docs(reader, file_path))

        assert len(docs) == len(all_hwp_files)

    @pytest.mark.parametrize("output_format", ["txt", "html", "markdown"])
    def test_load_data_output_format(
        self,
        sample_hwp_file: Path,
        output_format: Literal["txt", "html", "markdown"],
    ) -> None:
        """output_format 지정 → metadata에 반영.

        Given: 유효한 HWP 파일, output_format
        When: load_data(output_format=...) 호출
        Then: doc.metadata["format"] == output_format
        """
        reader = HWPReader()
        docs = reader.load_data(sample_hwp_file, output_format=output_format)
        assert len(docs) == 1
        doc = docs[0]
        assert isinstance(doc.text, str)
        assert doc.metadata.get("format") == output_format

    def test_load_data_with_extra_info(self, sample_hwp_file: Path) -> None:
        """extra_info → metadata에 병합.

        Given: extra_info={"category": "rule"}
        When: load_data 호출
        Then: doc.metadata["category"] == "rule"
        """
        reader = HWPReader()
        docs = reader.load_data(sample_hwp_file, extra_info={"category": "rule"})
        assert len(docs) == 1
        doc = docs[0]
        assert doc.metadata.get("category") == "rule"

    def test_load_data_odt_binary(self, sample_hwp_file: Path) -> None:
        """ODT 변환 → base64 문자열.

        Given: output_format="odt"
        When: load_data 호출
        Then: doc.text는 문자열, metadata["format"]=="odt"

        바이너리 ODT는 base64로 인코딩되어 반환.
        """
        reader = HWPReader()
        docs = reader.load_data(sample_hwp_file, output_format="odt")
        assert len(docs) == 1
        doc = docs[0]
        assert isinstance(doc.text, str)
        assert doc.metadata.get("format") == "odt"

    def test_load_data_large_file(self, all_hwp_files: list[Path]) -> None:
        """큰 파일 로드.

        Given: 가장 큰 HWP 파일
        When: load_data 호출
        Then: 정상 변환
        """
        reader = HWPReader()
        large_file = max(all_hwp_files, key=lambda f: f.stat().st_size)
        docs = reader.load_data(large_file)
        assert len(docs) == 1
        assert isinstance(docs[0].text, str)

    def test_load_data_bulk_files(self, small_hwp_files: list[Path]) -> None:
        """벌크 파일 로드.

        Given: 작은 HWP 파일 목록
        When: 각 파일에 load_data 호출
        Then: 파일 수만큼 Document 반환
        """
        reader = HWPReader()
        docs = []
        for file_path in small_hwp_files:
            docs.extend(reader.load_data(file_path))
        assert len(docs) == len(small_hwp_files)


# === 에지 케이스 ===


class TestHWPReaderEdgeCases:
    """HWPReader 에지 케이스 테스트."""

    def test_importerror_branch_on_reload(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """llama-index-core ImportError 분기.

        Given: llama_index import 실패하도록 mocking
        When: reader 모듈 reload
        Then: LLAMA_INDEX_AVAILABLE=False, Document=None

        선택적 의존성 미설치 시 graceful degradation.
        """
        import hwp_parser.adapters.llama_index.reader as reader_module

        original_import = builtins.__import__

        def _guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
            if name.startswith("llama_index"):
                raise ImportError("forced")
            return original_import(name, globals, locals, fromlist, level)

        monkeypatch.setattr(builtins, "__import__", _guarded_import)

        reloaded = importlib.reload(reader_module)
        assert reloaded.LLAMA_INDEX_AVAILABLE is False
        assert reloaded.Document is None
        assert reloaded.BaseReader is object

        builtins.__import__ = original_import
        importlib.reload(reader_module)

    def test_init_requires_llama_index(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """llama-index 미설치 → ImportError.

        Given: LLAMA_INDEX_AVAILABLE=False
        When: HWPReader() 생성
        Then: ImportError("llama-index-core") 발생
        """
        from hwp_parser.adapters.llama_index import reader as reader_module

        monkeypatch.setattr(reader_module, "LLAMA_INDEX_AVAILABLE", False)
        with pytest.raises(ImportError, match="llama-index-core"):
            reader_module.HWPReader()

    def test_load_data_accepts_string_path(self, sample_hwp_file: Path) -> None:
        """문자열 경로 입력 → Path 변환.

        Given: 문자열 형태의 파일 경로
        When: load_data 호출
        Then: 정상 변환
        """
        reader = HWPReader()
        docs = reader.load_data(str(sample_hwp_file))
        assert len(docs) == 1
