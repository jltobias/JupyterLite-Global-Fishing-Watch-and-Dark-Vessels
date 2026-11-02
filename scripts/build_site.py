"""Build one Pages artifact: book at root, JupyterLite under /lab/."""
from pathlib import Path
import argparse
import json
import shutil
import subprocess
import sys
import sysconfig
import nbformat
import re

ROOT=Path(__file__).resolve().parents[1]


def run(command):
    subprocess.run(command,cwd=ROOT,check=True)


def clean_generated(relative):
    allowed={"_site","_lite","_build/lite-content","_build/book"}
    if relative not in allowed:raise ValueError("Not a known generated directory")
    target=(ROOT/relative).resolve()
    if not target.is_relative_to(ROOT.resolve()) or target==ROOT.resolve():
        raise ValueError("Build target escapes the repository")
    if target.exists():shutil.rmtree(target)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--execute",action="store_true",help="Re-execute all notebooks before building")
    args=parser.parse_args()
    if args.execute:run([sys.executable,"scripts/execute_notebooks.py"])
    run([sys.executable,"scripts/create_visuals.py"])
    for relative in ["_site","_lite","_build/lite-content","_build/book"]:clean_generated(relative)
    run([sys.executable,"-c","from jupyter_book.cli.main import main; main()","build","content","--path-output","_build/book","-W","--keep-going"])
    site=ROOT/"_site"
    site.mkdir(exist_ok=True)
    shutil.copytree(ROOT/"_build/book/_build/html",site,dirs_exist_ok=True)
    # Desktop notebook exports use the Plotly CDN; the published book instead
    # resolves iframe scripts to its vendored local library.
    for page in site.glob("*.html"):
        source=page.read_text(encoding="utf-8")
        source=re.sub(r"https://cdn\.plot\.ly/plotly-[\d.]+\.min\.js", "_static/plotly.min.js", source)
        page.write_text(source,encoding="utf-8")
    # Stage only learning files; no provider originals or book-build config in Lite.
    staged=ROOT/"_build/lite-content"
    staged.mkdir(parents=True,exist_ok=True)
    for path in (ROOT/"content").glob("*.ipynb"):
        notebook=nbformat.read(path,as_version=4)
        for cell in notebook.cells:
            if cell.cell_type=="code":cell.outputs=[];cell.execution_count=None
        nbformat.write(notebook,staged/path.name)
    shutil.copy2(ROOT/"content/oceanlab.py",staged/"oceanlab.py")
    shutil.copytree(ROOT/"content/data",staged/"data",dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns("*.feather","*.geojson.bak"))
    shutil.copy2(ROOT/"content/LAB_README.md",staged/"README.md")
    executable=Path(sysconfig.get_path("scripts"))/("jupyter-lite.exe" if sys.platform=="win32" else "jupyter-lite")
    run([str(executable),"build","--contents",str(staged),"--output-dir",str(ROOT/"_lite")])
    # The Lite builder emits lab/, api/, extensions, service worker etc. Keep that
    # whole application under the same /lab base, with the lab front end at its root.
    shutil.copytree(ROOT/"_lite",site/"lab",dirs_exist_ok=True)
    shutil.copy2(ROOT/"content/_static/plotly.min.js",site/"lab/plotly.min.js")
    # Keep the parent config element: child apps parse it. Redirect directly so
    # notebook query parameters also survive Lite's root landing page.
    (site/"lab/index.html").write_text('''<!doctype html><html lang="en"><meta charset="utf-8"><title>Ocean Watch Lab</title>
<script id="jupyter-config-data" type="application/json" data-jupyter-lite-root=".">{}</script>
<script>location.replace("lab/index.html"+location.search+location.hash);</script>
<a href="lab/index.html">Open Ocean Watch Lab</a></html>''',encoding="utf-8")
    (site/".nojekyll").touch()
    print(f"Pages artifact: {site}")


if __name__=="__main__":main()
