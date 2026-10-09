# Ask Assent — private workspace launcher

The shared Ask Assent control opens the full personal workspace in the current
browser tab. The former embedded site-guide popup has been removed.

The default destination is http://127.0.0.1:8040/. This address belongs to the
visitor's own computer. The private service must be running there; this is not
a publicly hosted AI service or a way to access the owner's computer remotely.

For the owner's local installation, run private_assistant/start.ps1, then click
Ask Assent from any AssentTag page. The workspace provides projects, files,
research tools, tasks, and activity history. Its private source and data are
excluded from Git by the /private_assistant/ ignore rule.

The launcher destination is the public workspace field in
static/js/assistant-config.js. Only a navigation URL belongs there. Never add
API keys, access tokens, project contents, or other private data to that file.
Rebuild the shared website assets with python tools/build_ui_demo.py.

The private workspace reports its own model availability. The owner's GPT-7-or-
higher requirement remains unresolved; changing the launcher or its design
neither creates a model nor connects a lower model automatically.

Verification: python tools/verify_ui_demo.py checks exported resources and
navigation. Confirm a launcher click reaches the full workspace with the local
service running. Links must remain keyboard accessible, and motion honors the
visitor's reduced-motion setting. The private service permits top-level document
navigation while retaining same-origin restrictions on its data APIs.
