# 사용 가이드

HWP Parser의 다양한 기능을 활용하는 방법을 안내합니다.

---

## 어떤 가이드를 찾고 계신가요?

| 시나리오                                          | 추천 가이드                            |
| ------------------------------------------------- | -------------------------------------- |
| HWP 파일을 텍스트/HTML/Markdown으로 변환하고 싶다 | [📦 Core 사용법](core-usage.md)        |
| LlamaIndex로 HWP 문서 기반 RAG를 구축하고 싶다    | [🦙 LlamaIndex 어댑터](llama-index.md) |
| HTTP API로 HWP 변환 서비스를 제공하고 싶다        | [🌐 REST API](rest-api.md)             |

---

## 빠른 비교

| 기능                      | Core | LlamaIndex      | REST API    |
| ------------------------- | ---- | --------------- | ----------- |
| Python 코드에서 직접 호출 | ✅   | ✅              | ❌          |
| HTTP 요청으로 호출        | ❌   | ❌              | ✅          |
| RAG 파이프라인 통합       | ❌   | ✅              | ❌          |
| 추가 설치 필요            | ❌   | `[llama-index]` | `[bentoml]` |

---

## 주요 클래스

| 클래스             | 모듈                              | 용도                                |
| ------------------ | --------------------------------- | ----------------------------------- |
| `HWPConverter`     | `hwp_parser.core`                 | HWP → 텍스트/HTML/Markdown/ODT 변환 |
| `ConversionResult` | `hwp_parser.core`                 | 변환 결과 데이터                    |
| `HWPReader`        | `hwp_parser.adapters.llama_index` | LlamaIndex Document 로더            |
| `HWPService`       | `hwp_parser.adapters.api`         | BentoML REST API 서비스             |

---

## 코드 한 줄 요약

### Core - 파일 변환

```python
from hwp_parser import HWPConverter
result = HWPConverter().to_markdown("document.hwp")
```

### LlamaIndex - RAG 파이프라인

```python
from hwp_parser import HWPReader
docs = HWPReader().load_data("document.hwp")
```

### REST API - HTTP 서비스

```bash
bentoml serve hwp_parser:HWPService
# curl -F "file=@document.hwp" localhost:3000/convert/markdown
```
