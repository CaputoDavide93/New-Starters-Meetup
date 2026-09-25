from intro_common.config import allowed_email_domains, slack_cfg
from intro_common.emails import email_ref, parse_email_list

ALLOWED = {"example.com", "example.org"}


def test_allowed_domains_read_from_secret_and_normalised():
    # conftest sets "example.com, @Example.org"
    assert allowed_email_domains == ALLOWED


def test_trigger_channel_read_from_secret_key():
    assert slack_cfg["trigger_channel_id"] == "CTRIGGER"


def test_company_addresses_accepted_and_normalised():
    valid, rejected = parse_email_list(
        " Jane.Doe@Example.com, john@example.org\njane.doe@example.com", ALLOWED
    )
    assert valid == ["jane.doe@example.com", "john@example.org"]
    assert rejected == []


def test_external_and_lookalike_domains_rejected():
    valid, rejected = parse_email_list(
        "a@example.net, b@example.com.evil.io, c@evilexample.com, "
        "d@sub.example.org, e@example.org",
        ALLOWED,
    )
    assert valid == ["e@example.org"]
    assert rejected == [
        "a@example.net",
        "b@example.com.evil.io",
        "c@evilexample.com",
        "d@sub.example.org",
    ]


def test_malformed_addresses_rejected():
    valid, rejected = parse_email_list("not-an-email, x@@example.com, @example.org", ALLOWED)
    assert valid == []
    assert len(rejected) == 3


def test_empty_input():
    assert parse_email_list("", ALLOWED) == ([], [])
    assert parse_email_list(None, ALLOWED) == ([], [])


def test_email_ref_hides_address_and_is_stable():
    ref = email_ref("Jane.Doe@example.com")
    assert ref.startswith("user:") and len(ref) == 13
    assert "jane" not in ref
    assert ref == email_ref("jane.doe@example.com")
    assert email_ref(None) == "user:none"
