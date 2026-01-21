# Copilot Agent Instructions — Roundhouse / Trestle Architecture

Below is a **ready-to-paste Copilot Agent Instructions document** designed to **keep the architecture straight and enforce it mechanically**.
It is explicit, restrictive, and bias-correcting by design.

You can place this in something like:

- `.github/copilot/AGENT_INSTRUCTIONS.md`
- or repo-root `COPILOT_ARCHITECTURE_RULES.md`
- or your existing Copilot rules file

---

## 0. Prime Directive (Non-Negotiable)

**This repository follows a strict layered architecture.
You MUST preserve and enforce it.**

If a request would violate these rules, **STOP** and explain the violation instead of implementing it.

Do not “helpfully” blur boundaries.

---

## 1. Architectural Layers (Authoritative)

### 1.1 Core (Architecture Truth Layer)

**Purpose:**
Defines _what things are_, never _how they run_.

**Characteristics:**

- No FastAPI
- No React
- No filesystem access
- No subprocesses
- No simulators
- No HA specifics
- No environment assumptions

**Allowed contents:**

- Data models
- Schemas
- Enums
- Lifecycle state machines (pure logic)
- Validation rules
- Invariants

**Examples:**

- Node
- Node lifecycle states
- Capability descriptors
- Artifact metadata
- Registry interfaces (no IO)

**Rules:**

- Core MUST NOT import from any app
- Core MUST be deterministic and side-effect free

If asked to add logic here that:

- opens files
- starts processes
- mounts routes
- renders UI

→ **Refuse and redirect to an app layer**

---

### 1.2 Applications (Opinionated Runtimes)

Applications _use_ the core.
They do not redefine it.

#### Backend App (FastAPI)

**Owns:**

- HTTP routes
- Persistence
- Process execution
- Simulator orchestration
- HA integration
- Artifact storage

**May import:**

- core
- shared_py

**Must NOT:**

- Redefine core schemas
- Add lifecycle states not in core
- Embed frontend assumptions

---

#### Frontend App (Vite / React)

**Owns:**

- Rendering
- UX
- Routing
- UI composition

**May import:**

- shared-ts
- API-derived schemas

**Must NOT:**

- Invent backend lifecycle semantics
- Manage node lifecycle directly
- Assume simulator or process behavior

---

#### Control-Point App

**Owns:**

- Enforcement
- Validation
- Policy checks

**Uses:**

- core contracts

---

### 1.3 Shared Libraries

**Purpose:**
Cross-app reuse only.

**Rules:**

- May depend on core
- May NOT depend on applications
- No side effects at import time

---

### 1.4 Legacy Code

**Status:**
Read-only reference.

**Rules:**

- DO NOT import legacy code
- DO NOT extend legacy modules
- DO NOT mirror legacy structure unless explicitly instructed

---

## 2. Dependency Rules (Hard Gates)

### Allowed Imports

| From ↓        | Can Import →         |
| ------------- | -------------------- |
| core          | nothing app-specific |
| shared        | core                 |
| backend       | core, shared         |
| frontend      | shared               |
| control-point | core, shared         |

### Forbidden Imports (Always Errors)

- core → backend
- core → frontend
- core → simulator
- frontend → backend internals
- shared → applications
- any → legacy (unless explicitly requested)

If an import would violate this matrix → **STOP**

---

## 3. Node / Panel / Simulator Rules

### Canonical Rule

> **If code answers “what is a node?” → core**
> **If code answers “how do we run it?” → backend**
> **If code answers “how it looks?” → frontend**

---

### Node Model Rules

- There MUST be exactly **one canonical Node schema**
- Lifecycle states MUST live in core
- Backend may persist node state but not redefine it
- Frontend may display node state but not invent it

---

### Simulator Rules

- Simulator lifecycle is an **implementation detail**
- Simulator states map to core lifecycle states
- Simulator code MUST NOT define new lifecycle meanings
- Simulator UI is optional, not authoritative

---

## 4. WASM / LVGL / Panel Rules

- LVGL WASM is treated as a **frontend execution target**
- Backend hosts artifacts; frontend executes them
- Backend does NOT interpret UI state
- Frontend does NOT own lifecycle truth

If asked to:

- mix LVGL rendering logic into backend
- treat WASM as a backend process

→ **Stop and clarify architecture**

---

## 5. API Design Rules

- APIs reflect core models
- APIs do not invent new states or semantics
- CRUD routes operate on canonical core entities
- Lifecycle transitions must be validated against core rules

---

## 6. Copilot Behavior Constraints

When implementing:

- Prefer **small, explicit modules**
- Reject “convenient shortcuts” that cross layers
- Ask for clarification if placement is ambiguous
- Never duplicate schemas across layers
- Never silently add lifecycle states or flags

---

## 7. Mandatory Self-Check (Before Writing Code)

Before emitting code, answer internally:

1. Which layer does this belong to?
2. Does it introduce side effects?
3. Does it redefine a core concept?
4. Does it cross a forbidden dependency boundary?

If any answer is unclear → **STOP**

---

## 8. Failure Mode Override

If user instructions conflict with these rules:

- State the conflict explicitly
- Propose a compliant alternative
- Do NOT “just implement it anyway”

---

## 9. Summary Rule (Memory Anchor)

> **Core defines truth**
> **Apps enact truth**
> **Shared reuse truth**
> **Legacy is history**
> Below is a **companion document** you can paste directly under the Copilot instructions (or as separate files) that gives **concrete, enforceable steps** for:

1. **Pre-commit rules**
2. **Import linting**
3. **Automated architecture tests**

This is written so that:

- Humans can follow it
- Copilot can obey it
- CI can enforce it

No hand-waving, no “best effort”.

---

## Architecture Enforcement: Pre-commit, Import Lint, and Tests

