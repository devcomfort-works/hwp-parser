# CLI 사용법

커맨드라인에서 HWP 파일을 일괄 변환하는 방법을 설명합니다.

## 설치

CLI 도구는 기본 설치에 포함되어 있습니다:

```bash
pip install git+https://github.com/devcomfort-works/hwp-parser.git
```

## 기본 사용법

### 단일 파일 변환

```bash
# Markdown으로 변환 (기본값)
hwp-parser convert document.hwp

# 특정 포맷으로 변환
hwp-parser convert document.hwp --format txt
hwp-parser convert document.hwp --format html
hwp-parser convert document.hwp --format odt
```

### 여러 파일 변환

```bash
# 현재 디렉터리의 모든 HWP 파일
hwp-parser convert *.hwp

# 특정 디렉터리의 모든 HWP 파일
hwp-parser convert documents/

# 재귀적으로 모든 HWP 파일
hwp-parser convert "**/*.hwp"
```

## 옵션

### 출력 포맷 (`--format`, `-f`)

변환할 출력 포맷을 지정합니다.

```bash
hwp-parser convert document.hwp --format markdown  # 기본값
hwp-parser convert document.hwp -f txt
hwp-parser convert document.hwp -f html
hwp-parser convert document.hwp -f odt
```

| 포맷       | 설명          | 출력                                            |
| ---------- | ------------- | ----------------------------------------------- |
| `markdown` | Markdown 형식 | `document.md`                                   |
| `txt`      | 순수 텍스트   | `document.txt`                                  |
| `html`     | HTML 디렉터리 | `document/` (index.xhtml, styles.css, bindata/) |
| `odt`      | Open Document | `document.odt`                                  |

### 출력 디렉터리 (`--output-dir`, `-o`)

변환 결과를 저장할 디렉터리를 지정합니다.

```bash
# output/ 디렉터리에 저장
hwp-parser convert *.hwp --output-dir output/

# 축약형
hwp-parser convert *.hwp -o output/
```

### 병렬 처리 (`--workers`, `-w`)

병렬 처리에 사용할 프로세스 수를 지정합니다. 기본값은 CPU 코어 수입니다.

```bash
# 4개 프로세스로 병렬 처리
hwp-parser convert *.hwp --workers 4

# 축약형
hwp-parser convert *.hwp -w 4
```

### 상세 로그 (`--verbose`, `-v`)

변환 과정의 상세 로그를 출력합니다.

```bash
hwp-parser convert document.hwp --verbose
hwp-parser convert document.hwp -v
```

## 예제

### 문서 일괄 변환

```bash
# 모든 HWP 파일을 Markdown으로 변환
hwp-parser convert documents/*.hwp -o output/ -f markdown

# 4개 프로세스로 빠르게 변환
hwp-parser convert "**/*.hwp" -w 4 -v
```

### HTML 변환

HTML 변환은 디렉터리 구조로 출력됩니다:

```bash
hwp-parser convert document.hwp -f html -o output/
```

결과:

```
output/
└── document/
    ├── index.xhtml    # 메인 HTML
    ├── styles.css     # 스타일시트
    └── bindata/       # 이미지 등
        ├── BIN0001.png
        └── BIN0002.jpg
```

### 진행률 표시

여러 파일 변환 시 진행률이 표시됩니다:

```
$ hwp-parser convert *.hwp -w 4
총 10개의 파일을 변환합니다 (Format: markdown, Workers: 4)...
Converting [████████████████████████████████████████] 100%
모든 작업이 완료되었습니다.
```

## Python에서 CLI 호출

```python
import subprocess

# CLI 명령 실행
subprocess.run([
    "hwp-parser", "convert",
    "documents/*.hwp",
    "--format", "markdown",
    "--output-dir", "output/",
    "--workers", "4"
])
```

## 관련 문서

- [Core 사용법](core-usage.md) - Python API로 변환하기
- [LlamaIndex 어댑터](llama-index.md) - RAG 파이프라인 구축
