# SPDX-FileCopyrightText: 2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

from __future__ import annotations

import re
import uuid
from typing import TYPE_CHECKING
from urllib.parse import quote_plus

import pytest
from playwright.sync_api import expect

from tests.frontend.conftest import FRONTEND_PREFIX

if TYPE_CHECKING:
    from collections.abc import Callable

    from playwright.sync_api import Locator, Page, Request, Route

# Long enough for the search box's 500ms input delay to have run out.
PAST_SEARCH_DELAY_MS = 700


@pytest.mark.frontend
def test_the_page_renders_through_the_design_system(signed_in: Page) -> None:
    expect(signed_in.locator("u-page-header")).to_have_text("School Accounts")


@pytest.mark.frontend
def test_the_user_list_starts_empty_until_a_school_is_picked(signed_in: Page) -> None:
    expect(signed_in.locator("#results-region")).to_contain_text(
        "Select a school and a group to list users."
    )


@pytest.mark.frontend
def test_selecting_a_school_asks_for_a_group(
    signed_in: Page, select_school: Callable[..., None], school: str, listed_user: str
) -> None:
    select_school(school)

    expect(signed_in.locator("#results-region")).to_contain_text(
        "Select a class or work group to list its users."
    )
    expect(signed_in.locator("#results-region")).not_to_contain_text(listed_user)


@pytest.mark.frontend
def test_all_groups_swaps_in_the_users_of_the_school(
    signed_in: Page,
    list_school: Callable[..., None],
    school: str,
    listed_user: str,
) -> None:
    list_school(school)
    expect(signed_in.locator("#results-region")).to_contain_text(listed_user)


@pytest.mark.frontend
def test_a_group_narrows_the_result_further(
    signed_in: Page, select_school: Callable[..., None], school: str
) -> None:
    """U0015: the list view can be scoped by school and by class or work group."""
    select_school(school)

    # nth(0) is "All classes and work groups".
    signed_in.locator("#group-list").get_by_role("option").nth(1).click()

    expect(signed_in).to_have_url(re.compile(r"[?&]group="))


@pytest.mark.frontend
def test_a_filtered_list_view_is_bookmarkable(signed_in: Page, school_id: str, listed_user: str) -> None:
    """U0035: the URL carries the school and the group, and opening it reproduces the same state."""
    signed_in.goto(f"{FRONTEND_PREFIX}/users?school={school_id}&group=all")

    expect(signed_in.locator("#results-region")).to_contain_text(listed_user)
    expect(signed_in.locator("#school-list")).to_have_attribute("value", school_id)
    expect(signed_in.locator("#group-list")).to_have_attribute("value", "all")


def search_box(page: Page) -> Locator:
    # The text field sits in u-input's shadow root, which Playwright's CSS reaches into.
    return page.locator("#user-search input")


def search(page: Page, text: str) -> None:
    with page.expect_response(re.compile(r"/users\?(.*&)?q=")):
        search_box(page).fill(text)


@pytest.mark.frontend
def test_typing_narrows_the_rows_and_leaves_the_box_alone(
    signed_in: Page, list_school: Callable[..., None], school: str, listed_user: str
) -> None:
    """Only the rows are swapped, so the text and the focus stay as typed. The search
    is one history entry, however many pauses it took to type."""
    list_school(school)
    history_length = signed_in.evaluate("history.length")

    search(signed_in, listed_user[:3])
    search(signed_in, listed_user)

    expect(signed_in.locator("#user-rows")).to_contain_text(listed_user)
    expect(signed_in).to_have_url(re.compile(rf"[?&]q={re.escape(quote_plus(listed_user))}(&|$)"))
    expect(search_box(signed_in)).to_have_value(listed_user)
    expect(search_box(signed_in)).to_be_focused()
    assert signed_in.evaluate("history.length") == history_length + 1


@pytest.mark.frontend
def test_back_after_a_search_keeps_the_group(
    signed_in: Page, list_school: Callable[..., None], school: str
) -> None:
    list_school(school)
    group = signed_in.locator("#group-list").get_by_role("option").nth(1)
    group_label = group.inner_text().strip()
    group.click()
    expect(signed_in).not_to_have_url(re.compile(r"[?&]group=all(&|$)"))
    group_url = signed_in.url
    nobody = f"nobody-{uuid.uuid4().hex[:8]}"
    search(signed_in, nobody)
    # The response event fires on the headers; htmx pushes the URL once the body is in.
    expect(signed_in).to_have_url(re.compile(rf"[?&]q={nobody}(&|$)"))

    signed_in.go_back()

    expect(signed_in).to_have_url(group_url)
    expect(signed_in.locator("#results-region strong")).to_contain_text(group_label)
    expect(signed_in.locator("#user-rows")).not_to_contain_text(f"No users match “{nobody}”.")
    expect(search_box(signed_in)).to_have_value("")


