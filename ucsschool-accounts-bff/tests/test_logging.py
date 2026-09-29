# SPDX-FileCopyrightText: 2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
"""The default log format must stay parsable by the published log-format regex."""

from __future__ import annotations

import json
import logging
import pickle
import re
import time
from collections.abc import Iterator
from datetime import datetime, timezone
from typing import TYPE_CHECKING

import pytest
from loguru import logger
from port_loader.adapters import EnvSettingsProvider
from typing_extensions import override

from ucsschool_accounts_bff.logging import (
    DATA_SEPARATOR,
    LOG_FORMAT,
    InterceptHandler,
    LogLevel,
    _boolean_setting,
    _log_level,
    _patch_json_record,
    _patch_text_record,
)

if TYPE_CHECKING:
    from loguru import Record

SPEC_LOG_LINE_REGEX = re.compile(
    r"^(?P<date>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3,6}\+\d{2}:?\d{2}) +"
    r"(?P<level>\w+?) +\[(?P<request_id>.*?)\] (?P<message>.+?)\t\| (?P<data>.*?)$"
)


# ``logger.configure`` would install the patcher process-wide, and loguru cannot restore
# the previous one.
log = logger.patch(_patch_text_record)
structured_log = logger.patch(_patch_json_record)


@pytest.fixture
def lines() -> Iterator[list[str]]:
    """Collect what ``log`` renders, and take the sink back down again.

    Scoped to this module so that a record from elsewhere cannot reach a format
    string that expects the fields the patcher adds.
    """
    collected: list[str] = []
    sink_id = logger.add(
        collected.append, format=LOG_FORMAT, colorize=False, level="TRACE", filter=__name__
    )
    try:
        yield collected
    finally:
        logger.remove(sink_id)


@pytest.fixture
def json_lines() -> Iterator[list[str]]:
    """Collect what ``structured_log`` renders, the shape the JSON setting selects."""
    collected: list[str] = []
    sink_id = logger.add(
        collected.append, format="{message}", serialize=True, level="TRACE", filter=__name__
    )
    try:
        yield collected
    finally:
        logger.remove(sink_id)


def parse(line: str) -> re.Match[str]:
    match = SPEC_LOG_LINE_REGEX.match(line.rstrip("\n"))
    assert match is not None, f"not parsable as a log line: {line!r}"
    return match


LOGFMT_PAIR = re.compile(r'(?P<key>[^\s=]+)=(?P<value>"(?:[^"\\]|\\.)*"|\S+)')


def data_fields(line: str) -> dict[str, object]:
    return {pair["key"]: json.loads(pair["value"]) for pair in LOGFMT_PAIR.finditer(parse(line)["data"])}


def test_every_level_renders_a_parsable_line(lines: list[str]):
    for level in ("trace", "debug", "info", "warning", "error", "critical"):
        getattr(log, level)("An event happened.")
    assert len(lines) == 6
    assert [parse(line)["level"] for line in lines] == [
        "TRACE",
        "DEBUG",
        "INFO",
        "WARNING",
        "ERROR",
        "CRITICAL",
    ]


@pytest.mark.parametrize(
    "context,column,field",
    [
        ({"correlation_id": "31f863092ade1cb"}, "31f863092a", "31f863092ade1cb"),
        ({}, "-".rjust(10), "-"),
        ({"correlation_id": "a] forged"}, "a__forged".rjust(10), "a__forged"),
    ],
    ids=["present", "absent", "forged"],
)
def test_the_request_id_column_is_derived_from_the_correlation_id(
    lines: list[str], context: dict[str, str], column: str, field: str
):
    """The id is whatever the client put in ``X-Request-ID``, so it is not ours to trust."""
    with log.contextualize(**context):
        log.info("An event happened.")
    assert parse(lines[0])["request_id"] == column
    assert data_fields(lines[0])["request_id"] == field


def test_keyword_arguments_become_the_data_section(lines: list[str]):
    log.info("An event happened.", school="DEMOSCHOOL", count=3, missing=None)
    fields = data_fields(lines[0])
    assert fields["school"] == "DEMOSCHOOL"
    assert fields["count"] == 3
    assert fields["missing"] is None
    assert fields["module"] == __name__
    assert isinstance(fields["line"], int)
    assert isinstance(fields["pid"], int)


def test_a_message_cannot_break_the_line_apart(lines: list[str]):
    log.info(f"First{DATA_SEPARATOR}second\nthird\rfourth\tfifth")
    match = parse(lines[0])
    assert match["message"] == "First\\t| second\\nthird\\rfourth\\tfifth"
    assert match["data"].startswith("module=")


def test_the_timestamp_stays_parsable_where_the_host_is_behind_utc(
    lines: list[str], monkeypatch: pytest.MonkeyPatch
):
    """The published parsing regex accepts a positive offset only."""
    monkeypatch.setenv("TZ", "America/New_York")
    time.tzset()
    try:
        log.info("An event happened.")
    finally:
        monkeypatch.undo()
        time.tzset()
    assert parse(lines[0])["date"].endswith("+00:00")


