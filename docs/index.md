# HWP Parser

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: AGPL-3.0](https://img.shields.io/badge/License-AGPL%203.0-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![Coverage](https://raw.githubusercontent.com/devcomfort-works/hwp-parser/main/.github/badges/coverage.svg)](https://github.com/devcomfort-works/hwp-parser/actions/workflows/coverage.yml)
[![Hugging Face Spaces](https://img.shields.io/badge/%F0%9F%A4%97%20Hugging%20Face-Spaces-blue)](https://huggingface.co/spaces/devcomfort/hwp-parser)

**HWP 파일을 다양한 포맷으로 변환하는 Python 라이브러리**

> **✨ 체험하기**: 설치 없이 웹 브라우저에서 바로 사용해보세요! 👉 [Hugging Face Spaces 데모](https://huggingface.co/spaces/devcomfort/hwp-parser)

---

## HWP Parser란?

HWP Parser는 한글과컴퓨터의 HWP 파일을 텍스트, HTML, Markdown, ODT 형식으로 변환하는 Python 라이브러리입니다.

[pyhwp](https://github.com/mete0r/pyhwp) CLI 도구를 래핑하여 Python 코드에서 쉽게 HWP 파일을 처리할 수 있습니다.

```python
from hwp_parser import HWPConverter

result = HWPConverter().to_markdown("document.hwp")
print(result.content)
```

---

## 왜 HWP Parser인가?

### 🎯 문제

- HWP 파일은 한국에서 널리 사용되지만, 프로그래밍 언어에서 처리하기 어렵습니다
- pyhwp는 CLI 도구만 제공하여 Python 코드에서 직접 사용하기 불편합니다
- LLM/RAG 파이프라인에서 HWP 문서를 활용하려면 별도 변환 작업이 필요합니다

### ✅ 해결

| 기능                | 설명                                     |
| ------------------- | ---------------------------------------- |
| **간편한 API**      | 3줄 코드로 HWP → Markdown 변환           |
| **LlamaIndex 통합** | `HWPReader`로 RAG 파이프라인에 바로 연결 |
| **CLI 도구**        | 커맨드라인에서 HWP 파일 일괄 변환        |

---

## 주요 기능

| 기능                   | 설명                             |
| ---------------------- | -------------------------------- |
| 🔄 **다중 포맷 변환**  | HWP → Text, HTML, Markdown, ODT  |
| 🦙 **LlamaIndex 통합** | RAG 파이프라인에서 HWP 문서 활용 |
| 💻 **CLI 도구**        | 커맨드라인에서 일괄 변환         |
| ⚡ **병렬 처리**       | Worker 모드로 빠른 변환          |
| 🧪 **테스트 검증**     | 100% 커버리지                    |

---

## 빠른 시작

### 설치

```bash
# pip
pip install git+https://github.com/devcomfort-works/hwp-parser.git

# uv
uv add git+https://github.com/devcomfort-works/hwp-parser.git

# rye
rye add hwp-parser --git https://github.com/devcomfort-works/hwp-parser.git
```

> 📦 **PyPI 배포 예정**: 추후 PyPI에 `hwp-parser`라는 이름으로 배포될 예정입니다.

### 기본 사용

```python
from hwp_parser import HWPConverter

converter = HWPConverter()
result = converter.to_markdown("document.hwp")
print(result.content)
```

### 선택적 기능

| 명령어                                            | 용도                |
| ------------------------------------------------- | ------------------- |
| `pip install "hwp-parser[llama-index] @ git+..."` | LlamaIndex RAG 통합 |

[→ 상세 설치 가이드](getting-started/installation.md)

---

## 사용 시나리오

### 📦 파일 변환이 필요할 때

```python
from hwp_parser import HWPConverter

converter = HWPConverter()
markdown = converter.to_markdown("report.hwp")
html = converter.to_html("report.hwp")
text = converter.to_text("report.hwp")
```

[→ Core 사용법](guide/core-usage.md)

### 🦙 LLM/RAG 파이프라인을 구축할 때

```python
from hwp_parser import HWPReader
from llama_index.core import VectorStoreIndex

reader = HWPReader()
documents = reader.load_data("policy.hwp")
index = VectorStoreIndex.from_documents(documents)

response = index.as_query_engine().query("휴가 정책이 뭐야?")
```

[→ LlamaIndex 가이드](guide/llama-index.md)

### 💻 커맨드라인에서 일괄 변환할 때

```bash
# 모든 HWP 파일을 Markdown으로 변환
hwp-parser convert *.hwp --format markdown

# 4개 프로세스로 병렬 처리
hwp-parser convert documents/*.hwp --workers 4 --output-dir output/
```

[→ CLI 가이드](guide/cli.md)

---

## 변환 파이프라인

| 포맷       | 파이프라인             | 설명                    |
| ---------- | ---------------------- | ----------------------- |
| `txt`      | hwp → xhtml → txt      | html2text로 텍스트 추출 |
| `html`     | hwp → xhtml            | pyhwp hwp5html 명령     |
| `markdown` | hwp → xhtml → markdown | html-to-markdown 변환   |
| `odt`      | hwp → odt              | pyhwp hwp5odt 명령      |

---

## 문서 구조

| 섹션                                    | 내용                              |
| --------------------------------------- | --------------------------------- |
| [시작하기](getting-started/overview.md) | 설치, 요구사항, 빠른 시작         |
| [사용 가이드](guide/overview.md)        | Core, CLI, LlamaIndex 상세 가이드 |
| [문제 해결](troubleshooting.md)         | FAQ 및 트러블슈팅                 |

---

## 지원 및 기여

- [GitHub Issues](https://github.com/devcomfort-works/hwp-parser/issues) - 버그 리포트 및 기능 요청
- [GitHub Repository](https://github.com/devcomfort-works/hwp-parser) - 소스 코드 및 기여

---

## 라이선스

[AGPL-3.0](https://www.gnu.org/licenses/agpl-3.0) - pyhwp 라이선스 준수

---

## 관련 프로젝트

- [pyhwp](https://github.com/mete0r/pyhwp) - HWP 파일 파서 (핵심 의존성)
- [LlamaIndex](https://www.llamaindex.ai/) - LLM 데이터 프레임워크
