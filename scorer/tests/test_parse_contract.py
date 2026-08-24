"""Contract tests for the parsing half of the account health scorer.

Verifies that parse_usage parses the export text into list[MonthSnapshot]
according to the rules in docs/spec.md.
"""

from __future__ import annotations

from pathlib import Path

from main import load_export
from usage import MonthSnapshot, parse_usage

FIXTURE_PATH = Path(__file__).parent.parent.parent / "fixtures" / "usage.csv"


def test_parse_usage_full_fixture():
    """Verify parse_usage parses the full fixture usage.csv into exact snapshots."""
    csv_text = load_export(FIXTURE_PATH)
    parsed = parse_usage(csv_text)

    expected = {
        "hooli": [
            MonthSnapshot(account_id="hooli", month="2026-01", seats_active=12, logins=40, tickets_open=0),
            MonthSnapshot(account_id="hooli", month="2026-02", seats_active=12, logins=45, tickets_open=1),
        ],
        "acme": [
            MonthSnapshot(account_id="acme", month="2026-01", seats_active=10, logins=5, tickets_open=0),
            MonthSnapshot(account_id="acme", month="2026-02", seats_active=8, logins=5, tickets_open=0),
            MonthSnapshot(account_id="acme", month="2026-03", seats_active=0, logins=5, tickets_open=0),  # D3
        ],
        "globex": [
            MonthSnapshot(account_id="globex", month="2026-01", seats_active=4, logins=5, tickets_open=0),
            MonthSnapshot(account_id="globex", month="2026-02", seats_active=10, logins=5, tickets_open=0),
            MonthSnapshot(account_id="globex", month="2026-03", seats_active=6, logins=5, tickets_open=0),
        ],
        "vandelay": [
            MonthSnapshot(account_id="vandelay", month="2026-01", seats_active=10, logins=5, tickets_open=0),
            MonthSnapshot(account_id="vandelay", month="2026-02", seats_active=6, logins=5, tickets_open=0),
            MonthSnapshot(account_id="vandelay", month="2026-03", seats_active=5, logins=5, tickets_open=0),
        ],
        "initech": [
            MonthSnapshot(account_id="initech", month="2026-01", seats_active=6, logins=4, tickets_open=0),
            MonthSnapshot(account_id="initech", month="2026-02", seats_active=6, logins=2, tickets_open=3),
        ],
        "umbrella": [
            MonthSnapshot(account_id="umbrella", month="2026-02", seats_active=3, logins=10, tickets_open=0),
        ],
    }

    assert parsed == expected


def test_parse_usage_blank_seats_parsed_as_zero():
    """Verify that a blank seats_active field is parsed as 0."""
    csv_text = "account_id,month,seats_active,logins,tickets_open\nacme,2026-03,,5,0\n"
    parsed = parse_usage(csv_text)

    assert parsed["acme"] == [
        MonthSnapshot(account_id="acme", month="2026-03", seats_active=0, logins=5, tickets_open=0),  # D3
    ]


def test_parse_usage_sorts_months_in_ascending_order():
    """Verify that snapshots for each account are returned in ascending month order."""
    csv_text = (
        "account_id,month,seats_active,logins,tickets_open\n"
        "acme,2026-03,5,5,0\n"
        "acme,2026-01,10,5,0\n"
        "acme,2026-02,8,5,0\n"
    )
    parsed = parse_usage(csv_text)

    assert [snapshot.month for snapshot in parsed["acme"]] == ["2026-01", "2026-02", "2026-03"]


def test_parse_usage_omits_accounts_with_no_months():
    """Verify that an empty export produces an empty dictionary."""
    csv_text = "account_id,month,seats_active,logins,tickets_open\n"
    parsed = parse_usage(csv_text)

    assert parsed == {}
