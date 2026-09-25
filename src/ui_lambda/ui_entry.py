"""
IntroUI Lambda - Entry point for Slack UI interactions

Handles Slack slash commands and modal submissions.
Uses AWS Lambda with ARM64 (Graviton) architecture.
Python 3.13+
"""

import os
import json
import logging

import boto3
from slack_bolt import App
from slack_bolt.adapter.aws_lambda import SlackRequestHandler

from intro_common.config import slack_cfg, allowed_email_domains
from intro_common.emails import parse_email_list

# ──── CONFIG ─────────────────────────────────────────────────────────────
WORKER_FN = os.environ["WORKER_FUNCTION_NAME"]
TRIGGER_CH = slack_cfg["trigger_channel_id"]

# ──── CLIENTS ────────────────────────────────────────────────────────────
lambda_client = boto3.client("lambda")
logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger(__name__)

app = App(
    token=slack_cfg["bot_token"],
    signing_secret=slack_cfg["signing_secret"],
    process_before_response=True,
)
handler = SlackRequestHandler(app)

# ──── MODAL DEFINITION ───────────────────────────────────────────────────
INTRO_MODAL = {
    "type": "modal",
    "callback_id": "intro_submit",
    "title": {"type": "plain_text", "text": "Schedule Intros"},
    "submit": {"type": "plain_text", "text": "Book"},
    "close": {"type": "plain_text", "text": "Cancel"},
    "blocks": [
        {
            "type": "input",
            "block_id": "mode",
            "label": {"type": "plain_text", "text": "Which type of intro?"},
            "element": {
                "type": "radio_buttons",
                "action_id": "mode_select",
                "options": [
                    {
                        "text": {"type": "plain_text", "text": "☕️ Coffee"},
                        "value": "coffee"
                    },
                    {
                        "text": {"type": "plain_text", "text": "🤝 Buddy"},
                        "value": "buddy"
                    }
                ]
            }
        },
        {
            "type": "input",
            "block_id": "emails",
            "label": {"type": "plain_text", "text": "Participant emails:"},
            "element": {
                "type": "plain_text_input",
                "action_id": "emails_input",
                "multiline": True,
                "placeholder": {
                    "type": "plain_text",
                    "text": "john.doe@company.com, jane.smith@company.com",
                }
            }
        },
        {
            "type": "input",
            "block_id": "start",
            "label": {"type": "plain_text", "text": "Start date:"},
            "element": {"type": "datepicker", "action_id": "date_picker"}
        },
        {
            "type": "input",
            "block_id": "count",
            "label": {"type": "plain_text", "text": "Meetings per person:"},
            "element": {
                "type": "plain_text_input",
                "action_id": "meeting_count",
                "placeholder": {"type": "plain_text", "text": "0"}
            }
        }
    ]
}

# ──── SLASH COMMAND: /newintro ───────────────────────────────────────────
@app.command("/newintro")
def cmd_newintro(ack, body, client, logger):
    """Open the intro scheduling modal."""
    ack()
    client.views_open(
        trigger_id=body["trigger_id"],
        view={**INTRO_MODAL, "private_metadata": body["channel_id"]},
    )
    logger.info(f"Opened intro modal from channel: {body['channel_id']}")


# ──── MODAL SUBMISSION ───────────────────────────────────────────────────
@app.view("intro_submit")
def handle_submit(ack, body, client, logger):
    """Handle modal submission and invoke worker Lambda."""
    vals = body["view"]["state"]["values"]
    raw_emails = vals["emails"]["emails_input"]["value"]

    # Invites go out from the company calendar: only allow company addresses
    valid_emails, rejected = parse_email_list(raw_emails, allowed_email_domains)
    if rejected or not valid_emails:
        domains = " or ".join(f"@{d}" for d in sorted(allowed_email_domains))
        msg = f"Only {domains} addresses are allowed."
        if rejected:
            msg += f" Not allowed: {', '.join(rejected[:5])}"
        ack(response_action="errors", errors={"emails": msg[:150]})
        logger.warning(f"Rejected intro request: {len(rejected)} disallowed email(s)")
        return

    ack(response_action="clear")

    chan = body["view"]["private_metadata"] or TRIGGER_CH
    mode = vals["mode"]["mode_select"]["selected_option"]["value"]
    emails = ",".join(valid_emails)
    start = vals["start"]["date_picker"]["selected_date"]
    count = vals["count"]["meeting_count"]["value"]

    # Post status message
    icon = ":coffee:" if mode == "coffee" else ":busts_in_silhouette:"
    client.chat_postMessage(
        channel=chan,
        text=f"{icon} Booking {mode.capitalize()}…"
    )
    logger.info(f"Submitted intro request: mode={mode}, emails={len(valid_emails)} count={count}")

    # Invoke worker Lambda asynchronously
    payload = {
        "mode": mode,
        "channel": chan,
        "emails": emails,
        "start": start,
        "count": count,
    }

    try:
        lambda_client.invoke(
            FunctionName=WORKER_FN,
            InvocationType="Event",
            Payload=json.dumps(payload).encode("utf-8"),
        )
        logger.info(f"Worker Lambda invoked: {WORKER_FN}")
    except Exception as e:
        logger.error(f"Failed to invoke worker Lambda: {e}")
        client.chat_postMessage(
            channel=chan,
            text=f":warning: Failed to start booking: {e}"
        )


# ──── LAMBDA HANDLER ─────────────────────────────────────────────────────
def lambda_handler(event, context):
    """Lambda entry point for Slack requests."""
    return handler.handle(event, context)
