"""
Email helpers

Validates /newintro participant emails against the allowed company domains
and produces non-identifying references for log lines.
"""

import hashlib
import re

# Deliberately strict: one "@", no whitespace, dotted domain
_EMAIL_RE = re.compile(r"^[^@\s,;]+@[a-z0-9-]+(\.[a-z0-9-]+)+$")


def parse_email_list(raw: str, allowed_domains: set[str]) -> tuple[list[str], list[str]]:
    """
    Split a free-text email list and check every address against allowed_domains.

    Args:
        raw: Comma/semicolon/whitespace separated addresses
        allowed_domains: Lower-case domains that may receive invites (exact match)

    Returns:
        (valid, rejected) - valid is lower-cased and de-duplicated, order kept
    """
    valid: list[str] = []
    rejected: list[str] = []
    for token in re.split(r"[,;\s]+", raw or ""):
        email = token.strip().lower()
        if not email:
            continue
        domain = email.rsplit("@", 1)[-1]
        if _EMAIL_RE.match(email) and domain in allowed_domains:
            if email not in valid:
                valid.append(email)
        else:
            rejected.append(email)
    return valid, rejected


def email_ref(email: str | None) -> str:
    """Short stable hash of an email for logs (no PII in CloudWatch)."""
    if not email:
        return "user:none"
    return "user:" + hashlib.sha256(email.lower().encode("utf-8")).hexdigest()[:8]
