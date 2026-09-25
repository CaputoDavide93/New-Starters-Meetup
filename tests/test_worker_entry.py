import datetime
from unittest import mock


import worker_entry
from intro_common import calendar_utils

NEW = "new.starter@example.com"
MISSING = "missing.partner@example.com"
PARTNER = "partner@example.com"
TEAM_CAL = worker_entry.google_calendar_id


class FakeFreeBusyService:
    """FreeBusy returns notFound for MISSING and an empty calendar otherwise."""

    def freebusy(self):
        return self

    def query(self, body):
        self._ids = [item["id"] for item in body["items"]]
        return self

    def execute(self):
        cals = {}
        for cal_id in self._ids:
            if cal_id == MISSING:
                cals[cal_id] = {"errors": [{"domain": "global", "reason": "notFound"}]}
            else:
                cals[cal_id] = {"busy": []}
        return {"calendars": cals}


def test_find_next_free_slot_records_errored_calendars():
    slot = calendar_utils.find_next_free_slot(
        FakeFreeBusyService(), [TEAM_CAL, NEW, MISSING], datetime.date(2026, 10, 5)
    )
    assert slot is not None
    assert calendar_utils.last_errored_calendars == [MISSING]


def test_worker_skips_partner_whose_calendar_is_missing():
    picks = iter([MISSING, PARTNER])
    create_event = mock.Mock(return_value="evt1")
    next_monday = datetime.date.today() + datetime.timedelta(days=7 - datetime.date.today().weekday())

    with mock.patch.multiple(
        worker_entry,
        sync_azure_group=mock.Mock(return_value=0),
        get_calendar_service=mock.Mock(return_value=FakeFreeBusyService()),
        pick_one_intro_partner=mock.Mock(side_effect=lambda *a, **k: next(picks, None)),
        create_event=create_event,
        increment_user_weight=mock.Mock(),
        get_display_name=mock.Mock(side_effect=lambda e, t: e.split("@")[0]),
        _safe_slack_post=mock.Mock(),
    ):
        worker_entry.book_all_intros("coffee", "CCHAN", [NEW], next_monday, 1)

    create_event.assert_called_once()
    assert create_event.call_args.kwargs["attendees"] == [NEW, PARTNER]


def test_worker_refuses_external_emails():
    with mock.patch.object(worker_entry, "book_all_intros") as book:
        result = worker_entry.lambda_handler(
            {"emails": "ok@example.org,evil@gmail.com", "start": "2026-10-01",
             "count": "1", "mode": "coffee", "channel": "C1"},
            None,
        )
    assert result["statusCode"] == 500
    book.assert_not_called()


def test_worker_accepts_company_emails():
    with mock.patch.object(worker_entry, "book_all_intros") as book:
        result = worker_entry.lambda_handler(
            {"emails": "A@example.org, b@example.com", "start": "2026-10-01",
             "count": "1", "mode": "coffee", "channel": "C1"},
            None,
        )
    assert result["statusCode"] == 200
    assert book.call_args.kwargs["emails"] == ["a@example.org", "b@example.com"]


def test_no_emails_in_logs(caplog):
    caplog.set_level("DEBUG")
    picks = iter([PARTNER])
    next_monday = datetime.date.today() + datetime.timedelta(days=7 - datetime.date.today().weekday())
    with mock.patch.multiple(
        worker_entry,
        sync_azure_group=mock.Mock(return_value=0),
        get_calendar_service=mock.Mock(return_value=FakeFreeBusyService()),
        pick_one_intro_partner=mock.Mock(side_effect=lambda *a, **k: next(picks, None)),
        create_event=mock.Mock(return_value="evt1"),
        increment_user_weight=mock.Mock(),
        get_display_name=mock.Mock(return_value="Name"),
        _safe_slack_post=mock.Mock(),
    ):
        worker_entry.book_all_intros("coffee", "CCHAN", [NEW], next_monday, 1)
    assert caplog.records
    for rec in caplog.records:
        msg = rec.getMessage()
        assert NEW not in msg and PARTNER not in msg, msg
