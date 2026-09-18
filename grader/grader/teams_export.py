#!/usr/bin/env python3
# Copyright (C) 2026 Bryan A. Jones.
#
# This file is part of the literate programming book.
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# this program. If not, see
# [http://www.gnu.org/licenses/](http://www.gnu.org/licenses/).
#
# `teams_export.py` -- export a Teams channel's chat history over a date range
# ============================================================================
#
# This implements steps 1 and 2 of `chat_grader.md`: given a date range, pull
# the message history of one Microsoft Teams channel (root posts plus threaded
# replies) and write it out as
#
# -   a JSON archive holding the raw Microsoft Graph representation of every
#     message, so that nothing is lost, and
# -   a CSV with exactly three columns -- `timestamp`, `user`, `html` -- which
#     step 3 (grading) then appends criterion columns to.
#
# Authentication is delegated -- you sign in as yourself -- so the export sees
# exactly the channels you can already see in the Teams client. No Azure app
# registration is required: the default client ID below is Microsoft's own
# pre-registered, pre-consented "Microsoft Graph Command Line Tools" public
# client.
"""Export a Microsoft Teams channel's chat history to JSON and CSV.

See README.md in this directory for setup and usage.
"""

from __future__ import annotations

import csv
import html
import json
import re
import sys
import threading
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Annotated, Any, Callable, Iterator, Optional, Protocol
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

try:
    import msal
    import requests
    import typer
except ModuleNotFoundError as exc:  # pragma: no cover - setup guidance only.
    sys.exit(
        f"Missing dependency {exc.name!r}. Install this project's dependencies "
        "first:\n    uv sync"
    )


# Configuration
# -------------
#
# The Graph endpoint. `v1.0` is the generally-available surface; channel
# messages are fully supported there.
GRAPH = "https://graph.microsoft.com/v1.0"

# Microsoft's own public client for command-line Graph access. It is
# pre-registered in every tenant, which is what lets this script run without an
# app registration of its own. Override with `--client-id` if your tenant
# blocks it and you have registered a public client of your own.
DEFAULT_CLIENT_ID = "14d82eec-204b-4c2f-b7e8-296a70dab67e"

# Delegated permissions requested at sign-in. `ChannelMessage.Read.All` is the
# one that actually reads messages; the other two let us turn the team and
# channel *names* you type on the command line into the IDs Graph wants.
SCOPES = ["ChannelMessage.Read.All", "Team.ReadBasic.All", "Channel.ReadBasic.All"]

# Where the refresh token is cached, so that you sign in once rather than once
# per run.
DEFAULT_CACHE = Path.home() / ".teams_export_token.json"

# `$expand=replies` returns a thread's replies inline with its root post, which
# holds the export to one request per page. Graph caps that inline list, so any
# thread coming back with at least this many replies is re-fetched through the
# dedicated, fully paged replies endpoint. The cap is not documented as a fixed
# number, so this watermark is deliberately conservative.
REPLY_WATERMARK = 20

# Page size for message listings. 50 is Graph's documented maximum for channel
# messages.
PAGE_SIZE = 50

# How long a brokered sign-in is given to answer. The broker's whole premise is
# that the operating system already holds the account, so a successful answer
# takes about a second; one that has said nothing for this long is not slow but
# stuck, and the browser is the way out.
BROKER_TIMEOUT = 20.0

# Team IDs are GUIDs; channel IDs are not, and look like
# `19:abc...def@thread.tacv2`. Recognizing both lets the same option accept
# either a display name or an ID.
GUID_RE = re.compile(r"^[0-9a-fA-F]{8}-(?:[0-9a-fA-F]{4}-){3}[0-9a-fA-F]{12}$")
CHANNEL_ID_RE = re.compile(r"^19:[^@]+@thread\.\w+$")


