# 설치

HWP Parser를 설치하는 다양한 방법을 안내합니다.

> 📦 **PyPI 배포 예정**: 현재 PyPI에 배포되지 않았습니다. 추후 `hwp-parser`라는 이름으로 배포될 예정입니다.

## pip으로 설치

### 기본 설치

가장 기본적인 설치 방법입니다. 핵심 변환 기능만 포함됩니다.

```bash
pip install git+https://github.com/devcomfort-works/hwp-parser.git
```

### 선택적 기능 포함 설치

필요한 기능에 따라 추가 의존성과 함께 설치할 수 있습니다.

**LlamaIndex 어댑터**

RAG 파이프라인에서 HWP 문서를 활용하려면:

```bash
pip install "hwp-parser[llama-index] @ git+https://github.com/devcomfort-works/hwp-parser.git"
```

**REST API 서버**

BentoML 기반 REST API 서버를 사용하려면:

```bash
pip install "hwp-parser[bentoml] @ git+https://github.com/devcomfort-works/hwp-parser.git"
```

**모든 기능**

모든 선택적 기능을 포함하여 설치하려면:

```bash
pip install "hwp-parser[all] @ git+https://github.com/devcomfort-works/hwp-parser.git"
```

## rye로 설치

[rye](https://rye-up.com/)를 사용하는 경우:

```bash
# 기본 설치
rye add hwp-parser --git https://github.com/devcomfort-works/hwp-parser.git

# LlamaIndex 어댑터 포함
rye add "hwp-parser[llama-index]" --git https://github.com/devcomfort-works/hwp-parser.git

# REST API 서버 포함
rye add "hwp-parser[bentoml]" --git https://github.com/devcomfort-works/hwp-parser.git

# 모든 기능 포함
rye add "hwp-parser[all]" --git https://github.com/devcomfort-works/hwp-parser.git
```

## uv로 설치

[uv](https://docs.astral.sh/uv/)를 사용하는 경우:

```bash
# 기본 설치
uv add git+https://github.com/devcomfort-works/hwp-parser.git

# LlamaIndex 어댑터 포함
uv add git+https://github.com/devcomfort-works/hwp-parser.git --extra llama-index

# REST API 서버 포함
uv add git+https://github.com/devcomfort-works/hwp-parser.git --extra bentoml

# 모든 기능 포함
uv add git+https://github.com/devcomfort-works/hwp-parser.git --extra all
```

## 개발 환경 설치

소스 코드에서 개발 환경을 설정하려면:

```bash
# 저장소 클론
git clone https://github.com/devcomfort-works/hwp-parser.git
cd hwp-parser

# rye 사용 시 (권장)
rye sync

# pip 사용 시
pip install -e ".[dev]"
```

## 설치 확인

설치가 완료되었는지 확인합니다:

```python
from hwp_parser.core import HWPConverter

converter = HWPConverter()
print("HWP Parser 설치 완료!")
```

## 문제 해결

### pyhwp 설치 오류

pyhwp 설치 시 오류가 발생하면 시스템에 필요한 의존성이 없을 수 있습니다.

**Ubuntu/Debian**

```bash
sudo apt-get update
sudo apt-get install python3-dev libxml2-dev libxslt1-dev
```

**macOS**

```bash
brew install libxml2 libxslt
```

**Windows**

Windows에서는 Visual C++ Build Tools가 필요할 수 있습니다.
[Visual Studio Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)를 설치하세요.

> 💡 **가상 환경 사용 권장**
>
> 시스템 Python과의 충돌을 방지하기 위해 가상 환경을 사용하는 것을 권장합니다.
>
> ```bash
> python -m venv .venv
> source .venv/bin/activate  # Linux/macOS
> # 또는
> .venv\Scripts\activate     # Windows
> ```
