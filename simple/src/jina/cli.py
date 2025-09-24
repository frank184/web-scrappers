import json
import os
from pathlib import Path
import typer
from rich import print
from dotenv import load_dotenv
from .client import JinaReaderClient
import re

app = typer.Typer(add_completion=False)
load_dotenv()
OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR"), "jina")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def _save_json(filename: Path, items):
    with filename.open("a", encoding="utf-8") as f:
        for it in items:
            f.write(it.model_dump_json() + "\n")

def _save_md(filename: Path, content):
    with filename.open("w", encoding="utf-8") as f:
        f.write(content)

def _sanitize_filename(url: str) -> str:
    """
    Turn a URL into a safe filename.
    Example: https://example.com/foo?bar=1
    → https___example_com_foo_bar_1.jsonl
    """
    safe = re.sub(r"https://", "", url)
    safe = re.sub(r"\.com", "", safe)
    safe = re.sub(r"[^a-zA-Z0-9]+", "_", safe)
    return safe.strip("_")

@app.command()
def read(url: str, out: str = typer.Option(None, help="Output JSONL file")):
    """Read a single URL via Jina Reader and save to JSONL."""
    client = JinaReaderClient()
    res = client.read_url(url)

    base = Path(out).stem if out else _sanitize_filename(url)
    json_path = OUTPUT_DIR / f"{base}.json"
    md_path = OUTPUT_DIR / f"{base}.md"

    _save_json(json_path, [res])
    _save_md(md_path, res.content)

    if res.error:
        print(f"[red]Error ({res.status})[/red]: {res.error[:200]}")
    else:
        print(f"[green]Saved[/green] {url} ➜ {base}")

@app.command()
def read_bulk(urls_file: Path, out: str = typer.Option("pages.jsonl")):
    """Read many URLs (one per line) and save to JSONL."""
    client = JinaReaderClient()
    urls = [u.strip() for u in urls_file.read_text().splitlines() if u.strip()]
    results = client.read_bulk(urls)
    _save_jsonl(OUTPUT_DIR / out, results)
    ok = sum(1 for r in results if r.status == 200)
    print(f"[green]{ok} ok[/green], [yellow]{len(results)-ok} failed[/yellow]. Output: {OUTPUT_DIR/out}")

@app.command()
def search(query: str, top_k: int = 5, out: str = typer.Option("serp.jsonl")):
    """Search the web and get cleaned content from top results into JSONL."""
    client = JinaReaderClient()
    res = client.search_and_read(query=query, top_k=top_k)
    _save_jsonl(OUTPUT_DIR / out, [res])
    if res.error:
        print(f"[red]Error ({res.status})[/red]: {res.error[:200]}")
    else:
        print(f"[green]Saved[/green] SERP for '{query}' ➜ {OUTPUT_DIR/out}")

if __name__ == "__main__":
    app()