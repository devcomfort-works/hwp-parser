# 시작하기

HWP Parser를 사용하기 전에 확인해야 할 사항들입니다.

---

## 시작 전 체크리스트

| 항목   | 요구사항              | 확인 방법          |
| ------ | --------------------- | ------------------ |
| Python | 3.11 이상             | `python --version` |
| pip    | 최신 버전 권장        | `pip --version`    |
| OS     | Linux, macOS, Windows | -                  |

---

## 핵심 의존성

HWP Parser는 다음 라이브러리를 사용합니다:

| 패키지             | 용도                | 자동 설치 |
| ------------------ | ------------------- | --------- |
| `pyhwp`            | HWP 파일 파싱 (CLI) | ✅        |
| `html2text`        | HTML → 텍스트       | ✅        |
| `html-to-markdown` | HTML → Markdown     | ✅        |

---

## 어떤 기능이 필요하신가요?

| 사용 목적                       | 설치 명령어                                                                                      | 다음 단계                                    |
| ------------------------------- | ------------------------------------------------------------------------------------------------ | -------------------------------------------- |
| HWP → 텍스트/HTML/Markdown 변환 | `pip install git+https://github.com/devcomfort-works/hwp-parser.git`                             | [빠른 시작](quickstart.md)                   |
| 커맨드라인에서 일괄 변환        | `pip install git+https://github.com/devcomfort-works/hwp-parser.git`                             | [CLI 가이드](../guide/cli.md)                |
| LlamaIndex RAG 파이프라인       | `pip install "hwp-parser[llama-index] @ git+https://github.com/devcomfort-works/hwp-parser.git"` | [LlamaIndex 가이드](../guide/llama-index.md) |

---

## 다음 단계

1. **[📥 설치](installation.md)** - 패키지 설치 및 설치 옵션
2. **[🚀 빠른 시작](quickstart.md)** - 5분 만에 첫 HWP 변환
