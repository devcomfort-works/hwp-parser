"""
__init__.py 모듈 테스트 (Lazy Import 검증)
"""

import pytest

import hwp_parser


def test_lazy_imports():
    """Lazy import된 컴포넌트들이 정상적으로 로드되는지 확인"""
    # HWPReader (LlamaIndex Adapter)
    try:
        from hwp_parser import HWPReader

        assert HWPReader is not None
        assert HWPReader.__name__ == "HWPReader"
    except ImportError:
        pytest.skip("llama-index-core not installed")
    except AttributeError:
        pytest.fail("HWPReader attribute missing")


def test_core_imports():
    """Core 모듈이 정상적으로 로드되는지 확인"""
    from hwp_parser import ConversionResult, HWPConverter

    assert HWPConverter is not None
    assert ConversionResult is not None


def test_invalid_attribute():
    """존재하지 않는 속성 접근 시 AttributeError 발생 확인"""
    with pytest.raises(AttributeError) as excinfo:
        _ = hwp_parser.NonExistentAttribute

    assert "has no attribute 'NonExistentAttribute'" in str(excinfo.value)
