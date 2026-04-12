"""Locust profile for manual HTTP load tests.

Run against a live app, for example:
uv run locust -f tests/load/locustfile.py --host http://localhost:8000
"""

from __future__ import annotations

import os
import random
import uuid

from locust import HttpUser, between, task


def _ticket_ids() -> list[int]:
    raw = os.getenv("RESERVEX_LOAD_TICKET_IDS", "1,2,3,4,5")
    return [int(part.strip()) for part in raw.split(",") if part.strip()]


class ReservexUser(HttpUser):
    wait_time = between(0.1, 1.0)

    @task(4)
    def demo_metrics(self) -> None:
        self.client.get("/api/demo/metrics", name="/api/demo/metrics")

    @task(3)
    def list_tickets(self) -> None:
        event_id = int(os.getenv("RESERVEX_LOAD_EVENT_ID", "1"))
        self.client.get(f"/tickets/{event_id}", name="/tickets/{event_id}")

    @task(1)
    def reserve_ticket(self) -> None:
        ticket_id = random.choice(_ticket_ids())
        payload = {
            "user_id": random.randint(1, 1_000_000),
            "idempotency_key": str(uuid.uuid4()),
        }
        with self.client.post(
            f"/tickets/{ticket_id}/reserve",
            json=payload,
            headers={"Idempotency-Key": payload["idempotency_key"]},
            name="/tickets/{ticket_id}/reserve",
            catch_response=True,
        ) as response:
            if response.status_code in {200, 404, 409}:
                response.success()
            else:
                response.failure(f"unexpected status {response.status_code}")
