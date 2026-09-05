# Clothing Scraper and API

A small, extensible Scrapy-based scraping project plus a FastAPI service for storing and serving scraped product data.

This repository contains:
- scrapers for multiple stores (Bershka, Pull&Bear, Canda, Nike, Celio).
- a FastAPI app exposing CRUD endpoints for products (clothing_scraper/api).
- a PostgreSQL-based storage layer.

Goals of this PR:
- Organize the code into a Python package to make imports and testing easier.
- Introduce a single, documented entrypoint for running the API and running spiders.
- Add consistent logging configuration and README documentation.

Table of contents
- Features
- Repo layout / architecture
- Quick start (Docker)
- Development (local)
- Running spiders
- Logging & configuration
- Notes & troubleshooting

Features
- Scrapy spiders for multiple e-commerce stores.
- FastAPI backend providing REST endpoints and OpenAPI docs.
- PostgreSQL persistence.
- Docker & docker-compose for local/dev deployment.

Repository architecture
- clothing_scraper/
  - api/                FastAPI application (routers, models, db)
  - scrapers/           package containing individual spiders (bershka.py, ...)
  - core/               shared utilities (settings, logging configuration, database helpers)
  - database/           DB access layer / migrations/scripts
  - main.py             package CLI/entrypoint (run API, run spider)
  - run_all_spiders.py  convenience script (now imports package entrypoints)
  - config.yaml         runtime configuration
  - requirements.txt
  - Dockerfile
  - docker-compose.yml

Why this structure?
- Each spider lives under scrapers/ and can be imported as clothing_scraper.scrapers.bershka, enabling reuse in tests and shared utilities (e.g., parsers, item pipelines).
- core/ contains logging setup, common settings, and helper functions so they are not duplicated.
- main.py acts as the single command entrypoint both for local dev (python -m clothing_scraper) and for Docker (CMD/ENTRYPOINT).

Quick start — Docker (recommended)
1. Build images:
   docker-compose -f clothing_scraper/docker-compose.yml build
2. Start services:
   docker-compose -f clothing_scraper/docker-compose.yml up -d
3. Initialize database (example):
   docker-compose exec app python -m clothing_scraper.main setup-db
4. API will be available at http://localhost:8000 and docs at http://localhost:8000/docs

Local development (without Docker)
1. Create virtualenv:
   python3 -m venv venv
   source venv/bin/activate
2. Install dependencies:
   pip install -r clothing_scraper/requirements.txt
3. Run API:
   python -m clothing_scraper.main api
   or: uvicorn clothing_scraper.api.main:app --reload --host 0.0.0.0 --port 8000

Running spiders
- To run a single spider locally:
  python -m clothing_scraper.main scrape --spider bershka
- To run all spiders sequentially:
  python clothing_scraper/run_all_spiders.py
(Internally these call the Scrapy API via the package; spiders are importable modules under clothing_scraper.scrapers.)

Configuration & secrets
- config.yaml holds runtime settings used by both the API and spiders.
- Sensitive values (DB password, 2captcha API key) should be provided via environment variables in production or docker-compose.override.yml for local testing.
- Example: set 2CAPTCHA_API_KEY in env before running the celio spider.

Logging
- A single logging configuration (core/logging.py) configures structured logs and file/console handlers.
- Spiders and API use logging.getLogger(__name__) and benefit from consistent formatting and level control.
- Recommended log location in Docker: /var/log/clothing_scraper/

Development notes & migration steps (for maintainers)
1. Move top-level scripts (e.g., scrape_clothes_bershka.py) into clothing_scraper/scrapers/bershka.py.
2. Add clothing_scraper/__init__.py and expose CLI in clothing_scraper/main.py using argparse or Typer.
3. Replace ad-hoc DB initialization logic with a single setup-db command in main.py.
4. Add core/logging.py and update modules to import logging from there.
5. Update Dockerfile to run Python package entrypoint (python -m clothing_scraper.main api).
6. Add minimal unit tests that import spiders and core utilities (optional for this PR).

Celio spider notes
- The celio spider uses undetected_chromedriver and 2captcha. Provide 2CAPTCHA_API_KEY via env var or config. See clothing_scraper/scrapers/celio.py for the environment variable name.

Contact / Contributing
- Open an issue for new store scrapers or major changes.
- PRs should be based on the `main` branch and include tests where possible.
