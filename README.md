# HWP Parser

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: AGPL-3.0](https://img.shields.io/badge/License-AGPL%203.0-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![Coverage: 76%](https://img.shields.io/badge/coverage-76%25-green.svg)](https://github.com/devcomfort/hwp-parser)

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
from hwp_parser.core import HWPConverter

result = HWPConverter().to_markdown("document.hwp")
print(result.content)
```

## 주요 기능

| 기능                   | 설명                             |
| ---------------------- | -------------------------------- |
| 🔄 **다중 포맷 변환**  | HWP → Text, HTML, Markdown, ODT  |
| 🦙 **LlamaIndex 통합** | RAG 파이프라인에서 HWP 문서 활용 |
| 🌐 **REST API**        | BentoML 기반 HTTP API 서버       |

## 설치 옵션

```bash
# 기본 설치
pip install git+https://github.com/devcomfort-works/hwp-parser.git

# LlamaIndex 어댑터 포함
pip install "hwp-parser[llama-index] @ git+https://github.com/devcomfort-works/hwp-parser.git"

# REST API 서버 포함
pip install "hwp-parser[bentoml] @ git+https://github.com/devcomfort-works/hwp-parser.git"

# 전체 기능 포함
pip install "hwp-parser[all] @ git+https://github.com/devcomfort-works/hwp-parser.git"
```

## 사용 예시

### LlamaIndex RAG

```python
from hwp_parser.adapters.llama_index import HWPReader
from llama_index.core import VectorStoreIndex

documents = HWPReader().load_data("document.hwp")
index = VectorStoreIndex.from_documents(documents)
```

### REST API

```bash
bentoml serve hwp_parser.adapters.api:HWPService
curl -X POST http://localhost:3000/convert/markdown -F "file=@document.hwp"
```

## 문서

📖 **[공식 문서](https://devcomfort.github.io/hwp-parser/)** - 설치, 사용법, API 레퍼런스

## 개발

```bash
git clone https://github.com/devcomfort/hwp-parser.git
cd hwp-parser
rye sync          # 의존성 설치
rye run test      # 테스트 실행
rye run serve     # API 서버 실행
```

## 라이선스

[AGPL-3.0](LICENSE) - pyhwp 라이선스 준수

## 관련 링크

- [pyhwp](https://github.com/mete0r/pyhwp) - HWP 파일 파서 (핵심 의존성)
- [LlamaIndex](https://www.llamaindex.ai/) - LLM 데이터 프레임워크
- [BentoML](https://www.bentoml.com/) - ML 서비스 프레임워크
