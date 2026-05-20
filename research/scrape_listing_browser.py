#!/usr/bin/env python3
"""Extrae fichas con contacto del listado FacetWP (POST JSON a /cartilla/)."""
from __future__ import annotations

import json
import sys
from typing import Any

import requests

from discover import (
    CARTILLA_URL,
    FACETWP_DEFAULT_FACETS,
    USER_AGENT,
    fetch_listing_cards_facetwp,
    parse_listing_cards,
)

__all__ = [
    "CARTILLA_URL",
    "FACETWP_DEFAULT_FACETS",
    "fetch_listing_cards_facetwp",
    "parse_listing_cards",
    "scrape_listing_cards",
]


def scrape_listing_cards() -> dict[str, dict[str, Any]]:
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": USER_AGENT,
            "Referer": CARTILLA_URL,
        }
    )
    return fetch_listing_cards_facetwp(session)


def main() -> int:
    cards = scrape_listing_cards()
    print(json.dumps(cards, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
