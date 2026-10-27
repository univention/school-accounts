# SPDX-FileCopyrightText: 2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

from __future__ import annotations

import codecs
import re
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from playwright.sync_api import expect

from tests.frontend.conftest import tick, wait_until_held

if TYPE_CHECKING:
    from collections.abc import Callable

    from playwright.sync_api import Download, Page, Route


@pytest.mark.frontend
def test_export_without_a_selection_takes_the_searched_users(
    signed_in: Page, list_school: Callable[..., None], school: str, listed_user: str
) -> None:
    list_school(school)
    with signed_in.expect_response(re.compile(r"/users\?(.*&)?q=")):
        signed_in.locator("#user-search input").fill(listed_user)
    shown = signed_in.locator('#user-rows u-checkbox[name="user_id"]')
    expect(shown.first).to_be_visible()
    expect(signed_in.locator("#selection-form u-collapsible")).to_be_hidden()

    with signed_in.expect_download() as download_info:
        signed_in.locator("#selection-form").get_by_role("button", name="Export all as CSV").click()

    rows = Path(download_info.value.path()).read_bytes().decode("utf-16").splitlines()
    exported = [row.split("\t")[-1] for row in rows[1:]]
    assert listed_user in exported
    assert exported == [box.get_attribute("value") for box in shown.all()]


@pytest.mark.frontend
def test_exporting_the_selection_saves_it_as_the_class_list_csv(
    signed_in: Page, list_school: Callable[..., None], school: str, school_id: str, listed_user: str
) -> None:
    """The browser saves the server's bytes as they are: UTF-16LE with the BOM that
    keeps Excel from showing mojibake. Saved from a blob, so the page stays."""
    list_school(school)
    button = signed_in.locator("#export-csv")
    expect(button).to_have_text("Export all as CSV")
    before = button.bounding_box()
    tick(signed_in, listed_user)
    expect(button).to_have_text("Export as CSV")
    # Sized to the longer label, so the tick does not move the buttons beside it.
    after = button.bounding_box()
    assert before is not None
    assert after is not None
    assert after["width"] == before["width"]

    with signed_in.expect_download() as download_info:
        button.click()

    download = download_info.value
    # Named after the list: the school, and no group, as all of them are listed.
    assert re.fullmatch(
        rf"{re.escape(school_id)}_\d{{4}}-\d\d-\d\d_\d\d_\d\d_\d\d\.csv", download.suggested_filename
    )
    raw = Path(download.path()).read_bytes()
    assert raw.startswith(codecs.BOM_UTF16_LE)
    rows = raw.decode("utf-16").splitlines()
    assert rows[0] == "Firstname\tLastname\tUsername"
    assert [row.split("\t")[-1] for row in rows[1:]] == [listed_user]
    # Nothing was swapped: the table and the selection stay as they were.
    expect(signed_in.locator(f'u-checkbox[name="user_id"][value="{listed_user}"]')).to_be_visible()
    expect(signed_in.locator("#selection-form")).to_contain_text("1 users selected")


@pytest.mark.frontend
def test_the_export_is_named_with_the_browsers_local_time(
    signed_in: Page, list_school: Callable[..., None], school: str, school_id: str
) -> None:
    """The file is named with the browser's local time. A naive datetime is the test
    machine's local time, which the browser shares."""
    list_school(school)
    signed_in.clock.set_fixed_time(datetime(2026, 10, 27, 14, 30, 5))

    with signed_in.expect_download() as download_info:
        signed_in.locator("#export-csv").click()

    assert download_info.value.suggested_filename == f"{school_id}_2026-10-27_14_30_05.csv"


@pytest.mark.frontend
def test_the_export_button_spins_until_the_file_arrives(
    signed_in: Page, list_school: Callable[..., None], school: str
) -> None:
    list_school(school)
    held: list[Route] = []
    signed_in.route("**/users/export", lambda route: held.append(route))
    button = signed_in.locator("#export-csv")

    button.click()
    wait_until_held(signed_in, held)
    assert button.evaluate("button => button.loading")
    # The reset button belongs to the selection form's own request.
    assert not signed_in.locator("#selection-form u-button[type=submit]").evaluate(
        "button => button.loading"
    )

    with signed_in.expect_download():
        held[0].continue_()
    expect(button).to_have_js_property("loading", False)


@pytest.mark.frontend
def test_a_refused_export_shows_a_toast_and_saves_nothing(
    signed_in: Page, list_school: Callable[..., None], school: str
) -> None:
    """The error arrives as bytes like the file would, and must still read as the toast."""
    list_school(school)
    signed_in.locator("#selection-form").evaluate(
        """form => form.setAttribute("hx-headers", '{"X-CSRF-Token": "not-the-token"}')"""
    )
    downloads: list[Download] = []
    # Not the bound list.append itself: Playwright tags its handlers with an attribute,
    # which a built-in method cannot take.
    signed_in.on("download", lambda download: downloads.append(download))

    signed_in.locator("#export-csv").click()

    expect(signed_in.locator("#toast-region")).to_contain_text("security token")
    expect(signed_in.locator("#export-csv")).to_have_js_property("loading", False)
    assert downloads == []
