"""Integration tests for the account health scorer.

Verifies that parse_usage and score compose end-to-end on the fixture data
according to the rules and decisions in docs/spec.md.
"""

from __future__ import annotations

from pathlib import Path

from main import load_export
from usage import Result, parse_usage, score

FIXTURE_PATH = Path(__file__).parent.parent.parent / "fixtures" / "usage.csv"


def test_integration_full_pipeline():
    """Verify parse_usage composed with score on the fixture export."""
    csv_text = load_export(FIXTURE_PATH)
    accounts = parse_usage(csv_text)

    # hooli: no rules fire (12 -> 12 seats, 45 logins, 1 ticket)
    assert score(accounts["hooli"]) == Result(score=10, tier="HEALTHY", reasons=[])

    # acme: blank seats in 2026-03 parsed as 0 (8 -> 0 seats = 100% drop)
    assert score(accounts["acme"]) == Result(score=6, tier="MEDIUM", reasons=["seats down sharply"])  # D3

    # globex: 40% seat drop in 2026-03 (10 -> 6 seats)
    assert score(accounts["globex"]) == Result(score=6, tier="MEDIUM", reasons=["seats down sharply"])

    # vandelay: compares to preceding month (6 -> 5 seats = 16.7% drop, does not fire)
    assert score(accounts["vandelay"]) == Result(score=10, tier="HEALTHY", reasons=[])  # D1

    # initech: logins < 3 (-3), tickets >= 2 (-2), score 5 is MEDIUM tier
    assert score(accounts["initech"]) == Result(
        score=5,
        tier="MEDIUM",
        reasons=["low engagement", "unresolved support load"],
    )  # D2

    # umbrella: single month account cannot fire seat decline rule
    assert score(accounts["umbrella"]) == Result(score=10, tier="HEALTHY", reasons=[])
