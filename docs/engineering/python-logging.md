# Python Logging Conventions

## Philosophy
To maintain a high standard of observability, debuggability, and type safety, we follow strict conventions for structured logging across the application. These conventions apply to FastAPI endpoints, background workers, and core domain services.

## Core Rules

### 1. Structured Logging with `structlog`
We exclusively use `structlog` for structured, JSON-formatted logging. Never use the standard library `logging` module directly to emit logs, and avoid simple `print()` statements in production code.

### 2. Centralized Logger Definition
Instead of calling `structlog.stdlib.get_logger` directly, always import and use the centralized `get_logger` function from `doc_forge.app.logging`. This ensures consistent instantiation, strong typing, and centralized control over our logger definition.

**Correct:**
```python
from doc_forge.app.logging import get_logger

logger = get_logger(__name__)
```

**Incorrect:**
```python
import structlog
# Do not use structlog directly
logger = structlog.stdlib.get_logger(__name__)
```

### 3. FastAPI Dependency Injection
In FastAPI route handlers, never use a global module-level logger directly. Instead, inject the logger using `Depends()`.

**Why?**
* It scopes the logger to the request lifecycle.
* It ensures context variables (like `request_id` or `workspace_id` added by middleware) are correctly propagated and isolated per async request.
* It makes the endpoints easily mockable and testable.

**Pattern:**
```python
from fastapi import APIRouter, Depends
import structlog
from doc_forge.app.logging import get_logger as get_app_logger

router = APIRouter()

def get_logger() -> structlog.stdlib.BoundLogger:
    return get_app_logger(__name__)

@router.get("/status")
async def get_status(
    logger: structlog.stdlib.BoundLogger = Depends(get_logger)
):
    logger.info("status.requested")
    return {"status": "ok"}
```

### 4. Testing Endpoints with Injected Loggers
When writing tests that execute the raw Python endpoint function directly (e.g., `route.endpoint(...)`), the FastAPI dependency injection framework is bypassed. The `logger` argument will default to the un-evaluated `Depends(...)` object, causing `AttributeError` when you try to call `logger.info()`.

To resolve this, you must manually inject the logger when extracting the endpoint. Use `functools.partial` to bind a logger to the function before calling it.

**Example in a test suite:**
```python
import functools
import structlog
from fastapi import FastAPI
from fastapi.routing import APIRoute
from doc_forge.app.logging import get_logger

def _route_endpoint(app: FastAPI, path: str, method: str):
    for route in app.routes:
        if isinstance(route, APIRoute) and route.path == path and method in route.methods:
            # Manually inject the logger so tests don't crash on the Depends object
            return functools.partial(route.endpoint, logger=get_logger())
    raise ValueError("Route not found")
```

### 5. Class-Level Logger Injection (Services)
For service classes and domain models (e.g., `QueryService`, `DocumentLifecycleService`), accept an optional logger in the constructor. If one is not provided, fall back to a newly instantiated one using the central `get_logger`.

**Why?**
* This is excellent for unit testing (pass a mock or a `structlog.testing.ReturnLogger`).
* It allows higher-level components to pre-bind context to the logger (e.g., `service.logger.bind(component="query_service")`) before passing it down.

**Pattern:**
```python
import structlog
from doc_forge.app.logging import get_logger

class QueryService:
    def __init__(self, logger: structlog.stdlib.BoundLogger | None = None):
        self._logger = logger or get_logger(self.__class__.__name__)
        
    def execute(self):
        self._logger.info("query.execution.started")
```

### 6. Event Naming Convention
Log event names should be descriptive, hierarchical, and use dot-notation representing the `<domain>.<action>.<status>` lifecycle.
* Examples: `document.upload.accepted`, `query.api.started`, `system.readyz.failed`.
