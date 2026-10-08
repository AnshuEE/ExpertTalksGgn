#!/usr/bin/env python3
"""Report input/output token spend per Claude Code request.

Reads the session transcripts Claude Code writes to
``~/.claude/projects/<slug>/<session-id>.jsonl`` and reports tokens and
estimated cost per API request, per session, and per model.

Two things here are easy to get wrong:

1. A single API request emits *several* assistant rows — one per content block —
   each repeating the same ``usage`` object. Counting rows instead of distinct
   ``requestId`` values inflates every figure (measured ~2.7x on a sample
   session). ``iter_requests`` deduplicates on ``requestId``.
2. One session can span several models. Rates are per-model, so a blended
   rate is wrong; ``price`` resolves the rate by longest-prefix match so dated
   and ``[1m]`` model ids land on the right row.

Costs are estimates from public list prices, not an invoice.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

PROJECTS_DIR = Path.home() / ".claude" / "projects"

# USD per million tokens, keyed by model-id prefix. Longest prefix wins.
RATES: dict[str, tuple[float, float]] = {
    "claude-fable-5": (10.00, 50.00),
    "claude-mythos-5": (10.00, 50.00),
    "claude-opus-5": (5.00, 25.00),
    "claude-opus-4": (5.00, 25.00),
    "claude-sonnet-5": (2.00, 10.00),
    "claude-sonnet-4-6": (3.00, 15.00),
    "claude-haiku-4-5": (1.00, 5.00),
}

# Cache tokens are billed as multiples of the model's base input rate.
CACHE_READ_MULTIPLIER = 0.10
CACHE_WRITE_5M_MULTIPLIER = 1.25
CACHE_WRITE_1H_MULTIPLIER = 2.00


@dataclass(frozen=True)
class Request:
    """One API request, after deduplicating the rows that share its id."""

    request_id: str
    session_id: str
    timestamp: str
    model: str
    input_tokens: int
    output_tokens: int
    thinking_tokens: int
    cache_read_tokens: int
    cache_write_5m_tokens: int
    cache_write_1h_tokens: int

    @property
    def billable_input_tokens(self) -> int:
        return (
            self.input_tokens
            + self.cache_read_tokens
            + self.cache_write_5m_tokens
            + self.cache_write_1h_tokens
        )


def rate_for(model: str) -> tuple[float, float] | None:
    """Return (input, output) USD-per-Mtok for a model id, or None if unknown."""
    matches = [prefix for prefix in RATES if model.startswith(prefix)]
    if not matches:
        return None
    return RATES[max(matches, key=len)]


def price(request: Request) -> float | None:
    """Estimated USD for one request, or None when the model has no known rate."""
    rate = rate_for(request.model)
    if rate is None:
        return None
    input_rate, output_rate = rate
    cost = (
        request.input_tokens * input_rate
        + request.cache_read_tokens * input_rate * CACHE_READ_MULTIPLIER
        + request.cache_write_5m_tokens * input_rate * CACHE_WRITE_5M_MULTIPLIER
        + request.cache_write_1h_tokens * input_rate * CACHE_WRITE_1H_MULTIPLIER
        + request.output_tokens * output_rate
    )
    return cost / 1_000_000


def iter_requests(rows: list[dict]) -> list[Request]:
    """Collapse transcript rows into one Request per distinct requestId."""
    seen: dict[str, Request] = {}
    for row in rows:
        if row.get("type") != "assistant":
            continue
        message = row.get("message") or {}
        usage = message.get("usage")
        request_id = row.get("requestId")
        if not usage or not request_id or request_id in seen:
            continue
        cache_creation = usage.get("cache_creation") or {}
        details = usage.get("output_tokens_details") or {}
        seen[request_id] = Request(
            request_id=request_id,
            session_id=row.get("sessionId", ""),
            timestamp=row.get("timestamp", ""),
            model=message.get("model", "unknown"),
            input_tokens=usage.get("input_tokens", 0),
            output_tokens=usage.get("output_tokens", 0),
            thinking_tokens=details.get("thinking_tokens", 0),
            cache_read_tokens=usage.get("cache_read_input_tokens", 0),
            cache_write_5m_tokens=cache_creation.get("ephemeral_5m_input_tokens", 0),
            cache_write_1h_tokens=cache_creation.get("ephemeral_1h_input_tokens", 0),
        )
    return list(seen.values())


def read_transcript(path: Path) -> list[Request]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return iter_requests(rows)


def project_dir(slug: str | None) -> Path:
    """Resolve the transcript directory for a project slug or the cwd."""
    if slug:
        return PROJECTS_DIR / slug
    encoded = str(Path.cwd()).replace("/", "-")
    return PROJECTS_DIR / encoded


def _fmt_usd(cost: float | None) -> str:
    return "      n/a" if cost is None else f"${cost:>8.4f}"


def _totals(requests: list[Request]) -> tuple[int, int, float]:
    known = [price(r) for r in requests]
    total_cost = sum(c for c in known if c is not None)
    return (
        sum(r.billable_input_tokens for r in requests),
        sum(r.output_tokens for r in requests),
        total_cost,
    )


def report_requests(requests: list[Request]) -> None:
    print(
        f"{'timestamp':<21} {'model':<28} {'in':>9} {'cache_r':>9} "
        f"{'cache_w':>9} {'out':>8} {'think':>7} {'cost':>9}"
    )
    print("-" * 110)
    for request in sorted(requests, key=lambda r: r.timestamp):
        cache_write = request.cache_write_5m_tokens + request.cache_write_1h_tokens
        print(
            f"{request.timestamp[:19]:<21} {request.model:<28} "
            f"{request.input_tokens:>9,} {request.cache_read_tokens:>9,} "
            f"{cache_write:>9,} {request.output_tokens:>8,} "
            f"{request.thinking_tokens:>7,} {_fmt_usd(price(request))}"
        )
    inp, out, cost = _totals(requests)
    print("-" * 110)
    print(
        f"{len(requests)} requests    input(billable) {inp:,}    output {out:,}    est. ${cost:.4f}"
    )


def report_by_model(requests: list[Request]) -> None:
    grouped: dict[str, list[Request]] = defaultdict(list)
    for request in requests:
        grouped[request.model].append(request)

    print(f"{'model':<30} {'reqs':>6} {'in(billable)':>14} {'out':>10} {'cost':>10}")
    print("-" * 74)
    for model, group in sorted(grouped.items()):
        inp, out, cost = _totals(group)
        print(f"{model:<30} {len(group):>6} {inp:>14,} {out:>10,} {_fmt_usd(cost)}")


def report_sessions(directory: Path, limit: int) -> None:
    transcripts = sorted(directory.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not transcripts:
        print(f"No transcripts in {directory}", file=sys.stderr)
        return

    print(f"{'session':<38} {'when':<17} {'reqs':>6} {'in':>12} {'out':>9} {'cost':>10}")
    print("-" * 97)
    grand = 0.0
    for path in transcripts[:limit]:
        requests = read_transcript(path)
        if not requests:
            continue
        inp, out, cost = _totals(requests)
        grand += cost
        when = min(r.timestamp for r in requests)[:16].replace("T", " ")
        print(
            f"{path.stem:<38} {when:<17} {len(requests):>6} {inp:>12,} {out:>9,} {_fmt_usd(cost)}"
        )
    print("-" * 97)
    print(f"{'total':<63} {_fmt_usd(grand)}")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("session", nargs="?", help="session id; omit to list sessions")
    parser.add_argument("--project", help="project slug under ~/.claude/projects")
    parser.add_argument("--by-model", action="store_true", help="group totals by model")
    parser.add_argument("--limit", type=int, default=15, help="sessions to list")
    args = parser.parse_args(argv)

    directory = project_dir(args.project)
    if not directory.is_dir():
        print(f"No such project directory: {directory}", file=sys.stderr)
        return 1

    if args.session is None:
        report_sessions(directory, args.limit)
        return 0

    transcript = directory / f"{args.session}.jsonl"
    if not transcript.is_file():
        print(f"No such session transcript: {transcript}", file=sys.stderr)
        return 1

    requests = read_transcript(transcript)
    if not requests:
        print("No billable requests in that transcript.", file=sys.stderr)
        return 1

    if args.by_model:
        report_by_model(requests)
    else:
        report_requests(requests)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
