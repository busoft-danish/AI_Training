# KidShuttle — Safety Protocol & Route Knowledge Base
production-grade markdown synchronization pipeline for RAG preparation.

---

## Architecture Overview

```
Excel + PostgreSQL
      ↓
Source Connectors  (ExcelConnector, PostgresConnector)
      ↓
Change Detector    (HashSyncStrategy / WatermarkSyncStrategy)
      ↓
Markdown Renderer  (Jinja2 templates)
      ↓
Local Markdown Files  (output/drivers/, output/incidents/)
      ↓
MinIO Upload       (UploadService via boto3)
      ↓
Manifest SQLite    (ManifestRepository)
      ↓
Incremental Sync   (IncrementalSyncService)
```

The system reads from two sources, detects changes, renders markdown files, uploads them to MinIO, and tracks everything in a SQLite manifest database.

---

## Folder Structure

```
team_d_kidshuttle/
├── controllers/        # Thin orchestrators — no business logic
├── connectors/         # Source data adapters (Excel, PostgreSQL)
├── renderers/          # Jinja2 markdown renderers + factory
├── strategies/         # Sync strategies (hash-based, watermark-based)
├── services/           # Business logic (sync, upload, manifest, hash)
├── repositories/       # Data access layer for SQLite manifest
├── factories/          # Dependency injection / wiring
├── models/             # Pydantic + dataclass models
├── database/           # DB engine factories
├── templates/          # Jinja2 .j2 templates
├── output/             # Generated markdown files
├── logs/               # Log output
├── config/             # Settings via pydantic-settings
├── utils/              # Helpers, constants, exceptions
├── tests/              # Pytest tests + simulation scripts
├── .env                # Environment variables
├── main.py             # Entry point
├── pyproject.toml      # uv project config + dependencies
├── docker-compose.yml  # PostgreSQL + MinIO local services
└── uv.lock             # Locked dependency versions
```

---

## Setup Instructions

### 1. Install uv (if not already installed)

```bash
# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Create virtual environment and install all dependencies

```bash
uv sync --all-groups
```

This reads `pyproject.toml`, creates `.venv`, and installs all runtime + dev dependencies in one step.

### 3. Activate the virtual environment

```bash
# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

### 4. Configure environment

Update `.env` with your local values:

```bash
# Edit .env directly — it is already pre-populated with local defaults
```

### Common uv commands

```bash
# Add a new runtime dependency
uv add <package>

# Add a dev-only dependency
uv add --group dev <package>

# Remove a dependency
uv remove <package>

# Run a command inside the venv without activating it
uv run python main.py full
uv run pytest tests/ -v

# Show installed packages
uv pip list

# Upgrade all packages to latest allowed versions
uv lock --upgrade
uv sync
```

---

## Infrastructure Setup

### PostgreSQL
- Install PostgreSQL locally
- Create a database named `kidshuttle_`
- Update `.env` with your credentials

### MinIO
- Download `minio.exe` from https://dl.min.io/server/minio/release/windows-amd64/minio.exe
- Save to `C:\minio\minio.exe`
- Start MinIO in a separate terminal:
```bash
C:\minio\minio.exe server C:\minio\data --console-address ":9001"
```
- MinIO Console: http://localhost:9001 — login with `minioadmin / minioadmin`
- The bucket `kidshuttle` is created automatically on first sync run.

---

## Running Full Sync

```bash
uv run python main.py full
```

Fetches all records from Excel and PostgreSQL, renders markdown, uploads to MinIO, and creates manifest entries.

---

## Running Incremental Sync

```bash
uv run python main.py incremental
```

- For Excel (drivers): fetches all records, skips unchanged ones using hash comparison.
- For PostgreSQL (incidents): fetches only records updated after the last watermark.

---

## Simulating Changes

```bash
# Stage 1: Seed initial data
uv run python tests/simulate_changes.py seed

# Run full sync
uv run python main.py full

# Stage 2: Update 3 records
uv run python tests/simulate_changes.py update

# Run incremental sync — only changed records processed
uv run python main.py incremental

# Stage 3: Delete 2 records
uv run python tests/simulate_changes.py delete

# Run incremental sync — deleted records marked in manifest
uv run python main.py incremental
```

---

## Running Tests

```bash
uv run pytest tests/ -v
```

---

## Design Patterns Used

| Pattern | Where Used | Why |
|---|---|---|
| Repository | ManifestRepository | Isolates DB access from business logic |
| Strategy | HashSyncStrategy, WatermarkSyncStrategy | Swap sync algorithms without changing callers |
| Factory | ConnectorFactory, RendererFactory, ServiceFactory | Decouple object creation from usage |
| Dependency Injection | All services via constructors | Testable, swappable dependencies |
| ABC Interfaces | BaseSourceConnector, BaseRenderer, BaseSyncStrategy | Enforce contracts, enable polymorphism |

---

## SOLID Principles

**S — Single Responsibility**
Each class does one thing. `HashService` only hashes. `UploadService` only uploads. `ManifestRepository` only talks to SQLite.

**O — Open/Closed**
Add a new entity type by registering it in `RendererFactory` and `ConnectorFactory`. No existing code changes.

**L — Liskov Substitution**
`ExcelConnector` and `PostgresConnector` are fully interchangeable wherever `BaseSourceConnector` is expected.

**I — Interface Segregation**
`BaseSourceConnector` has only two methods. Connectors aren't forced to implement methods they don't need.

**D — Dependency Inversion**
`FullSyncService` depends on `BaseSourceConnector` and `BaseSyncStrategy` — not on Excel or Postgres directly.

---

## Sync Strategy Comparison

| Feature | Hash-Based | Watermark-Based |
|---|---|---|
| Best for | Excel, flat files | PostgreSQL, timestamped tables |
| Change detection | SHA-256 hash of record | `updated_at > last_watermark` |
| Deletion detection | Yes (set difference) | No (needs periodic full sync) |
| DB query load | Fetches all records | Fetches only changed records |
| Clock skew risk | None | Low (use UTC, add buffer) |

---
Proof - 

<img width="1918" height="987" alt="image" src="https://github.com/user-attachments/assets/b1c3cfa1-2d48-489d-ad5a-6c586166a63b" />

<img width="1897" height="891" alt="image" src="https://github.com/user-attachments/assets/811dadcc-0655-41f3-bc1e-2ede0f9b9f44" />

<img width="1905" height="977" alt="image" src="https://github.com/user-attachments/assets/aea14d6f-cbdc-49ce-83e3-35a1c551d404" />

