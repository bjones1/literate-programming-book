"""Order model for the specification-quality exercise.

Students receive this file in Round 1. It describes the data, not the policy:
every field needed to implement the real cancellation rules is present here,
but nothing tells you what the rules *are*. That gap is the exercise.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class OrderItem:
    sku: str
    name: str
    kind: str
    """Either "physical" or "digital"."""

    shipped_at: datetime | None = None
    """UTC timestamp the item left the warehouse; None if not shipped.

    Always None for digital items.
    """

    download_started_at: datetime | None = None
    """UTC timestamp the customer began downloading; None if not started.

    Always None for physical items.
    """


@dataclass
class Order:
    order_id: str

    placed_at: datetime
    """UTC timestamp the order was placed."""

    merchant_timezone: str
    """IANA timezone name for the fulfilling merchant, e.g. "America/Chicago"."""

    status: str
    """One of "open", "cancelled", or "delivered"."""

    items: list[OrderItem] = field(default_factory=list)
