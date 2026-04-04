# Catapult 2026

GR86/BRZ Build Graph Planner MVP.

## Workspace Layout

- `apps/web` - Next.js single-page cockpit UI
- `apps/api` - FastAPI deterministic recommendation engine
- `data/seed` - curated trims, parts, packages, and VIN cache
- `docker-compose.yml` - local app + Postgres + Neo4j stack

## Local Development

### Web

```bash
npm install
npm run dev --workspace apps/web
```

### API

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r apps/api/requirements.txt
uvicorn app.main:app --app-dir apps/api --reload
```

### Full Stack

```bash
docker compose up --build
```

## Demo Flows

- `2022 GR86 Base` daily brake + wheel upgrade under `$2,500`
- `2023 BRZ Premium` winter build vs budget grip build
- conflict explanation for a big brake kit that needs 18-inch clearance

