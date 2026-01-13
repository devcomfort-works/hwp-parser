# LlamaIndex 어댑터

LlamaIndex와 통합하여 RAG(Retrieval-Augmented Generation) 파이프라인에서 HWP 문서를 활용하는 방법을 설명합니다.

## 설치

LlamaIndex 어댑터를 사용하려면 추가 의존성을 설치해야 합니다:

```bash
pip install hwp-parser[llama-index]
```

## 기본 사용법

### HWPReader

`HWPReader`는 LlamaIndex의 `BaseReader` 인터페이스를 구현한 클래스입니다.

```python
from pathlib import Path
from hwp_parser.adapters.llama_index import HWPReader

reader = HWPReader()

# 단일 파일 로드
documents = reader.load_data(Path("document.hwp"))

# Document 내용 확인
doc = documents[0]
print(doc.text)           # 변환된 텍스트
print(doc.metadata)       # 메타데이터
```

### 출력 포맷 지정

기본적으로 Markdown 포맷으로 변환됩니다. 다른 포맷을 지정할 수 있습니다:

```python
# Markdown (기본값)
documents = reader.load_data(Path("document.hwp"))

# 텍스트
documents = reader.load_data(Path("document.hwp"), output_format="txt")

# HTML
documents = reader.load_data(Path("document.hwp"), output_format="html")
```

### 추가 메타데이터

문서에 추가 메타데이터를 포함할 수 있습니다:

```python
documents = reader.load_data(
    Path("document.hwp"),
    extra_info={
        "category": "regulation",
        "department": "HR",
        "year": 2024
    }
)

# 메타데이터 확인
print(documents[0].metadata)
# {
#     "file_name": "document.hwp",
#     "file_path": "/path/to/document.hwp",
#     "output_format": "markdown",
#     "category": "regulation",
#     "department": "HR",
#     "year": 2024
# }
```

## RAG 파이프라인 구축

### 기본 질의응답 시스템

```python
from pathlib import Path
from hwp_parser.adapters.llama_index import HWPReader
from llama_index.core import VectorStoreIndex, Settings
from llama_index.llms.openai import OpenAI

# 설정
Settings.llm = OpenAI(model="gpt-4o-mini")

# HWP 문서 로드
reader = HWPReader()
documents = reader.load_data(Path("company_policy.hwp"))

# 인덱스 생성
index = VectorStoreIndex.from_documents(documents)

# 질의응답
query_engine = index.as_query_engine()
response = query_engine.query("휴가 정책에 대해 알려주세요")
print(response)
```

### 여러 문서 로드

```python
from pathlib import Path
from hwp_parser.adapters.llama_index import HWPReader
from llama_index.core import VectorStoreIndex

reader = HWPReader()
all_documents = []

# 디렉토리 내 모든 HWP 파일 로드
for hwp_file in Path("docs").glob("**/*.hwp"):
    docs = reader.load_data(hwp_file)
    all_documents.extend(docs)

# 통합 인덱스 생성
index = VectorStoreIndex.from_documents(all_documents)
```

### 부서별 문서 분류

```python
from pathlib import Path
from hwp_parser.adapters.llama_index import HWPReader

reader = HWPReader()

# 부서별 디렉토리 구조에서 로드
departments = ["hr", "finance", "engineering"]
all_documents = []

for dept in departments:
    dept_path = Path(f"docs/{dept}")
    for hwp_file in dept_path.glob("*.hwp"):
        docs = reader.load_data(
            hwp_file,
            extra_info={"department": dept}
        )
        all_documents.extend(docs)
```

## 고급 사용법

### 메타데이터 필터링

LlamaIndex의 메타데이터 필터를 활용하여 특정 문서만 검색할 수 있습니다:

```python
from llama_index.core.vector_stores import MetadataFilters, ExactMatchFilter

# 특정 부서의 문서만 검색
filters = MetadataFilters(
    filters=[ExactMatchFilter(key="department", value="HR")]
)

retriever = index.as_retriever(filters=filters)
nodes = retriever.retrieve("휴가 정책")
```

### 청킹 전략

대용량 문서의 경우 적절한 청킹 전략을 사용합니다:

