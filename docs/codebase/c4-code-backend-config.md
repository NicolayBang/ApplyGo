# C4 Code Level: Backend Configuration

## Overview

- **Name**: ApplyPilot Backend Configuration
- **Description**: Environment-backed configuration management using Pydantic Settings. Centralizes all application settings with `.env` file support and a cached singleton accessor.
- **Location**: `backend/src/applypilot/config/`
- **Language**: Python
- **Purpose**: Provide type-safe, environment-variable-driven configuration for the FastAPI app, database connection, and Redis URL.

---

## Code Elements

### settings.py

**Location:** `backend/src/applypilot/config/settings.py`

#### `Settings` class (lines 8–18)
Pydantic `BaseSettings` subclass. Loads from environment variables with `.env` file fallback. Unknown variables silently ignored (`extra="ignore"`).

| Field | Type | Default | Env Var |
|-------|------|---------|---------|
| `app_name` | `str` | `"ApplyPilot"` | `APP_NAME` |
| `app_env` | `str` | `"development"` | `APP_ENV` |
| `debug` | `bool` | `True` | `DEBUG` |
| `database_url` | `str` | `postgresql+psycopg://applypilot:applypilot@localhost:5432/applypilot` | `DATABASE_URL` |
| `redis_url` | `str` | `redis://localhost:6379/0` | `REDIS_URL` |

#### `get_settings() -> Settings` (lines 20–23)
`@lru_cache`-decorated factory returning the same cached `Settings` instance on every call.

---

## Dependencies

### Internal
None — leaf module with no internal imports.

### External
- `pydantic-settings` — `BaseSettings`, `SettingsConfigDict`
- `functools.lru_cache` — stdlib caching

### Dependents
- `applypilot.main` — `app_name`, `debug`
- `applypilot.db.session` — `database_url`

---

## Relationships

```mermaid
graph TD
    env[".env / environment vars"] --> Settings
    Settings --> get_settings["get_settings() @lru_cache"]
    get_settings --> main["applypilot.main"]
    get_settings --> session["applypilot.db.session"]
```
