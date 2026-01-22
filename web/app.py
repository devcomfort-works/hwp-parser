"""
HWP Parser Web Demo (Gradio)
"""

import shutil
import tempfile
import base64
from pathlib import Path
from typing import Any

import gradio as gr

from hwp_parser.core import HWPConverter


def save_to_temp(content, filename, is_binary=False):
    """일반 임시 디렉터리에 파일을 저장하여 Gradio가 접근 가능하게 함"""
    temp_dir = Path(tempfile.gettempdir())
    out_path = temp_dir / filename

    mode = "wb" if is_binary else "w"
    encoding = None if is_binary else "utf-8"

    with open(out_path, mode, encoding=encoding) as f:
        f.write(content)
    return str(out_path)


def convert(file_obj, formats):
    """
    선택된 포맷들로 변환을 수행하고 결과(내용+파일경로)를 반환합니다.

    Returns:
        순서: [md_view, md_file, html_preview, html_zip, txt_view, txt_file, odt_file, odt_status]
    """
    if file_obj is None:
        return [None] * 8

    # Gradio Input 처리
    if isinstance(file_obj, str):
        src_path = Path(file_obj)
    else:
        src_path = Path(file_obj.name)

    base_stem = src_path.stem

    # 작업용 임시 디렉터리 (변환 작업 중 파일 충돌 방지 및 안전한 실행)
    with tempfile.TemporaryDirectory() as temp_dir:
        working_path = Path(temp_dir)

        # 입력 파일 준비 (.hwp 확장자 보장)
        if src_path.suffix.lower() != ".hwp":
            input_hwp = working_path / "input.hwp"
            shutil.copy(src_path, input_hwp)
        else:
            input_hwp = src_path

        converter = HWPConverter()

        # 결과 저장소
        # [md_view, md_file, html_preview, html_zip, txt_view, txt_file, odt_file, odt_status]
        results: list[Any] = [None] * 8

        # 1. Markdown
        if "markdown" in formats:
            try:
                res = converter.to_markdown(input_hwp)
                results[0] = res.content
                results[1] = save_to_temp(res.content, f"{base_stem}.md")
            except Exception as e:
                results[0] = f"Error converting to Markdown: {e}"

        # 2. HTML (디렉터리 변환 사용)
        if "html" in formats:
            try:
                html_res = converter.to_html(input_hwp)

                # 미리보기용 HTML (CSS, 이미지 인라인) - IFrame 격리 렌더링
                preview_html = html_res.get_preview_html()

                # Data URI 생성 (파일 서빙 문제 해결)
                encoded_html = base64.b64encode(preview_html.encode("utf-8")).decode(
                    "utf-8"
                )
                data_uri = f"data:text/html;charset=utf-8;base64,{encoded_html}"

                # IFrame 태그 생성
                # 스크롤 기능 활성화 (height: 800px 유지)
                iframe_html = f'<iframe src="{data_uri}" style="width: 100%; height: 800px; border: 1px solid #ddd; background: white; overflow: auto;" scrolling="yes"></iframe>'

                results[2] = iframe_html  # IFrame 태그 전달

                # ZIP 다운로드 (전체 구조)
                zip_bytes = html_res.to_zip_bytes()
                results[3] = save_to_temp(
                    zip_bytes, f"{base_stem}_html.zip", is_binary=True
                )
            except Exception as e:
                # 에러 시 에러 메시지를 HTML로 표시
                error_html = f"<div style='color: red; padding: 20px;'><h2>⚠️ 변환 오류</h2><pre>{e}</pre></div>"
                results[2] = error_html

        # 3. Text
        if "txt" in formats:
            try:
                res = converter.to_text(input_hwp)
                results[4] = res.content
                results[5] = save_to_temp(res.content, f"{base_stem}.txt")
            except Exception as e:
                results[4] = f"Error converting to Text: {e}"

        # 4. ODT (바이너리)
        if "odt" in formats:
            try:
                res = converter.to_odt(input_hwp)
                results[6] = save_to_temp(
                    res.content, f"{base_stem}.odt", is_binary=True
                )
                results[7] = "✅ **ODT 변환 성공**"
            except Exception as e:
                # ODT 변환 실패 시 에러 메시지를 마크다운으로 표시
                error_msg = f"""## ❌ ODT 변환 실패

**에러 내용:**
```
{str(e)}
```

**참고:**
대부분의 변환 실패는 HWP 파일 내부 구조(XML)가 ODT 표준 스키마(RelaxNG)와 맞지 않아 발생합니다.
"""
                results[7] = error_msg

        return results


