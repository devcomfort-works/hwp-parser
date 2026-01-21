# 문제 해결

HWP Parser 사용 중 발생할 수 있는 일반적인 문제와 해결 방법입니다.

## 설치 문제

### pyhwp 설치 실패

#### 증상

```
error: command 'gcc' failed with exit status 1
```

#### 원인

C 컴파일러 또는 개발 헤더가 없습니다.

#### 해결 방법

**Ubuntu/Debian**

```bash
sudo apt-get update
sudo apt-get install python3-dev libxml2-dev libxslt1-dev build-essential
```

**macOS**

```bash
xcode-select --install
brew install libxml2 libxslt
```

**Windows**

[Visual Studio Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/) 설치

---

### ImportError: No module named 'hwp_parser'

#### 원인

패키지가 설치되지 않았거나 다른 가상 환경에 설치됨

#### 해결 방법

```bash
# 가상 환경 확인
which python

# 패키지 설치 확인
pip list | grep hwp-parser

# 재설치
pip install --upgrade git+https://github.com/devcomfort-works/hwp-parser.git
```

---

## 변환 문제

### FileNotFoundError

#### 증상

```
FileNotFoundError: [Errno 2] No such file or directory: 'document.hwp'
```

#### 해결 방법

```python
from pathlib import Path

# 절대 경로 사용
hwp_path = Path("/full/path/to/document.hwp")

# 경로 존재 확인
if not hwp_path.exists():
    print(f"파일이 없습니다: {hwp_path}")
else:
    result = converter.to_markdown(hwp_path)
```

---

### ValueError: Directory path not allowed

#### 원인

파일 경로 대신 디렉토리 경로를 입력함

#### 해결 방법

```python
# 잘못된 사용
converter.to_markdown("/path/to/directory/")  # 오류!

# 올바른 사용
converter.to_markdown("/path/to/directory/file.hwp")
```

---

### ODT 변환 실패 (RelaxNG 오류)

#### 증상

```
RelaxNG validation error
```

#### 원인

HWP 파일에 ODT 스키마와 호환되지 않는 복잡한 서식이 있음

#### 해결 방법

HTML 또는 Markdown 변환을 사용하세요:

```python
# ODT 대신 Markdown 사용
result = converter.to_markdown("document.hwp")

# 또는 HTML
result = converter.to_html("document.hwp")
```

---

### 한글 깨짐

#### 원인

파일 인코딩 문제 또는 터미널 설정

#### 해결 방법

```python
# 결과 저장 시 UTF-8 명시
result = converter.to_markdown("document.hwp")
Path("output.md").write_text(result.content, encoding="utf-8")
```

---

## API 서버 문제

### 포트 충돌

#### 증상

```
OSError: [Errno 98] Address already in use
```

#### 해결 방법

```bash
# 사용 중인 프로세스 확인
lsof -i :3000

# 프로세스 종료
kill -9 <PID>

# 또는 다른 포트 사용
HWP_SERVICE_PORT=8080 rye run serve
```

---

### CORS 오류

#### 증상

브라우저에서 API 호출 시:

```
Access to fetch at 'http://localhost:3000/...' has been blocked by CORS policy
```

#### 해결 방법

`.env` 파일에서 CORS 설정:

```bash
HWP_SERVICE_CORS_ENABLED=true
HWP_SERVICE_CORS_ORIGINS=http://localhost:3001,https://myapp.com
```

---

### 타임아웃 오류

#### 증상

대용량 파일 처리 시:

```
504 Gateway Timeout
```

#### 해결 방법

```bash
# 타임아웃 증가
HWP_SERVICE_TIMEOUT=600  # 10분
```

---

## LlamaIndex 문제

### 메모리 부족

#### 증상

대량의 문서 처리 시:

```
MemoryError
```

#### 해결 방법

```python
import gc
from hwp_parser.adapters.llama_index import HWPReader

reader = HWPReader()
all_documents = []

# 배치 처리
batch_size = 10
hwp_files = list(Path("docs").glob("*.hwp"))

for i in range(0, len(hwp_files), batch_size):
    batch = hwp_files[i:i+batch_size]
    for hwp_file in batch:
        docs = reader.load_data(hwp_file)
        all_documents.extend(docs)

    # 메모리 정리
    gc.collect()
```

---

### OpenAI API 오류

#### 증상

```
openai.RateLimitError: Rate limit reached
```

#### 해결 방법

```python
from llama_index.core import Settings
from llama_index.llms.openai import OpenAI

# 재시도 설정
Settings.llm = OpenAI(
    model="gpt-4o-mini",
    max_retries=5,
    timeout=60
)
```

---

## 성능 문제

### 변환 속도가 느림

#### 해결 방법

1. **워커 수 증가**

   ```bash
   HWP_SERVICE_WORKERS=4
   ```

2. **병렬 처리**

   ```python
   from multiprocessing import Pool

   def convert_file(path):
       converter = HWPConverter()
       return converter.to_markdown(path)

   with Pool(4) as pool:
       results = pool.map(convert_file, hwp_files)
   ```

3. **SSD 사용**

   임시 파일 I/O가 많으므로 SSD 사용 권장

---

## 도움 요청

문제가 해결되지 않으면:

1. [GitHub Issues](https://github.com/devcomfort-works/hwp-parser/issues)에서 기존 이슈 검색
2. 새 이슈 생성 시 다음 정보 포함:
   - Python 버전: `python --version`
   - 패키지 버전: `pip show hwp-parser`
   - OS 정보
   - 전체 오류 메시지
   - 재현 가능한 최소 코드
