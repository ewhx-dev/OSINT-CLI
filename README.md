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

## Deep Search (law‑respecting, configurable)

This project includes a Deep Search source that performs broad discovery while respecting laws and provider terms:

- Purpose: gather additional indexed web results, code references and profile hits related to the target by using official APIs and safe heuristics.
- Providers supported (optional, enable with environment variables):
  - Bing Web Search API (BING_API_KEY) — broad web discovery (web pages, snippets)
  - GitHub Search API (GITHUB_TOKEN) — find user profiles and code mentions
- Fallback: if no API keys are configured, the Deep Search runs a conservative simulated mode that returns clearly labeled simulated results for local testing.
- Safeguards:
  - Uses official APIs when available; does not perform unauthorized scraping.
  - Conservative rate delays and small result limits to avoid abusive traffic.
  - Deduplicates results and returns standardized Pydantic models (WebSearchHit, SocialMediaHits) for integration with the gatherer.
- Configuration (examples):
```bash
export BING_API_KEY="your_bing_key"
export BING_ENDPOINT="https://api.bing.microsoft.com/v7.0/search"  # optional
export GITHUB_TOKEN="your_github_token"
export MAX_BING_RESULTS=6
export MAX_GITHUB_USERS=5
```
- Note: Always respect API usage policies; use scoped tokens and monitor quotas.

---

## Security & ethics

This tool is for lawful and ethical OSINT research only. Be mindful of:
- Terms of service of third-party sites/APIs.
- Local laws and authorization before scanning or probing systems.
- Avoid automated scraping of services that prohibit it.

---

## What the Dockerfiles do

Two Dockerfiles are provided to build container images for local development and reproducible environments:

- backend/Dockerfile
  - Base: python:3.11-slim.
  - Installs minimal build tools required by some Python packages.
  - Installs Python dependencies from backend/requirements.txt with pip.
  - Copies the repository into the image and sets PYTHONPATH to /app so local packages (backend, sources) resolve.
  - Exposes port 8001 and runs the FastAPI app with uvicorn: uvicorn backend.api:app --host 0.0.0.0 --port 8001.
  - Intended for development: the docker-compose mounts the repo so you can iterate on code without rebuilding every change.

- services/gateway/Dockerfile
  - Base: golang:1.20-bullseye.
  - Copies the gateway source (services/gateway) and builds a static gateway binary via go build.
  - Exposes port 8080 and runs the compiled gateway binary.
  - Keeps the gateway lightweight and reproducible inside a container.

- docker-compose.yml
  - Orchestrates three services: redis, backend (Python FastAPI), and gateway (Go).
  - Mounts the repo into containers for development convenience and wires Redis to the Python service for caching.
  - Environment variables (BING_API_KEY, GITHUB_TOKEN, REDIS_URL, etc.) can be injected at runtime or via an env file.

Use docker compose up --build from project root to start all services (Redis :6379, Python :8001, Gateway :8080).

---

## OSINT-CLI (CLI) file — purpose and functionality

The command-line interface is implemented in Node.js at cmd/analyze_cli.js (referred to as "osint-cli") and provides a user-friendly way to run analyses:

- Purpose:
  - Send an analysis request for a domain or username to the Go Gateway endpoint: http://localhost:8080/analyze?target=<target>.
  - Receive the normalized JSON report produced by the Python core and format it into a readable terminal report.

- Key behaviors:
  - Accepts a single positional argument: the target (domain or username).
  - Calls the Gateway and handles HTTP statuses:
    - Formats and prints a human-friendly report when response is OK.
    - Detects and reports rate limit responses (429) and other HTTP errors.
    - Attempts to parse JSON, and prints response body when parsing fails for debugging.
  - Adds timing information to show total analysis duration.
  - Uses colorized terminal output and icons to highlight findings (profiles, vulnerabilities, dorks).
  - Minimal dependencies: Node fetch (native in modern Node) and no heavy UI libraries.

- How to run:
  - Ensure Gateway and Python services are running.
  - From repo root: node cmd/analyze_cli.js <target>
  - Examples:
    - node cmd/analyze_cli.js example.com
    - node cmd/analyze_cli.js johndoe

- Integration:
  - CLI expects the Gateway at :8080 which enforces per-IP rate limiting and proxies to the Python API.
  - The CLI does not perform collection itself — it delegates to the API stack and focuses on presentation and UX.

---

## Future updates

This project will be actively updated with new data sources, improved normalization, more integrations (secure API connectors), and usability improvements. Check the repository for future commits and releases.
