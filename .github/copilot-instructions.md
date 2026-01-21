# Copilot Instructions (hwp-parser)

## ⚠️ 절대 규칙 (CRITICAL)

### Rye는 pip이 아니다
```bash
# ❌ 절대 하지 마라
pip install ...
python -m pip install ...
rye run python -m pip install ...
pipx install rye

# ✅ 반드시 이렇게 해라
rye sync                      # 프로젝트 의존성 설치
rye add <package>             # 프로젝트에 패키지 추가
rye tools install <package>   # 글로벌 도구 설치 (coverage-badge 등)
```

- **Rye는 내부적으로 uv를 사용한다. pip 명령어는 존재하지 않는다.**
- GitHub Actions에서 Rye 설치: `curl -sSf https://rye.astral.sh/get | RYE_INSTALL_OPTION="--yes" bash`

### 행동 원칙
- **확인만 하지 말고 바로 실행해라.** 문서 확인 후 "맞네요"로 끝내지 마라.
- **물어보지 말고 해라.** 명확한 작업이면 허락 구하지 마라.
- **커밋은 논리적으로 분리해라.** 파일별이 아닌 변경 의도별로.

---

## 프로젝트 구조

```
src/hwp_parser/
├── core/converter.py      # HWPConverter - 모든 변환의 진입점
├── adapters/
│   ├── api/service.py     # HWPService (BentoML REST API)
│   └── llama_index/reader.py  # HWPReader (LlamaIndex 통합)
tests/
├── test_python_api.py     # Python API 테스트
├── test_rest_api.py       # REST API 테스트  
├── test_llama_index_api.py # LlamaIndex 테스트
├── benchmarks.py          # 성능 벤치마크
└── fixtures/              # 테스트용 HWP 파일들
```

## 핵심 명령어

```bash
rye sync              # 의존성 설치 (항상 먼저 실행)
rye run test          # 테스트 (pytest, 병렬)
rye run test-cov      # 테스트 + 커버리지
rye run test-cov-html # 테스트 + 커버리지 + HTML 리포트
rye run benchmark     # 벤치마크 실행
rye run serve         # BentoML API 서버 실행
rye run docs          # 문서 로컬 서버
```

## 변환 파이프라인

1. `HWPConverter`가 pyhwp CLI(`hwp5html`, `hwp5odt`)를 subprocess로 호출
2. 결과는 `ConversionResult` 데이터클래스로 반환 (`content`, `pipeline`, `converted_at`)
3. 임시 디렉터리 사용 → `finally`에서 반드시 정리

```python
# 사용 예시
from hwp_parser.core import HWPConverter
result = HWPConverter().to_markdown("file.hwp")
print(result.content)
```

## 테스트 작성 규칙

- **fixture는 `tests/fixtures/`에 있는 실제 HWP 파일 사용**
- **pytest fixture 스코프 주의**: `session` 스코프 fixture와 `function` 스코프 테스트 혼용 시 `ScopeMismatch` 에러 발생
- **벤치마크에서 fixture 의존성 피하기**: `@pytest.fixture`가 아닌 일반 헬퍼 함수 사용

```python
# ❌ ScopeMismatch 유발
@pytest.fixture(scope="session")
def my_fixture(): ...

def test_something(my_fixture): ...  # function scope에서 session fixture 사용

# ✅ 벤치마크에서는 직접 호출
def get_sample_files():
    return list(Path("tests/fixtures").glob("*.hwp"))

def test_benchmark(benchmark):
    files = get_sample_files()  # fixture 대신 직접 호출
```

## GitHub Actions CI

- 워크플로우: `.github/workflows/coverage.yml`
- 커버리지 배지: `.github/badges/coverage.svg` (자동 업데이트)
- **Rye 설치 시 반드시 curl 사용** (pipx 아님)

## 설정/환경변수

REST API 설정 (`src/hwp_parser/adapters/api/config.py`):
- `HWP_SERVICE_PORT` - 서버 포트
- `HWP_SERVICE_TIMEOUT` - 요청 타임아웃
- `HWP_SERVICE_CORS_ENABLED` - CORS 활성화

## 외부 의존성

- **pyhwp**: HWP 파일 파서 (CLI 도구 `hwp5html`, `hwp5odt` 필요)
- **BentoML**: REST API 프레임워크
- **LlamaIndex**: RAG 파이프라인 통합

---

## 기억해야 할 것 (Memory Checklist)

| 항목 | 내용 |
|------|------|
| 패키지 관리 | `rye` (pip 아님, uv 기반) |
| 의존성 설치 | `rye sync` |
| 글로벌 도구 | `rye tools install <pkg>` |
| 테스트 실행 | `rye run test` |
| 변환 진입점 | `HWPConverter` |
| API 진입점 | `HWPService` |
| LlamaIndex 진입점 | `HWPReader` |
| CI Rye 설치 | curl (pipx 아님) |
