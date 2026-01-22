# Core 사용법

`HWPConverter` 클래스를 사용하여 HWP 파일을 변환하는 방법을 상세히 설명합니다.

## HWPConverter 클래스

`HWPConverter`는 HWP 파일 변환의 핵심 클래스입니다.

```python
from hwp_parser import HWPConverter

converter = HWPConverter()
```

성능을 확인하고 싶다면 `verbose=True`로 로깅을 활성화할 수 있습니다.

```python
from hwp_parser import HWPConverter

converter = HWPConverter(verbose=True)
result = converter.to_markdown("document.hwp")
```

> 로깅은 `loguru` 기반으로 동작하며, 기본 포맷에는 시간/레벨/컬러가 포함됩니다.

## 변환 메서드

### to_text()

HWP 파일을 순수 텍스트로 변환합니다.

```python
result = converter.to_text("document.hwp")
print(result.content)
```

**파이프라인**: `hwp → xhtml → txt`

텍스트 변환은 `html2text` 라이브러리를 사용하여 HTML에서 텍스트를 추출합니다.

### to_html()

HWP 파일을 HTML 디렉터리 구조로 변환합니다. `ConversionResult`가 아닌 `HTMLDirResult`를 반환합니다.

```python
result = converter.to_html("document.hwp")

# HTMLDirResult 속성
print(result.xhtml_content)  # 메인 HTML 콘텐츠
print(result.css_content)    # CSS 스타일시트 (없으면 None)
print(result.bindata)        # 이미지 등 바이너리 데이터 {filename: bytes}
```

**파이프라인**: `hwp → xhtml (디렉터리)`

#### HTMLDirResult

| 속성            | 타입               | 설명                    |
| --------------- | ------------------ | ----------------------- |
| `xhtml_content` | `str`              | 메인 XHTML 콘텐츠       |
| `css_content`   | `str \| None`      | CSS 스타일시트          |
| `bindata`       | `dict[str, bytes]` | 이미지 등 바이너리 파일 |
| `source_path`   | `Path`             | 원본 파일 경로          |
| `converted_at`  | `datetime`         | 변환 시각               |

#### 파일로 저장

```python
from pathlib import Path

result = converter.to_html("document.hwp")
output_dir = Path("output/document")
output_dir.mkdir(parents=True, exist_ok=True)

# XHTML 저장
(output_dir / "index.xhtml").write_text(result.xhtml_content)

# CSS 저장 (있는 경우)
if result.css_content:
    (output_dir / "styles.css").write_text(result.css_content)

# 이미지 저장
if result.bindata:
    bindata_dir = output_dir / "bindata"
    bindata_dir.mkdir(exist_ok=True)
    for filename, data in result.bindata.items():
        (bindata_dir / filename).write_bytes(data)
```

#### ZIP으로 압축

```python
# ZIP 바이트로 변환
zip_bytes = result.to_zip_bytes()

# 파일로 저장
Path("document.zip").write_bytes(zip_bytes)
```

#### 미리보기 HTML 생성

CSS와 이미지를 인라인으로 포함한 단일 HTML을 생성합니다:

```python
# CSS는 <style> 태그로, 이미지는 base64 data URI로 인라인
preview_html = result.get_preview_html()

# 브라우저에서 바로 열 수 있는 HTML
Path("preview.html").write_text(preview_html)
```

> ℹ️ **pyhwp 변환**
>
> HTML 변환은 pyhwp의 `hwp5html` 명령을 내부적으로 사용합니다.

### to_markdown()

HWP 파일을 Markdown으로 변환합니다. **가장 권장되는 변환 방식**입니다.

```python
from pathlib import Path

result = converter.to_markdown("document.hwp")

# 파일로 저장
Path("output.md").write_text(result.content)
```

**파이프라인**: `hwp → xhtml → markdown`

Markdown 변환은 `html-to-markdown` 라이브러리를 사용합니다.

### to_odt()

HWP 파일을 ODT(Open Document Text) 형식으로 변환합니다.

```python
from pathlib import Path

result = converter.to_odt("document.hwp")

# 바이너리 파일로 저장
Path("output.odt").write_bytes(result.content)
```

**파이프라인**: `hwp → odt`