This document defines **mechanical enforcement** of the Roundhouse / Trestle architecture.

These rules exist to prevent silent erosion of the system boundaries.

---

## 1. Pre-commit Enforcement (Mandatory)

### 1.1 Pre-commit Framework

**Tool:** `pre-commit`
**Status:** Required for all contributors

Create or update `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.6.0
    hooks:
      - id: check-yaml
      - id: check-json
      - id: end-of-file-fixer
      - id: trailing-whitespace

  - repo: local
    hooks:
      - id: architecture-import-check
        name: Architecture Import Check
        entry: python scripts/arch/import_check.py
        language: system
        types: [python]

      - id: architecture-path-check
        name: Architecture Path Check
        entry: python scripts/arch/path_check.py
        language: system
        types: [python]

      - id: frontend-import-check
        name: Frontend Architecture Check
        entry: node scripts/arch/frontend_import_check.js
        language: system
        files: ^apps/frontend/
```

---

### 1.2 What Pre-commit Must Enforce

#### Python (Backend / Shared / Core)

- ❌ `core` importing from any app
- ❌ `shared` importing from apps
- ❌ any non-legacy importing from `legacy_*`
- ❌ backend importing frontend code
- ❌ duplicate schema definitions across layers

Violations **fail commit immediately**.

---

## 2. Import Linting (Hard Rules)

### 2.1 Python Import Rules

Create `scripts/arch/import_rules.yaml`:

```yaml
layers:
  core:
    path: core/
    forbidden_imports:
      - apps.backend
      - apps.frontend
      - simulator
      - fastapi
      - uvicorn
      - os
      - subprocess

  shared:
    path: shared_py/
    allowed_imports:
      - core
    forbidden_imports:
      - apps.backend
      - apps.frontend

  backend:
    path: apps/backend/
    allowed_imports:
      - core
      - shared_py
    forbidden_imports:
      - apps/frontend

  frontend:
    path: apps/frontend/
    forbidden_imports:
      - apps/backend
      - core

  legacy:
    path: legacy/
    allow_any: true
```

---

### 2.2 Python Import Check Script

Create `scripts/arch/import_check.py`:

```python
import ast
import sys
from pathlib import Path
import yaml

rules = yaml.safe_load(open("scripts/arch/import_rules.yaml"))

def detect_layer(path: Path):
    for layer, rule in rules["layers"].items():
        if path.as_posix().startswith(rule["path"]):
            return layer, rule
    return None, None

def main():
    for file in sys.argv[1:]:
        path = Path(file)
        layer, rule = detect_layer(path)
        if not rule or rule.get("allow_any"):
            continue

        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for n in node.names:
                    check_import(path, n.name, rule)
            elif isinstance(node, ast.ImportFrom):
                check_import(path, node.module, rule)

def check_import(path, module, rule):
    if not module:
        return
    for forbidden in rule.get("forbidden_imports", []):
        if module.startswith(forbidden):
            raise SystemExit(
                f"[ARCH VIOLATION] {path}: illegal import '{module}'"
            )

if __name__ == "__main__":
    main()
```

---

## 3. Frontend Import Enforcement (React / TS)

### 3.1 Frontend Rules

- ❌ frontend importing backend internals
- ❌ frontend defining lifecycle semantics
- ❌ frontend bypassing API contracts

Only API clients and shared-ts allowed.

---

### 3.2 Frontend Import Check Script

Create `scripts/arch/frontend_import_check.js`:

```js
import fs from "fs";

const forbidden = ["apps/backend", "core/"];

const files = process.argv.slice(2);

for (const file of files) {
  const content = fs.readFileSync(file, "utf8");
  for (const bad of forbidden) {
    if (content.includes(bad)) {
      console.error(
        `[ARCH VIOLATION] ${file} imports forbidden module: ${bad}`,
      );
      process.exit(1);
    }
  }
}
```

---

## 4. Automated Architecture Tests (CI-Level)

These are **tests**, not lint. They assert architectural invariants.

---

### 4.1 Python Architecture Tests (pytest)

Create `tests/architecture/test_layers.py`:

```python
from pathlib import Path

FORBIDDEN = {
    "core": ["apps", "simulator", "fastapi"],
    "shared_py": ["apps"],
}

def test_no_forbidden_imports():
    for layer, banned in FORBIDDEN.items():
        for py in Path(layer).rglob("*.py"):
            text = py.read_text()
            for b in banned:
                assert f"import {b}" not in text, f"{py} imports {b}"
```

---

### 4.2 Schema Singularity Test

Guarantees **no duplicate models**.

```python
def test_single_node_schema():
    matches = list(Path(".").rglob("Node*.py"))
    assert len(matches) == 1, f"Multiple Node schemas found: {matches}"
```

---

### 4.3 Lifecycle State Lock Test

```python
from core.lifecycle import LifecycleState

def test_lifecycle_states_are_frozen():
    expected = {
        "STOPPED",
        "STARTING",
        "RUNNING",
        "ERROR",
    }
    assert set(LifecycleState.__members__) == expected
```

---

## 5. CI Enforcement (Required)

### 5.1 CI Must Run

- `pre-commit run --all-files`
- `pytest tests/architecture`
- frontend lint (ESLint / custom check)

Any failure blocks merge.

---

## 6. Copilot-Specific Enforcement Clause

**Copilot MUST assume:**

- Architecture tests will be added
- Import lint will run
- Violations are not acceptable shortcuts

Copilot must:

- Choose correct layer before writing code
- Refuse to generate code that would fail these checks

---

## 7. Final Guardrail (Authoritative)

> **If it cannot pass pre-commit, it does not belong in the repo.**
> **If it violates architecture tests, it is a bug, not a feature.**

---
