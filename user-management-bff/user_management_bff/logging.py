# SPDX-FileCopyrightText: 2023-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
from __future__ import annotations

import json
import logging
import re
import sys
import unicodedata
from enum import StrEnum
from typing import TYPE_CHECKING, Final, cast

import port_loader  # type: ignore[import-not-found]
from loguru import logger
from port_loader import AsyncAdapterSettingsProvider

from .correlation_id import correlation_id_ctx_var

if TYPE_CHECKING:
    from loguru import Record


class LogLevel(StrEnum):
    TRACE = "TRACE"
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


DEFAULT_LOG_LEVEL: Final = LogLevel.INFO

DATA_SEPARATOR: Final = "\t| "

_UNSAFE_IN_REQUEST_ID: Final = re.compile(r"[^A-Za-z0-9._:+-]")

_LINE_ESCAPES: Final = str.maketrans({"\n": "\\n", "\r": "\\r", "\t": "\\t"})

_CONTROL_ESCAPES: Final = str.maketrans(
    {
        chr(code): chr(code).encode("unicode_escape").decode()
        for code in range(0x7F, sys.maxunicode + 1)
        if unicodedata.category(chr(code)) in ("Cc", "Cf")
    }
)

LOG_FORMAT: Final = (
    "<green>{time:YYYY-MM-DDTHH:mm:ss.SSSZ!UTC}</green> <level>{level: <8}</level> "
    "[{extra[request_id]:>10.10}] <level>{message}</level>" + DATA_SEPARATOR + "{extra[data]}"
)


def _logfmt_value(value: object) -> str:
    """Encode one data-section value."""
    try:
        return json.dumps(value, default=str)
    except Exception:
        try:
            return json.dumps(repr(value))
        except Exception:
            return json.dumps(f"<unrenderable {type(value).__name__}>")


def _request_id(extra: dict[str, object]) -> str:
    return _UNSAFE_IN_REQUEST_ID.sub("_", str(extra.get("correlation_id") or "-"))


def _escape_controls(text: str) -> str:
    """Escape the control and invisible characters JSON leaves raw, so a terminal shows them."""
    return text.translate(_CONTROL_ESCAPES)


def _escape_controls_in(value: object) -> object:
    if isinstance(value, str):
        return _escape_controls(value)
    if isinstance(value, list):
        return [_escape_controls_in(item) for item in cast("list[object]", value)]
    if isinstance(value, dict):
        items = cast("dict[object, object]", value).items()
        return {_escape_controls(str(key)): _escape_controls_in(item) for key, item in items}
    return value


def _patch_json_record(record: Record) -> None:
    """Add the ``request_id`` field, and hand loguru's serializer values it can encode.

    Unlike the text format, the id is not replaced: JSON escaping already guards the structure.
    """
    extra: dict[str, object] = record["extra"]
    request_id = str(extra.pop("correlation_id", None) or "-")
    extra.update({key: json.loads(_logfmt_value(value)) for key, value in extra.items()})
    extra.update({key: _escape_controls_in(value) for key, value in extra.items()})
    extra["request_id"] = _escape_controls(request_id)
    record["message"] = _escape_controls(record["message"])


def _data_section(record: Record, request_id: str) -> str:
    """Render the logfmt half of the line: the call's own fields, then the derived ones."""
    extra: dict[str, object] = record["extra"]
    fields = {key: value for key, value in extra.items() if key != "correlation_id"} | {
        "module": record["name"],
        "line": record["line"],
        "pid": record["process"].id,
        "request_id": request_id,
    }
    return " ".join(f"{key}={_logfmt_value(value)}" for key, value in fields.items())


def _patch_text_record(record: Record) -> None:
    """Add the ``request_id`` and ``data`` fields the log format string reads."""
    request_id = _request_id(record["extra"])
    data = _data_section(record, request_id)
    record["extra"] = {"request_id": request_id, "data": data}
    record["message"] = record["message"].translate(_LINE_ESCAPES)


class InterceptHandler(logging.Handler):  # pragma: no cover
    """Route stdlib logging into loguru, so library records take the configured format.

    See https://loguru.readthedocs.io/en/stable/overview.html#entirely-compatible-with-standard-logging
    """

    def emit(self, record: logging.LogRecord):
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame, depth = sys._getframe(6), 6
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).bind(
            correlation_id=correlation_id_ctx_var.get(None)
        ).log(level, record.getMessage())


def _log_level(requested: str) -> LogLevel:
    try:
        return LogLevel(requested.strip().upper())
    except ValueError:
        logger.warning(
            "Unknown log level, so the application logs at INFO. Set the level to one of "
            "the names the application accepts to pick another one.",
            requested=requested,
            accepted=[level.value for level in LogLevel],
        )
        return DEFAULT_LOG_LEVEL


async def _boolean_setting(settings_port: AsyncAdapterSettingsProvider, name: str) -> bool:
    """Read one boolean logging setting, treating an unusable value as off."""
    try:
        return await settings_port.get_setting(name, bool, False)
    except Exception:
        logger.warning(
            "Unusable value for a logging setting, so the setting stays off. Set it to "
            "'1' or '0', or unset it, to pick a value.",
            setting=name,
        )
        return False


def _install_sink(  # pragma: no cover
    level: LogLevel, structured: bool, backtrace: bool = False, diagnose: bool = False
) -> None:
    """Write log records to stderr, in the Univention log format or as one JSON object each."""
    logger.remove()
    logger.configure(patcher=_patch_json_record if structured else _patch_text_record)
    logger.add(
        sys.stderr,
        format="{message}" if structured else LOG_FORMAT,
        serialize=structured,
        level=level,
        colorize=None,
        enqueue=True,
        backtrace=backtrace,
        diagnose=diagnose,
    )


async def configure_logger(settings_port: AsyncAdapterSettingsProvider):  # pragma: no cover
    for logger_name in ("uvicorn", "uvicorn.error", "uvicorn.access", "fastapi"):
        logging.getLogger(logger_name).handlers = [InterceptHandler()]
    logger.enable(port_loader.__name__)
    # Reading the settings can log a warning, so somewhere to write it must exist first.
    _install_sink(DEFAULT_LOG_LEVEL, structured=False)
    level = _log_level(
        await settings_port.get_setting("user_management.logging.level", str, DEFAULT_LOG_LEVEL)
    )
    structured = await _boolean_setting(settings_port, "user_management.logging.structured")
    backtrace = await _boolean_setting(settings_port, "user_management.logging.backtrace")
    diagnose = await _boolean_setting(settings_port, "user_management.logging.diagnose")
    _install_sink(level, structured, backtrace, diagnose)
    logger.info("Configured logging.", level=level, structured=structured)
