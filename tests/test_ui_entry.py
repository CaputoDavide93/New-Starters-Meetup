from unittest import mock

from slack_sdk import WebClient

# Bolt calls auth.test when the App is created; stub it so import is offline
with mock.patch.object(WebClient, "auth_test", return_value={"ok": True, "user_id": "UBOT", "bot_id": "BBOT"}):
    import ui_entry


def _body(emails, count="2"):
    return {
        "view": {
            "private_metadata": "CCHAN",
            "state": {
                "values": {
                    "mode": {"mode_select": {"selected_option": {"value": "coffee"}}},
                    "emails": {"emails_input": {"value": emails}},
                    "start": {"date_picker": {"selected_date": "2026-10-01"}},
                    "count": {"meeting_count": {"value": count}},
                }
            },
        }
    }


def test_external_email_rejected_with_modal_error():
    ack, client, logger = mock.Mock(), mock.Mock(), mock.Mock()
    with mock.patch.object(ui_entry, "lambda_client") as lam:
        ui_entry.handle_submit(ack, _body("ok@example.com, bad@example.net"), client, logger)
    ack.assert_called_once()
    kwargs = ack.call_args.kwargs
    assert kwargs["response_action"] == "errors"
    assert "bad@example.net" in kwargs["errors"]["emails"]
    lam.invoke.assert_not_called()
    client.chat_postMessage.assert_not_called()


def test_company_emails_invoke_worker_with_normalised_list():
    ack, client, logger = mock.Mock(), mock.Mock(), mock.Mock()
    with mock.patch.object(ui_entry, "lambda_client") as lam:
        ui_entry.handle_submit(ack, _body("A@Example.com,\n b@example.org"), client, logger)
    ack.assert_called_once_with(response_action="clear")
    payload = lam.invoke.call_args.kwargs["Payload"].decode()
    assert '"emails": "a@example.com,b@example.org"' in payload
