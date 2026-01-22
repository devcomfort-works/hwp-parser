# 빠른 시작

HWP Parser를 사용하여 첫 번째 HWP 파일을 변환해봅니다.

## 어떤 용도로 사용하시나요?

| 용도               | 설명                            | 바로가기                                                                   |
| ------------------ | ------------------------------- | -------------------------------------------------------------------------- |
| 🌐 **웹 데모**     | 설치 없이 브라우저에서 체험     | [Hugging Face Spaces](https://huggingface.co/spaces/devcomfort/hwp-parser) |
| 📄 **파일 변환**   | HWP → Markdown, HTML, Text 변환 | [라이브러리로 시작](#라이브러리로-시작)                                    |
| 💻 **일괄 변환**   | CLI로 여러 파일 한 번에 변환    | [CLI로 시작](#cli로-시작)                                                  |
| 🤖 **AI/RAG 연동** | LlamaIndex로 HWP 문서 로드      | [LlamaIndex로 시작](#llamaindex로-시작)                                    |

---

## 라이브러리로 시작

Python 코드에서 직접 HWP 파일을 변환합니다.

### 설치

```bash
pip install git+https://github.com/devcomfort-works/hwp-parser.git
```

### 기본 변환

```python
from pathlib import Path
from hwp_parser import HWPConverter

# Converter 인스턴스 생성
converter = HWPConverter()

# Markdown으로 변환
result = converter.to_markdown("document.hwp")
print(result.content)
```

### 다양한 포맷

```python
from pathlib import Path

# 텍스트로 변환
text_result = converter.to_text("document.hwp")

# HTML로 변환
html_result = converter.to_html("document.hwp")

# ODT로 변환 (바이너리)
odt_result = converter.to_odt("document.hwp")
Path("output.odt").write_bytes(odt_result.content)
```

### 여러 파일 일괄 변환

```python
from pathlib import Path
from hwp_parser import HWPConverter

converter = HWPConverter()

for hwp_file in Path("documents").glob("*.hwp"):
    result = converter.to_markdown(hwp_file)
    hwp_file.with_suffix(".md").write_text(result.content)
    print(f"✅ {hwp_file.name} → .md")
```

👉 더 자세한 내용: [Core 사용법](../guide/core-usage.md)

---

## CLI로 시작

커맨드라인에서 HWP 파일을 변환합니다.

### 기본 사용

```bash
# 단일 파일 변환
hwp-parser convert document.hwp

# 특정 포맷으로 변환
hwp-parser convert document.hwp --format txt
hwp-parser convert document.hwp --format html
```

### 여러 파일 일괄 변환

```bash
# 현재 디렉터리의 모든 HWP 파일
hwp-parser convert *.hwp

# 특정 디렉터리에 저장
hwp-parser convert *.hwp --output-dir output/

# 4개 프로세스로 병렬 처리
hwp-parser convert *.hwp --workers 4
```

### 진행률 표시

```
$ hwp-parser convert *.hwp -w 4
총 10개의 파일을 변환합니다 (Format: markdown, Workers: 4)...
Converting [████████████████████████████████████████] 100%
모든 작업이 완료되었습니다.
```

👉 더 자세한 내용: [CLI 가이드](../guide/cli.md)

---

## LlamaIndex로 시작

LlamaIndex를 사용하여 HWP 문서를 RAG 파이프라인에 통합합니다.

### 설치

```bash
pip install "hwp-parser[llama-index] @ git+https://github.com/devcomfort-works/hwp-parser.git"
```

### HWP 문서 로드

```python
from pathlib import Path
from hwp_parser import HWPReader

reader = HWPReader()

# HWP 파일을 LlamaIndex Document로 로드
documents = reader.load_data(Path("document.hwp"))

# 변환된 내용 확인
print(documents[0].text)
```

### RAG 파이프라인 구축

```python
from pathlib import Path
from hwp_parser import HWPReader
from llama_index.core import VectorStoreIndex

reader = HWPReader()

# 여러 HWP 문서 로드
all_docs = []
for hwp_file in Path("docs").glob("*.hwp"):
    all_docs.extend(reader.load_data(hwp_file))

# 벡터 인덱스 생성
index = VectorStoreIndex.from_documents(all_docs)

# 질의응답
query_engine = index.as_query_engine()
response = query_engine.query("휴가 정책에 대해 알려주세요")
print(response)
```

### 메타데이터 추가

```python
from pathlib import Path
from hwp_parser import HWPReader

reader = HWPReader()
documents = reader.load_data(
    Path("policy.hwp"),
    extra_info={
        "category": "HR",
        "department": "인사팀",
        "year": 2024
    }
)

# 메타데이터 기반 필터링에 활용 가능
print(documents[0].metadata)
```

👉 더 자세한 내용: [LlamaIndex 어댑터](../guide/llama-index.md)

---

## 다음 단계

- [Core 사용법](../guide/core-usage.md): 변환 옵션 상세 설명
- [LlamaIndex 어댑터](../guide/llama-index.md): RAG 파이프라인 고급 사용법
- [REST API](../guide/rest-api.md): API 엔드포인트 전체 목록 및 환경변수 설정
