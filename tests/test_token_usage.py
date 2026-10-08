"""Tests for the per-request token usage report. AAA pattern per CLAUDE.md."""

import pytest

from src.scripts.token_usage import Request, iter_requests, price, rate_for


def assistant_row(request_id, model="claude-opus-5", output_tokens=100):
    return {
        "type": "assistant",
        "requestId": request_id,
        "sessionId": "session-1",
        "timestamp": "2026-10-08T18:00:00.000Z",
        "message": {
            "model": model,
            "usage": {
                "input_tokens": 10,
                "output_tokens": output_tokens,
                "cache_read_input_tokens": 27_023,
                "cache_creation": {
                    "ephemeral_5m_input_tokens": 0,
                    "ephemeral_1h_input_tokens": 8_783,
                },
                "output_tokens_details": {"thinking_tokens": 311},
            },
        },
    }


def test_collapses_repeated_rows_sharing_one_request_id():
    # Arrange — one API request emitted as three content-block rows
    rows = [assistant_row("req_A"), assistant_row("req_A"), assistant_row("req_A")]

    # Act
    requests = iter_requests(rows)

    # Assert
    assert len(requests) == 1
    assert requests[0].output_tokens == 100


def test_counts_distinct_request_ids_separately():
    # Arrange
    rows = [assistant_row("req_A"), assistant_row("req_B")]

    # Act
    requests = iter_requests(rows)

    # Assert
    assert {r.request_id for r in requests} == {"req_A", "req_B"}


@pytest.mark.parametrize(
    "row",
    [
        {"type": "user", "requestId": "req_A", "message": {"usage": {}}},
        {"type": "assistant", "requestId": "req_A", "message": {}},
        {"type": "assistant", "message": {"usage": {"input_tokens": 5}}},
    ],
)
def test_ignores_rows_without_usable_usage(row):
    # Arrange — row supplied by parametrize

    # Act
    requests = iter_requests([row])

    # Assert
    assert requests == []


def test_extracts_cache_and_thinking_token_fields():
    # Arrange
    rows = [assistant_row("req_A")]

    # Act
    request = iter_requests(rows)[0]

    # Assert
    assert request.cache_read_tokens == 27_023
    assert request.cache_write_1h_tokens == 8_783
    assert request.thinking_tokens == 311


def test_billable_input_sums_fresh_and_cache_tokens():
    # Arrange
    request = Request(
        request_id="req_A",
        session_id="s",
        timestamp="t",
        model="claude-opus-5",
        input_tokens=10,
        output_tokens=0,
        thinking_tokens=0,
        cache_read_tokens=100,
        cache_write_5m_tokens=1_000,
        cache_write_1h_tokens=10_000,
    )

    # Act
    billable = request.billable_input_tokens

    # Assert
    assert billable == 11_110


@pytest.mark.parametrize(
    ("model", "expected"),
    [
        ("claude-opus-5", (5.00, 25.00)),
        ("claude-opus-5[1m]", (5.00, 25.00)),
        ("claude-haiku-4-5-20251001", (1.00, 5.00)),
        ("claude-sonnet-4-6", (3.00, 15.00)),
        ("claude-sonnet-5", (2.00, 10.00)),
    ],
)
def test_resolves_rate_for_dated_and_suffixed_model_ids(model, expected):
    # Arrange — model supplied by parametrize

    # Act
    rate = rate_for(model)

    # Assert
    assert rate == expected


def test_unknown_model_has_no_rate_and_no_price():
    # Arrange
    request = Request(
        request_id="req_A",
        session_id="s",
        timestamp="t",
        model="some-future-model",
        input_tokens=1_000,
        output_tokens=1_000,
        thinking_tokens=0,
        cache_read_tokens=0,
        cache_write_5m_tokens=0,
        cache_write_1h_tokens=0,
    )

    # Act
    cost = price(request)

    # Assert
    assert rate_for("some-future-model") is None
    assert cost is None


def test_prices_cache_tokens_at_their_own_multipliers():
    # Arrange — 1M of every token class on a $5/$25 model.
    # 5.00 input + 0.50 cache read + 6.25 write-5m + 10.00 write-1h + 25.00 output
    request = Request(
        request_id="req_A",
        session_id="s",
        timestamp="t",
        model="claude-opus-5",
        input_tokens=1_000_000,
        output_tokens=1_000_000,
        thinking_tokens=0,
        cache_read_tokens=1_000_000,
        cache_write_5m_tokens=1_000_000,
        cache_write_1h_tokens=1_000_000,
    )

    # Act
    cost = price(request)

    # Assert
    assert cost == pytest.approx(46.75)
