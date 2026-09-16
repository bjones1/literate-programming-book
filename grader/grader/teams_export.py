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
# Authentication uses the OAuth 2.0 device code flow against a delegated
# (sign-in-as-yourself) Graph session, so it sees exactly the channels you can
# already see in the Teams client. No Azure app registration is required: the
# default client ID below is Microsoft's own pre-registered, pre-consented
# "Microsoft Graph Command Line Tools" public client.
"""Export a Microsoft Teams channel's chat history to JSON and CSV.

See README.md in this directory for setup and usage.
"""

from __future__ import annotations

import csv
import html
import json
import re
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Annotated, Any, Iterator, Optional, Protocol
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

try:
    import msal
    import requests
    import typer
except ModuleNotFoundError as exc:  # pragma: no cover - setup guidance only.
    sys.exit(
        f"Missing dependency {exc.name!r}. Install this project's dependencies "
        "first:\n    poetry install"
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

# Team IDs are GUIDs; channel IDs are not, and look like
# `19:abc...def@thread.tacv2`. Recognizing both lets the same option accept
# either a display name or an ID.
GUID_RE = re.compile(r"^[0-9a-fA-F]{8}-(?:[0-9a-fA-F]{4}-){3}[0-9a-fA-F]{12}$")
CHANNEL_ID_RE = re.compile(r"^19:[^@]+@thread\.\w+$")


# Authentication
# --------------
def acquire_token(client_id: str, tenant: str, cache_path: Path) -> str:
    """Sign in (or reuse a cached sign-in) and return a Graph access token."""
    cache = msal.SerializableTokenCache()
    if cache_path.exists():
        try:
            cache.deserialize(cache_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            # A corrupt cache is not worth failing over; just sign in again.
            pass

    app = msal.PublicClientApplication(
        client_id,
        authority=f"https://login.microsoftonline.com/{tenant}",
        token_cache=cache,
    )

    result = None
    accounts = app.get_accounts()
    if accounts:
        result = app.acquire_token_silent(SCOPES, account=accounts[0])

    if not result:
        flow = app.initiate_device_flow(scopes=SCOPES)
        if "user_code" not in flow:
            sys.exit(
                "Could not start device code sign-in: "
                f"{flow.get('error_description', flow)}"
            )
        # Prompt on stderr so that stdout stays clean for piping.
        print(flow["message"], file=sys.stderr, flush=True)
        result = app.acquire_token_by_device_flow(flow)

    if "access_token" not in result:
        sys.exit(
            "Sign-in failed: "
            f"{result.get('error_description') or result.get('error') or result}"
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
                        f"  throttled ({response.status_code}); "
                        f"retrying in {delay}s",
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
    token_cache: Annotated[
        Path, typer.Option(help="Where to cache the sign-in.")
    ] = DEFAULT_CACHE,
    client_id: Annotated[str, typer.Option(hidden=True)] = DEFAULT_CLIENT_ID,
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

    token = acquire_token(client_id, tenant, token_cache)
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
