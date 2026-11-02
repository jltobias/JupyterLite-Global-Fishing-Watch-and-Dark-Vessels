"""Validate the assembled artifact and local book links without external requests."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote,urlsplit
import json
import nbformat

ROOT=Path(__file__).resolve().parents[1]
SITE=ROOT/"_site"


class Links(HTMLParser):
    def __init__(self):super().__init__();self.links=[]
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        for key in ("href","src"):
            if key in attrs:self.links.append(attrs[key])
        if "srcdoc" in attrs:
            nested=Links();nested.feed(attrs["srcdoc"]);self.links.extend(nested.links)


def main():
    required=["index.html","sources.html","01_observed_ocean.html","lab/index.html","lab/lab/index.html",
              "lab/service-worker.js","lab/api/contents/all.json","lab/plotly.min.js","_static/plotly.min.js",
              "_static/observed-globe.html","_static/ocean-scene.html"]
    errors=[]
    for path in required:
        if not (SITE/path).is_file():errors.append(f"Missing site entry: {path}")
    root_lite=(SITE/"lab/index.html").read_text(encoding="utf-8")
    if 'id="jupyter-config-data"' not in root_lite:errors.append("Lite root must retain parent config element")
    pages=[p for p in SITE.rglob("*.html") if "lab" not in p.relative_to(SITE).parts and not p.name.endswith("webpack-macros.html")]
    for path in pages:
        parser=Links();parser.feed(path.read_text(encoding="utf-8"))
        for link in parser.links:
            parts=urlsplit(link)
            if parts.scheme or parts.netloc or not parts.path:continue
            if parts.path.startswith("/"):continue  # external-domain absolute links, if any
            target=(path.parent/unquote(parts.path)).resolve()
            if not target.exists():errors.append(f"{path.relative_to(SITE)} -> missing {parts.path}")
    count=0
    for path in (ROOT/"content").glob("*.ipynb"):
        nb=nbformat.read(path,as_version=4);nbformat.validate(nb);count+=1
        codes=[c for c in nb.cells if c.cell_type=="code"]
        if not codes or any(c.execution_count is None for c in codes):errors.append(f"Unexecuted notebook: {path.name}")
        for cell in codes:
            if any(o.output_type=="error" for o in cell.outputs):errors.append(f"Notebook error: {path.name}")
    if count!=9:errors.append(f"Expected 9 notebooks; found {count}")
    if errors:raise SystemExit("\n".join(errors))
    print(f"Validated {len(pages)} HTML pages, local links, required Lite assets, and {count} executed notebooks")


if __name__=="__main__":main()
