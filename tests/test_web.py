"""Web UI 모듈 테스트."""

from unittest.mock import MagicMock, patch

import gradio as gr
import pytest

from hwp_parser.web import ui
from hwp_parser.web.app import convert


class TestWebUI:
    """웹 UI 관련 테스트."""

    def test_ui_creation(self) -> None:
        """UI 블록 생성 테스트."""
        demo = ui()
        assert isinstance(demo, gr.Blocks)
        # title 설정 확인
        assert demo.title == "HWP Parser Demo"

    @patch("hwp_parser.web.app.HWPConverter")
    @patch("hwp_parser.web.app.save_to_temp")
    @patch("tempfile.TemporaryDirectory")
    @patch("shutil.copy")
    def test_convert_function(
        self,
        mock_copy: MagicMock,
        mock_temp_dir: MagicMock,
        mock_save_to_temp: MagicMock,
        mock_converter_cls: MagicMock,
    ) -> None:
        """변환 함수 로직 테스트."""
        # Setup mocks
        mock_converter = mock_converter_cls.return_value
        mock_temp_dir.return_value.__enter__.return_value = "/tmp/fake_dir"
        
        # Test input
        mock_file_obj = MagicMock()
        mock_file_obj.name = "/path/to/test.hwp"
        formats = ["markdown", "html", "txt", "odt"]

        # 1. 파일이 없을 때
        result = convert(None, formats)
        assert len(result) == 8
        assert all(r is None for r in result)

        # 2. 정상 변환 시나리오
        # Mock result objects
        mock_md_res = MagicMock()
        mock_md_res.content = "Markdown Content"
        mock_converter.to_markdown.return_value = mock_md_res
        
        mock_html_res = MagicMock()
        mock_html_res.get_preview_html.return_value = "<html>Preview</html>"
        mock_html_res.to_zip_bytes.return_value = b"zip_content"
        mock_converter.to_html.return_value = mock_html_res
        
        mock_txt_res = MagicMock()
        mock_txt_res.content = "Text Content"
        mock_converter.to_text.return_value = mock_txt_res
        
        mock_odt_res = MagicMock()
        mock_odt_res.content = b"odt_content"
        mock_converter.to_odt.return_value = mock_odt_res

        # Call convert
        results = convert(mock_file_obj, formats)
        
        # assertions
        assert len(results) == 8
        
        # Markdown
        assert results[0] == "Markdown Content"  # md_view
        
        # HTML - IFrame
        assert "<iframe" in results[2]
        assert "data:text/html;charset=utf-8;base64," in results[2]

        # ODT Status
        assert "ODT 변환 성공" in results[7]

    @patch("hwp_parser.web.app.HWPConverter")
    @patch("tempfile.TemporaryDirectory")
    def test_convert_error_handling(
        self,
        mock_temp_dir: MagicMock,
        mock_converter_cls: MagicMock,
    ) -> None:
        """ODT 변환 에러 핸들링 테스트."""
        mock_converter = mock_converter_cls.return_value
        mock_temp_dir.return_value.__enter__.return_value = "/tmp/fake_dir"
        
        # ODT 변환에서 에러 발생 설정
        mock_converter.to_odt.side_effect = RuntimeError("RelaxNG Error")
        
        mock_file_obj = MagicMock()
        mock_file_obj.name = "test.hwp"
        
        results = convert(mock_file_obj, ["odt"])
        
        # ODT 에러 메시지가 결과에 포함되어야 함
        assert "ODT 변환 실패" in results[7]
        assert "RelaxNG Error" in results[7]
