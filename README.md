# AssentTag — Consent-Based Face Privacy Framework 🛡️👁️

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Framework-Django-green.svg)](https://www.djangoproject.com/)
[![Computer Vision](https://img.shields.io/badge/Vision-OpenCV%20%7C%20Dlib-orange.svg)](https://github.com/davisking/dlib)
[![License](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)

## Open the full project UI locally

**[Open AssentTag — full website](http://127.0.0.1:8010/)** · [Login](http://127.0.0.1:8010/login/login/) · [Messages](http://127.0.0.1:8010/login/messages/)

On your computer, double-click [Start AssentTag.cmd](Start%20AssentTag.cmd) in the downloaded project folder to start the server and open the full website. If it is already running, use [Open AssentTag.url](Open%20AssentTag.url).

These links open your own computer's local server; GitHub stores the project code and does not host this Django application. The local MySQL service and project dependencies must be available. After login, the website links to the dashboard and the other project pages.

**AssentTag** is an intelligent, automated face privacy and identity consent management platform built with Django and Computer Vision. It protects individuals against unauthorized visual media exposure across social feeds, posts, and stories by enforcing privacy-by-default face obfuscation, real-time facial recognition matching, dynamic consent granting, and cryptographic authorization workflows.

---

## 🌟 Key Features

- **🔒 Privacy-By-Default Face Blurring**: Uploaded photos and stories are automatically scanned for human faces. Unconsented faces are obscured in real-time.
- **🎯 68-Point Landmark & Deep ResNet Recognition**: High-precision facial vector extraction and Euclidean distance thresholding (\(d \le 0.42\)) against registered face vectors.
- **✨ The Veil — Dynamic Consent Unblur**: Once a tagged individual grants explicit permission, the system dynamically lifts the facial obfuscation mask for authorized viewers.
- **🔐 Multi-Factor Security & OTP Verification**: High-risk operations (identity authorization, security changes, financial PIN transactions) are safeguarded with transactional OTPs and email notifications.
- **📱 Social Feed & Ephemeral Stories**: Full social feed with explore streams, ephemeral stories, follower connections, direct messaging, and notification center.
- **🛡️ Administrative Governance**: Admin dashboard for monitoring user identities, uploaded media audit trails, forensic verification logs, and feedback management.

---

## 🏗️ Architecture & Apps

| Module / App | Description |
|---|---|
| **`image/`** | Face detection, landmark extraction, Euclidean vector comparison, image obfuscation/blurring, and story processing. |
| **`register/`** | Biometric enrollment, live camera capture verification, user profile setup, and credential management. |
| **`login/`** | Authentication gateway, session management, secure direct messaging, and transaction PIN authorization. |
| **`temp/`** | Core dashboard, interactive explore feed, live notification hub, and consent tag verification views. |
| **`varify/`** | Identity approval workflow and biometric authorization engine. |
| **`generate/`** | Automated PDF audit and compliance reporting. |
| **`feedback/` & `complaint/`** | Privacy violation complaints, ticket triage, and user feedback loop. |

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.9+
- CMake & C++ Build Tools (required for building `dlib`)
- Virtual environment (`venv` or `conda`)

### 2. Installation

Clone the repository:
```bash
git clone https://github.com/oyadarsh-hue/AssentTag-Consent-Based-Face-Privacy-Framework.git
cd AssentTag-Consent-Based-Face-Privacy-Framework
```

Create and activate a virtual environment:
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

Install dependencies:
```bash
pip install django opencv-python dlib numpy pillow cryptography
```

### 3. Database Migration
```bash
python manage.py makemigrations
python manage.py migrate
```

### 4. Run the Development Server
```bash
python manage.py runserver
```
Navigate to `http://127.0.0.1:8000/` in your browser.

For a one-click local launch, double-click **Start AssentTag.cmd**. It opens `http://127.0.0.1:8010/` and includes the background message-expiry worker. **Open AssentTag.url** opens that address when the server is already running. See [Disappearing messages](docs/DISAPPEARING_MESSAGES.md) for timer behaviour, upgrading existing databases and verification.

---

## 📖 System Design & Motion Specification

For detailed token system, UI typography, spatial grid, and "The Veil" motion design specifications, see [DESIGN.md](DESIGN.md).

The shared colorful visual layer is in `static/css/visual-experience.css` and `static/js/visual-experience.js`, included by every full-page template. Generated logo and image assets are kept in `static/assets/`. Motion respects the device's reduced-motion setting and adds no animation toggle.

For real Gmail OTP delivery, follow [Gmail setup](docs/GMAIL_SETUP.md). Run `python setup_email.py` to enter a Gmail App Password privately, restart Django, then use `python manage.py check_email --send-to YOUR_ADDRESS` to test delivery. A connected Codex Gmail account does not configure the application's SMTP sender automatically.

MySQL's `caching_sha2_password` authentication requires `cryptography`. This workspace has a project-local copy in the ignored `.runtime/` directory, which `manage.py` loads when present. For another environment, install the package normally.

---

## 📄 License
This project is licensed under the MIT License.
