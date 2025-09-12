# Repository Guidelines

## Project Structure & Module Organization
- Core app: `main.py` (FastAPI entry) and `config.py` (ports, paths, Milvus, DB).
- API routes: `api/` (e.g., `mgfd_routes.py`, `specs_routes.py`, `history_routes.py`, `milvus_routes.py`).
- Shared code: `libs/`, `utils/`.
- UI assets: `templates/` (Jinja2), `static/` (CSS/JS).
- Data and storage: `data/`, `db/` (DuckDB/SQLite files), `logs/`.
- Tests and scenarios: `common_tests/` (pytest-style `test_*.py`), `test/` (utility scripts, datasets).
- Config and docs: `requirements.txt`, `README*.md`, `docs/`, `scripts/`.

## Build, Test, and Development Commands
- Setup env: `python -m venv .venv && source .venv/bin/activate`
- Install deps: `pip install -r requirements.txt`
- Run dev server: `uvicorn main:app --reload --host 0.0.0.0 --port 8001` (uses `config.py` defaults) or `python main.py`.
- Quick health check: `curl http://localhost:8001/health`.
- Run tests (pytest): `pip install pytest && pytest common_tests -q`.
- Alt tests (unittest): `python -m unittest discover -s common_tests -p 'test_*.py'`.

## Coding Style & Naming Conventions
- Python 3.10+, PEP 8, 4‑space indent; prefer type hints for new/edited functions.
- Modules: lowercase with underscores (e.g., `sales_routes.py`).
- Routes: group endpoints per domain in `api/*.py`; expose a `router`.
- Templates: Jinja2 under `templates/`; static assets in `static/`.
- Keep configuration in `config.py`; read secrets via `.env` (don’t commit secrets).

## Testing Guidelines
- Place unit/integration tests in `common_tests/` with `test_*.py` naming.
- Write deterministic tests; avoid network unless mocked.
- Target coverage pragmatically for changed code; include edge cases for API params and DB paths.

## Commit & Pull Request Guidelines
- Commits: imperative, concise, scoped. Examples:
  - `feat(api): add milvus search route`
  - `fix(config): correct APP_PORT default`
  - `refactor(utils): simplify chunking`
- PRs: include summary, motivation, screenshots of `/docs` or UI (if relevant), and steps to validate (commands, endpoints tested). Link issues where applicable.

## Security & Configuration Tips
- Configure via `.env` (e.g., `APP_PORT`, Milvus host/port, API keys). Never commit secrets.
- Ensure Milvus and DuckDB/SQLite files under `db/` exist before running data routes.
