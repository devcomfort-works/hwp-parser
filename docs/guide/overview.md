# 사용 가이드

HWP Parser의 다양한 기능을 활용하는 방법을 안내합니다.

---

## 어떤 가이드를 찾고 계신가요?

| 시나리오                                           | 추천 가이드                                                                   |
| -------------------------------------------------- | ----------------------------------------------------------------------------- |
| **(설치 없음)** 웹 브라우저에서 바로 체험하고 싶다 | [🌐 Hugging Face Spaces](https://huggingface.co/spaces/devcomfort/hwp-parser) |
| HWP 파일을 텍스트/HTML/Markdown으로 변환하고 싶다  | [📦 Core 사용법](core-usage.md)                                               |
| 커맨드라인에서 HWP 파일을 일괄 변환하고 싶다       | [💻 CLI 사용법](cli.md)                                                       |
| LlamaIndex로 HWP 문서 기반 RAG를 구축하고 싶다     | [🦙 LlamaIndex 어댑터](llama-index.md)                                        |

---

## 빠른 비교

| 기능                      | Core | CLI | LlamaIndex      |
| ------------------------- | ---- | --- | --------------- |
| Python 코드에서 직접 호출 | ✅   | ❌  | ✅              |
| 커맨드라인 사용           | ❌   | ✅  | ❌              |
| 병렬 처리 (Worker)        | ✅   | ✅  | ❌              |
| RAG 파이프라인 통합       | ❌   | ❌  | ✅              |
| 추가 설치 필요            | ❌   | ❌  | `[llama-index]` |

---

## 주요 클래스

| 클래스             | 모듈                              | 용도                                |
| ------------------ | --------------------------------- | ----------------------------------- |
| `HWPConverter`     | `hwp_parser.core`                 | HWP → 텍스트/HTML/Markdown/ODT 변환 |
| `ConversionResult` | `hwp_parser.core`                 | 변환 결과 데이터 (txt/md/odt)       |
| `HTMLDirResult`    | `hwp_parser.core`                 | HTML 변환 결과 (xhtml/css/bindata)  |
| `HWPReader`        | `hwp_parser.adapters.llama_index` | LlamaIndex Document 로더            |

---

## 코드 한 줄 요약

### Core - 파일 변환

```python
from hwp_parser import HWPConverter
result = HWPConverter().to_markdown("document.hwp")
```

### CLI - 커맨드라인 변환

```bash
hwp-parser convert *.hwp --format markdown --workers 4
```

### LlamaIndex - RAG 파이프라인

```python
from hwp_parser import HWPReader
docs = HWPReader().load_data("document.hwp")
```
