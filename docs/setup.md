# Setup

This walks through a first deployment. Steps 1 and 2 were run in this repository's
checks; steps 3 to 6 need your own AWS, Slack, Azure AD and Google accounts and are
unverified here. There are no screenshots because the product has no interface
beyond a Slack modal.

## 1. Build the packages

You need Python 3.13, `pip` and `zip`, plus network access.

```bash
git clone https://github.com/CaputoDavide93/New-Starters-Meetup.git
cd New-Starters-Meetup
./scripts/build.sh
```

The script installs the hash-pinned `requirements.txt` for Python 3.13 on ARM64
into `build/layer/`, copies `src/common/*.py` into the layer as the `intro_common`
package, and writes `dist/ui-lambda.zip`, `dist/worker-lambda.zip` and
`dist/layer-python313-arm64.zip`.

## 2. Check the code

```bash
make venv
make check
```

## 3. Store the configuration

All application config is one JSON secret in AWS Secrets Manager. Both Lambdas
read it once at cold start. `src/common/config.py` reads it from the `eu-west-1`
region, so create the secret there or change that line.

| Key | Required | Description |
|-----|:--------:|-------------|
| `slack_bot_token` | yes | Slack bot token (`xoxb-...`) |
| `slack_signing_secret` | yes | Slack app signing secret |
| `slack_trigger_channel_id` | yes | Fallback channel for status messages (the older key `slack_trigger_channel` is still read) |
| `allowed_email_domains` | yes in practice | Comma-separated domains that may be booked, such as `example.com,example.org`. The built-in default is the placeholder `example.com` |
| `azure_tenant_id`, `azure_client_id`, `azure_client_secret` | yes | Azure AD app that reads the coffee-intro group |
| `azure_group_id` | yes | Azure AD group holding coffee-intro partners |
| `buddy_azure_tenant_id`, `buddy_azure_client_id`, `buddy_azure_client_secret` | no | Buddy-intro override; falls back to the coffee values |
| `buddy_azure_group_id` | yes | Azure AD group holding buddy-intro partners |
| `google_service_account_key` | yes | Service-account key as a JSON string |
| `google_delegated_user` | yes | Workspace user the service account impersonates |
| `google_calendar_id` | yes | Calendar the events are created on |
| `dynamodb_table_name` | yes | Partner table for coffee intros |
| `buddy_dynamodb_table_name` | yes | Partner table for buddy intros |
| `meeting_title_template`, `meeting_description_template` | no | Coffee event title and description |
| `buddy_meeting_title_template`, `buddy_meeting_description_template` | no | Buddy event title and description |

Templates take `{person1}` and `{person2}` (display names) and `{email1}` and
`{email2}`. An unknown placeholder falls back to a plain default title.

## 4. Create the tables and the Lambdas

Create two DynamoDB tables (the names are the values of `dynamodb_table_name` and
`buddy_dynamodb_table_name`) with a string partition key named `email`. The
examples in `.env.example` use `IntroUsers` and `BuddyUsers`.

Publish the layer and create the functions with your usual tooling, then upload the
code:

```bash
aws lambda publish-layer-version \
  --layer-name newstarters-deps \
  --compatible-runtimes python3.13 \
  --compatible-architectures arm64 \
  --zip-file fileb://dist/layer-python313-arm64.zip

aws lambda update-function-code --function-name intro-ui-lambda \
  --zip-file fileb://dist/ui-lambda.zip
aws lambda update-function-code --function-name intro-worker-lambda \
  --zip-file fileb://dist/worker-lambda.zip
```

Settings for both functions: runtime Python 3.13, architecture arm64, the layer
attached. Handlers are `ui_entry.lambda_handler` and `worker_entry.lambda_handler`.
Set `CONFIG_SECRET` on both and `WORKER_FUNCTION_NAME` on the UI function. Give the
worker the 15-minute maximum timeout; it posts a warning at 14 minutes and stops at
14.5 minutes.

IAM permissions the code uses:

| Role | Actions |
|------|---------|
| Both | `secretsmanager:GetSecretValue` on the config secret |
| UI | `lambda:InvokeFunction` on the worker |
| Worker | `dynamodb:GetItem`, `BatchGetItem`, `PutItem`, `UpdateItem`, `DeleteItem`, `Scan` on both tables |

## 5. Create the Slack app

1. Create a Slack app and copy its signing secret into the config secret.
2. Add a slash command `/newintro` and set its request URL to the UI Lambda's URL.
3. Add the bot token scopes `commands` and `chat:write`, install the app, and copy the bot token into the config secret.
4. Invite the bot to any channel where you will run the command.

## 6. Run it

In Slack, run `/newintro`, choose Coffee or Buddy, enter one test address on an
allowed domain, pick a start date and set meetings per person to 1. The channel
shows `Booking Coffee...`, a line per booked meeting and a final summary.

If nothing happens, see [Troubleshooting](troubleshooting.md).
