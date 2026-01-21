# Trestle Roundhouse Monorepo

Nx monorepo for Roundhouse, containing the backend runtime, frontend UI, core contracts, and shared libraries.

## Repository layout

- apps/backend — FastAPI backend runtime (routes, persistence, simulators). See [apps/backend/README.md](apps/backend/README.md).
- apps/frontend — Vite/React UI. See [apps/frontend/README.md](apps/frontend/README.md).
- apps/control-point — Control-point app boundaries and contracts.
- core — Architecture truth layer: models, schemas, lifecycle, invariants. See [core/README.md](core/README.md).
- libs/shared_py — Shared Python utilities used by backend and control-point.
- libs/shared-ts — Shared TypeScript utilities used by frontend.
- scripts/arch — Architecture import/path checks.
- tests/architecture — Architecture invariants tests.
- trestle-dev-tools_legacy_backend and trestle-roundhouse-frontend_legacy — Legacy reference only (do not import).
- docs — Reserved for project documentation (currently minimal).

## Standards, architecture, and tooling

- Architecture rules: [AGENT_INSTRUCTIONS.md](AGENT_INSTRUCTIONS.md).
- Standards pin: [.trestle/standards.version](.trestle/standards.version).
- Tooling configs: [ruff.toml](ruff.toml), [mypy.ini](mypy.ini), [pyrightconfig.json](pyrightconfig.json), [biome.json](biome.json), [tsconfig.base.json](tsconfig.base.json), [nx.json](nx.json), [.pre-commit-config.yaml](.pre-commit-config.yaml).

## Getting started

See [README-dev.md](README-dev.md) for local setup and run instructions.
