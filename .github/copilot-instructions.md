# Copilot Instructions (hwp-parser)

## ⚠️ 절대 규칙 (CRITICAL)

### Rye는 pip이 아니다

```bash
# ❌ 절대 하지 마라
pip install ...
python -m pip install ...
pipx install rye

# ✅ 반드시 이렇게 해라
rye sync                      # 프로젝트 의존성 설치
rye add <package>             # 프로젝트에 패키지 추가
rye tools install <package>   # 글로벌 도구 설치 (coverage-badge 등)
```

- **Rye는 내부적으로 uv를 사용한다. pip 명령어는 존재하지 않는다.**
- GitHub Actions에서 Rye 설치: `curl -sSf https://rye.astral.sh/get | RYE_INSTALL_OPTION="--yes" bash`

### 커밋 컨벤션

- **한국어로 작성해라.** 영어 커밋 메시지 금지.
- **Conventional Commits 형식 준수**: `<type>(<scope>): <설명>`

```bash
# ❌ 영어 커밋 금지
git commit -m "feat(converter): add PDF export support"

# ✅ 한국어로 작성
git commit -m "feat(converter): PDF 내보내기 기능 추가"
git commit -m "fix(api): 타임아웃 설정이 적용되지 않는 버그 수정"
git commit -m "refactor(config): 데드 코드 제거"
git commit -m "test(config): _load_dotenv 테스트를 임시 파일 기반으로 리팩터링"
git commit -m "docs: copilot-instructions 업데이트"
git commit -m "chore(ci): 커버리지 배지 자동 업데이트 설정"
```

### 행동 원칙

- **확인만 하지 말고 바로 실행해라.** 문서 확인 후 "맞네요"로 끝내지 마라.
- **물어보지 말고 해라.** 명확한 작업이면 허락 구하지 마라.
- **커밋은 논리적으로 분리해라.** 파일별이 아닌 변경 의도별로.

---

## 아키텍처

```
src/hwp_parser/
├── core/converter.py           # HWPConverter - 모든 변환의 진입점
├── adapters/
│   ├── api/
│   │   ├── service.py          # HWPService (BentoML REST API)
│   │   └── config.py           # 설정 관리 (_get_int, _get_float, _get_bool, _get_str)
│   └── llama_index/reader.py   # HWPReader (LlamaIndex 통합)
tests/
├── conftest.py                 # 공용 fixtures (converter, sample_hwp_file, all_hwp_files)
├── test_converter.py           # HWPConverter 단위 테스트
├── test_config.py              # config 헬퍼 함수 테스트
├── test_python_api.py          # Python API 통합 테스트
├── test_rest_api.py            # REST API 테스트
├── test_llama_index_api.py     # LlamaIndex 테스트
├── benchmarks.py               # 성능 벤치마크 (pytest-benchmark)
└── fixtures/                   # 테스트용 실제 HWP 파일들
```

### 변환 파이프라인

```
HWP → pyhwp CLI (hwp5html/hwp5odt) → HTML/ODT → html2text/html-to-markdown → txt/markdown
```

- `HWPConverter`가 subprocess로 pyhwp CLI 호출
- 결과는 `ConversionResult` 데이터클래스 (`content`, `pipeline`, `converted_at`)
- 임시 디렉터리 사용 → `finally`에서 반드시 정리

## 핵심 명령어

```bash
rye sync              # 의존성 설치 (항상 먼저 실행)
rye run test          # 테스트 (pytest -n auto, 병렬)
rye run test-cov      # 테스트 + 커버리지 (100% 유지 필수)
rye run benchmark     # 벤치마크 (pytest-benchmark)
rye run serve         # BentoML API 서버 (localhost:3000)
rye run docs          # 문서 로컬 서버 (zensical)
```

## 테스트 가이드

### 테스트 파일별 목적

| 파일 | 목적 | 언제 수정/추가? |
|------|------|----------------|
| `test_converter.py` | `HWPConverter` 단위 테스트 | 변환 로직, 포맷 지원, 에러 처리 변경 시 |
| `test_config.py` | 설정 헬퍼 함수 테스트 | `_get_*` 함수, `.env` 로딩 로직 변경 시 |
| `test_python_api.py` | Python API 통합 테스트 | 공개 API 인터페이스 변경 시 |
| `test_rest_api.py` | BentoML REST API 테스트 | 엔드포인트, 요청/응답 스키마 변경 시 |
| `test_llama_index_api.py` | `HWPReader` 테스트 | LlamaIndex 통합 로직 변경 시 |
| `benchmarks.py` | 성능 벤치마크 | 성능 최적화 작업 시 (CI에서 실행 안 함) |