@pytest.mark.frontend
def test_spaces_alone_do_not_search_again(
    signed_in: Page, list_school: Callable[..., None], school: str, listed_user: str
) -> None:
    """Spaces leave the search words unchanged, so the box sends no request and the URL stays."""
    list_school(school)
    search(signed_in, listed_user)
    expect(signed_in).to_have_url(re.compile(r"[?&]q="))
    searched_url = signed_in.url
    sent: list[str] = []

    def record(request: Request) -> None:
        if "q=" in request.url:
            sent.append(request.url)

    signed_in.on("request", record)

    search_box(signed_in).press_sequentially("  ")
    search_box(signed_in).press("Home")
    search_box(signed_in).press_sequentially(" ")
    signed_in.wait_for_timeout(PAST_SEARCH_DELAY_MS)

    assert sent == []
    expect(signed_in).to_have_url(searched_url)


@pytest.mark.frontend
def test_a_search_that_matches_nobody_says_so_and_clearing_it_lists_again(
    signed_in: Page, list_school: Callable[..., None], school: str, listed_user: str
) -> None:
    list_school(school)
    nobody = f"nobody-{uuid.uuid4().hex[:8]}"

    search(signed_in, nobody)

    expect(signed_in.locator("#user-rows")).to_contain_text(f"No users match “{nobody}”.")
    expect(signed_in.locator("#user-rows")).not_to_contain_text(listed_user)

    with signed_in.expect_response(re.compile(r"/users\?")):
        search_box(signed_in).fill("")

    expect(signed_in.locator("#user-rows")).to_contain_text(listed_user)
    expect(signed_in).not_to_have_url(re.compile(r"[?&]q="))


@pytest.mark.frontend
@pytest.mark.parametrize(
    ("failure", "message"),
    [
        (414, "The search is too long. Please shorten it."),
        (502, "An unexpected error occurred. Please try again later."),
        ("no connection", "An unexpected error occurred. Please try again later."),
    ],
)
def test_a_search_that_fails_in_front_of_the_app_says_so(
    signed_in: Page,
    list_school: Callable[..., None],
    school: str,
    listed_user: str,
    failure: int | str,
    message: str,
) -> None:
    """The proxy answers a search past its request line with a 414, which htmx swaps nothing for."""
    list_school(school)
    signed_in.route(
        re.compile(r"/users\?(.*&)?q="),
        lambda route: route.fulfill(status=failure) if isinstance(failure, int) else route.abort(),
    )

    search_box(signed_in).fill(f"nobody-{uuid.uuid4().hex[:8]}")

    expect(signed_in.locator("#toast-region")).to_contain_text(message)
    expect(signed_in.locator("#user-rows")).to_contain_text(listed_user)


@pytest.mark.frontend
def test_a_search_tells_a_screen_reader_what_it_found(
    signed_in: Page, list_school: Callable[..., None], school: str, listed_user: str
) -> None:
    """WCAG 4.1.3: the focus stays in the box, so the result is announced. Only a live
    region already on the page when its text changes is announced reliably, so the
    swap has to fill it, not replace it."""
    list_school(school)
    status = signed_in.locator("search").get_by_role("status")
    region = status.element_handle()

    search(signed_in, listed_user)
    expect(status).to_have_text(
        re.compile(rf"^Users found for “{re.escape(listed_user)}”: [1-9][0-9]*\.$")
    )

    nobody = f"nobody-{uuid.uuid4().hex[:8]}"
    search(signed_in, nobody)
    expect(status).to_have_text(f"No users match “{nobody}”.")
    assert region.evaluate("element => element.isConnected")
    expect(signed_in.locator("#user-rows")).not_to_have_attribute("aria-busy", "true")


@pytest.mark.frontend
def test_a_group_change_keeps_the_search(
    signed_in: Page, list_school: Callable[..., None], school: str
) -> None:
    list_school(school)
    nobody = f"nobody-{uuid.uuid4().hex[:8]}"
    search(signed_in, nobody)

    # nth(0) is "All classes and work groups", the one listed already.
    signed_in.locator("#group-list").get_by_role("option").nth(1).click()

    expect(signed_in).not_to_have_url(re.compile(r"[?&]group=all(&|$)"))
    expect(signed_in).to_have_url(re.compile(rf"[?&]q={nobody}(&|$)"))
    expect(search_box(signed_in)).to_have_value(nobody)
    expect(signed_in.locator("#user-rows")).to_contain_text(f"No users match “{nobody}”.")


