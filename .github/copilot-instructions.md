# Main-Line Project Guidelines

## Overview

Main-Line is a chess web application. The stack: Rust/Axum backend, Next.js 15 (App Router) frontend, PostgreSQL 17, MinIO (S3-compatible object storage), and Stockfish (chess engine over WebSocket). The project is mid-transition from Docker Compose to Kubernetes (Kind cluster locally).

Current focus: Kubernetes observability stack (Loki → Grafana Alloy → OpenTelemetry Operator/Collector → Grafana Dashboard → Prometheus → Tempo). See [docs/current_work/README.md](../docs/current_work/README.md).

## Architecture

```
frontend (Next.js, port 3001)
    ↓ REST/JSON (generated TypeScript client)
backend (Axum, port 3000)  ←→  PostgreSQL (port 5432)
                           ←→  MinIO (ports 9000/9001)
stockfish (WebSocket, port 9002)
```

**Rust workspace crates** (`rust/`):
- `backend` — Axum HTTP server entry point
- `backend_lib` — Business logic, DB models, route handlers
- `shared_items_lib` — Types shared with TypeScript (exported via `specta`)
- `mnln_core_items` — Zero-dep foundational types (used across all crates)
- `mnln_env` — Environment variable config
- `object_storage` — S3/MinIO abstraction
- `openapi_spec` — Generates `openapi_spec.json` via `utoipa`/`utoipauto`
- `export_shared_types` — CLI binary that exports Specta types as TypeScript

## Build & Run

### Local (Docker Compose)
```bash
python -m scripts.generate_secrets          # Create JWT/DB/MinIO secrets (run once)
python -m scripts.generate_certs            # Create TLS certs for MinIO (run once)
python -m scripts.build_intermediate_images # Build rust_workspace, backend_lib, openapi_spec, api_client
docker compose up --build                   # Start all services
```

Services: frontend http://localhost:3001, backend http://localhost:3000, Swagger UI http://localhost:3000/swagger-ui/, PgAdmin http://localhost:8080, MinIO console http://localhost:9001.

### Kubernetes (Kind)
```bash
python -m scripts.bootstrap_kind_cluster --help        # See all steps and flags
python -m scripts.bootstrap_kind_cluster               # Run all steps
python -m scripts.bootstrap_kind_cluster --steps=<s1,s2>  # Run specific steps
python -m scripts.bootstrap_kind_cluster --until-step=<name>  # Run up to a step
python -m scripts.bootstrap_kind_cluster --skip_steps=<s1,s2> # Skip steps
```

Bootstrap steps are defined in `scripts/bootstrap_kind_cluster/steps/` and orchestrated by `scripts/bootstrap_kind_cluster/__main__.py`. Each step is a `Step` object with `name`, `perform`, and optional `depends_on`.

### Frontend
```bash
cd frontend && npm run dev    # Dev server on port 3001
cd frontend && npm run build  # Production build
```

### Rust
```bash
cd rust && cargo build --release
cargo sqlx prepare --workspace  # Regenerate SQLx compile-time query cache
```

### Code Generation Pipeline
```
Rust (utoipa annotations) → openapi_spec.json → TypeScript client (openapi-ts)
Rust (specta types) → export_shared_types binary → TypeScript types
```
To regenerate: `python -m scripts.extract_artifacts` (extracts from Docker images into workspace).

## Conventions

### Rust
- **Workspace edition**: 2024 for all crates. Shared dependency versions in `[workspace.dependencies]`.
- **Web framework**: Axum (not Actix-web — the Cargo.toml has axum).
- **Database**: SQLx with compile-time query checking. Run `cargo sqlx prepare --workspace` after adding queries.
- **OpenAPI**: Add `utoipa` `#[utoipa::path(...)]` attributes to handlers in `backend_lib`; `openapi_spec` crate aggregates them.
- **Type sharing**: Types needed by both backend and frontend go in `shared_items_lib` with `specta::Type` and `utoipa::ToSchema` derives.
- **Tracing**: Use `tracing` crate macros (`info!`, `error!`, etc.), not `println!`.

### Passwords
Argon2 hash on the **frontend** (argon2-browser) before transmission; backend re-hashes with Argon2. See [docs/practices/password_storage.md](../docs/practices/password_storage.md).

### Secrets & Config
- Secrets live in `secrets/*.env` (git-ignored). Example files: `secrets/*.example.env`.
- Run `python -m scripts.generate_secrets` to generate missing secrets.
- Never commit actual `.env` files.

### Dockerfiles
- Named `Dockerfile.<component>` at workspace root.
- Multi-stage builds; cargo-chef for Rust dependency layer caching.
- Image name pattern: `main-line-<component>`.

### Kubernetes / Scripts
- Kubernetes manifests: `k8s/<component>/`.
- Helm chart helpers: `scripts/common/helm.py`. Each service has a dedicated deploy function.
- `Step` objects use `depends_on` for ordering; add new bootstrap steps to `ALL_STEPS` in `__main__.py`.
- `StepKind.Required()` runs by default; `StepKind.Optional(enable_flag=...)` requires an explicit flag.

### Naming
- Rust: `snake_case` everywhere (crates, modules, variables).
- TypeScript/Next.js: `camelCase` functions, `PascalCase` components, file structure follows Next.js App Router conventions.
- K8s namespaces match component names (e.g., `grafana-dashboard`, `opentelemetry-collector`).
