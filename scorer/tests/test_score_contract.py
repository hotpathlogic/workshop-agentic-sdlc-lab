"""Contract tests for the scoring half of the account health scorer.

Verifies that score(<longhand MonthSnapshot list>) produces the exact score, tier,
and reasons according to the rules and decisions in docs/spec.md.
"""

from __future__ import annotations

from usage import MonthSnapshot, Result, score


def test_score_healthy_account_no_rules_fired():
    """Verify an account with stable seats, high logins, and low tickets scores 10 HEALTHY."""
    months = [
        MonthSnapshot(account_id="hooli", month="2026-01", seats_active=12, logins=40, tickets_open=0),
        MonthSnapshot(account_id="hooli", month="2026-02", seats_active=12, logins=45, tickets_open=1),
    ]
    assert score(months) == Result(score=10, tier="HEALTHY", reasons=[])


def test_score_preceding_month_comparison_vandelay():
    """Verify seat decline compares latest month (2026-03: 5) to immediately preceding month (2026-02: 6), not 2026-01 (10)."""
    months = [
        MonthSnapshot(account_id="vandelay", month="2026-01", seats_active=10, logins=5, tickets_open=0),
        MonthSnapshot(account_id="vandelay", month="2026-02", seats_active=6, logins=5, tickets_open=0),
        MonthSnapshot(account_id="vandelay", month="2026-03", seats_active=5, logins=5, tickets_open=0),
    ]
    assert score(months) == Result(score=10, tier="HEALTHY", reasons=[])  # D1


def test_score_blank_seats_parsed_as_zero_triggers_seat_drop_acme():
    """Verify 0 active seats in latest month triggers >= 40% seat drop (-4 deduction, MEDIUM tier)."""
    months = [
        MonthSnapshot(account_id="acme", month="2026-01", seats_active=10, logins=5, tickets_open=0),
        MonthSnapshot(account_id="acme", month="2026-02", seats_active=8, logins=5, tickets_open=0),
        MonthSnapshot(account_id="acme", month="2026-03", seats_active=0, logins=5, tickets_open=0),
    ]
    assert score(months) == Result(score=6, tier="MEDIUM", reasons=["seats down sharply"])  # D3


def test_score_exact_40_percent_seat_drop_globex():
    """Verify exactly 40% seat drop (10 -> 6) triggers seat drop rule (-4 deduction)."""
    months = [
        MonthSnapshot(account_id="globex", month="2026-01", seats_active=4, logins=5, tickets_open=0),
        MonthSnapshot(account_id="globex", month="2026-02", seats_active=10, logins=5, tickets_open=0),
        MonthSnapshot(account_id="globex", month="2026-03", seats_active=6, logins=5, tickets_open=0),
    ]
    assert score(months) == Result(score=6, tier="MEDIUM", reasons=["seats down sharply"])


def test_score_5_is_medium_tier_initech():
    """Verify score 5 belongs to MEDIUM tier with low engagement and unresolved support load reasons."""
    months = [
        MonthSnapshot(account_id="initech", month="2026-01", seats_active=6, logins=4, tickets_open=0),
        MonthSnapshot(account_id="initech", month="2026-02", seats_active=6, logins=2, tickets_open=3),
    ]
    assert score(months) == Result(score=5, tier="MEDIUM", reasons=["low engagement", "unresolved support load"])  # D2


def test_score_single_month_cannot_fire_seat_decline_umbrella():
    """Verify an account with a single month cannot fire the seat decline rule."""
    months = [
        MonthSnapshot(account_id="umbrella", month="2026-02", seats_active=3, logins=10, tickets_open=0),
    ]
    assert score(months) == Result(score=10, tier="HEALTHY", reasons=[])


def test_score_tier_boundary_healthy_score_8():
    """Verify score 8 (tickets_open >= 2, -2) is in HEALTHY tier."""
    months = [
        MonthSnapshot(account_id="test", month="2026-01", seats_active=10, logins=5, tickets_open=2),
    ]
    assert score(months) == Result(score=8, tier="HEALTHY", reasons=["unresolved support load"])  # D2


def test_score_tier_boundary_medium_score_7():
    """Verify score 7 (logins < 3, -3) is in MEDIUM tier."""
    months = [
        MonthSnapshot(account_id="test", month="2026-01", seats_active=10, logins=2, tickets_open=0),
    ]
    assert score(months) == Result(score=7, tier="MEDIUM", reasons=["low engagement"])  # D2


def test_score_tier_boundary_at_risk_score_4():
    """Verify score 4 (seat drop -4, tickets -2) is in AT RISK tier."""
    months = [
        MonthSnapshot(account_id="test", month="2026-01", seats_active=10, logins=5, tickets_open=0),
        MonthSnapshot(account_id="test", month="2026-02", seats_active=5, logins=5, tickets_open=2),
    ]
    assert score(months) == Result(score=4, tier="AT RISK", reasons=["seats down sharply", "unresolved support load"])  # D2


def test_score_all_rules_fired_and_reason_ordering():
    """Verify that when all rules fire, score is 1, tier is AT RISK, and reasons preserve rule order."""
    months = [
        MonthSnapshot(account_id="test", month="2026-01", seats_active=10, logins=5, tickets_open=0),
        MonthSnapshot(account_id="test", month="2026-02", seats_active=5, logins=2, tickets_open=2),
    ]
    assert score(months) == Result(
        score=1,
        tier="AT RISK",
        reasons=["seats down sharply", "low engagement", "unresolved support load"],
    )  # D2