# HTML 미리보기를 위한 커스텀 CSS
CUSTOM_CSS = """
/* IFrame이 자체적으로 스타일을 격리하므로 별도 CSS 불필요 */
"""


def ui():
    with gr.Blocks(title="HWP Parser Demo", css=CUSTOM_CSS) as demo:
        gr.Markdown("## 📄 HWP Parser Web Demo")
        gr.Markdown("HWP 파일을 업로드하여 다양한 포맷으로 변환하고 다운로드하세요.")

        with gr.Row():
            # 왼쪽: 입력 컨트롤
            with gr.Column(scale=1):
                input_file = gr.File(label="HWP 파일 업로드", file_types=[".hwp"])

                check_formats = gr.CheckboxGroup(
                    choices=["markdown", "html", "txt", "odt"],
                    value=["markdown", "html", "txt", "odt"],  # 기본적으로 모두 선택
                    label="변환할 포맷 선택",
                )

                btn_submit = gr.Button("일괄 변환하기", variant="primary")

            # 오른쪽: 결과 탭
            with gr.Column(scale=2):
                with gr.Tabs():
                    with gr.Tab("Markdown"):
                        md_view = gr.Code(
                            label="미리보기", language="markdown", lines=20
                        )
                        md_file = gr.File(label="파일 다운로드 (.md)")

                    with gr.Tab("HTML"):
                        gr.Markdown(
                            "💡 HTML 변환은 여러 파일(xhtml, css, 이미지)을 생성합니다. "
                            "**ZIP 파일**로 전체 구조를 다운로드할 수 있습니다."
                        )
                        html_preview = gr.HTML(
                            label="미리보기 (IFrame)",
                            # elem_id="html-preview",  # IFrame 사용으로 CSS ID 불필요
                        )
                        html_zip = gr.File(label="ZIP 다운로드 (전체 구조)")

                    with gr.Tab("Text"):
                        txt_view = gr.Code(label="미리보기", language=None, lines=20)
                        txt_file = gr.File(label="파일 다운로드 (.txt)")

                    with gr.Tab("ODT"):
                        odt_status = gr.Markdown()  # 상태/에러 메시지 표시용
                        gr.Markdown(
                            "ODT 포맷은 바이너리 형식이므로 다운로드만 지원합니다."
                        )
                        odt_file = gr.File(label="파일 다운로드 (.odt)")

        # 이벤트 연결
        btn_submit.click(
            fn=convert,
            inputs=[input_file, check_formats],
            outputs=[
                md_view,
                md_file,
                html_preview,
                html_zip,
                txt_view,
                txt_file,
                odt_file,
                odt_status,
            ],
        )

    return demo


if __name__ == "__main__":
    import argparse

    DEFAULT_HOST = "0.0.0.0"
    DEFAULT_PORT = 7860

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help=f"Web UI Port (default: {DEFAULT_PORT})",
    )
    parser.add_argument(
        "--host",
        type=str,
        default=DEFAULT_HOST,
        help=f"Web UI Host (default: {DEFAULT_HOST})",
    )
    args = parser.parse_args()

    demo = ui()

    # 임시 디렉터리의 파일(미리보기 HTML 등)에 접근할 수 있도록 허용
    import tempfile

    demo.launch(
        server_name=args.host,
        server_port=args.port,
        allowed_paths=[tempfile.gettempdir()],
    )
