"""Seam interface for account health scoring.

Defines the data structures and function signatures resolved in docs/spec.md.
Every function body raises NotImplementedError until implemented.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MonthSnapshot:
    account_id: str
    month: str  # "YYYY-MM"
    seats_active: int
    logins: int
    tickets_open: int


@dataclass(frozen=True)
class Result:
    score: int
    tier: str  # "HEALTHY" | "MEDIUM" | "AT RISK"
    reasons: list[str]


def parse_usage(csv_text: str) -> dict[str, list[MonthSnapshot]]:
    """Group the export text by account, each list in ascending month order.

    An account with no months to score is omitted, so score() is never
    called with an empty list.
    """
    import csv
    import io

    reader = csv.DictReader(io.StringIO(csv_text))
    accounts: dict[str, list[MonthSnapshot]] = {}
    for row in reader:
        if not row or not row.get("account_id"):
            continue
        account_id = row["account_id"].strip()
        if not account_id:
            continue

        month = row["month"].strip()
        seats_raw = (row.get("seats_active") or "").strip()
        seats_active = int(seats_raw) if seats_raw else 0
        logins = int(row["logins"].strip())
        tickets_open = int(row["tickets_open"].strip())

        snapshot = MonthSnapshot(
            account_id=account_id,
            month=month,
            seats_active=seats_active,
            logins=logins,
            tickets_open=tickets_open,
        )
        if account_id not in accounts:
            accounts[account_id] = []
        accounts[account_id].append(snapshot)

    for account_id in accounts:
        accounts[account_id].sort(key=lambda x: x.month)

    return accounts


def score(months: list[MonthSnapshot]) -> Result:
    """Score one account's months. Never reads the CSV."""
    if not months:
        raise ValueError("score() called with empty months list")

    current_score = 10
    reasons: list[str] = []

    latest = months[-1]

    # Rule 1: Seat count fell by 40% or more from immediately preceding month
    if len(months) >= 2:
        prev = months[-2]
        if prev.seats_active > 0:
            if (prev.seats_active - latest.seats_active) * 10 >= prev.seats_active * 4:
                current_score -= 4
                reasons.append("seats down sharply")

    # Rule 2: Fewer than 3 logins in the latest month
    if latest.logins < 3:
        current_score -= 3
        reasons.append("low engagement")

    # Rule 3: 2 or more tickets open in the latest month
    if latest.tickets_open >= 2:
        current_score -= 2
        reasons.append("unresolved support load")

    current_score = max(0, current_score)

    if current_score >= 8:
        tier = "HEALTHY"
    elif current_score >= 5:
        tier = "MEDIUM"
    else:
        tier = "AT RISK"

    return Result(score=current_score, tier=tier, reasons=reasons)
