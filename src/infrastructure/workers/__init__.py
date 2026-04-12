"""Background workers - part of infrastructure layer (LAYER 4).

Contains the outbox relay worker, ProcessPoolExecutor (PDF), and ThreadPoolExecutor
(SMTP).
"""
from __future__ import annotations