# Authentication
# --------------
#
# Sign-in is interactive and uses the OAuth 2.0 authorization code flow with
# PKCE: MSAL opens a browser (or hands the request to the operating system's
# sign-in broker, below) and collects the authorization code back on a loopback
# redirect that only this process is listening on.
#
# This deliberately replaces the device code flow, in which you typed a code
# into a browser on some *other* device. That indirection is exactly what makes
# device code phishable -- an attacker can mail you a code and have your
# sign-in mint a token for their session -- so many tenants now refuse it by
# Conditional Access policy. Nothing else about the script changes: same
# client, same delegated scopes, same cache.
#
# Where it works, the broker -- Web Account Manager on Windows, Company Portal
# on macOS -- is better still. It signs in through the account the operating
# system already holds, which binds the token to this device, usually without
# prompting at all. *Where it works*: it needs the `msal[broker]` extra
# installed, and it needs a tenant it can actually authenticate against. So a
# broker that is missing, refuses to start, or declines the request falls back
# to the browser rather than failing.
#
# It also needs a time limit, which is why it is off by default. A broker can
# fail by never answering at all: against a federated (WS-Trust) tenant, the
# Windows broker's silent attempt comes back `InteractionRequired`, and the
# interactive attempt that follows then hangs with its window never shown --
# no error, no exception, no timeout, because the `threading.Event` MSAL waits
# on is given neither a deadline nor a way to cancel. That is the one failure
# a "broker first, browser second" fallback cannot see, since it is watching
# for an answer that never comes. So the brokered attempt is run on a thread of
# its own and abandoned when it goes quiet, and `--broker` must be asked for.
def build_app(
    client_id: str, tenant: str, cache: msal.SerializableTokenCache, broker: bool
) -> msal.PublicClientApplication:
    """Build the MSAL client, with or without broker support. Asking for the
    broker when `msal[broker]` is not installed raises `ImportError`, which is
    the caller's cue to build an unbrokered client instead."""
    return msal.PublicClientApplication(
        client_id,
        authority=f"https://login.microsoftonline.com/{tenant}",
        token_cache=cache,
        # `None`, not `False`, is MSAL's "do not use a broker": passing `False`
        # is an opt-out that it treats no differently, but `None` is what its
        # documentation calls the default.
        enable_broker_on_windows=broker or None,
        enable_broker_on_mac=broker or None,
    )


class SupportsInteractiveSignIn(Protocol):
    """The one method of MSAL's client that `sign_in` uses. Declaring the
    dependency structurally, as `fetch_thread` does with `SupportsPaging`, is
    what lets the tests drive the broker-then-browser fallback with a stub."""

    def acquire_token_interactive(
        self, scopes: list[str], **kwargs: Any
    ) -> dict[str, Any]: ...


def call_within(call: Callable[[], Any], timeout: float) -> tuple[bool, Any]:
    """Run `call()` on a thread of its own and give it `timeout` seconds.
    Returns `(True, outcome)` once it finishes -- `outcome` being whatever it
    returned, or the exception it raised -- and `(False, None)` while it is
    still going.

    A thread is the only handle there is: a stuck brokered sign-in is parked in
    native code below an uncancellable wait, so it cannot be interrupted, only
    left behind. Hence `daemon=True`, so that an abandoned attempt cannot keep
    the process alive. Abandoning it while it still holds the MSAL client and
    the token cache is safe, because `msal` guards every cache mutation with a
    lock: the worst a broker that finally answers can do is add a perfectly
    good token to a cache no one is reading any more."""
    outcome: list[Any] = []

    def run() -> None:
        try:
            outcome.append(call())
        # Carried across the thread boundary rather than handled, so that the
        # caller sees exactly what a direct call would have raised.
        except BaseException as exc:
            outcome.append(exc)

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    thread.join(timeout)
    return (True, outcome[0]) if outcome else (False, None)


def sign_in(
    app: SupportsInteractiveSignIn, broker: bool, timeout: Optional[float] = None
) -> Optional[dict[str, Any]]:
    """Run one interactive sign-in. Returns MSAL's result, or `None` when a
    brokered attempt failed -- or never answered -- in a way a browser attempt
    might survive.

    `timeout` defaults to `BROKER_TIMEOUT`, but is read here rather than
    written as the default argument, which would freeze the value at import
    and put it beyond the reach of anything -- a test, a future option --
    wanting to say otherwise."""
    timeout = BROKER_TIMEOUT if timeout is None else timeout
    print(
        "Signing in through the system account manager..."
        if broker
        else "Opening a browser to sign in...",
        file=sys.stderr,
        flush=True,
    )

    def attempt() -> dict[str, Any]:
        return app.acquire_token_interactive(
            SCOPES,
            # A console program has no window of its own to parent the broker's
            # dialog to, and this constant is how MSAL is told so. The browser
            # path ignores it.
            parent_window_handle=msal.PublicClientApplication.CONSOLE_WINDOW_HANDLE,
        )

    # A browser sign-in blocks for as long as the sign-in page is open, which is
    # the user's own time and not something to cut short; and it has nothing to
    # fall back to, so its exceptions belong to the caller. Only the broker is
    # put on a clock.
    if not broker:
        return attempt()

    finished, outcome = call_within(attempt, timeout)
    if not finished:
        print(
            f"  the account manager never answered ({timeout:.0f}s); abandoning it.",
            file=sys.stderr,
        )
        return None
    # The broker reports trouble as any of several exception types, and any
    # of them means the same thing here: try the browser instead.
    if isinstance(outcome, BaseException):
        print(f"  the account manager declined ({outcome}).", file=sys.stderr)
        return None
    if "access_token" not in outcome:
        print(
            "  the account manager could not complete the sign-in "
            f"({outcome.get('error_description') or outcome.get('error')}).",
            file=sys.stderr,
        )
        return None
    return outcome


