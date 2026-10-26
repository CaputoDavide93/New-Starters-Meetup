# Troubleshooting

Find your symptom, then follow the fix. Logs are in CloudWatch under
`/aws/lambda/<function name>`; replace the names below with yours.

```bash
aws logs tail /aws/lambda/intro-ui-lambda --follow
aws logs tail /aws/lambda/intro-worker-lambda --follow
```

Logs show `user:` plus a short hash instead of email addresses.

## Slack says the command failed or times out

The request URL on the slash command must be the UI Lambda's URL, and the UI Lambda
must answer within three seconds. Cold starts that load the layer and the secret can
exceed that on the first call; run the command again.

## "Signature mismatch" or 401 from the UI Lambda

`slack_signing_secret` in the config secret does not match the Slack app. Copy it
again from the app's Basic Information page.

## `not_authed` or `invalid_auth` from Slack

The bot token is wrong or the app was reinstalled. Check it:

```bash
curl -X POST https://slack.com/api/auth.test -H "Authorization: Bearer $SLACK_BOT_TOKEN"
```

## The modal says "Only @... addresses are allowed"

An address is outside `allowed_email_domains`, or is malformed. Fix the address, or
add its domain to the secret. The match is exact, so `mail.example.com` does not
match `example.com`.

## No booking starts after you submit

Check the UI Lambda log for `Failed to invoke worker Lambda`. The usual causes are a
wrong `WORKER_FUNCTION_NAME` or a UI role without `lambda:InvokeFunction` on the
worker.

## "No partner available for ..."

The worker has no candidate left. Check that the Azure AD group for that intro type
has members and that the sync ran: the DynamoDB item with `email = members` should
hold a `member_list`. A buddy request reads `buddy_azure_group_id`, not
`azure_group_id`.

## Azure AD sync fails

Look for `Failed to sync Azure AD group` in the worker log. The app needs permission
to read group members in Microsoft Graph, with admin consent, and the tenant, client
and group IDs in the secret must match.

## "No slot for ..." in the results

No window between 11:00 and 15:00 (Europe/Dublin, lunch 12:00 to 13:30 excluded) was
free for all three calendars in the 7 days searched. Try a later start date.

## FreeBusy `notFound` warnings

The calendar is not readable by the service account. Confirm domain-wide delegation
is granted for the Calendar scope, `google_delegated_user` is a real Workspace
user, and the person has a Google Workspace calendar. Partners whose calendar errors
are skipped and logged as warnings.

## "Permission denied" or AccessDenied in the log

An IAM role lacks one of the actions listed in [Setup](setup.md#4-create-the-tables-and-the-lambdas).

## A timeout warning appears in the channel

The worker warns at 14 minutes and stops at 14.5 minutes. Reduce the email list or
the meetings per person, and submit the rest as a second request.

## Duplicate people in a DynamoDB table

Records created with different email capitalisation can duplicate. Preview, then
apply:

```bash
python scripts/cleanup_db.py --table <table name> --dry-run
python scripts/cleanup_db.py --table <table name> --apply
```

The script keeps the highest weight when it merges records.

If your problem is not here, [open an issue](https://github.com/CaputoDavide93/New-Starters-Meetup/issues) with the diagnostics in [CONTRIBUTING.md](../CONTRIBUTING.md#-reporting-an-untested-setup).
