# Repository Guidelines

This guide sets clear, lightweight conventions for the GelBlasterUK repository. It is suitable for an initializing codebase and should be refined as the stack solidifies.

## Project Structure & Module Organization
- Source: place application code in `./src/` (e.g., `src/app/`, `src/components/`, `src/lib/`).
- Tests: keep tests near code (`src/**/__tests__/`) or in `./tests/` (choose one and stick to it).
- Assets: static files in `./public/`; images/fonts in `./assets/`.
- Config: root-level config files (e.g., `.editorconfig`, `.prettierrc`, `pyproject.toml`, `.eslint*`).

## Build, Test, and Development Commands
- Node (if applicable): `npm ci`; `npm run dev` (local server); `npm test`; `npm run build` (production bundle).
- Python (if applicable): `python -m venv .venv && source .venv/bin/activate`; `pip install -r requirements.txt`; `pytest -q`.
- Lint/format: `npm run lint && npm run format` or `ruff check && black .` depending on stack.

## Coding Style & Naming Conventions
- Indentation: 2 spaces for JS/TS; 4 spaces for Python.
- Formatting/Linting: Prettier + ESLint (JS/TS) or Black + Ruff (Python). Add configs to repo root.
- Naming: kebab-case for files and folders; PascalCase for React components/classes; snake_case for Python modules/functions; environment variables in UPPER_SNAKE_CASE.

## Testing Guidelines
- Frameworks: Jest + Testing Library (JS/TS) or Pytest (Python).
- Coverage: target ≥ 80% lines for changed code; include edge cases and error paths.
- Naming: `*.test.ts[x]` or `test_*.py`. Example: `src/lib/__tests__/date.test.ts` or `tests/test_date.py`.

## Commit & Pull Request Guidelines
- Commits: follow Conventional Commits. Examples: `feat: add cart badge`, `fix(api): handle 404 on product lookup`, `chore: update deps`.
- PRs: concise description, linked issue (`Closes #123`), screenshots for UI changes, steps to reproduce/verify, and notes on breaking changes/migrations.
- Keep PRs focused and small; include tests and updated docs when behavior changes.

## Security & Configuration Tips
- Never commit secrets; use `.env` and provide `.env.example`.
- Add `.gitignore` early for common artifacts (e.g., `node_modules/`, `.venv/`, `dist/`).
- Prefer least-privilege API keys and rotate when needed.