> ⚠️ **ODT 변환 제한**
>
> 일부 복잡한 서식의 HWP 파일은 ODT 변환 시 RelaxNG 검증 오류가 발생할 수 있습니다.
> 이 경우 HTML 또는 Markdown 변환을 권장합니다.

### convert()

포맷을 문자열로 지정하여 변환합니다.

```python
# 동적으로 포맷 지정
output_format = "markdown"
result = converter.convert("document.hwp", output_format=output_format)
```

지원되는 포맷:

- `txt` 또는 `text`
- `html`
- `markdown` 또는 `md`
- `odt`

## ConversionResult

모든 변환 메서드는 `ConversionResult` 객체를 반환합니다.

### 속성

| 속성            | 타입           | 설명                 |
| --------------- | -------------- | -------------------- |
| `content`       | `str \| bytes` | 변환된 콘텐츠        |
| `source_path`   | `Path`         | 원본 파일 경로       |
| `source_name`   | `str`          | 원본 파일 이름       |
| `output_format` | `str`          | 출력 포맷            |
| `pipeline`      | `str`          | 변환 파이프라인 설명 |
| `converted_at`  | `datetime`     | 변환 시각            |
| `is_binary`     | `bool`         | 바이너리 여부        |

### 메서드

```python
# 딕셔너리로 변환
data = result.to_dict()
```

## 예외 처리

```python
from pathlib import Path
from hwp_parser import HWPConverter

converter = HWPConverter()

try:
    result = converter.to_markdown("document.hwp")
except FileNotFoundError:
    print("파일을 찾을 수 없습니다.")
except ValueError as e:
    print(f"변환 오류: {e}")
except Exception as e:
    print(f"예상치 못한 오류: {e}")
```

### 일반적인 오류

| 오류                            | 원인                 | 해결 방법          |
| ------------------------------- | -------------------- | ------------------ |
| `FileNotFoundError`             | 파일이 존재하지 않음 | 파일 경로 확인     |
| `ValueError`                    | 디렉토리 경로 입력   | 파일 경로만 입력   |
| `subprocess.CalledProcessError` | pyhwp 명령 실패      | HWP 파일 손상 확인 |

## 안전 기능

### 디렉토리 경로 보호

디렉토리 경로가 입력되면 `ValueError`가 발생합니다.

```python
# 잘못된 사용 - ValueError 발생
converter.to_markdown("/path/to/directory/")

# 올바른 사용
converter.to_markdown("/path/to/file.hwp")
```

> 🚨 **안전 장치**
>
> 이 보호 기능은 과거 실수로 프로젝트 전체가 삭제되는 사고를 방지하기 위한 안전장치입니다.

## 성능 고려사항

### 대용량 파일

큰 HWP 파일을 변환할 때는 충분한 메모리를 확보하세요.

### 배치 처리

여러 파일을 처리할 때는 `HWPConverter` 인스턴스를 재사용합니다:

```python
converter = HWPConverter()  # 한 번만 생성

for hwp_file in hwp_files:
    result = converter.to_markdown(hwp_file)  # 재사용
```

### 병렬 처리 (Worker 모드)

CPU 바운드 작업이므로 `multiprocessing`을 사용한 병렬 처리가 효과적입니다.

#### num_workers 옵션 (권장)

`HWPConverter`는 내장 Worker 모드를 지원합니다:

```python
from hwp_parser import HWPConverter

# 4개의 워커 프로세스로 병렬 처리
converter = HWPConverter(num_workers=4)

# 이후 변환 호출은 워커 풀에서 처리됨
for hwp_file in hwp_files:
    result = converter.to_markdown(hwp_file)
```

Worker 모드는 프로세스 풀을 미리 생성하여 재사용하므로,
여러 파일을 변환할 때 프로세스 생성 오버헤드를 줄일 수 있습니다.

> ⚠️ **Worker 모드 제한**
>
> Worker 모드에서는 `to_odt()` 변환이 지원되지 않습니다.
> ODT 변환은 기본 모드에서만 사용 가능합니다.

#### 직접 multiprocessing 사용

```python
from pathlib import Path
from multiprocessing import Pool
from hwp_parser import HWPConverter

def convert_file(hwp_path):
    converter = HWPConverter()
    return converter.to_markdown(hwp_path)

hwp_files = list(Path("documents").glob("*.hwp"))
with Pool(4) as pool:
    results = pool.map(convert_file, hwp_files)
```
