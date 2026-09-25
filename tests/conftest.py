"""
Test setup: expose src/common as the intro_common package (as in the Lambda
layer) and stub the Secrets Manager config load done at import time.
"""

import importlib.util
import json
import os
import sys
from pathlib import Path
from unittest import mock

import boto3

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"

os.environ.setdefault("AWS_DEFAULT_REGION", "eu-west-1")
os.environ.setdefault("CONFIG_SECRET", "arn:aws:secretsmanager:eu-west-1:000000000000:secret:test")
os.environ.setdefault("WORKER_FUNCTION_NAME", "IntroWorker-Test")

TEST_SECRET = {
    "slack_bot_token": "xoxb-test",
    "slack_signing_secret": "test-signing-secret",
    "slack_trigger_channel_id": "CTRIGGER",
    "google_service_account_key": "{}",
    "google_calendar_id": "team@group.calendar.google.com",
    "dynamodb_table_name": "IntroUsers",
    "buddy_dynamodb_table_name": "BuddyUsers",
    # Fictitious allow-list so tests never depend on real company domains
    "allowed_email_domains": "example.com, @Example.org",
}

_real_client = boto3.client


def _fake_client(service, *args, **kwargs):
    if service == "secretsmanager":
        fake = mock.MagicMock()
        fake.get_secret_value.return_value = {"SecretString": json.dumps(TEST_SECRET)}
        return fake
    return _real_client(service, *args, **kwargs)


def _load_intro_common():
    spec = importlib.util.spec_from_file_location(
        "intro_common",
        SRC / "common" / "__init__.py",
        submodule_search_locations=[str(SRC / "common")],
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules["intro_common"] = module
    spec.loader.exec_module(module)


with mock.patch.object(boto3, "client", _fake_client):
    _load_intro_common()
    import intro_common.config  # noqa: E402,F401  (loads secrets once)

sys.path.insert(0, str(SRC / "worker_lambda"))
sys.path.insert(0, str(SRC / "ui_lambda"))
