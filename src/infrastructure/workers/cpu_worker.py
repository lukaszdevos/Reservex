"""CPU-bound worker for PDF generation via ProcessPoolExecutor.

Layer: infrastructure/workers
_render_pdf_sync must be a top-level module function to remain pickle-able
when passed to run_in_executor.
"""

from __future__ import annotations

import asyncio
from concurrent.futures import ProcessPoolExecutor


def _render_pdf_sync(ticket_dict: dict[str, object]) -> bytes:
    """Generate a ticket PDF - runs synchronously inside a subprocess."""
    from io import BytesIO

    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    c.setFont("Helvetica-Bold", 24)
    c.drawString(100, 750, "ReserveX - Ticket Confirmation")
    c.setFont("Helvetica", 14)
    y = 700
    for key, value in ticket_dict.items():
        c.drawString(100, y, f"{key}: {value}")
        y -= 25
    c.save()
    return buffer.getvalue()


async def generate_ticket_pdf(
    ticket_dict: dict[str, object],
    process_pool: ProcessPoolExecutor,
) -> bytes:
    """Offload PDF rendering to a subprocess via ProcessPoolExecutor."""
    loop = asyncio.get_running_loop()
    result: bytes = await loop.run_in_executor(
        process_pool, _render_pdf_sync, ticket_dict
    )
    return result
