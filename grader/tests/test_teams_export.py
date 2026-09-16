# ***********************************************
# |docname| - Offline tests for `teams_export.py`
# ***********************************************
# These exercise everything except the network: timestamp and date-range
# handling, name resolution, thread flattening (against a stubbed Graph), and
# the two output formats. Run them with ``poetry run pytest``.
#
#
# Imports
# =======
# These are listed in the order prescribed by `PEP 8`_.
#
# Standard library
# ----------------
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional
from zoneinfo import ZoneInfo

# Third-party imports
# -------------------
import pytest
from typer.testing import CliRunner

# Local application imports
# -------------------------
from grader import teams_export as te

# Fixtures and helpers
# ====================
CHICAGO = ZoneInfo("America/Chicago")


def _msg(mid: str, name: str, when: str, text: str) -> Dict[str, Any]:
    # Build a message shaped like the ones Graph returns.
    return {
        "id": mid,
        "createdDateTime": when,
        "messageType": "message",
        "from": {"user": {"displayName": name}},
        "body": {"contentType": "html", "content": "<p>{}</p>".format(text)},
    }


class FakeGraph:
    # Stands in for `Graph`, replaying canned pages instead of calling out.
    def __init__(self, pages: Dict[str, List[Dict[str, Any]]]) -> None:
        self.pages = pages
        self.requested: List[str] = []

    def paged(
        self, url: str, params: Optional[Dict[str, Any]] = None
    ) -> Iterator[Dict[str, Any]]:
        self.requested.append(url)
        yield from self.pages.get(url, [])


# Timestamps
# ==========
def test_parse_graph_time() -> None:
    # Graph's usual form.
    assert te.parse_graph_time("2026-09-08T14:02:11Z") == datetime(
        2026, 9, 8, 14, 2, 11, tzinfo=timezone.utc
    )
    # Seven fractional digits, which ``fromisoformat`` alone rejects.
    assert te.parse_graph_time("2026-09-08T14:02:11.1234567Z").microsecond == 123456
    # An explicit offset is preserved as the same instant.
    assert te.parse_graph_time("2026-09-08T09:02:11-05:00") == datetime(
        2026, 9, 8, 14, 2, 11, tzinfo=timezone.utc
    )


def test_parse_boundary() -> None:
    # A bare start date means midnight local. CDT is UTC-5.
    start = te.parse_boundary("2026-09-01", CHICAGO, end_of_day=False)
    assert start == datetime(2026, 9, 1, 5, 0, tzinfo=timezone.utc)

    # A bare end date means the *end* of that local day, so ``--end`` is inclusive.
    end = te.parse_boundary("2026-09-14", CHICAGO, end_of_day=True)
    assert end.astimezone(CHICAGO).strftime("%Y-%m-%d %H:%M") == "2026-09-14 23:59"

    # A full timestamp is taken literally, even as the end boundary.
    exact = te.parse_boundary("2026-09-14T09:30", CHICAGO, end_of_day=True)
    assert exact.astimezone(CHICAGO).strftime("%Y-%m-%d %H:%M") == "2026-09-14 09:30"

    # Anything unparseable stops the run rather than silently shifting the range.
    with pytest.raises(SystemExit, match="Cannot read"):
        te.parse_boundary("last Tuesday", CHICAGO, end_of_day=False)


# Message fields
# ==============
def test_author_of() -> None:
    assert (
        te.author_of({"from": {"user": {"displayName": "Alice Nguyen"}}})
        == "Alice Nguyen"
    )
    assert te.author_of({"from": {"application": {"displayName": "Bot"}}}) == "Bot"
    # A join/leave event has no sender identity.
    assert (
        te.author_of({"from": None, "messageType": "systemEventMessage"}) == "(system)"
    )
    assert (
        te.author_of({"from": {"user": None}, "messageType": "message"}) == "(unknown)"
    )


def test_body_html() -> None:
    assert (
        te.body_html({"body": {"contentType": "html", "content": "<p>hi</p>"}})
        == "<p>hi</p>"
    )
    # Plain text is escaped and wrapped, so the column is uniformly HTML.
    assert (
        te.body_html({"body": {"contentType": "text", "content": "a < b"}})
        == "<p>a &lt; b</p>"
    )
    assert te.body_html({}) == ""


# Date-range filtering
# ====================
def test_keep() -> None:
    start = te.parse_boundary("2026-09-01", CHICAGO, end_of_day=False)
    end = te.parse_boundary("2026-09-14", CHICAGO, end_of_day=True)

    def message(**overrides: Any) -> Dict[str, Any]:
        base = {"createdDateTime": "2026-09-08T14:02:11Z", "messageType": "message"}
        return {**base, **overrides}

    assert te.keep(message(), start, end, False, False)
    # Outside the range on either side.
    assert not te.keep(
        message(createdDateTime="2026-08-31T12:00:00Z"), start, end, False, False
    )
    assert not te.keep(
        message(createdDateTime="2026-09-15T12:00:00Z"), start, end, False, False
    )
    # The last local day is included...
    assert te.keep(
        message(createdDateTime="2026-09-14T23:00:00-05:00"), start, end, False, False
    )
    # ...and system and deleted messages are excluded unless asked for.
    assert not te.keep(
        message(messageType="systemEventMessage"), start, end, False, False
    )
    assert te.keep(message(messageType="systemEventMessage"), start, end, True, False)
    assert not te.keep(
        message(deletedDateTime="2026-09-09T00:00:00Z"), start, end, False, False
    )
    assert te.keep(
        message(deletedDateTime="2026-09-09T00:00:00Z"), start, end, False, True
    )


