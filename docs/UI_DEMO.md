# Public UI showcase

Live link: https://oyadarsh-hue.github.io/AssentTag/

This is a static portfolio demonstration, not a hosted Django service.

- Every exported page uses the original Django template, inline CSS, shared styles and visual animation scripts. The complete mapping is recorded in `ui-template-map.json`.
- `demo.html` is the original three-column dashboard, including its Ghost Text animation and scroll-photo transitions. `explore.html` preserves the original 3D orbit and fusion animations; profiles preserve the original Time-Stream.
- The backend adapter supplies sample responses and prevents real submissions. It does not replace page layout or animation code. The verification page retains its scanner styling but disables webcam authentication.
- Timer changes and demo messages exist only until navigation or reload; they do not communicate with other users. A 60-second option demonstrates expiry. Changing the timer does not alter messages already composed.
- Registration and login use fixed fictional values. The demo never requests a camera, real password, email OTP, or user file.
- Illustrations are allowlisted from `static/assets`; databases, environment files, biometric models, and uploaded user media are excluded.

## Build and preview

Run `python tools/build_ui_demo.py` using an environment with Django installed. Make layout and animation changes in the original project templates/styles; `tools/ui_demo/` contains only static-demo adapters and a dismissible notice. The exporter asserts that inline styles are preserved. Preview with `python -m http.server 8020 --bind 127.0.0.1 --directory docs`.

GitHub Pages uses the `main` branch and `/docs` directory. `.nojekyll` serves these files directly. A push updates the site without running the Django app or requiring Render.
