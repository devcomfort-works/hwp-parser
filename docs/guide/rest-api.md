# REST API

BentoML 기반의 REST API 서버를 실행하고 사용하는 방법을 설명합니다.

## 설치

REST API 서버를 사용하려면 추가 의존성을 설치해야 합니다:

```bash
pip install "hwp-parser[bentoml] @ git+https://github.com/devcomfort-works/hwp-parser.git"
```

## 서버 실행

### 기본 실행

```bash
# rye 사용 시 (권장)
rye run serve

# 또는 직접 실행
bentoml serve hwp_parser.adapters.api:HWPService
```

서버는 기본적으로 `http://localhost:3000`에서 실행됩니다.

### 개발 모드

파일 변경 시 자동으로 서버를 재시작합니다:

```bash
bentoml serve hwp_parser.adapters.api:HWPService --reload
```

## 환경변수 설정

`.env.example`을 `.env`로 복사하여 설정을 커스터마이징할 수 있습니다:

```bash
cp .env.example .env
```

### 사용 가능한 환경변수

| 환경변수                      | 설명                           | 기본값       |
| ----------------------------- | ------------------------------ | ------------ |
| `HWP_SERVICE_NAME`            | 서비스 이름                    | `hwp-parser` |
| `HWP_SERVICE_WORKERS`         | 워커 수 (프로세스 병렬화)      | `1`          |
| `HWP_SERVICE_TIMEOUT`         | 요청 타임아웃 (초)             | `300`        |
| `HWP_SERVICE_MAX_CONCURRENCY` | 최대 동시 요청 수              | `50`         |
| `HWP_SERVICE_PORT`            | HTTP 서버 포트                 | `3000`       |
| `HWP_SERVICE_CORS_ENABLED`    | CORS 활성화 여부               | `false`      |
| `HWP_SERVICE_CORS_ORIGINS`    | CORS 허용 오리진 (콤마로 구분) | `*`          |

### .env 예시

```bash
# 서비스 설정
HWP_SERVICE_NAME=hwp-parser
HWP_SERVICE_WORKERS=4
HWP_SERVICE_TIMEOUT=600
HWP_SERVICE_MAX_CONCURRENCY=100

# HTTP 설정
HWP_SERVICE_PORT=8080

# CORS 설정
HWP_SERVICE_CORS_ENABLED=true
HWP_SERVICE_CORS_ORIGINS=http://localhost:3000,https://myapp.com
```

## API 문서

BentoML은 자동으로 OpenAPI/Swagger 문서를 생성합니다.

| URL                            | 설명                |
| ------------------------------ | ------------------- |
| `http://localhost:3000`        | Swagger UI          |
| `http://localhost:3000/docs`   | Swagger UI (별칭)   |
| `http://localhost:3000/schema` | OpenAPI JSON 스키마 |

## API 엔드포인트

### 헬스 체크

서버 상태를 확인합니다.

**요청**

```bash
curl -X POST http://localhost:3000/health
```

**응답**

```json
{
  "status": "healthy",
  "service": "hwp-parser"
}
```

### 지원 포맷 확인

지원되는 출력 포맷 목록을 반환합니다.

**요청**

```bash
curl -X POST http://localhost:3000/formats
```

**응답**

```json
{
  "supported_formats": ["txt", "html", "markdown", "odt"],
  "default_format": "markdown"
}
```

### 텍스트로 변환

**요청**

```bash
curl -X POST http://localhost:3000/convert/text \
    -F "file=@document.hwp"
```

**응답**

```json
{
  "content": "변환된 텍스트 내용...",
  "source_name": "document.hwp",
  "output_format": "txt",
  "pipeline": "hwp→xhtml→txt",
  "is_binary": false,
  "content_length": 1234
}
```

### HTML로 변환

**요청**

```bash
curl -X POST http://localhost:3000/convert/html \
    -F "file=@document.hwp"
```

**응답**

```json
{
  "content": "<html>...</html>",
  "source_name": "document.hwp",
  "output_format": "html",
  "pipeline": "hwp→xhtml",
  "is_binary": false,
  "content_length": 5678
}
```

### Markdown으로 변환

**요청**

```bash
curl -X POST http://localhost:3000/convert/markdown \
    -F "file=@document.hwp"
```

**응답**

```json
{
  "content": "# 제목\n\n본문 내용...",
  "source_name": "document.hwp",
  "output_format": "markdown",
  "pipeline": "hwp→xhtml→markdown",
  "is_binary": false,
  "content_length": 2345
}
```

### ODT로 변환

**요청**

```bash
curl -X POST http://localhost:3000/convert/odt \
    -F "file=@document.hwp"
```

**응답**

