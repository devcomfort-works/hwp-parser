# Copilot Instructions (hwp-parser)

## 프로젝트 큰 그림

- Core 변환 로직은 [src/hwp_parser/core/converter.py](src/hwp_parser/core/converter.py)에서 `HWPConverter`가 담당하며, pyhwp CLI(`hwp5html`, `hwp5odt`)를 호출해 HWP → HTML/텍스트/Markdown/ODT로 변환합니다.
- REST API는 BentoML 서비스 [src/hwp_parser/adapters/api/service.py](src/hwp_parser/adapters/api/service.py)로 노출되며 `HWPConverter`를 사용해 `/convert/*` 엔드포인트를 제공합니다.
- LlamaIndex 통합은 [src/hwp_parser/adapters/llama_index/reader.py](src/hwp_parser/adapters/llama_index/reader.py)에서 `HWPReader`가 `HWPConverter` 결과를 Document로 래핑합니다.

## 핵심 워크플로우

- 의존성 설치: `rye sync`
- 테스트: `rye run test` (벤치마크 제외)
- API 서버: `rye run serve` 또는 `bentoml serve hwp_parser.adapters.api:HWPService`

## 프로젝트 고유 패턴/규칙

- 변환 결과는 `ConversionResult` 데이터 클래스(`content`, `pipeline`, `converted_at` 등)로 반환하며 `to_dict()`를 통해 응답/출력에 사용됩니다.
- `HWPConverter(verbose=True)`일 때 loguru 로거를 내부에서 설정하고 변환 시작/완료 로그에 입력/출력 용량 및 소요 시간을 기록합니다.
- 변환은 임시 디렉터리(`tempfile.mkdtemp`)를 사용하고 `finally`에서 항상 정리합니다.
- `to_markdown`은 `html-to-markdown`을 사용하고, `to_text`는 `html2text`로 HTML → 텍스트 변환 후 이스케이프 제거를 수행합니다.

## 설정/환경

- REST API 설정은 [src/hwp_parser/adapters/api/config.py](src/hwp_parser/adapters/api/config.py)에서 `.env` 또는 환경변수로 읽습니다.
  - 예: `HWP_SERVICE_PORT`, `HWP_SERVICE_TIMEOUT`, `HWP_SERVICE_CORS_ENABLED`

## 테스트/데모 참고

- 샘플 HWP 파일은 [tests/fixtures](tests/fixtures) 아래에 있습니다.
- REST API 데모 노트북은 [sandbox/demo_verbose_logging.ipynb](sandbox/demo_verbose_logging.ipynb)이며, API 호출로 변환을 확인합니다.

## 통합 지점

- 외부 의존성: pyhwp CLI 도구 설치 필요 (없으면 변환 실패).
- BentoML API는 `ConversionResponse` 모델로 바이너리(ODT) 콘텐츠를 base64 인코딩하여 반환합니다.
