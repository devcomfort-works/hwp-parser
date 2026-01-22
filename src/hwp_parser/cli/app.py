"""
HWP Parser CLI
Click 기반의 커맨드라인 인터페이스
"""

import os
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import List

import click

from hwp_parser.core import HWPConverter
from hwp_parser.core.converter import HTMLDirResult


def convert_file(
    file_path: Path, output_format: str, output_dir: Path | None, verbose: bool
) -> str:
    """단일 파일 변환 (ProcessPoolExecutor에서 실행됨)"""
    try:
        converter = HWPConverter(verbose=verbose)

        # 변환 메서드 동적 호출
        if output_format == "markdown":
            result = converter.to_markdown(file_path)
        elif output_format == "html":
            html_result = converter.to_html(file_path)
            # HTML은 별도로 디렉터리 구조로 저장
            return _save_html_result(file_path, html_result, output_dir)
        elif output_format == "txt":
            result = converter.to_text(file_path)
        elif output_format == "odt":
            result = converter.to_odt(file_path)
        else:
            return (
                f"[Error] {file_path.name}: 지원하지 않는 포맷입니다 -> {output_format}"
            )

        # 결과 저장 (HTML 외 포맷)
        if output_dir:
            # 출력 디렉터리가 지정된 경우 해당 위치에 저장
            output_dir.mkdir(parents=True, exist_ok=True)
            # 원본 확장자만 변경
            ext = "md" if output_format == "markdown" else output_format
            output_path = output_dir / f"{file_path.stem}.{ext}"
        else:
            # 지정되지 않은 경우 원본 파일과 같은 위치
            ext = "md" if output_format == "markdown" else output_format
            output_path = file_path.with_suffix(f".{ext}")

        # 파일 쓰기
        mode = "wb" if result.is_binary else "w"
        encoding = None if result.is_binary else "utf-8"

        with open(output_path, mode, encoding=encoding) as f:
            f.write(result.content)

        return f"[Success] {file_path.name} -> {output_path.name}"

    except Exception as e:
        return f"[Fail] {file_path.name}: {str(e)}"


def _save_html_result(
    file_path: Path, html_result: HTMLDirResult, output_dir: Path | None
) -> str:
    """HTML 결과를 디렉터리 구조로 저장"""
    # 출력 디렉터리 결정
    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)
        html_dir = output_dir / file_path.stem
    else:
        html_dir = file_path.parent / file_path.stem

    html_dir.mkdir(parents=True, exist_ok=True)

    # index.xhtml 저장
    (html_dir / "index.xhtml").write_text(html_result.xhtml_content, encoding="utf-8")

    # styles.css 저장 (내용이 있는 경우만)
    if html_result.css_content:
        (html_dir / "styles.css").write_text(html_result.css_content, encoding="utf-8")

    # bindata 저장 (파일이 있는 경우만)
    if html_result.bindata:
        bindata_dir = html_dir / "bindata"
        bindata_dir.mkdir(exist_ok=True)
        for filename, content in html_result.bindata.items():
            (bindata_dir / filename).write_bytes(content)

    return f"[Success] {file_path.name} -> {html_dir.name}/"


@click.group()
def cli() -> None:
    """HWP Parser CLI 도구"""
    pass


