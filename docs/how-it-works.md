# How it works

One `/newintro` request, in order. Everything here is read from the code in `src/`.

## The two Lambdas

Slack gives a slash command three seconds to answer. The **UI Lambda**
(`src/ui_lambda/ui_entry.py`, Slack Bolt) opens the modal and handles the submit. It
hands the slow work to the **Worker Lambda** (`src/worker_lambda/worker_entry.py`)
with an asynchronous invoke, so Slack is never kept waiting.

## From modal to booking

1. `/newintro` opens a modal with the intro type, a list of emails, a start date and meetings per person.
2. On submit, the UI Lambda splits the list on commas, semicolons and whitespace, lower-cases and de-duplicates it, and checks each address against `allowed_email_domains` (exact domain match). Any address outside the list shows an error in the modal and nothing is booked.
3. The UI Lambda posts `Booking Coffee...` (or Buddy) to the channel and invokes the worker with the type, channel, emails, start date and count.
4. The worker checks the allowlist again, because the worker can be invoked directly.
5. The worker syncs the Azure AD group for that intro type into DynamoDB, and deletes records for people no longer in the group.
6. For each email and each meeting it picks a partner, searches for a slot, creates the event and adds one to the partner's count.

## Choosing a partner

The group sync stores the member list in DynamoDB. Each partner has a `weight`, the
number of intros they have done. The worker excludes the new starters in the request
and partners already used for that person, then picks at random among the candidates
with the lowest count. A partner with no record counts as zero.

## Finding a slot

The worker asks Google Calendar's FreeBusy API once for three calendars: the team
calendar, the new starter and the partner. It checks 15-minute steps between 11:00
and 15:00 in the `Europe/Dublin` time zone, skips 12:00 to 13:30, and takes the first
free slot. It looks at up to 7 days from the start, skipping weekends and past dates.
If no slot exists with a partner, it tries another partner. If a partner's calendar
returns an error, that partner is skipped. If nobody works, the worker posts
`No partner available` for that address, or records `No slot` in the summary.

The second and later meetings for one person start at least two business days after
the previous one.

## The event

The worker creates a 15-minute event on `google_calendar_id` with both people as
attendees, a Google Meet link, and invites sent to attendees. Title and description
come from the templates in the config secret.

## Reporting

The worker posts a warning about departed users removed, a line per booking, and a
final `Booking complete! N succeeded, M failed.` Logs carry `user:` plus 8 hex
characters of a SHA-256 hash instead of email addresses.

## Limits

- Window, time zone, lunch break, cadence and meeting length are constants in code.
- The worker stops itself near 14.5 minutes to stay inside the Lambda limit; addresses not reached are reported as failures.
- The Secrets Manager region is fixed to `eu-west-1`.
