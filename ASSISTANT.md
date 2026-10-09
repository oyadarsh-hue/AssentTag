# Assent, the AssentTag personal helper

The dot launcher is included on every full website page. It offers conversational
OpenAI integration for chat, captions and planning, site navigation, and a personal checklist.
It can respond whenever its backend is running. It does not run unattended tasks,
send messages, access photos, or schedule background notifications.

**Current status (9 October 2026):** the owner requires GPT-7 or higher. The
configured API account lists GPT-6 Astra, GPT-6.1 Sol, GPT-6 Sol, and GPT-6 Luna,
but no GPT-7 or higher. AI generation is therefore disabled; there is no fallback
to a lower model. The provider also returned `credit_balance_exhausted` during
the initial integration test. Site-guide answers and local tasks work now.
When an eligible model becomes available to the account, set `OPENAI_MODEL` to
its verified API model ID, fund the API account, and activate the hosted service.

## Run locally

From the repository root, using Python 3.10 or later:

```powershell
python assistant_service.py
```

Open http://127.0.0.1:8030/login.html. This serves the exported public preview
plus the real assistant API without needing MySQL or the full Django app.
`tools/start_assistant.ps1` starts it in a hidden window and records its PID
under `output/assistant.pid`. Stop that PID when finished.
The service reads `OPENAI_API_KEY` from the server environment or ignored `.env`.
The key must never be put in JavaScript, `docs/`, or committed to Git.
The existing Django app also exposes the same assistant API.

## Public website and continuous availability

GitHub Pages cannot run the Python backend. On Pages, the widget provides an
honestly labeled site guide and working local tasks until a backend is connected.
For AI to be available after the developer's computer is switched off, deploy
the independent service to an always-on HTTPS Python host:

1. Install `requirements-assistant.txt` on the host and run
   `waitress-serve --listen=0.0.0.0:$PORT assistant_service:application`
   (use the host's assigned port; shell expansion differs on Windows).
2. Add `OPENAI_API_KEY` through that host's secret manager, only with the owner's
   authorization. `OPENAI_MODEL` must be a verified, available GPT-7-or-higher
   model ID. There is deliberately no default model.
3. Set `ASSISTANT_ACCESS_CODE` to a random private code of at least 24 characters.
   Keep it private; it is separate from the OpenAI API key. The hosted endpoint
   will refuse chat without the code. Never put the code in the repository.
4. Set `ASSISTANT_ALLOWED_ORIGINS` to an exact comma-separated list, including
   `https://oyadarsh-hue.github.io` and the backend's own HTTPS origin if serving
   the UI there. Configure the host to use HTTPS and restart on failure.
5. Set the public `backend` origin in `static/js/assistant-config.js`, rebuild
   the demo, and publish. Alternatively, enter the URL in the widget's Connection
   screen. Enter the private access code there; it stays in that browser tab's
   session storage. Never enter an OpenAI API key into the widget.

The hosting account, secret destination, and always-on plan must be selected
before deployment. Uptime depends on the host, internet, and API availability;
a frontend launcher cannot guarantee 24/7 uptime.

### Prepared Render deployment

`render.yaml` provides a single Python service in Singapore, paid `0.5c-512mb`
compute, a 1 GB persistent disk for limits, a health check, and automatic updates
from the repository. It generates a private access code and prompts for the
OpenAI key and the eligible model ID. No paid service has been activated by adding this file.

[Review and deploy on Render](https://render.com/deploy?repo=https://github.com/oyadarsh-hue/AssentTag)

Sign in to your Render account, review the displayed charges, and authorize the
secret destination before transferring the key. After deployment, use its exact
HTTPS URL in the widget's Connection screen, or set the public config for all
visitors. Retrieve the generated private access code from Render's environment
settings. Add the deployed origin to `ASSISTANT_ALLOWED_ORIGINS` to use the UI
served by that backend as well as GitHub Pages.

References: [Render Blueprints](https://render.com/docs/blueprint-spec),
[compute plans](https://render.com/docs/compute-plans), and
[deployment buttons](https://render.com/docs/deploy-to-render).

## Privacy and limits

- Only typed chat history (last six messages) and the page scene name go to the
  backend/OpenAI. No account data, photos, OTPs, or task list is read or sent.
- Chat is saved in session storage for the current tab; New chat clears it.
  Tasks use local storage per app account (a shared preview list on demo pages).
  Remove tasks with their delete buttons. Avoid private information on shared devices.
- API responses use `store: false`. This does not override the provider's other
  applicable data retention policies.
- Default request caps: 20 per IP per hour and 150 total per day, persisted in
  `output/assistant/limits.sqlite3`. Override with `ASSISTANT_HOURLY_LIMIT` and
  `ASSISTANT_DAILY_LIMIT`. A persistent volume is required across host restarts;
  `ASSISTANT_LIMITS_PATH` selects that volume's SQLite path.
  use one service instance, or replace the limiter with shared storage when scaling.
  Behind a reverse proxy, clients may share the hourly cap; untrusted forwarding
  headers are intentionally ignored. These request caps are not a dollar budget.
- Requests are bounded to 2,000 input characters and 650 output tokens. Errors
  are sanitized; secrets and chat text are not printed in service logs.
- Set a provider project budget/alert as appropriate. Billing/quota errors are
  shown visibly, without pretending an AI answer was generated.

## Verification

```powershell
python -m unittest tests.test_assistant
python tools/build_ui_demo.py
python tools/verify_ui_demo.py
node --check static/js/assistant.js
```

The automated tests mock the paid API; they do not make billable requests.
Browser checks should also cover sending a real chat, error handling, task
persistence, clearing history, keyboard dismissal, and a narrow mobile viewport.
