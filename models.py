from __future__ import annotations
from dataclasses import dataclass


@dataclass
class Deal:
    store: str
    name: str
    description: str
    sale_price: float
    original_price: float | None
    discount_pct: float | None
    valid_until: str | None
    image_url: str = ""
    category: str = "Other"


@dataclass
class Recipe:
    name: str
    url: str
    image_url: str
    matched_deals: list[Deal]
    store_count: int
