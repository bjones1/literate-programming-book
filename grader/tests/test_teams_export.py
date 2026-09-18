# ***********************************************
# |docname| - Offline tests for `teams_export.py`
# ***********************************************
# These exercise everything except the network: timestamp and date-range
# handling, name resolution, thread flattening (against a stubbed Graph), and
# the two output formats. Run them with ``uv run pytest``.
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
import threading
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


# Sign-in
# =======
# The sign-in itself needs a live tenant, but the choice of *how* to sign in --
# broker first, browser when the broker is missing or says no -- is ordinary
# logic, and this is where a tenant that blocks one method gets handled.
class FakeApp:
    # Stands in for `msal.PublicClientApplication`. `interactive` is what
    # `acquire_token_interactive` should do: raise it, or return it.
    def __init__(self, interactive: Any) -> None:
        self.interactive = interactive
        self.calls = 0

    def get_accounts(self) -> List[Dict[str, Any]]:
        return []

    def acquire_token_silent(self, scopes: Any, account: Any) -> None:
        return None

    def acquire_token_interactive(self, scopes: Any, **kwargs: Any) -> Any:
        self.calls += 1
        if isinstance(self.interactive, Exception):
            raise self.interactive
        return self.interactive


def test_sign_in_swallows_broker_failures() -> None:
    # A broker that throws is a reason to try the browser, not to stop...
    assert te.sign_in(FakeApp(RuntimeError("no broker")), broker=True) is None
    # ...as is one that answers, but without a token.
    refused = {"error": "broker_error", "error_description": "not compliant"}
    assert te.sign_in(FakeApp(refused), broker=True) is None
    # The browser has nothing to fall back *to*, so its failures propagate.
    with pytest.raises(RuntimeError):
        te.sign_in(FakeApp(RuntimeError("no browser")), broker=False)


def test_acquire_token_falls_back_to_the_browser(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    asked: List[bool] = []

    def fake_build(client_id: str, tenant: str, cache: Any, broker: bool) -> FakeApp:
        asked.append(broker)
        return FakeApp(RuntimeError("declined") if broker else {"access_token": "tok"})

    # A broker is only ever asked for on Windows and macOS, so these tests say
    # which platform they are describing rather than inheriting the host's.
    monkeypatch.setattr(te.sys, "platform", "win32")
    monkeypatch.setattr(te, "build_app", fake_build)
    token = te.acquire_token("cid", "organizations", tmp_path / "cache.json", True)
    assert token == "tok"
    # Brokered first, then unbrokered.
    assert asked == [True, False]


def test_acquire_token_without_the_broker_extra(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Where `msal[broker]` is not installed, MSAL refuses to build the client
    # at all, and the sign-in must still go through.
    asked: List[bool] = []

    def fake_build(client_id: str, tenant: str, cache: Any, broker: bool) -> FakeApp:
        asked.append(broker)
        if broker:
            raise ImportError('pip install "msal[broker]"')
        return FakeApp({"access_token": "tok"})

    monkeypatch.setattr(te.sys, "platform", "darwin")
    monkeypatch.setattr(te, "build_app", fake_build)
    path = tmp_path / "cache.json"
    assert te.acquire_token("cid", "organizations", path, True) == "tok"
    assert asked == [True, False]


def test_acquire_token_does_not_ask_for_an_impossible_broker(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # MSAL's `enable_broker_on_windows` is ANDed with the platform, so on Linux
    # it builds an unbrokered client and says nothing. Asking anyway would make
    # `broker` a lie: the browser would be announced as the account manager,
    # and a user who cancelled it would get a second browser rather than an
    # error.
    asked: List[bool] = []

    def fake_build(client_id: str, tenant: str, cache: Any, broker: bool) -> FakeApp:
        asked.append(broker)
        return FakeApp({"access_token": "tok"})

    monkeypatch.setattr(te.sys, "platform", "linux")
    monkeypatch.setattr(te, "build_app", fake_build)
    path = tmp_path / "cache.json"
    assert te.acquire_token("cid", "organizations", path, True) == "tok"
    # One client, unbrokered, and so one sign-in.
    assert asked == [False]


def test_acquire_token_reports_a_browser_that_will_not_open(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Nothing is left to fall back to, but that is a message, not a traceback.
    monkeypatch.setattr(te.sys, "platform", "linux")
    monkeypatch.setattr(
        te,
        "build_app",
        lambda client_id, tenant, cache, broker: FakeApp(RuntimeError("no browser")),
    )
    with pytest.raises(SystemExit) as caught:
        te.acquire_token("cid", "organizations", tmp_path / "cache.json")
    assert "no browser" in str(caught.value)


# The failure that motivated the timeout: a broker that neither returns nor
# raises. `FakeApp` cannot express it, since it always does one or the other.
class HangingApp:
    """A broker that answers only when told to, which -- in these tests -- is
    never. `released` lets the test unblock it, so that no abandoned thread
    outlives the run."""

    def __init__(self) -> None:
        self.released = threading.Event()
        self.entered = threading.Event()

    def get_accounts(self) -> List[Dict[str, Any]]:
        return []

    def acquire_token_silent(self, scopes: Any, account: Any) -> None:
        return None

    def acquire_token_interactive(self, scopes: Any, **kwargs: Any) -> Any:
        self.entered.set()
        self.released.wait(30)
        return {"access_token": "too late"}


def test_sign_in_abandons_a_broker_that_never_answers() -> None:
    # The whole point: no exception and no result, so the fallback has to be
    # driven by the clock rather than by anything the broker says.
    app = HangingApp()
    try:
        assert te.sign_in(app, broker=True, timeout=0.1) is None
        assert app.entered.wait(5), "the sign-in never reached the broker"
    finally:
        app.released.set()


def test_acquire_token_falls_back_when_the_broker_hangs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    hanging = HangingApp()
    apps: List[Any] = []

    def fake_build(client_id: str, tenant: str, cache: Any, broker: bool) -> Any:
        apps.append(hanging if broker else FakeApp({"access_token": "tok"}))
        return apps[-1]

    monkeypatch.setattr(te.sys, "platform", "win32")
    monkeypatch.setattr(te, "build_app", fake_build)
    monkeypatch.setattr(te, "BROKER_TIMEOUT", 0.1)
    try:
        token = te.acquire_token("cid", "organizations", tmp_path / "c.json", True)
        assert token == "tok"
    finally:
        hanging.released.set()


def test_call_within_carries_the_outcome_back() -> None:
    assert te.call_within(lambda: 42, 5) == (True, 42)
    finished, outcome = te.call_within(lambda: 1 / 0, 5)
    assert finished and isinstance(outcome, ZeroDivisionError)


def test_acquire_token_reports_a_failed_sign_in(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        te,
        "build_app",
        lambda client_id, tenant, cache, broker: FakeApp(
            {"error": "access_denied", "error_description": "policy says no"}
        ),
    )
    with pytest.raises(SystemExit) as caught:
        te.acquire_token("cid", "organizations", tmp_path / "cache.json", broker=False)
    assert "policy says no" in str(caught.value)


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
        [
            "--team",
            "X",
            "--channel",
            "Y",
            "--start",
            "2026-09-01",
            "--end",
            "2026-09-14",
            "--tz",
            "Mars/Olympus",
        ],
    )
    assert result.exit_code == 2
    assert "Unknown time zone" in _said(result)
