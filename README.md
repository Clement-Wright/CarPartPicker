# CarPartPicker

CarPartPicker is a personal build-planning project focused on the GR86/BRZ platform. It combines a cockpit-style web app with a FastAPI backend so I can configure builds, tune engine and drivetrain settings, validate compatibility, and compare tradeoffs in one place.

## What It Does

- Builds and compares GR86/BRZ configurations
- Applies subsystem part changes and preset overlays
- Supports engine-builder and drivetrain tuning inputs
- Decodes VINs into supported trims
- Surfaces validation, dyno, vehicle-metric, scenario, and graph views
- Runs target-spec search from plain-language goals like budget, power, or usage

## Repo Layout

- `apps/web` - Next.js planner UI
- `apps/api` - FastAPI backend and build logic
- `data/seed` - seeded trims, parts, presets, and VIN cache
- `docker-compose.yml` - local stack for web, API, worker, Postgres, and Neo4j

## Local Development

### Web

```bash
npm install
npm run dev:web
```

The web app runs on `http://localhost:3000` and uses `http://localhost:8000/api` by default.

### API

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r apps/api/requirements.txt
uvicorn app.main:app --app-dir apps/api --reload
```

The API runs on `http://localhost:8000`.

### Full Stack

```bash
docker compose up --build
```

## Useful Commands

```bash
npm run build:web
npm run lint:web
npm run test:web
pytest apps/api/app/tests -q
```
