# Jina LLM-Ready Scraper

- **Reader API**: prepend `https://r.jina.ai/` to any URL to get clean, LLM-ready content.
- **Search+Read**: use `https://s.jina.ai/?q=...` to search and auto-fetch the top results.

> Reader is free and keyless, but you get higher RPM if you pass `Authorization: Bearer <JINA_API_KEY>`. See the rate limit table on Jina’s docs. :contentReference[oaicite:1]{index=1}

## Quickstart
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Optional: put a JINA_API_KEY in .env for higher limits
echo "JINA_API_KEY=sk-..." >> .env

# Read one URL
python -m src.jina.cli read "https://example.com/interesting-