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
    """HWPReader LlamaIndex 호환성 테스트 스위트.

    테스트 대상:
        - HWPReader.load_data() 메서드 (LlamaIndex BaseReader 인터페이스)

    검증 범위:
        1. HWP 파일 로드 → Document 객체 반환
        2. Document.text, Document.metadata 속성 존재
        3. output_format 파라미터 지원 (txt, html, markdown, odt)
        4. extra_info가 metadata에 병합
        5. 여러 파일/큰 파일 처리

    비즈니스 컨텍스트:
        HWPReader는 LlamaIndex의 BaseReader를 상속받아
        RAG 파이프라인에서 HWP 문서를 활용할 수 있게 한다.
        VectorStoreIndex.from_documents()에 직접 전달 가능하다.

    의존성:
        - 외부 라이브러리: llama-index-core
        - pytest fixture: sample_hwp_file, all_hwp_files, small_hwp_files (conftest.py)
        - 테스트 데이터: tests/fixtures/*.hwp

    관련 테스트:
        - TestHWPReaderEdgeCases: 선택적 의존성 미설치 시 동작
    """

    def test_load_data_returns_document(self, sample_hwp_file: Path) -> None:
        """HWP 파일 로드 시 LlamaIndex Document 객체를 반환하는지 검증.

        시나리오:
            load_data()는 파일당 1개의 Document를 반환한다.
            Document는 text(변환된 콘텐츠)와 metadata(파일 정보)를 포함한다.

        의존성:
            - pytest fixture: sample_hwp_file
            - 모듈: hwp_parser.adapters.llama_index.HWPReader

        검증 항목:
            - Document 반환 개수 == 1
            - text, metadata 속성 존재
            - metadata에 file_name, format, source, conversion_pipeline 포함
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
        """여러 HWP 파일 로드 시 파일 수만큼 Document를 반환하는지 검증.

        시나리오:
            실제 RAG 파이프라인에서는 여러 문서를 로드하는 경우가 많다.
            각 파일에 대해 load_data()를 호출하면 파일 수만큼 Document가 생성된다.

        의존성:
            - pytest fixture: all_hwp_files (tests/fixtures/*.hwp 전체)
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
        """output_format 파라미터가 Document.metadata에 반영되는지 검증.

        시나리오:
            load_data(output_format=...)로 변환 포맷을 지정할 수 있다.
            지정된 포맷은 metadata["format"]에 저장된다.

        의존성:
            - pytest fixture: sample_hwp_file
            - 테스트 데이터: output_format 파라미터 (txt, html, markdown)

        관련 테스트:
            - test_python_api.TestConvert: HWPConverter.convert() 포맷 지정
        """
        reader = HWPReader()
        docs = reader.load_data(sample_hwp_file, output_format=output_format)
        assert len(docs) == 1
        doc = docs[0]
        assert isinstance(doc.text, str)
        assert doc.metadata.get("format") == output_format

    def test_load_data_with_extra_info(self, sample_hwp_file: Path) -> None:
        """extra_info 파라미터가 Document.metadata에 병합되는지 검증.

        시나리오:
            extra_info로 추가 메타데이터를 전달할 수 있다.
            이는 문서 분류, 출처 등 사용자 정의 정보를 추가할 때 유용하다.

        의존성:
            - pytest fixture: sample_hwp_file
            - 테스트 데이터: extra_info={"category": "rule"}
        """
        reader = HWPReader()
        docs = reader.load_data(sample_hwp_file, extra_info={"category": "rule"})
        assert len(docs) == 1
        doc = docs[0]
        assert doc.metadata.get("category") == "rule"

    def test_load_data_odt_binary(self, sample_hwp_file: Path) -> None:
        """ODT 포맷 변환 시 base64 문자열로 반환되는지 검증.

        시나리오:
            ODT는 바이너리 포맷이지만, Document.text는 문자열이어야 한다.
            따라서 바이너리 데이터는 base64로 인코딩되어 반환된다.

        의존성:
            - pytest fixture: sample_hwp_file
            - 테스트 데이터: output_format="odt"

        관련 테스트:
            - test_rest_api.TestResultToResponse.test_binary_result_to_response: REST API의 base64 처리
        """
        reader = HWPReader()
        docs = reader.load_data(sample_hwp_file, output_format="odt")
        assert len(docs) == 1
        doc = docs[0]
        assert isinstance(doc.text, str)
        assert doc.metadata.get("format") == "odt"

    def test_load_data_large_file(self, all_hwp_files: list[Path]) -> None:
        """큰 HWP 파일이 정상적으로 로드되는지 검증.

        시나리오:
            큰 파일도 메모리 초과나 타임아웃 없이 처리되어야 한다.
            tests/fixtures 중 가장 큰 파일로 테스트한다.

        의존성:
            - pytest fixture: all_hwp_files
        """
        reader = HWPReader()
        large_file = max(all_hwp_files, key=lambda f: f.stat().st_size)
        docs = reader.load_data(large_file)
        assert len(docs) == 1
        assert isinstance(docs[0].text, str)

    def test_load_data_bulk_files(self, small_hwp_files: list[Path]) -> None:
        """여러 파일 순차 로드가 정상적으로 동작하는지 검증.

        시나리오:
            RAG 파이프라인에서는 여러 문서를 순차적으로 로드하는 경우가 많다.
            작은 파일 목록으로 순차 로드를 테스트한다.

        의존성:
            - pytest fixture: small_hwp_files (크기 상위 3개 파일)
        """
        reader = HWPReader()
        docs = []
        for file_path in small_hwp_files:
            docs.extend(reader.load_data(file_path))
        assert len(docs) == len(small_hwp_files)


# === 에지 케이스 ===


class TestHWPReaderEdgeCases:
    """HWPReader 에지 케이스 테스트 스위트.

    테스트 대상:
        - llama-index-core 선택적 의존성 미설치 시 동작
        - 문자열 경로 입력 처리

    검증 범위:
        1. llama-index import 실패 시 graceful degradation
        2. LLAMA_INDEX_AVAILABLE=False 시 HWPReader() 생성 실패
        3. 문자열 경로 입력 시 Path로 자동 변환

    비즈니스 컨텍스트:
        llama-index-core는 선택적 의존성이다.
        미설치 시 HWPReader를 import할 수 있지만,
        인스턴스 생성 시 ImportError를 발생시켜야 한다.

    테스트 전략:
        builtins.__import__를 mocking하여 import 실패을 재현한다.
        importlib.reload()로 모듈을 다시 로드하여 상태를 재설정한다.

    관련 테스트:
        - TestHWPReaderCompatibility: 정상 동작 테스트
    """

    def test_importerror_branch_on_reload(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """llama-index import 실패 시 LLAMA_INDEX_AVAILABLE=False가 되는지 검증.

        시나리오:
            llama-index-core가 설치되지 않은 환경에서 모듈을 import하면
            LLAMA_INDEX_AVAILABLE=False로 설정되고, Document와 BaseReader는
            None/object로 fallback된다.

        의존성:
            - pytest fixture: monkeypatch
            - mock: builtins.__import__ (llama_index* import 시 ImportError)
            - 모듈: hwp_parser.adapters.llama_index.reader

        테스트 후 정리:
            모듈을 다시 reload하여 정상 상태로 복구한다.
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
        """LLAMA_INDEX_AVAILABLE=False 시 HWPReader 생성이 실패하는지 검증.

        시나리오:
            llama-index가 설치되지 않은 상태에서 HWPReader()를 생성하면
            ImportError를 발생시켜 사용자에게 의존성 설치를 안내해야 한다.

        의존성:
            - pytest fixture: monkeypatch
            - mock: reader_module.LLAMA_INDEX_AVAILABLE = False
        """
        from hwp_parser.adapters.llama_index import reader as reader_module

        monkeypatch.setattr(reader_module, "LLAMA_INDEX_AVAILABLE", False)
        with pytest.raises(ImportError, match="llama-index-core"):
            reader_module.HWPReader()

    def test_load_data_accepts_string_path(self, sample_hwp_file: Path) -> None:
        """문자열 경로 입력이 Path로 자동 변환되는지 검증.

        시나리오:
            사용자 편의를 위해 문자열 경로도 허용한다.
            내부적으로 Path로 변환하여 처리한다.

        의존성:
            - pytest fixture: sample_hwp_file

        관련 테스트:
            - test_python_api.TestFileValidation.test_validate_string_path: HWPConverter의 동일한 동작
        """
        reader = HWPReader()
        docs = reader.load_data(str(sample_hwp_file))
        assert len(docs) == 1