@pytest.mark.frontend
def test_typing_while_a_group_loads(
    signed_in: Page, list_school: Callable[..., None], school: str
) -> None:
    """The group change lands whole, and the text typed meanwhile stays and filters it.

    Its answer is held back until the typing has sent its own request. Cancelling
    the group change would leave the heading and the history on the previous group;
    redrawing the box from the group change's `q` would drop the text."""
    list_school(school)
    # Takes Chromium down the path of a browser without moveBefore, where htmx
    # re-inserts the box instead of moving it, and the focus drops to <body>.
    signed_in.evaluate("delete Element.prototype.moveBefore")
    held: list[Route] = []

    def hold_group_changes(route: Route) -> None:
        if route.request.headers.get("hx-target") == "results-region":
            held.append(route)
        else:
            route.continue_()

    signed_in.route(re.compile(r"/users\?"), hold_group_changes)
    history_length = signed_in.evaluate("history.length")
    group = signed_in.locator("#group-list").get_by_role("option").nth(1)
    group_label = group.inner_text().strip()
    with signed_in.expect_request(lambda request: request.headers.get("hx-target") == "results-region"):
        group.click()
    while not held:
        signed_in.wait_for_timeout(50)

    nobody = f"nobody-{uuid.uuid4().hex[:8]}"
    search_box(signed_in).fill(nobody)
    # So the search's request is due while the group change loads.
    signed_in.wait_for_timeout(PAST_SEARCH_DELAY_MS)
    held.pop().continue_()

    expect(signed_in.locator("#user-rows")).to_contain_text(f"No users match “{nobody}”.")
    expect(signed_in.locator("#results-region strong")).to_contain_text(group_label)
    expect(signed_in).not_to_have_url(re.compile(r"[?&]group=all(&|$)"))
    expect(signed_in).to_have_url(re.compile(rf"[?&]q={nobody}(&|$)"))
    assert signed_in.evaluate("history.length") == history_length + 2  # The group, then the search.
    expect(search_box(signed_in)).to_have_value(nobody)
    expect(search_box(signed_in)).to_be_focused()


@pytest.mark.frontend
def test_a_new_search_cancels_the_one_still_loading(
    signed_in: Page, list_school: Callable[..., None], school: str, listed_user: str
) -> None:
    """The first search's answer is held back. Waiting for it would show the new rows
    only after two whole listings, and its late answer must not replace them."""
    list_school(school)
    history_length = signed_in.evaluate("history.length")
    held: list[Route] = []

    def hold_the_first_search(route: Route) -> None:
        if held:
            route.continue_()
        else:
            held.append(route)

    signed_in.route(re.compile(r"/users\?(.*&)?q="), hold_the_first_search)
    search_box(signed_in).fill(listed_user)
    while not held:
        signed_in.wait_for_timeout(50)

    nobody = f"nobody-{uuid.uuid4().hex[:8]}"
    with signed_in.expect_event("requestfailed", lambda request: request.url == held[0].request.url):
        search(signed_in, nobody)

    expect(signed_in.locator("#user-rows")).to_contain_text(f"No users match “{nobody}”.")
    held[0].continue_()
    signed_in.wait_for_timeout(PAST_SEARCH_DELAY_MS)
    expect(signed_in.locator("#user-rows")).to_contain_text(f"No users match “{nobody}”.")
    expect(signed_in).to_have_url(re.compile(rf"[?&]q={nobody}(&|$)"))
    assert signed_in.evaluate("history.length") == history_length + 1


@pytest.mark.frontend
def test_a_search_after_a_failed_group_change_narrows_what_is_listed(
    signed_in: Page, list_school: Callable[..., None], school: str
) -> None:
    """After a failed group change the sidebar already shows the new group, while the table
    still lists the old one. A search narrows the old one, which its heading names."""
    list_school(school)
    listing_url = signed_in.url
    heading = signed_in.locator("#results-region strong").inner_text()
    signed_in.route(
        re.compile(r"/users\?"),
        lambda route: (
            route.abort()
            if route.request.headers.get("hx-target") == "results-region"
            else route.fallback()
        ),
    )
    with signed_in.expect_event(
        "requestfailed", lambda request: request.headers.get("hx-target") == "results-region"
    ):
        signed_in.locator("#group-list").get_by_role("option").nth(1).click()
    signed_in.unroute(re.compile(r"/users\?"))

    nobody = f"nobody-{uuid.uuid4().hex[:8]}"
    search(signed_in, nobody)

    expect(signed_in).to_have_url(f"{listing_url}&q={nobody}")
    expect(signed_in.locator("#results-region strong")).to_have_text(heading)
    expect(signed_in.locator("#user-rows")).to_contain_text(f"No users match “{nobody}”.")


