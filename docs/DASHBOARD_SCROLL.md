# Dashboard photography and success feedback

Three new realistic photographs were generated with the built-in image tool, saved as original PNGs and optimized WebPs in `static/assets/`. Final prompts, generation paths, and saved asset paths are recorded in `DASHBOARD_SCROLL_ASSETS.json`.

| Photograph | Location in dashboard | Action |
| --- | --- | --- |
| `dashboard-scroll-discover.webp` — Kochi waterfront photo walk | After the first post, or the empty-feed message | Explore feed |
| `dashboard-scroll-private.webp` — private travel-photo collection | After the second post, or after the first when only one exists | Upload photo |
| `dashboard-scroll-consent.webp` — garden consent review | After the feed | Tagged notifications |

All three remain visible when the feed is empty. Each panel reveals on entry, repeats when returning, moves its photo slightly with scrolling, and crossfades the page background. Motion uses transforms and opacity, with animation work limited to visible photographs. Reduced-motion preferences disable the movement. The two earlier dashboard photo links remain available below these panels.

Login and admin login queue a Django success message before redirecting to their dashboards. Completed registration redirects to login with its success message. A shared native dialog displays those messages with a colorful frame, check animation, accessible focus, keyboard dismissal, and a Continue button. The popup script is local and works without the SweetAlert CDN. Registration capture, profile updates, uploads, stories, text posts, comments, consent approval, verified-message delivery, reports, and feedback use the same success styling. Messages are inserted as text, and notification messages are consumed once after redirects.

Registration, feedback, and report submission use a redirect after successful saving, preventing a browser refresh from submitting them again. Feedback success is now confirmed by the server rather than shown for any fetch response. Failed login or registration does not queue a success popup.

Validation artifacts are saved under `output/ui/`, including the three dashboard panels, mobile panel, and authentication success dialogs.

Checks passed: 22 authentication/registration tests, 42 desktop/mobile page checks, dashboard photo decoding, background transitions, scroll parallax, replay on returning, reduced motion, three success-dialog routes with the external alert library blocked, one-time dismissal, and safe rendering of message text. Index scrolling and the existing theme control also passed their regression checks.
