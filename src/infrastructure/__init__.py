"""Infrastructure layer — LAYER 4.

Imports everything. Wires all layers together via FastAPI, SQLAlchemy, Redis clients.
Contains the app factory, DI container, middleware, routes, workers, and observability.
"""
from __future__ import annotations