@pytest.mark.frontend
@pytest.mark.parametrize("search", ["delayed", "loading"])
def test_back_during_a_search_lands_where_it_points(
    signed_in: Page, list_school: Callable[..., None], school: str, listed_user: str, search: str
) -> None:
    """Back drops a search still waiting out its delay or loading.

    Its answer is held back until the restored page is in. Without the guard, that late
    answer would rewrite the URL, swap its rows into a listing it does not belong to,
    and leave the box with the text typed before Back."""
    list_school(school)
    listing_url = signed_in.url
    signed_in.locator("#group-list").get_by_role("option").nth(1).click()
    expect(signed_in).not_to_have_url(re.compile(r"[?&]group=all(&|$)"))
    held: list[Route] = []
    signed_in.route(re.compile(r"/users\?(.*&)?q="), lambda route: held.append(route))

    search_box(signed_in).fill(f"nobody-{uuid.uuid4().hex[:8]}")
    if search == "loading":
        while not held:
            signed_in.wait_for_timeout(50)
    signed_in.go_back()
    expect(signed_in.locator("#user-rows")).to_contain_text(listed_user)
    for route in held:
        route.continue_()
    # A search still waiting out its delay would have sent its request by now.
    signed_in.wait_for_timeout(PAST_SEARCH_DELAY_MS)

    assert len(held) == (search == "loading")
    expect(signed_in).to_have_url(listing_url)
    expect(signed_in.locator("#user-rows")).to_contain_text(listed_user)
    expect(search_box(signed_in)).to_have_value("")


@pytest.mark.frontend
@pytest.mark.parametrize("failure", ["error status", "network error"])
def test_back_reloads_when_the_restore_fails(
    signed_in: Page, list_school: Callable[..., None], school: str, failure: str
) -> None:
    """A failed restore swaps nothing, so the page left behind would stay under the new
    URL with every filter blocked by the back-navigation guard."""
    list_school(school)
    listing_url = signed_in.url
    group = signed_in.locator("#group-list").get_by_role("option").nth(1)
    group.click()
    expect(signed_in).not_to_have_url(re.compile(r"[?&]group=all(&|$)"))

    def fail_the_restore(route: Route) -> None:
        if route.request.headers.get("hx-history-restore-request") != "true":
            route.continue_()
        elif failure == "error status":
            route.fulfill(status=502)
        else:
            route.abort()

    signed_in.route(re.compile(r"/users\?"), fail_the_restore)
    signed_in.go_back()

    expect(signed_in).to_have_url(listing_url)
    expect(signed_in.locator("#group-list")).to_have_attribute("value", "all")
    group.click()
    expect(signed_in).not_to_have_url(re.compile(r"[?&]group=all(&|$)"))


@pytest.mark.frontend
def test_an_unknown_school_falls_back_instead_of_failing(signed_in: Page) -> None:
    """U0036: a URL naming a school that does not exist renders the view with nothing chosen."""
    signed_in.goto(f"{FRONTEND_PREFIX}/users?school=school-that-does-not-exist")

    expect(signed_in.locator("u-table")).to_be_visible()
    expect(signed_in.locator("#results-region")).to_contain_text(
        "Select a school and a group to list users."
    )


def _choose_role(page: Page, role: str) -> None:
    page.locator(f'#role-filter u-filter-chip[value="{role}"]').click()
    expect(page).to_have_url(re.compile(rf"[?&]role={role}(&|$)"))


def _role_cells(page: Page) -> list[str]:
    return page.locator("#results-region u-tbody u-tr u-td:nth-child(5)").all_inner_texts()


@pytest.mark.frontend
def test_a_role_narrows_the_list_to_users_holding_it(
    signed_in: Page, list_school: Callable[..., None], school: str
) -> None:
    list_school(school)

    _choose_role(signed_in, "teacher")

    assert all("Teacher" in cell for cell in _role_cells(signed_in))


