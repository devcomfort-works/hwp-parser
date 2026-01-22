"""
hwp5.xmlmodel 모듈 타입 스텁

HWP 파일을 XML 모델로 파싱하고 조작하는 클래스들을 정의합니다.

참조:
    - https://github.com/mete0r/pyhwp/blob/main/src/hwp5/xmlmodel.py
    - https://github.com/mete0r/pyhwp/blob/main/src/hwp5/filestructure.py
    - https://github.com/mete0r/pyhwp/blob/main/src/hwp5/binmodel/__init__.py

타입 결정 근거:
    1. Hwp5File.__init__(stg):
       - filestructure.py:186-195: `if isinstance(stg, basestring):`로 문자열 경로 허용
       - filestructure.py:219-221: 테스트에서 `Hwp5File(self.hwp5file_path)` 사용 확인
       - 결론: str | PathLike | OleStorage (우리는 str만 사용)

    2. Hwp5File.wrapped:
       - Hwp5FileBase는 ItemConversionStorage를 상속
       - ItemConversionStorage는 Storage 프로토콜을 감싸는 래퍼
       - wrapped 속성은 내부 OleStorage 객체 반환
       - OleStorage는 olefile.OleFileIO를 감싸며, close() 메서드 제공

    3. Hwp5File은 contextlib.closing()과 함께 사용 가능:
       - hwp5html.py:149: `with closing(Hwp5File(hwp5path)) as hwp5file:`
       - hwp5odt.py:363: `with closing(Hwp5File(hwp5path)) as hwp5file:`
       - wrapped.close()를 통해 리소스 해제
"""

from typing import Any, Protocol

class Closeable(Protocol):
    """닫을 수 있는 객체 프로토콜.

    참조:
        - hwp5/storage/ole.py의 OleStorage 클래스
        - olefile.OleFileIO.close() 메서드
    """

    def close(self) -> None:
        """리소스를 해제합니다."""
        ...

class Hwp5File:
    """HWP v5 파일을 파싱하고 조작하는 메인 클래스.

    계층 구조:
        xmlmodel.Hwp5File
          └── binmodel.Hwp5File
                └── recordstream.Hwp5File
                      └── filestructure.Hwp5File
                            └── ItemConversionStorage

    참조:
        - https://github.com/mete0r/pyhwp/blob/main/src/hwp5/xmlmodel.py#L793-L816
        - https://github.com/mete0r/pyhwp/blob/main/src/hwp5/filestructure.py#L528-L598

    사용 예시:
        >>> hwp5file = Hwp5File("/path/to/document.hwp")
        >>> try:
        ...     # hwp5file 사용
        ... finally:
        ...     hwp5file.wrapped.close()

        >>> from contextlib import closing
        >>> with closing(Hwp5File("/path/to/document.hwp")) as hwp5file:
        ...     # hwp5file 사용
    """

    wrapped: Closeable
    """내부 스토리지 객체 (OleStorage).

    참조:
        - filestructure.py의 ItemConversionStorage 클래스
        - storage/ole.py의 OleStorage 클래스

    Note:
        Hwp5File 자체에는 close() 메서드가 없습니다.
        리소스를 해제하려면 wrapped.close()를 호출해야 합니다.
    """

    def __init__(self, stg: str | Any) -> None:
        """HWP 파일을 엽니다.

        Args:
            stg: HWP 파일 경로 (str) 또는 OLE 스토리지 객체.
                 문자열인 경우 내부적으로 OleStorage로 변환됩니다.

        Raises:
            InvalidHwp5FileError: 유효하지 않은 HWP v5 파일인 경우
            InvalidOleStorageError: OLE2 Compound Binary 파일이 아닌 경우

        참조:
            - filestructure.py:186-195: 생성자 구현
            - filestructure.py:219-221: 문자열 경로 테스트

        사용 예시:
            >>> hwp5file = Hwp5File("/path/to/document.hwp")
        """
        ...
