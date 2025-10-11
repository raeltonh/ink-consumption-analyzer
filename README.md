Presto MAX — ml/m² & ROI Analyzer

Interactive Streamlit app to analyze printing jobs from ZIP/XML files: channel previews, per‑channel consumption (ml/m²), A×B comparison, Sales quick quote and break‑even.

Run locally

- Prerequisites: Python 3.10+ and pip
- Install and run:

```
pip install -r requirements.txt
streamlit run app_en.py
```

Open http://localhost:8501.

Run with Docker

Build and run without a local Python:

```
docker build -t ink-analyzer .
docker run --rm -p 8501:8501 ink-analyzer
```

Deploy — Streamlit Community Cloud

- Push this repo to GitHub
- New app → select repo → entrypoint `app_en.py`
- Dependencies are read from `requirements.txt`

Project layout

- `app_en.py` — main Streamlit app (English UI)
- `assets/` — optional images used by the header and page icon
- `requirements.txt` — Python dependencies

Tips

- For stale UI styles: click Rerun and Clear cache in the Streamlit menu.