@pytest.mark.frontend
def test_only_one_role_is_selected_at_a_time(
    signed_in: Page, list_school: Callable[..., None], school: str, listed_user: str
) -> None:
    list_school(school)
    _choose_role(signed_in, "student")

    _choose_role(signed_in, "teacher")

    expect(signed_in.locator("#role-filter u-filter-chip[selected]")).to_have_attribute(
        "value", "teacher"
    )
    signed_in.locator('#role-filter u-filter-chip[value="teacher"]').click()
    expect(signed_in).not_to_have_url(re.compile(r"[?&]role="))
    expect(signed_in.locator("#results-region")).to_contain_text(listed_user)


@pytest.mark.frontend
def test_all_clears_the_role(
    signed_in: Page, list_school: Callable[..., None], school: str, listed_user: str
) -> None:
    list_school(school)
    _choose_role(signed_in, "student")

    signed_in.locator("#role-filter").get_by_role("button", name="All").click()

    expect(signed_in).not_to_have_url(re.compile(r"[?&]role="))
    expect(signed_in.locator("#results-region")).to_contain_text(listed_user)
    expect(signed_in.locator("#role-filter u-filter-chip[selected]")).to_have_count(0)


@pytest.mark.frontend
def test_a_group_change_keeps_the_role(
    signed_in: Page, list_school: Callable[..., None], school: str
) -> None:
    list_school(school)
    _choose_role(signed_in, "teacher")

    # nth(0) is "All classes and work groups".
    signed_in.locator("#group-list").get_by_role("option").nth(1).click()

    expect(signed_in).to_have_url(re.compile(r"[?&]group=(school_class|work_group)"))
    expect(signed_in).to_have_url(re.compile(r"[?&]role=teacher(&|$)"))
    expect(signed_in.locator("#role-filter u-filter-chip[selected]")).to_have_attribute(
        "value", "teacher"
    )


@pytest.mark.frontend
def test_the_role_and_the_search_keep_each_other(
    signed_in: Page, list_school: Callable[..., None], school: str
) -> None:
    list_school(school)
    nobody = f"nobody-{uuid.uuid4().hex[:8]}"
    search(signed_in, nobody)

    _choose_role(signed_in, "teacher")

    expect(signed_in).to_have_url(re.compile(rf"[?&]q={nobody}(&|$)"))
    expect(search_box(signed_in)).to_have_value(nobody)

    search(signed_in, f"{nobody}x")

    expect(signed_in).to_have_url(re.compile(r"[?&]role=teacher(&|$)"))
    expect(signed_in.locator("#role-filter u-filter-chip[selected]")).to_have_attribute(
        "value", "teacher"
    )


@pytest.mark.frontend
def test_the_chosen_role_keeps_the_keyboard_focus(
    signed_in: Page, list_school: Callable[..., None], school: str
) -> None:
    list_school(school)
    signed_in.locator('#role-filter u-filter-chip[value="staff"]').focus()

    signed_in.keyboard.press("Space")

    expect(signed_in).to_have_url(re.compile(r"[?&]role=staff(&|$)"))
    expect(signed_in.locator('#role-filter u-filter-chip[value="staff"]')).to_be_focused()


@pytest.mark.frontend
def test_all_keeps_the_keyboard_focus(
    signed_in: Page, list_school: Callable[..., None], school: str
) -> None:
    list_school(school)
    _choose_role(signed_in, "staff")
    all_button = signed_in.locator("#role-filter").get_by_role("button", name="All")
    all_button.focus()

    signed_in.keyboard.press("Space")

    expect(signed_in).not_to_have_url(re.compile(r"[?&]role="))
    expect(all_button).to_be_focused()


@pytest.mark.frontend
def test_history_navigation_reruns_the_page_script_without_error(
    signed_in: Page, list_school: Callable[..., None], school: str
) -> None:
    errors: list[str] = []
    signed_in.on("pageerror", lambda error: errors.append(error.message))
    list_school(school)
    _choose_role(signed_in, "student")

    signed_in.go_back()
    expect(signed_in).not_to_have_url(re.compile(r"[?&]role="))
    expect(signed_in.locator("#role-filter u-filter-chip[selected]")).to_have_count(0)
    signed_in.go_forward()
    expect(signed_in).to_have_url(re.compile(r"[?&]role=student(&|$)"))
    expect(signed_in.locator("#role-filter u-filter-chip[selected]")).to_have_attribute(
        "value", "student"
    )

    assert errors == []
