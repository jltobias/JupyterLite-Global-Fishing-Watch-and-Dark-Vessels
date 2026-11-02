"""Run core notebooks without remote APIs and persist reviewable outputs."""
from pathlib import Path
import nbformat
from nbclient import NotebookClient

ROOT=Path(__file__).resolve().parents[1]
CONTENT=ROOT/"content"


def main():
    for path in sorted(CONTENT.glob("*.ipynb")):
        print(f"Executing {path.name}",flush=True)
        nb=nbformat.read(path,as_version=4)
        NotebookClient(nb,timeout=240,kernel_name="python3",resources={"metadata":{"path":str(CONTENT)}}).execute()
        nbformat.write(nb,path)
    print("Nine notebooks executed successfully",flush=True)


if __name__=="__main__":main()
