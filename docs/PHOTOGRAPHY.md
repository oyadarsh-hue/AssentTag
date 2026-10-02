# Photographic workflow assets

Thirty-two separate realistic photographs were generated with the built-in image generation tool: eight workflow photographs, twenty-one additional page photographs, and three new dashboard scroll photographs. Each selected original PNG is saved under `static/assets/`, with a matching optimized 1536×1024 WebP for the website. The earlier illustration drafts were superseded by the user's request for realistic photography and are not referenced by the website.

| Stage | Project asset | Used on |
| --- | --- | --- |
| Registration and live enrollment | `static/assets/photo-registration.webp` | Index chapter 01 and registration page |
| Login | `static/assets/photo-login.webp` | Index chapter 02 and login page |
| Dashboard workflow | `static/assets/photo-dashboard.webp` | Index chapter 03 |
| Upload and tagging | `static/assets/photo-upload.webp` | Index chapter 04 |
| Face detection and matching | `static/assets/photo-detection.webp` | Index chapter 05 and identity-verification background |
| Privacy blur | `static/assets/photo-protection.webp` | Index chapter 06 |
| Notification and live verification | `static/assets/photo-notification.webp` | Index chapter 07 |
| Approval and selective reveal | `static/assets/photo-consent.webp` | Index chapter 08 |

Full final prompts and original generation paths are recorded in `docs/PHOTO_ASSETS.json`, `docs/PAGE_PHOTO_ASSETS.json`, and `docs/DASHBOARD_SCROLL_ASSETS.json`. The images are generated explanatory scenes, not screenshots of the running application or photographs of registered users. Existing user photos, live camera capture, and face-blur logic are preserved.

The index uses a new rooftop consent-sharing photograph (`photo-index-hero-v2.webp`) in a centered frame with two layered backplates. Its background crossfades as the reader enters each workflow chapter. Every chapter also displays its own photograph directly. The dashboard uses new studio, hiking, and rooftop photographs that do not appear on the index. Registration, login, profile, upload, notifications, module, Explore, messages, OTP, stories, support, feedback, and admin pages have distinct photographic scenes; the 21 primary routes were checked for unique images.

Typography uses Inter for body and controls, and Space Grotesk for headings. Navigation, post controls, profile actions, and cards use coordinated asymmetric rounded corners. The profile avatar uses an octagonal frame, statistics use individual chips, and Suggestions and Trending Tags have separate frames. Dashboard sidebars remain accessible on mobile. Headings reveal word by word, replay when returning to view, and retain readable content without JavaScript. Reduced-motion preferences are respected. The existing theme control has a new shape and synchronized label/icon; no animation toggle was added.
