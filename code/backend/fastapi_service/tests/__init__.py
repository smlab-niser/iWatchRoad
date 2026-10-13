"""
Smoke tests for the FastAPI internal service.

These tests verify:
  1. FastAPI app can be imported and built without errors
  2. All schemas validate correctly
  3. All business logic functions return expected types
  4. Routers are registered correctly

Run from backend/ directory:
    pytest fastapi_service/tests/ -v

These run WITHOUT a running socket — pure unit tests, no Django, no DB.
"""
