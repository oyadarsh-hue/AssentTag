# Public UI showcase

Live link: https://oyadarsh-hue.github.io/AssentTag/

This is a static portfolio demonstration, not a hosted Django service.

- `index.html`, `messages.html`, and `chat.html` reuse the application's templates with fictional fixtures and relative navigation.
- `demo.html` contains an interactive browser-only preview of the feed, explore, consent, profile, post composition, and authentication layouts.
- Timer changes and demo messages exist only until navigation or reload; they do not communicate with other users. A 60-second option demonstrates expiry. Changing the timer does not alter messages already composed.
- Registration and login use fixed fictional values. The demo never requests a camera, real password, email OTP, or user file.
- Illustrations are allowlisted from `static/assets`; databases, environment files, biometric models, and uploaded user media are excluded.

## Build and preview

Run `python tools/build_ui_demo.py` using an environment with Django installed. Edit the demo sources in `tools/ui_demo/`, not their generated copies. Preview with `python -m http.server 8020 --bind 127.0.0.1 --directory docs`.

GitHub Pages uses the `main` branch and `/docs` directory. `.nojekyll` serves these files directly. A push updates the site without running the Django app or requiring Render.
