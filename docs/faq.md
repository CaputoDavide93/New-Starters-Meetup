# FAQ

## What does New Starters MeetUp do?

It is a Slack `/newintro` command that books 15-minute coffee-chat or buddy meetings
for new starters in Google Calendar. You give it a list of email addresses, and it
picks a partner for each meeting, finds a free slot and creates the invite.

## Who is it for?

Onboarding coordinators and team leads who book intro meetings for new cohorts and
can deploy two AWS Lambdas. It needs Slack, Azure AD (Microsoft Entra ID) and Google
Workspace.

## What is the difference between a Coffee and a Buddy intro?

Only the pool and the wording. Each type reads its own Azure AD group, keeps its own
DynamoDB table and uses its own event title and description templates.

## How does it pick the partner?

It picks at random among the partners with the fewest previous intros. The count is
stored in DynamoDB and goes up by one for each booked meeting.

## When are meetings booked?

On weekdays between 11:00 and 15:00 in the Europe/Dublin time zone, in 15-minute
steps, never between 12:00 and 13:30. These values are constants in
`src/common/calendar_utils.py` and `src/worker_lambda/worker_entry.py`.

## Can I change the time window or time zone?

Yes, in code. They are not settings in the config secret. Edit the constants and
rebuild with `./scripts/build.sh`.

## How long are the meetings?

15 minutes. Each event includes a Google Meet link and sends invites to both people.

## Can I book someone outside my organisation?

No. Only addresses on `allowed_email_domains` pass, in the modal and again in the
worker. The match is exact, so subdomains need their own entry.

## Does it store email addresses in the logs?

No. Log lines carry `user:` and 8 hex characters of a SHA-256 hash. Emails are
stored in your DynamoDB tables and in the Slack messages the bot posts.

## Where does it store data?

In two DynamoDB tables that you create (partner list, display names and intro
counts), and in your Secrets Manager secret. Nothing is sent anywhere else.

## Does it need Azure AD?

Yes. The partner pool comes from an Azure AD group read through Microsoft Graph.
Without one, there are no partners to pick.

## What happens to people who leave?

On each request the worker syncs the group and deletes DynamoDB records of people who
are no longer members.

## What does it cost to run?

It runs on Lambda, DynamoDB and Secrets Manager. The repository does not measure
usage or cost, so check AWS pricing for your volume.

## Does it work in regions other than eu-west-1?

Unverified. The code reads the config secret from `eu-west-1`, and `scripts/cleanup_db.py` uses that region for DynamoDB. The Lambdas use their own region for DynamoDB. Change the hard-coded region in `src/common/config.py` to read the secret elsewhere.

## Is there a screenshot?

No. The only interface is a Slack modal, and no check can render it. See the
[tested and unverified table](../README.md#-tested-and-unverified).

## How do I report a problem or an untested setup?

Open an issue with the details listed in
[CONTRIBUTING.md](../CONTRIBUTING.md#-reporting-an-untested-setup).