```python
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core import VectorStoreIndex

# 문서 로드
reader = HWPReader()
documents = reader.load_data(Path("large_document.hwp"))

# 커스텀 노드 파서
parser = SentenceSplitter(chunk_size=1024, chunk_overlap=200)
nodes = parser.get_nodes_from_documents(documents)

# 인덱스 생성
index = VectorStoreIndex(nodes)
```

### 임베딩 모델 변경

```python
from llama_index.core import Settings, VectorStoreIndex
from llama_index.embeddings.openai import OpenAIEmbedding

# 임베딩 모델 설정
Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small")

# 인덱스 생성
index = VectorStoreIndex.from_documents(documents)
```

## 실전 예제: 사내 문서 검색 시스템

```python
from pathlib import Path
from hwp_parser.adapters.llama_index import HWPReader
from llama_index.core import VectorStoreIndex, Settings
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding

# 설정
Settings.llm = OpenAI(model="gpt-4o-mini", temperature=0)
Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small")

def load_company_documents(docs_dir: Path) -> list:
    """회사 문서 로드"""
    reader = HWPReader()
    all_docs = []

    # 문서 유형별 분류
    doc_types = {
        "policy": "정책",
        "manual": "매뉴얼",
        "report": "보고서"
    }

    for doc_type, korean_name in doc_types.items():
        type_dir = docs_dir / doc_type
        if type_dir.exists():
            for hwp_file in type_dir.glob("*.hwp"):
                docs = reader.load_data(
                    hwp_file,
                    extra_info={
                        "doc_type": doc_type,
                        "doc_type_korean": korean_name
                    }
                )
                all_docs.extend(docs)

    return all_docs

def create_search_engine(documents: list):
    """검색 엔진 생성"""
    index = VectorStoreIndex.from_documents(documents)
    return index.as_query_engine(
        response_mode="tree_summarize",
        similarity_top_k=5
    )

# 사용
if __name__ == "__main__":
    docs = load_company_documents(Path("company_docs"))
    engine = create_search_engine(docs)

    # 질문하기
    response = engine.query("신입사원 온보딩 절차가 어떻게 되나요?")
    print(response)
```

## 트러블슈팅

### 메모리 부족

대량의 문서를 처리할 때 메모리 부족이 발생할 수 있습니다:

```python
# 배치 처리로 메모리 관리
batch_size = 10
for i in range(0, len(hwp_files), batch_size):
    batch = hwp_files[i:i+batch_size]
    # 배치 처리 후 가비지 컬렉션
    import gc
    gc.collect()
```

### 변환 실패 처리

일부 파일 변환 실패 시 계속 진행:

```python
documents = []
for hwp_file in hwp_files:
    try:
        docs = reader.load_data(hwp_file)
        documents.extend(docs)
    except Exception as e:
        print(f"변환 실패: {hwp_file.name} - {e}")
        continue
```

---

## API 레퍼런스

### HWPReader

```python
class HWPReader(BaseReader):
    """LlamaIndex용 HWP 파일 리더"""
```

#### load_data()

```python
def load_data(
    self,
    file: Path,
    output_format: str = "markdown",
    extra_info: dict | None = None
) -> list[Document]:
    """
    HWP 파일을 LlamaIndex Document로 로드합니다.

    Args:
        file: HWP 파일 경로
        output_format: 출력 포맷 ("txt", "html", "markdown")
        extra_info: Document에 추가할 메타데이터

    Returns:
        list[Document]: 변환된 Document 리스트

    Raises:
        FileNotFoundError: 파일이 존재하지 않는 경우
        ImportError: llama-index가 설치되지 않은 경우
    """
```

> ⚠️ ODT 포맷은 바이너리이므로 지원하지 않습니다.

#### Document 메타데이터

반환되는 Document에 포함되는 기본 메타데이터:

| 키              | 설명                 |
| --------------- | -------------------- |
| `file_name`     | 원본 파일 이름       |
| `file_path`     | 원본 파일 전체 경로  |
| `output_format` | 사용된 출력 포맷     |
| `pipeline`      | 변환 파이프라인      |
| `converted_at`  | 변환 시각 (ISO 형식) |
