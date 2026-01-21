# Copilot Instructions (hwp-parser)

## 프로젝트 큰 그림

- Core 변환 로직은 [src/hwp_parser/core/converter.py](src/hwp_parser/core/converter.py)의 `HWPConverter`가 담당하며, pyhwp CLI(`hwp5html`, `hwp5odt`)를 호출해 HWP → HTML/텍스트/Markdown/ODT로 변환합니다.
- REST API는 BentoML 서비스 [src/hwp_parser/adapters/api/service.py](src/hwp_parser/adapters/api/service.py)로 노출되며 `HWPConverter`를 사용해 `/convert/*` 엔드포인트를 제공합니다.
- LlamaIndex 통합은 [src/hwp_parser/adapters/llama_index/reader.py](src/hwp_parser/adapters/llama_index/reader.py)의 `HWPReader`가 `HWPConverter` 결과를 Document로 래핑합니다.

## 핵심 워크플로우

- 의존성 설치: `rye sync`
- 테스트(병렬): `rye run test`
- 커버리지: `rye run test-cov` 또는 `rye run test-cov-html` (HTML 생성)
- API 서버: `rye run serve` 또는 `bentoml serve hwp_parser.adapters.api:HWPService`
- 벤치마크: `rye run benchmark` (파일: [tests/benchmarks.py](tests/benchmarks.py))

## 프로젝트 고유 패턴/규칙

- 변환 결과는 `ConversionResult` 데이터 클래스(`content`, `pipeline`, `converted_at` 등)로 반환하며 `to_dict()`를 통해 응답/출력에 사용됩니다.
- `HWPConverter(verbose=True)`일 때 loguru 로거를 내부에서 설정하고 변환 시작/완료 로그에 입력/출력 용량 및 소요 시간을 기록합니다.
- 변환은 임시 디렉터리(`tempfile.mkdtemp`)를 사용하고 `finally`에서 항상 정리합니다.
- `to_markdown`은 `html-to-markdown`의 `ConversionOptions` + `convert` API를 사용합니다. `to_text`는 `html2text`로 HTML → 텍스트 변환 후 이스케이프 제거를 수행합니다.

## 설정/환경

- REST API 설정은 [src/hwp_parser/adapters/api/config.py](src/hwp_parser/adapters/api/config.py)에서 `.env` 또는 환경변수로 읽습니다.
  - 예: `HWP_SERVICE_PORT`, `HWP_SERVICE_TIMEOUT`, `HWP_SERVICE_CORS_ENABLED`

## 테스트 구성

- 샘플 HWP 파일은 [tests/fixtures](tests/fixtures) 아래에 있습니다.
- API/Converter/LlamaIndex 테스트는 각각 [tests/test_rest_api.py](tests/test_rest_api.py), [tests/test_python_api.py](tests/test_python_api.py), [tests/test_llama_index_api.py](tests/test_llama_index_api.py)로 분리되어 있습니다.

## 통합 지점

- 외부 의존성: pyhwp CLI 도구 설치 필요 (없으면 변환 실패).
- BentoML API는 `ConversionResponse` 모델로 바이너리(ODT) 콘텐츠를 base64 인코딩하여 반환합니다.

## 기억해야 할 핵심 규칙 (Memory Checklist)

- 변환 진입점: `HWPConverter` ([src/hwp_parser/core/converter.py](src/hwp_parser/core/converter.py)).
- API 진입점: `HWPService` ([src/hwp_parser/adapters/api/service.py](src/hwp_parser/adapters/api/service.py)).
- LlamaIndex 진입점: `HWPReader` ([src/hwp_parser/adapters/llama_index/reader.py](src/hwp_parser/adapters/llama_index/reader.py)).
- 테스트 파일 분리: REST API/[tests/test_rest_api.py](tests/test_rest_api.py), Python API/[tests/test_python_api.py](tests/test_python_api.py), LlamaIndex/[tests/test_llama_index_api.py](tests/test_llama_index_api.py), 벤치마크/[tests/benchmarks.py](tests/benchmarks.py).
- 환경설정 로드: `.env` 및 환경변수는 [src/hwp_parser/adapters/api/config.py](src/hwp_parser/adapters/api/config.py)에서 직접 파싱.
- 기본 워크플로우 명령: `rye sync`, `rye run test`, `rye run test-cov`, `rye run test-cov-html`, `rye run serve`, `rye run benchmark`.
- Markdown 변환은 `html-to-markdown`의 `ConversionOptions` + `convert` 사용.
- 변환은 임시 디렉터리 사용 후 `finally`에서 정리(누락 금지).