def acquire_token(
    client_id: str, tenant: str, cache_path: Path, broker: bool = False
) -> str:
    """Sign in (or reuse a cached sign-in) and return a Graph access token."""
    cache = msal.SerializableTokenCache()
    if cache_path.exists():
        try:
            cache.deserialize(cache_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            # A corrupt cache is not worth failing over; just sign in again.
            pass

    # MSAL ANDs each of its `enable_broker_on_*` arguments with the platform
    # that argument names, so asking for a broker anywhere else yields an
    # unbrokered client *quietly* -- no `ImportError`, nothing to notice. Ask
    # only where the answer can be yes, so that `broker` below keeps saying
    # what this sign-in is actually doing; a flag that drifts from MSAL's own
    # state would mislabel the browser as the account manager and, worse, read
    # a cancelled browser sign-in as a broker refusal worth retrying.
    broker = broker and sys.platform in ("win32", "darwin")

    try:
        app = build_app(client_id, tenant, cache, broker)
    except ImportError:
        # The `msal[broker]` extra is not installed. This project installs it
        # on Windows only, so macOS arrives here as a matter of course.
        broker = False
        app = build_app(client_id, tenant, cache, broker)

    result = None
    accounts = app.get_accounts()
    if accounts:
        result = app.acquire_token_silent(SCOPES, account=accounts[0])

    # A browser sign-in that raises has nothing left to try, and `sign_in` lets
    # it through rather than papering over it. Report it the way every other
    # sign-in failure is reported, instead of as a traceback.
    try:
        if not result:
            result = sign_in(app, broker)
        if not result and broker:
            # The broker was there and said no. Retry the whole sign-in through
            # the browser, on a client built without it.
            print("  falling back to the browser.", file=sys.stderr)
            app = build_app(client_id, tenant, cache, False)
            result = sign_in(app, False)
    except Exception as exc:
        sys.exit(f"Sign-in failed: {exc}")

    if not result or "access_token" not in result:
        details = result or {}
        sys.exit(
            "Sign-in failed: "
            f"{details.get('error_description') or details.get('error') or details}"
        )

    if cache.has_state_changed:
        cache_path.write_text(cache.serialize(), encoding="utf-8")
        try:
            cache_path.chmod(0o600)
        except OSError:
            # Windows ACLs may refuse this; the file still lives in the user
            # profile, so this is hardening rather than a requirement.
            pass

    return result["access_token"]


# Graph access
# ------------
class Graph:
    """A minimal Graph client that pages and survives throttling."""

    def __init__(self, token: str, verbose: bool = False) -> None:
        self.session = requests.Session()
        self.session.headers["Authorization"] = f"Bearer {token}"
        self.verbose = verbose

    def get(self, url: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        if not url.startswith("http"):
            url = GRAPH + url
        # Graph throttles message endpoints aggressively, so honor
        # `Retry-After` and back off on transient server errors.
        for attempt in range(6):
            response = self.session.get(url, params=params, timeout=60)
            if response.status_code in (429, 503, 504):
                delay = int(response.headers.get("Retry-After", 2**attempt))
                if self.verbose:
                    print(
                        f"  throttled ({response.status_code}); retrying in {delay}s",
                        file=sys.stderr,
                    )
                time.sleep(delay)
                continue
            if not response.ok:
                sys.exit(
                    f"Graph request failed ({response.status_code}) for {url}:\n"
                    f"{response.text[:2000]}"
                )
            return response.json()
        sys.exit(f"Graph kept throttling {url}; giving up.")

    def paged(
        self, url: str, params: dict[str, Any] | None = None
    ) -> Iterator[dict[str, Any]]:
        """Yield every item across every page of a Graph collection."""
        page = 0
        while url:
            payload = self.get(url, params)
            page += 1
            items = payload.get("value", [])
            if self.verbose:
                print(f"  page {page}: {len(items)} item(s)", file=sys.stderr)
            yield from items
            url = payload.get("@odata.nextLink", "")
            # A `nextLink` already carries its own query string.
            params = None


# Name resolution
# ---------------
def resolve_team(graph: Graph, wanted: str) -> tuple[str, str]:
    """Turn a team name (or ID) into an `(id, displayName)` pair."""
    if GUID_RE.match(wanted):
        team = graph.get(f"/teams/{wanted}")
        return team["id"], team.get("displayName", wanted)

    teams = list(graph.paged("/me/joinedTeams"))
    return _pick(teams, wanted, "team")


def resolve_channel(graph: Graph, team_id: str, wanted: str) -> tuple[str, str]:
    """Turn a channel name (or ID) into an `(id, displayName)` pair."""
    if CHANNEL_ID_RE.match(wanted):
        channel = graph.get(f"/teams/{team_id}/channels/{wanted}")
        return channel["id"], channel.get("displayName", wanted)

    channels = list(graph.paged(f"/teams/{team_id}/channels"))
    return _pick(channels, wanted, "channel")


def _pick(items: list[dict[str, Any]], wanted: str, kind: str) -> tuple[str, str]:
    """Match `wanted` against the display names of `items` -- exactly, then
    case-insensitively, then as a substring -- failing loudly, and listing the
    choices, when that is ambiguous or finds nothing."""
    names = [item.get("displayName") or "" for item in items]
    for predicate in (
        lambda n: n == wanted,
        lambda n: n.casefold() == wanted.casefold(),
        lambda n: wanted.casefold() in n.casefold(),
    ):
        matches = [item for item, name in zip(items, names) if predicate(name)]
        if len(matches) == 1:
            return matches[0]["id"], matches[0].get("displayName", wanted)
        if len(matches) > 1:
            choices = "\n".join(f"  - {m.get('displayName')}" for m in matches)
            sys.exit(f"{wanted!r} matches more than one {kind}:\n{choices}")

    choices = "\n".join(f"  - {n}" for n in sorted(names)) or "  (none found)"
    sys.exit(f"No {kind} named {wanted!r}. Available:\n{choices}")


# Message retrieval
# -----------------
class SupportsPaging(Protocol):
    """The one slice of `Graph` that `fetch_thread` actually needs. Declaring
    the dependency structurally, rather than as `Graph` itself, is what lets
    the tests drive `fetch_thread` with a stub that never touches the network."""

    def paged(
        self, url: str, params: dict[str, Any] | None = None
    ) -> Iterator[dict[str, Any]]: ...


def fetch_thread(
    graph: SupportsPaging, team_id: str, channel_id: str, verbose: bool
) -> Iterator[dict[str, Any]]:
    """Yield every message in the channel -- root posts and their replies --
    with each message tagged by the thread it belongs to."""
    base = f"/teams/{team_id}/channels/{channel_id}/messages"
    for root in graph.paged(base, {"$top": PAGE_SIZE, "$expand": "replies"}):
        replies = root.pop("replies", None) or []
        # Graph truncates the inline `replies` expansion on long threads, so
        # re-fetch anything near the cap through the paged replies endpoint.
        if len(replies) >= REPLY_WATERMARK:
            if verbose:
                print(
                    f"  thread {root['id']} has {len(replies)} inline replies; "
                    "re-fetching in full",
                    file=sys.stderr,
                )
            replies = list(
                graph.paged(f"{base}/{root['id']}/replies", {"$top": PAGE_SIZE})
            )

        root["_thread_id"] = root["id"]
        root["_is_reply"] = False
        yield root
        for reply in replies:
            reply["_thread_id"] = root["id"]
            reply["_is_reply"] = True
            yield reply


# Filtering and formatting
# ------------------------
def parse_graph_time(value: str) -> datetime:
    """Parse a Graph timestamp. Graph sometimes emits seven fractional digits,
    which `fromisoformat` rejects, so trim to microseconds first."""
    text = re.sub(r"\.(\d{6})\d+", r".\1", value.replace("Z", "+00:00"))
    stamp = datetime.fromisoformat(text)
    return stamp if stamp.tzinfo else stamp.replace(tzinfo=timezone.utc)


def parse_boundary(value: str, tz: Any, end_of_day: bool) -> datetime:
    """Parse `--start`/`--end` into an aware UTC instant. A bare date means the
    whole of that local day, which is what makes `--end` inclusive; a full
    timestamp is taken literally."""
    try:
        stamp = datetime.fromisoformat(value)
    except ValueError:
        raise SystemExit(
            f"Cannot read {value!r} as a date. Use YYYY-MM-DD or an ISO 8601 "
            "timestamp such as 2026-09-08T14:30."
        ) from None
    bare_date = "T" not in value and " " not in value
    if bare_date and end_of_day:
        stamp += timedelta(days=1) - timedelta(microseconds=1)
    if stamp.tzinfo is None:
        stamp = stamp.replace(tzinfo=tz)
    return stamp.astimezone(timezone.utc)


def author_of(message: dict[str, Any]) -> str:
    """The display name a message should be credited to."""
    sender = message.get("from") or {}
    for key in ("user", "application", "device"):
        identity = sender.get(key) or {}
        if identity.get("displayName"):
            return identity["displayName"]
    if message.get("messageType") != "message":
        return "(system)"
    return "(unknown)"


def body_html(message: dict[str, Any]) -> str:
    """The message body as HTML. Teams bodies are usually HTML already; plain
    text bodies are escaped and wrapped so the column is uniformly HTML."""
    body = message.get("body") or {}
    content = body.get("content") or ""
    if body.get("contentType") == "text":
        return f"<p>{html.escape(content)}</p>"
    return content


def keep(
    message: dict[str, Any],
    start: datetime,
    end: datetime,
    include_system: bool,
    include_deleted: bool,
) -> bool:
    """Should this message appear in the export?"""
    if message.get("deletedDateTime") and not include_deleted:
        return False
    if message.get("messageType") != "message" and not include_system:
        return False
    created = parse_graph_time(message["createdDateTime"])
    return start <= created <= end


# Output
# ------
def write_json(
    path: Path, messages: list[dict[str, Any]], meta: dict[str, Any]
) -> None:
    """Write the step 1 archive: the raw Graph records, plus what produced them."""
    payload = {"exported": meta, "messages": messages}
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def write_csv(path: Path, messages: list[dict[str, Any]], tz: Any) -> None:
    """Write the step 2 CSV: timestamp, user name, and HTML of the chat."""
    # `utf-8-sig` so that Excel recognizes the encoding on a double-click, and
    # `newline=""` so that the csv module controls line endings itself.
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["timestamp", "user", "html"])
        for message in messages:
            local = parse_graph_time(message["createdDateTime"]).astimezone(tz)
            writer.writerow([local.isoformat(), author_of(message), body_html(message)])


# Command line
# ------------
#
# One Typer command, collapsed to a bare command line because the app defines
# only one. `Annotated` carries each option's help text next to its type, so
# the signature is the whole interface.
app = typer.Typer(
    add_completion=False,
    context_settings={"help_option_names": ["-h", "--help"]},
)


@app.command(
    epilog="""Example: teams-export --team "CSE 4283 Fall 2026" --channel General
--start 2026-09-01 --end 2026-09-14 --out chats -- which writes chats.json
(full Graph records) and chats.csv (timestamp, user, html)."""
)
def export(
    team: Annotated[
        str, typer.Option(help="Team display name or ID.", show_default=False)
    ],
    channel: Annotated[
        str, typer.Option(help="Channel display name or ID.")
    ] = "General",
    start: Annotated[
        Optional[str],
        typer.Option(
            help="First day, YYYY-MM-DD, inclusive. A full ISO 8601 timestamp "
            "slices more finely.",
            show_default="one week ago",
        ),
    ] = None,
    end: Annotated[
        Optional[str],
        typer.Option(
            help="Last day, YYYY-MM-DD, inclusive. A full ISO 8601 timestamp "
            "slices more finely.",
            show_default="now",
        ),
    ] = None,
    out: Annotated[
        Path,
        typer.Option(help="Output path; '.json' and '.csv' are appended."),
    ] = Path("chats"),
    tz: Annotated[
        Optional[str],
        typer.Option(
            help="IANA time zone used to read --start/--end and to write the "
            "CSV timestamps.  [default: this machine's local time zone]",
            show_default=False,
        ),
    ] = None,
    replies: Annotated[
        bool,
        typer.Option(
            "--replies/--no-replies",
            help="Export threaded replies as rows of their own, or only "
            "top-level posts.",
        ),
    ] = True,
    # Naming the flag explicitly keeps Typer from also generating a
    # ``--no-include-system`` that no one would ever pass.
    include_system: Annotated[
        bool,
        typer.Option(
            "--include-system",
            help="Also export join/leave and other system event messages.",
        ),
    ] = False,
    include_deleted: Annotated[
        bool,
        typer.Option(
            "--include-deleted",
            help="Also export deleted messages; their bodies are usually empty.",
        ),
    ] = False,
    tenant: Annotated[
        str,
        typer.Option(
            help="Tenant to sign in to: 'organizations', or your tenant ID/domain."
        ),
    ] = "organizations",
    broker: Annotated[
        bool,
        typer.Option(
            "--broker/--no-broker",
            help="Try the operating system's account manager before the "
            "browser. Off by default: it cannot authenticate against a "
            "federated tenant, and takes "
            f"{BROKER_TIMEOUT:.0f}s to give up when it cannot.",
        ),
    ] = False,
    token_cache: Annotated[
        Path, typer.Option(help="Where to cache the sign-in.")
    ] = DEFAULT_CACHE,
    # Documented rather than hidden, because the one tenant that needs it is
    # the one whose administrator has refused consent for the default client,
    # and nothing else in the tool's output would then point the way out.
    client_id: Annotated[
        str,
        typer.Option(
            help="Public client to sign in as. The default is Microsoft's own "
            "pre-consented Graph CLI client; override it with a public client "
            "registered in your tenant if that one is blocked.",
            show_default="the Graph CLI client",
        ),
    ] = DEFAULT_CLIENT_ID,
    verbose: Annotated[
        bool, typer.Option("--verbose", "-v", help="Report progress on stderr.")
    ] = False,
) -> None:
    """Export a Microsoft Teams channel's chat history over a date range to
    JSON and CSV."""
    # Validate the options against each other before signing in, so that a
    # typo costs nothing. `BadParameter` names the offending option and prints
    # the usage line, which a bare message would not.
    try:
        zone = ZoneInfo(tz) if tz else datetime.now().astimezone().tzinfo
    except (ZoneInfoNotFoundError, ValueError):
        raise typer.BadParameter(
            f"Unknown time zone {tz!r}. Use an IANA name, e.g. America/Chicago.",
            param_hint="--tz",
        )
    # The default range is the week ending now. Both defaults are full
    # timestamps, so `parse_boundary` takes them literally rather than widening
    # them to whole local days.
    now = datetime.now(zone)
    if start is None:
        start = (now - timedelta(days=7)).isoformat()
    if end is None:
        end = now.isoformat()
    first = parse_boundary(start, zone, end_of_day=False)
    last = parse_boundary(end, zone, end_of_day=True)
    if last < first:
        raise typer.BadParameter(
            f"{end} falls before --start ({start}).", param_hint="--end"
        )

    token = acquire_token(client_id, tenant, token_cache, broker)
    graph = Graph(token, verbose=verbose)

    team_id, team_name = resolve_team(graph, team)
    channel_id, channel_name = resolve_channel(graph, team_id, channel)
    typer.echo(f"Exporting {team_name} / {channel_name}", err=True)
    typer.echo(
        f"  {first.astimezone(zone).isoformat()} .. {last.astimezone(zone).isoformat()}",
        err=True,
    )

    # Graph orders channel messages by last modification, not creation, and
    # offers no server-side date filter on this endpoint -- so page the whole
    # channel and filter locally. A class channel is small enough that this is
    # both fast and, unlike an early exit, always correct.
    seen = 0
    kept: list[dict[str, Any]] = []
    for message in fetch_thread(graph, team_id, channel_id, verbose):
        seen += 1
        if not replies and message["_is_reply"]:
            continue
        if keep(message, first, last, include_system, include_deleted):
            kept.append(message)

    kept.sort(key=lambda m: parse_graph_time(m["createdDateTime"]))

    json_path = out.with_suffix(".json")
    csv_path = out.with_suffix(".csv")
    write_json(
        json_path,
        kept,
        {
            "team": {"id": team_id, "displayName": team_name},
            "channel": {"id": channel_id, "displayName": channel_name},
            "start": first.isoformat(),
            "end": last.isoformat(),
            "timeZone": str(zone),
            "generatedAt": datetime.now(timezone.utc).isoformat(),
            "messagesScanned": seen,
            "messagesExported": len(kept),
        },
    )
    write_csv(csv_path, kept, zone)

    authors = sorted({author_of(m) for m in kept})
    typer.echo(
        f"Scanned {seen} message(s); exported {len(kept)} "
        f"from {len(authors)} author(s).",
        err=True,
    )
    typer.echo(f"  {json_path}\n  {csv_path}", err=True)


def main() -> None:
    """The ``teams-export`` console script."""
    app()


if __name__ == "__main__":
    main()