@cli.command()
@click.argument("sources", nargs=-1, type=click.Path(exists=False))
@click.option(
    "--format",
    "-f",
    type=click.Choice(["markdown", "html", "txt", "odt"], case_sensitive=False),
    default="markdown",
    help="변환할 출력 포맷 (기본값: markdown)",
)
@click.option(
    "--output-dir",
    "-o",
    type=click.Path(file_okay=False, dir_okay=True, writable=True),
    help="결과물을 저장할 디렉터리 (기본값: 원본 파일과 동일한 위치)",
)
@click.option(
    "--workers",
    "-w",
    type=int,
    default=os.cpu_count(),
    help=f"병렬 처리를 위한 프로세스 수 (기본값: CPU 코어 수, {os.cpu_count()})",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="상세 로그 출력",
)
def convert(
    sources: tuple[str, ...],
    format: str,
    output_dir: str | None,
    workers: int,
    verbose: bool,
) -> None:
    """
    HWP 파일을 지정된 포맷으로 변환합니다.

    SOURCES: 변환할 HWP 파일 경로 또는 Glob 패턴 (예: *.hwp, data/**/*.hwp)
    """
    # 1. 대상 파일 수집 (Glob 패턴 처리)
    target_files: List[Path] = []
    for source in sources:
        # 쉘이 글로빙을 처리하지 않는 경우(예: 따옴표로 감쌈)를 위해 직접 glob 처리
        if "*" in source or "?" in source or "[" in source:
            # 재귀 패턴(**)이 포함된 경우 rglob과 유사하게 처리하기 위해 pathlib 사용
            # 하지만 단순함을 위해 현재 디렉토리 기준 glob이나 절대 경로 glob 사용
            # pathlib의 glob은 재귀(**)를 지원함

            # 입력이 경로를 포함하는지 확인
            p = Path(source)
            if p.is_absolute():
                base = p.root
                pattern = str(p.relative_to(base))
                found = list(Path(base).glob(pattern))
            else:
                found = list(Path(".").glob(source))

            if not found:
                click.echo(
                    f"Warning: 패턴 '{source}'에 매칭되는 파일이 없습니다.", err=True
                )
            target_files.extend(found)
        else:
            path = Path(source)
            if path.exists() and path.is_file():
                target_files.append(path)
            elif path.is_dir():
                # 디렉터리가 입력되면 그 안의 모든 .hwp 파일을 대상으로 함 (편의성)
                target_files.extend(path.glob("**/*.hwp"))
            else:
                click.echo(f"Warning: 파일 '{source}'를 찾을 수 없습니다.", err=True)

    # 중복 제거 및 정렬
    target_files = sorted(list(set(target_files)))

    if not target_files:
        click.echo("변환할 파일이 없습니다.")
        return

    click.echo(
        f"총 {len(target_files)}개의 파일을 변환합니다 (Format: {format}, Workers: {workers})..."
    )

    output_path_obj = Path(output_dir) if output_dir else None

    # 2. 병렬 처리
    if workers < 1:
        workers = 1

    with ProcessPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(convert_file, f, format, output_path_obj, verbose): f
            for f in target_files
        }

        # click.progressbar를 사용하여 진행률 표시
        with click.progressbar(
            length=len(target_files), label="Converting", show_eta=True
        ) as bar:
            for future in as_completed(futures):
                result = future.result()
                if (
                    verbose
                    or result.startswith("[Error]")
                    or result.startswith("[Fail]")
                ):
                    # 진행바를 깨뜨리지 않으려면 click.echo 대신 다른 방식이 필요할 수 있으나
                    # 간단하게 에러나 verbose일 때만 출력
                    if not getattr(bar, "is_hidden", False):
                        # 진행바 위에 로그 출력 (약간 깨질 수 있음)
                        click.echo(f"\r{result}")

                bar.update(1)

    click.echo("모든 작업이 완료되었습니다.")


@cli.command()
@click.option(
    "--host",
    default="0.0.0.0",
    help="서버 호스트 (기본값: 0.0.0.0)",
)
@click.option(
    "--port",
    type=int,
    default=7860,
    help="서버 포트 (기본값: 7860)",
)
def web(host: str, port: int) -> None:
    """Gradio 기반의 웹 데모를 실행합니다."""
    try:
        import tempfile
        from hwp_parser.web.app import ui
        
        click.echo(f"Starting Web UI on http://{host}:{port}")
        demo = ui()
        demo.launch(
            server_name=host,
            server_port=port,
            allowed_paths=[tempfile.gettempdir()],
        )
    except ImportError as e:
        click.echo(f"Web UI 실행 실패: {e}", err=True)
        click.echo("pip install hwp-parser 를 확인해주세요.", err=True)


def main() -> None:
    cli()


if __name__ == "__main__":  # pragma: no cover
    main()
