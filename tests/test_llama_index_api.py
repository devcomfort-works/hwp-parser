"""
LlamaIndex API (HWPReader) 테스트

Issue #3: HWPReader가 LlamaIndex Document를 정상 반환하는지 확인
"""

from __future__ import annotations

from pathlib import Path
import builtins
import importlib
from typing import Literal

import pytest

from hwp_parser.adapters.llama_index import HWPReader


# === 핵심 케이스 ===
def _load_docs(reader: HWPReader, file_path: Path) -> list:
    """HWPReader 로드 헬퍼.

    Parameters
    ----------
    reader : HWPReader
        LlamaIndex 리더.
    file_path : Path
        HWP 파일 경로.

    Returns
    -------
    list
        Document 목록.

    Notes
    -----
    - 목적: load_data 호출을 공통화.
    - 로직: reader.load_data 호출 결과 반환.
    - 데이터: 전달된 file_path.
    """
    return reader.load_data(file_path)


class TestHWPReaderCompatibility:
    def test_load_data_returns_document(self, sample_hwp_file: Path) -> None:
        """Document 반환 검증.

        Parameters
        ----------
        sample_hwp_file : Path
            샘플 HWP 파일.

        Notes
        -----
        - 목적: HWPReader가 Document 1개를 반환하는지 확인.
        - 로직: text/metadata 존재 및 메타데이터 값 검사.
        - 데이터: fixture `sample_hwp_file`.
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
        """여러 파일 로드 결과 개수 검증.

        Parameters
        ----------
        all_hwp_files : list[Path]
            전체 HWP 파일 목록.

        Notes
        -----
        - 목적: 파일 수와 문서 수가 일치하는지 확인.
        - 로직: 각 파일을 load_data로 누적 후 길이 비교.
        - 데이터: fixture `all_hwp_files`.
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
        """output_format별 Document 메타데이터 검증.

        Parameters
        ----------
        sample_hwp_file : Path
            샘플 HWP 파일.
        output_format : {"txt", "html", "markdown"}
            변환 포맷.

        Notes
        -----
        - 목적: 포맷이 메타데이터에 반영되는지 확인.
        - 로직: doc.metadata["format"] 비교.
        - 데이터: fixture `sample_hwp_file`, parametrize 값.
        """
        reader = HWPReader()
        docs = reader.load_data(sample_hwp_file, output_format=output_format)
        assert len(docs) == 1
        doc = docs[0]
        assert isinstance(doc.text, str)
        assert doc.metadata.get("format") == output_format

    def test_load_data_with_extra_info(self, sample_hwp_file: Path) -> None:
        """extra_info 병합 검증.

        Parameters
        ----------
        sample_hwp_file : Path
            샘플 HWP 파일.

        Notes
        -----
        - 목적: extra_info가 metadata에 병합되는지 확인.
        - 로직: extra_info 키가 metadata에 포함되는지 검사.
        - 데이터: extra_info 딕셔너리.
        """
        reader = HWPReader()
        docs = reader.load_data(sample_hwp_file, extra_info={"category": "rule"})
        assert len(docs) == 1
        doc = docs[0]
        assert doc.metadata.get("category") == "rule"

    def test_load_data_odt_binary(self, sample_hwp_file: Path) -> None:
        """ODT 변환 시 base64 인코딩 경로 검증.

        Parameters
        ----------
        sample_hwp_file : Path
            샘플 HWP 파일.

        Notes
        -----
        - 목적: ODT 바이너리 결과가 base64 문자열로 반환되는지 확인.
        - 로직: 결과 타입과 metadata 포맷 검사.
        - 데이터: fixture `sample_hwp_file`.
        """
        reader = HWPReader()
        docs = reader.load_data(sample_hwp_file, output_format="odt")
        assert len(docs) == 1
        doc = docs[0]
        assert isinstance(doc.text, str)
        assert doc.metadata.get("format") == "odt"

    def test_load_data_large_file(self, all_hwp_files: list[Path]) -> None:
        """큰 파일 변환 검증.

        Parameters
        ----------
        all_hwp_files : list[Path]
            전체 HWP 파일 목록.

        Notes
        -----
        - 목적: 가장 큰 파일도 정상 변환되는지 확인.
        - 로직: max(size) 파일을 load_data로 변환.
        - 데이터: fixture `all_hwp_files`.
        """
        reader = HWPReader()
        large_file = max(all_hwp_files, key=lambda f: f.stat().st_size)
        docs = reader.load_data(large_file)
        assert len(docs) == 1
        assert isinstance(docs[0].text, str)

    def test_load_data_bulk_files(self, small_hwp_files: list[Path]) -> None:
        """벌크 파일 변환 검증.

        Parameters
        ----------
        small_hwp_files : list[Path]
            작은 HWP 파일 목록.

        Notes
        -----
        - 목적: 여러 파일 변환 결과 개수 확인.
        - 로직: 각 파일 load_data 결과를 합산.
        - 데이터: fixture `small_hwp_files`.
        """
        reader = HWPReader()
        docs = []
        for file_path in small_hwp_files:
            docs.extend(reader.load_data(file_path))
        assert len(docs) == len(small_hwp_files)


# === 에지 케이스 ===


class TestHWPReaderEdgeCases:
    def test_importerror_branch_on_reload(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """llama-index-core ImportError 분기 커버.

        Notes
        -----
        - 목적: reader 모듈의 except ImportError 분기 실행.
        - 로직: import 훅으로 llama_index import 실패 유도 후 reload.
        - 데이터: 없음.
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
        """llama-index-core 미설치 경로 검증.

        Notes
        -----
        - 목적: LLAMA_INDEX_AVAILABLE=False 분기 커버.
        - 로직: 플래그를 False로 패치 후 ImportError 확인.
        - 데이터: 없음.
        """
        from hwp_parser.adapters.llama_index import reader as reader_module

        monkeypatch.setattr(reader_module, "LLAMA_INDEX_AVAILABLE", False)
        with pytest.raises(ImportError, match="llama-index-core"):
            reader_module.HWPReader()

    def test_load_data_accepts_string_path(self, sample_hwp_file: Path) -> None:
        """문자열 경로 입력 처리 검증.

        Parameters
        ----------
        sample_hwp_file : Path
            샘플 HWP 파일.

        Notes
        -----
        - 목적: Path 변환 분기 커버.
        - 로직: str 경로로 load_data 호출.
        - 데이터: fixture `sample_hwp_file`.
        """
        reader = HWPReader()
        docs = reader.load_data(str(sample_hwp_file))
        assert len(docs) == 1
