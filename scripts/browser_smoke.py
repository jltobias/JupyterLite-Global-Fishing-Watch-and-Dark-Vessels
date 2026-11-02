"""Optional headless browser QA of this repository's generated static site.

Install playwright and its Chromium browser separately. Does not control an
existing browser profile. Screenshots and diagnostics stay under _build/qa/.
"""
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
import argparse
import json
import threading
import sys
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
QA=ROOT/"_build/qa"
PREFIX="/JupyterLite-Global-Fishing-Watch-and-Dark-Vessels"


class Handler(SimpleHTTPRequestHandler):
    def translate_path(self,path):
        if path.startswith(PREFIX):path=path[len(PREFIX):] or "/"
        return super().translate_path(path)
    def log_message(self,*args):pass


def main():
    if hasattr(sys.stdout,"reconfigure"):sys.stdout.reconfigure(encoding="utf-8",errors="replace")
    parser=argparse.ArgumentParser()
    parser.add_argument("--run-notebook",action="store_true")
    parser.add_argument("--lab-only",action="store_true")
    parser.add_argument("--book-only",action="store_true")
    args=parser.parse_args()
    QA.mkdir(parents=True,exist_ok=True)
    server=ThreadingHTTPServer(("127.0.0.1",0),partial(Handler,directory=str(ROOT/"_site")))
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    base=f"http://127.0.0.1:{server.server_port}{PREFIX}"
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(headless=True,args=["--enable-unsafe-swiftshader"])
            context=browser.new_context(viewport={"width":1440,"height":1000})
            page=context.new_page()
            app_errors=[]
            def page_error(error):
                print("Browser error:",error.stack[:2000],flush=True)
                app_errors.append(str(error))
            page.on("pageerror",page_error)
            page.on("console",lambda msg:print("Console:",msg.type,msg.text[:600],flush=True) if msg.type in {"error","warning"} else None)
            page.on("requestfailed",lambda request:print("Request failed:",request.url.split("?")[0],request.failure,flush=True))
            if not args.lab_only:
                check_book(page,base)
            if args.book_only:
                browser.close()
                return
            print("Opening browser lab",flush=True)
            app_errors.clear()
            page.goto(base+"/lab/index.html?path=04_sar_detection.ipynb",wait_until="domcontentloaded")
            print("Lab navigated:",page.url,flush=True)
            try:
                page.get_by_role("menuitem",name="Run",exact=True).wait_for(timeout=60000)
            except Exception:
                print("LAB DIAGNOSTIC:",page.locator("body").inner_text()[:5000],flush=True)
                page.screenshot(path=str(QA/"lab-error.png"))
                raise
            page.screenshot(path=str(QA/"lab-open.png"))
            try:
                page.locator(".jp-Notebook").wait_for(timeout=120000)
                page.get_by_role("heading",name="04 · A radar return is not a vessel label",exact=True).wait_for(timeout=120000)
            except Exception:
                print("Notebook-open diagnostic:",page.locator("body").inner_text()[:6000],flush=True)
                page.screenshot(path=str(QA/"notebook-open-error.png"))
                raise
            print("Notebook source loaded; waiting for browser kernel execution",flush=True)
            if args.run_notebook:
                page.get_by_role("menuitem",name="Run",exact=True).click()
                page.get_by_role("menuitem",name="Run All Cells",exact=True).click()
                print("Started Run All Cells in Pyodide",flush=True)
                page.wait_for_function("[...document.querySelectorAll('.jp-OutputArea-output')].some(e => /Runtime: 3\\.14|Runtime: 3\\.13/.test(e.textContent||''))",timeout=240000)
                page.wait_for_function("![...document.querySelectorAll('.jp-InputPrompt')].some(e=>e.textContent.includes('*'))",timeout=240000)
                page.wait_for_function("[...document.querySelectorAll('.jp-OutputArea-output table')].some(e => e.textContent.includes('precision') && e.textContent.includes('recall'))",timeout=60000)
                warnings=page.locator('.jp-OutputArea-output[data-mime-type="application/vnd.jupyter.stderr"]').all_text_contents()
                if warnings:print("Kernel diagnostics:"," ".join(warnings)[:600],flush=True)
                assert not page.locator('.jp-OutputArea-output[data-mime-type="application/vnd.jupyter.error"]').count(),"Notebook execution error"
                assert not app_errors,app_errors
                page.screenshot(path=str(QA/"lab-run.png"))
                text=page.locator("body").inner_text()
                (QA/"lab-body.txt").write_text(text,encoding="utf-8")
                print("Browser execution completed: real radar crop and precision/recall table rendered",flush=True)
            browser.close()
    finally:server.shutdown()


def check_book(page,base):
    page.goto(base+"/",wait_until="networkidle")
    assert page.locator(".hero img").evaluate("im=>im.complete && im.naturalWidth>0")
    page.screenshot(path=str(QA/"book-desktop.png"))
    print("Desktop book loaded with cover",flush=True)
    page.set_viewport_size({"width":390,"height":844})
    page.reload(wait_until="networkidle")
    page.screenshot(path=str(QA/"book-mobile.png"))
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth+2"),"Mobile page overflows"
    page.set_viewport_size({"width":1440,"height":1000})
    for name in ["observed-map","observed-globe","ocean-scene","radar-surface","stock-scenarios"]:
        page.goto(base+f"/_static/{name}.html",wait_until="networkidle")
        page.wait_for_function("document.querySelector('.js-plotly-plot')?._fullLayout !== undefined",timeout=30000)
        page.screenshot(path=str(QA/(name+".png")))
        print("Rendered",name,flush=True)

if __name__=="__main__":main()
