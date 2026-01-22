# HWP Parser

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: AGPL-3.0](https://img.shields.io/badge/License-AGPL%203.0-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![Coverage](https://raw.githubusercontent.com/devcomfort-works/hwp-parser/main/.github/badges/coverage.svg)](https://github.com/devcomfort-works/hwp-parser/actions/workflows/coverage.yml)

HWP 파일을 텍스트, HTML, Markdown, ODT로 변환하는 Python 라이브러리입니다.

## 빠른 시작

```bash
# pip
pip install git+https://github.com/devcomfort-works/hwp-parser.git

# uv
uv add git+https://github.com/devcomfort-works/hwp-parser.git

# rye
rye add hwp-parser --git https://github.com/devcomfort-works/hwp-parser.git
```

> 📦 **PyPI 배포 예정**: 추후 PyPI에 `hwp-parser`라는 이름으로 배포될 예정입니다.

```python
# 1. 기본 변환 (Python API)
from hwp_parser import HWPConverter

result = HWPConverter().to_markdown("document.hwp")
print(result.content)

# 2. RAG 파이프라인 (LlamaIndex)
from hwp_parser import HWPReader
from llama_index.core import VectorStoreIndex

documents = HWPReader().load_data("document.hwp")
index = VectorStoreIndex.from_documents(documents)
```

```bash
# 3. CLI 도구 사용
hwp-parser convert *.hwp

# 4. Web UI 실행 (Gradio)
hwp-parser web
```

## 주요 기능

| 기능                   | 설명                             |
| ---------------------- | -------------------------------- |
| 🔄 **다중 포맷 변환**  | HWP → Text, HTML, Markdown, ODT  |
| 💻 **CLI 도구**        | 터미널에서 대량 파일 변환 처리   |
| 🖥️ **Web UI**          | Gradio 기반의 대화형 변환 데모   |
| 🦙 **LlamaIndex 통합** | RAG 파이프라인에서 HWP 문서 활용 |

## 설치 옵션

```bash
# pip 기본 설치
pip install git+https://github.com/devcomfort-works/hwp-parser.git

# pip LlamaIndex 어댑터 포함
pip install "hwp-parser[llama-index] @ git+https://github.com/devcomfort-works/hwp-parser.git"

# uv 기본 설치
uv add git+https://github.com/devcomfort-works/hwp-parser.git

# uv LlamaIndex 어댑터 포함
uv add "git+https://github.com/devcomfort-works/hwp-parser.git[llama-index]"

# rye 기본 설치
rye add hwp-parser --git https://github.com/devcomfort-works/hwp-parser.git

# rye LlamaIndex 어댑터 포함
rye add "hwp-parser[llama-index]" --git https://github.com/devcomfort-works/hwp-parser.git
```

## 사용 예시

### LlamaIndex RAG

```python
from hwp_parser import HWPReader
from llama_index.core import VectorStoreIndex

documents = HWPReader().load_data("document.hwp")
index = VectorStoreIndex.from_documents(documents)
```

## 개발

```bash
git clone https://github.com/devcomfort-works/hwp-parser.git
cd hwp-parser
rye sync          # 의존성 설치
```

### 사용 가능한 명령어

`pyproject.toml`에 정의된 주요 스크립트입니다. (개발 환경 전용)

| 명령어              | 설명                                                     |
| ------------------- | -------------------------------------------------------- |
| `rye run web`       | **Web UI 실행**: `hwp-parser web`의 단축 명령어입니다.   |
| `rye run test`      | **테스트**: 전체 테스트 스위트를 병렬로 실행합니다.      |
| `rye run test-cov`  | **커버리지**: 테스트 실행 및 코드 커버리지를 측정합니다. |
| `rye run benchmark` | **벤치마크**: 변환 성능을 측정합니다.                    |
| `rye run docs`      | **문서 서버**: 로컬에서 문서를 미리 봅니다.              |

## 라이선스

[AGPL-3.0](LICENSE) - pyhwp 라이선스 준수

## 관련 링크

- [pyhwp](https://github.com/mete0r/pyhwp) - HWP 파일 파서 (핵심 의존성)
- [LlamaIndex](https://www.llamaindex.ai/) - LLM 데이터 프레임워크