```json
{
  "content": "UEsDBBQAAAA...",
  "source_name": "document.hwp",
  "output_format": "odt",
  "pipeline": "hwp→odt",
  "is_binary": true,
  "content_length": 12345
}
```

> 💡 **ODT 디코딩**
>
> ODT 응답은 base64로 인코딩되어 있습니다. 파일로 저장하려면:
>
> ```bash
> curl -X POST http://localhost:3000/convert/odt \
>     -F "file=@document.hwp" | \
>     jq -r '.content' | \
>     base64 -d > output.odt
> ```

### 포맷 지정 변환

쿼리 파라미터로 출력 포맷을 지정합니다.

**요청**

```bash
curl -X POST "http://localhost:3000/convert?output_format=html" \
    -F "file=@document.hwp"
```

**응답**

```json
{
  "content": "<html>...</html>",
  "source_name": "document.hwp",
  "output_format": "html",
  "pipeline": "hwp→xhtml",
  "is_binary": false,
  "content_length": 5678
}
```

## 클라이언트 예제

### Python (requests)

```python
import requests

def convert_hwp(file_path: str, output_format: str = "markdown") -> dict:
    """HWP 파일을 지정된 포맷으로 변환"""
    url = f"http://localhost:3000/convert/{output_format}"

    with open(file_path, "rb") as f:
        files = {"file": (file_path, f, "application/octet-stream")}
        response = requests.post(url, files=files)

    response.raise_for_status()
    return response.json()

# 사용
result = convert_hwp("document.hwp", "markdown")
print(result["content"])
```

### JavaScript (fetch)

```javascript
async function convertHwp(file, outputFormat = "markdown") {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(
    `http://localhost:3000/convert/${outputFormat}`,
    {
      method: "POST",
      body: formData,
    },
  );

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  return await response.json();
}

// 사용 (브라우저)
const fileInput = document.getElementById("fileInput");
fileInput.addEventListener("change", async (e) => {
  const file = e.target.files[0];
  const result = await convertHwp(file, "markdown");
  console.log(result.content);
});
```

### cURL 배치 변환

```bash
#!/bin/bash

# 디렉토리 내 모든 HWP 파일 변환
for file in *.hwp; do
    echo "변환 중: $file"
    curl -s -X POST http://localhost:3000/convert/markdown \
        -F "file=@$file" | \
        jq -r '.content' > "${file%.hwp}.md"
done
```

## 프로덕션 배포

### Gunicorn 설정

```bash
bentoml serve hwp_parser.adapters.api:HWPService \
    --workers 4 \
    --timeout 300
```

### Docker 실행

```bash
# 이미지 빌드 (bentoml build 필요)
bentoml build

# 컨테이너 실행
docker run -p 3000:3000 hwp-parser:latest
```

### 리버스 프록시 (Nginx)

```nginx
upstream hwp_parser {
    server localhost:3000;
}

server {
    listen 80;
    server_name api.example.com;

    client_max_body_size 50M;

    location / {
        proxy_pass http://hwp_parser;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 오류 처리

### HTTP 상태 코드

| 상태 코드 | 설명                                        |
| --------- | ------------------------------------------- |
| `200`     | 성공                                        |
| `400`     | 잘못된 요청 (파일 누락, 지원하지 않는 포맷) |
| `422`     | 처리 불가 (HWP 변환 실패)                   |
| `500`     | 서버 내부 오류                              |

### 오류 응답 형식

```json
{
  "error": "Unsupported format: xyz",
  "detail": "Supported formats: txt, html, markdown, odt"
}
```

---

## API 레퍼런스

### HWPService

```python
@bentoml.service(...)
class HWPService:
    """HWP 변환 REST API 서비스"""
```

#### 엔드포인트 목록

| 엔드포인트          | 메서드 | 설명                  |
| ------------------- | ------ | --------------------- |
| `/health`           | POST   | 서비스 상태 확인      |
| `/formats`          | POST   | 지원 포맷 목록        |
| `/convert`          | POST   | 파일 변환 (포맷 지정) |
| `/convert/text`     | POST   | 텍스트 변환           |
| `/convert/html`     | POST   | HTML 변환             |
| `/convert/markdown` | POST   | Markdown 변환         |
| `/convert/odt`      | POST   | ODT 변환              |

#### ConversionResponse

API 응답 스키마:

| 필드             | 타입      | 설명                         |
| ---------------- | --------- | ---------------------------- |
| `content`        | `string`  | 변환된 콘텐츠 (ODT는 base64) |
| `source_name`    | `string`  | 원본 파일 이름               |
| `output_format`  | `string`  | 출력 포맷                    |
| `pipeline`       | `string`  | 변환 파이프라인              |
| `is_binary`      | `boolean` | 바이너리 여부                |
| `content_length` | `integer` | 콘텐츠 길이                  |