def test_the_rendered_line_leaves_nothing_behind_that_a_queue_cannot_carry(lines: list[str]):
    """``enqueue=True`` pickles the record once the sink has formatted it."""
    captured: list[Record] = []
    sink_id = logger.add(lambda message: captured.append(message.record), level="TRACE", filter=__name__)
    try:
        log.info("An event happened.", odd=lambda: 1)
    finally:
        logger.remove(sink_id)
    assert set(captured[0]["extra"]) == {"request_id", "data"}
    pickle.dumps(captured[0]["extra"])
    assert str(data_fields(lines[0])["odd"]).startswith("<function")


class Hostile:
    # Module level so that the queue behind ``enqueue=True`` can still pickle it.
    @override
    def __str__(self) -> str:
        raise RuntimeError("cannot stringify")

    @override
    def __repr__(self) -> str:
        raise RuntimeError("cannot repr either")


@pytest.mark.parametrize(
    "odd,expected",
    [
        (datetime(2026, 9, 23, tzinfo=timezone.utc), "2026-09-23 00:00:00+00:00"),
        ({(1, 2): "x"}, "{(1, 2): 'x'}"),
        (Hostile(), "<unrenderable Hostile>"),
    ],
    ids=["stringable", "unencodable", "unrenderable"],
)
def test_a_value_the_encoder_chokes_on_does_not_lose_the_line(
    lines: list[str], odd: object, expected: str
):
    log.info("An event happened.", odd=odd)
    assert data_fields(lines[0])["odd"] == expected


def test_an_intercepted_message_is_not_taken_for_a_format_string():
    """uvicorn logs dicts and JSON bodies, and loguru formats a message that carries kwargs."""
    collected: list[str] = []
    sink_id = logger.add(collected.append, level="TRACE", format="{message}")
    intercepted = logging.getLogger("test-intercept")
    intercepted.handlers = [InterceptHandler()]
    intercepted.setLevel(logging.INFO)
    try:
        intercepted.info('payload {"a": 1} received')
    finally:
        logger.remove(sink_id)
        intercepted.handlers = []
    assert collected[0].rstrip() == 'payload {"a": 1} received'


def test_the_record_keeps_the_field_names_it_derives_itself(lines: list[str]):
    """The record wins, a keyword argument does not."""
    log.info("An event happened.", module="kelvin", line="L1", pid="none", request_id="forged")
    fields = data_fields(lines[0])
    assert fields["module"] == __name__
    assert isinstance(fields["line"], int)
    assert fields["request_id"] == "-"


def test_the_json_shape_keeps_the_request_id_as_the_header_carries_it(json_lines: list[str]):
    """Only the text format needs the id sanitized; JSON escaping keeps the record intact."""
    with structured_log.contextualize(correlation_id="abc/def="):
        structured_log.info("An event happened.")
    extra = json.loads(json_lines[0])["record"]["extra"]
    assert extra == {"request_id": "abc/def="}


def test_the_json_shape_shows_control_and_invisible_characters(json_lines: list[str]):
    """JSON leaves anything from U+0080 up raw, and a terminal may act on it."""
    with structured_log.contextualize(correlation_id="id\u202e"):
        structured_log.info("Grüße\x9b", errors=[{"input": "\u200bghost"}], count=3)
    record = json.loads(json_lines[0])["record"]
    assert record["message"] == "Grüße\\x9b"
    assert record["extra"] == {
        "errors": [{"input": "\\u200bghost"}],
        "count": 3,
        "request_id": "id\\u202e",
    }


@pytest.mark.parametrize("odd", [{(1, 2): "x"}, Hostile()])
def test_the_json_shape_survives_a_value_json_cannot_encode(json_lines: list[str], odd: object):
    """loguru encodes the record itself here, and would drop it whole over one value."""
    structured_log.info("An event happened.", odd=odd)
    assert json.loads(json_lines[0])["record"]["extra"]["request_id"] == "-"


@pytest.mark.parametrize(
    "requested,expected",
    [
        ("debug", LogLevel.DEBUG),
        (" WARNING ", LogLevel.WARNING),
        ("", LogLevel.INFO),
        ("WARN", LogLevel.INFO),
    ],
)
def test_the_log_level_falls_back_to_info_rather_than_failing_the_startup(
    requested: str, expected: LogLevel
):
    assert _log_level(requested) is expected


@pytest.mark.asyncio
@pytest.mark.parametrize("value,expected", [("1", True), ("", False)])
async def test_an_unusable_switch_stays_off_rather_than_failing_the_startup(
    value: str, expected: bool, monkeypatch: pytest.MonkeyPatch
):
    """An unset UCR variable reaches the container as an empty string, which is no boolean."""
    monkeypatch.setenv("UCSSCHOOL_ACCOUNTS__LOGGING__STRUCTURED", value)
    assert (
        await _boolean_setting(EnvSettingsProvider(), "ucsschool_accounts.logging.structured")
        is expected
    )