# Name resolution
# ===============
def test_pick() -> None:
    items = [
        {"id": "1", "displayName": "General"},
        {"id": "2", "displayName": "general discussion"},
        {"id": "3", "displayName": "Homework"},
    ]
    # An exact match wins, even though "general" is a substring of another name.
    assert te._pick(items, "General", "channel") == ("1", "General")
    # Case-insensitive match.
    assert te._pick(items, "HOMEWORK", "channel") == ("3", "Homework")
    # Substring match, unambiguous.
    assert te._pick(items, "discuss", "channel") == ("2", "general discussion")


@pytest.mark.parametrize("wanted", ["gener", "Nonesuch"])
def test_pick_refuses_to_guess(wanted: str) -> None:
    # Ambiguity and absence both stop the run, listing the real choices.
    items = [
        {"id": "1", "displayName": "General"},
        {"id": "2", "displayName": "general discussion"},
    ]
    with pytest.raises(SystemExit, match="channel"):
        te._pick(items, wanted, "channel")


# Thread flattening
# =================
def test_fetch_thread() -> None:
    base = "/teams/T/channels/C/messages"
    root_a = _msg("a", "Alice Nguyen", "2026-09-08T14:02:11Z", "root a")
    root_a["replies"] = [_msg("a1", "Bob Ruiz", "2026-09-08T14:09:44Z", "reply a1")]
    # A thread at the inline-expansion watermark must be re-fetched in full.
    root_b = _msg("b", "Carol Diaz", "2026-09-09T10:00:00Z", "root b")
    root_b["replies"] = [
        _msg(
            "b{}".format(i), "Dave Park", "2026-09-09T10:05:00Z", "inline {}".format(i)
        )
        for i in range(te.REPLY_WATERMARK)
    ]
    full_b = root_b["replies"] + [
        _msg("b-extra", "Erin Cole", "2026-09-09T11:00:00Z", "truncated reply")
    ]

    graph = FakeGraph({base: [root_a, root_b], "{}/b/replies".format(base): full_b})
    got = list(te.fetch_thread(graph, "T", "C", verbose=False))

    assert [m["id"] for m in got] == (
        ["a", "a1", "b"]
        + ["b{}".format(i) for i in range(te.REPLY_WATERMARK)]
        + ["b-extra"]
    )
    # The short thread was not re-fetched; the long one was.
    assert graph.requested == [base, "{}/b/replies".format(base)]
    # Replies carry their thread, and ``replies`` is not left nested in the row.
    assert got[1]["_thread_id"] == "a" and got[1]["_is_reply"] is True
    assert got[0]["_is_reply"] is False and "replies" not in got[0]


# Output formats
# ==============
def test_outputs(tmp_path: Path) -> None:
    messages = [
        _msg("a", "Alice Nguyen", "2026-09-08T14:02:11Z", "hello, world"),
        _msg("b", "Bob Ruiz", "2026-09-08T14:09:44Z", 'quotes, "commas" & <b>tags</b>'),
    ]
    csv_path = tmp_path / "chats.csv"
    json_path = tmp_path / "chats.json"
    te.write_csv(csv_path, messages, CHICAGO)
    te.write_json(json_path, messages, {"team": "T"})

    # The CSV opens cleanly in Excel: a BOM, three columns, local timestamps,
    # and embedded quotes/commas/markup survive the round trip.
    assert csv_path.read_bytes().startswith(b"\xef\xbb\xbf")
    with csv_path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.reader(handle))
    assert rows[0] == ["timestamp", "user", "html"]
    assert rows[1] == [
        "2026-09-08T09:02:11-05:00",
        "Alice Nguyen",
        "<p>hello, world</p>",
    ]
    assert rows[2][2] == '<p>quotes, "commas" & <b>tags</b></p>'

    archive = json.loads(json_path.read_text(encoding="utf-8"))
    assert archive["exported"] == {"team": "T"}
    assert [m["id"] for m in archive["messages"]] == ["a", "b"]


# Command line
# ============
# Typer's `CliRunner` drives the real command in-process. These three cases all
# fail during option validation, which happens before sign-in, so they never
# touch the network.
def _said(result: Any) -> str:
    # Rich wraps its error boxes to the terminal width, so collapse whitespace
    # before looking for a phrase.
    return " ".join((result.output + (result.stderr or "")).split())


def test_cli_help() -> None:
    result = CliRunner().invoke(te.app, ["--help"])
    assert result.exit_code == 0
    said = _said(result)
    # The flags the README documents are really there.
    for option in ("--team", "--channel", "--start", "--end", "--no-replies"):
        assert option in said
    # ...and the on-only flags grew no pointless negative twin.
    assert "--no-include-system" not in said


def test_cli_rejects_reversed_range() -> None:
    result = CliRunner().invoke(
        te.app,
        [
            "--team",
            "X",
            "--channel",
            "Y",
            "--start",
            "2026-09-14",
            "--end",
            "2026-09-01",
        ],
    )
    # 2 is the conventional exit code for a usage error.
    assert result.exit_code == 2
    assert "falls before" in _said(result)


def test_cli_rejects_unknown_time_zone() -> None:
    result = CliRunner().invoke(
        te.app,
        # fmt: off
        [
            "--team", "X", "--channel", "Y",
            "--start", "2026-09-01", "--end", "2026-09-14",
            "--tz", "Mars/Olympus",
        ],
        # fmt: on
    )
    assert result.exit_code == 2
    assert "Unknown time zone" in _said(result)