### 테스트 작성 원칙

1. **실제 파일 사용**: `tests/fixtures/*.hwp` 파일로 테스트 (mocking 지양)
2. **tmp_path 활용**: 파일 I/O 테스트는 pytest의 `tmp_path` fixture 사용
3. **커버리지 100% 유지**: 새 코드 추가 시 반드시 테스트 작성

### 실제 파일 기반 테스트 (mocking 지양)

```python
# ✅ tmp_path fixture로 실제 파일 I/O 테스트
def test_load_dotenv_finds_env_file(tmp_path: Path, monkeypatch) -> None:
    # 임시 디렉터리 구조 생성
    project_root = tmp_path / "project"
    project_root.mkdir()
    (project_root / "pyproject.toml").touch()
    (project_root / ".env").write_text("MY_VAR=hello")
    
    # __file__ 위치 조작으로 테스트
    fake_module = project_root / "src" / "module.py"
    fake_module.parent.mkdir(parents=True)
    fake_module.touch()
    monkeypatch.setattr("hwp_parser.adapters.api.config.__file__", str(fake_module))
```

### pytest 경고 처리

`pyproject.toml`의 `filterwarnings`에서 외부 라이브러리 경고 억제:
```toml
filterwarnings = [
    "ignore::pytest_benchmark.logger.PytestBenchmarkWarning",  # xdist 충돌
    "ignore:The `__get_pydantic_core_schema__`:pydantic.warnings.PydanticDeprecatedSince211",  # BentoML
]
```

### 벤치마크 fixture 주의

```python
# ❌ ScopeMismatch: session fixture를 function scope에서 사용
@pytest.fixture(scope="session")
def my_fixture(): ...

# ✅ 벤치마크에서는 일반 함수로 직접 호출
def get_sample_files():
    return list(Path("tests/fixtures").glob("*.hwp"))
```

## 설정 (config.py)

### 환경변수

| 변수 | 타입 | 기본값 | 설명 |
|------|------|--------|------|
| `HWP_SERVICE_NAME` | str | "hwp-service" | 서비스 이름 |
| `HWP_SERVICE_PORT` | int | 3000 | HTTP 포트 |
| `HWP_SERVICE_TIMEOUT` | float | 300.0 | 요청 타임아웃(초) |
| `HWP_SERVICE_WORKERS` | int | 1 | 워커 수 |
| `HWP_SERVICE_CORS_ENABLED` | bool | false | CORS 활성화 |

### 타입 검증 헬퍼

`_get_int`, `_get_float`, `_get_bool`, `_get_str` 함수는 **런타임 타입 검증** 포함:
```python
# default 타입이 맞지 않으면 즉시 TypeError 발생 (fail-fast)
_get_int("KEY", "wrong")  # TypeError: default must be int, got str
```

## CI/CD

### 워크플로우

| 워크플로우 | 트리거 | 목적 |
|-----------|--------|------|
| `coverage.yml` | `src/`, `tests/`, `pyproject.toml` 변경 시 | 테스트 실행 + 커버리지 배지 업데이트 |
| `cloudflare-pages.yml` | `docs/`, `zensical.toml` 변경 시 | 문서 사이트 배포 (Cloudflare Pages) |

### CI 주의사항

- **Rye 설치**: 반드시 curl 사용 (`pipx install rye` ❌)
- **커버리지 배지**: `.github/badges/coverage.svg` (main push 시 자동 업데이트)
- **문서 빌드**: Zensical 사용 (`pip install zensical` → `zensical build`)

---

## Quick Reference

| 항목 | 내용 |
|------|------|
| 패키지 관리 | `rye` (pip 아님, uv 기반) |
| 테스트 실행 | `rye run test` (pytest -n auto) |
| 커버리지 목표 | **100%** (필수) |
| 변환 진입점 | `HWPConverter` |
| API 진입점 | `HWPService` |
| LlamaIndex 진입점 | `HWPReader` |
| fixture 위치 | `tests/fixtures/*.hwp` |
