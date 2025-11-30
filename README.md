# 🕵️ OSINT-PRO: Multi-Layered Digital Footprint Analyzer

**Hashtags:** `#OSINT #Polyglot #Go #Python #NodeJS #Redis #Microservices #Cybersecurity #EthicalHacking #Asyncio`

OSINT‑PRO is a small, production-oriented proof-of-concept OSINT pipeline that demonstrates a polyglot microservice architecture for gathering, normalizing and caching digital footprint data. It is not an exhaustive OSINT suite — it is architected so you can add real connectors (WHOIS, Shodan, search APIs) behind the simple source interface.

---

## What is this and how it works

This repository shows a three-layer architecture:

- CLI Frontend (Node.js)
  - Simple command-line UI that requests an analysis and formats a human-friendly report.
- API Gateway (Go)
  - Lightweight reverse proxy with per-IP rate limiting and timeout management.
- Core Engine (Python / FastAPI)
  - Asynchronous orchestrator that loads multiple "sources" (modules under `sources/`) in parallel, normalizes outputs with Pydantic models, and caches results in Redis.
- Optional Redis server
  - In-memory cache for report payloads and a user-agent pool used by network utilities.

Execution flow:
1. CLI -> Go Gateway (port 8080)
2. Gateway -> Python FastAPI (port 8001)
3. Python checks cache (Redis), otherwise runs all sources concurrently
4. Results are normalized to `DigitalFootprintReport` and returned to CLI via the Gateway

Design goals:
- Clear separation of concerns to make adding new sources easy.
- Safe defaults and graceful degradation when Redis or other infra are not available.
- Fast, parallel collection to minimize latency.

---

## Git & repo guidance

Quick starter (first time, from project root):

```bash
git init
git add .
git commit -m "Initial import: OSINT-PRO"
git branch -M main
# add remote and push if available:
# git remote add origin git@github.com:youruser/OSINT-CLI.git
# git push -u origin main
```

Recommended .gitignore entries:

```
# Python
__pycache__/
*.pyc
backend/.venv/
.env

# Node
node_modules/

# IDE
.vscode/
.idea/
.DS_Store

# Logs
*.log
```

Branching workflow (suggested):
- main — stable
- develop — ongoing work
- feature/<name> — new features
- Use PRs, small commits, readable messages.

Tagging release example:
```bash
git tag -a v0.1.0 -m "Initial working prototype"
git push origin v0.1.0
```

---

## Quick setup & tutorial (commands)

Prerequisites:
- Linux (tested), Go 1.20+, Python 3.10+, Node.js 18+, Redis (optional but recommended)

Install Python deps:
```bash
# from project root
python -m pip install -r backend/requirements.txt
```

Start Redis (Debian/Ubuntu example):
```bash
sudo apt update
sudo apt install redis-server
sudo systemctl enable --now redis-server
# verify
redis-cli ping
# should respond: PONG
```

Environment tip:
Set PYTHONPATH so Python service imports local packages:
```bash
export PYTHONPATH="$(pwd)"
```

Run services (use separate terminals):

1) Start Python Core (FastAPI)
```bash
cd backend
# from project root with PYTHONPATH exported:
uvicorn backend.api:app --host 0.0.0.0 --port 8001 --reload
```

2) Start Go Gateway
```bash
cd services/gateway
go run main.go
# Gateway listens on :8080 and forwards to Python on :8001
```

3) Run CLI (Node.js)
```bash
# from project root
node cmd/analyze_cli.js <target>
# Examples:
node cmd/analyze_cli.js secure-company.com
node cmd/analyze_cli.js dev_ops_admin42
```

Expected flow:
- CLI calls http://localhost:8080/analyze?target=<target>
- Gateway enforces rate limit and proxies to Python
- Python returns JSON report; CLI formats it for human reading

Troubleshooting:
- If Go gateway returns 503: ensure Python FastAPI is running and reachable on port 8001.
- If CLI shows invalid JSON: check Python logs (uvicorn output) and the gateway logs.
- If caching not working: ensure Redis is running on localhost:6379 or the project will gracefully proceed without cache.

Advanced runs:
- Run Go binary build:
  ```bash
  cd services/gateway
  go build -o gateway
  ./gateway
  ```
- Run Python in a virtualenv:
  ```bash
  python -m venv .venv
  source .venv/bin/activate
  pip install -r backend/requirements.txt
  export PYTHONPATH="$(pwd)"
  uvicorn backend.api:app --host 0.0.0.0 --port 8001
  ```

---

## Extending the engine

- Add new source modules under `sources/`. Each module must export `async def collect_data(target: str)` and return:
  - a single Pydantic model (e.g., DomainInfo) or
  - a list of Pydantic models (SocialMediaHits, VulnerabilityHit, WebSearchHit)
- Use `backend/core/models.py` to extend or add new models.
- Implement real connectors (WHOIS, Shodan, GSA API, Google Programmable Search) behind that interface and keep them async.

---

## Security & ethics

This tool is for lawful and ethical OSINT research only. Be mindful of:
- Terms of service of third-party sites/APIs.
- Local laws and authorization before scanning or probing systems.
- Avoid automated scraping of services that prohibit it.

---

## Next recommended steps

- Add Docker Compose to orchestrate Redis, Python and gateway for reproducible local environments.
- Add unit tests for `backend/core/gatherer.py` normalization and caching.
- Add integration connectors for real OSINT APIs (with secure storage for keys).

---

If you want, I can:
- generate a Docker Compose file for Python + Go + Redis,
- add a .github/workflows CI step to run linters and unit tests,
- scaffold a basic integration test for the gatherer.