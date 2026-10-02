# Disappearing messages

The old Auto-Delete dropdown has been replaced with shared conversation settings. Choose **Off**, **1 minute**, **24 hours**, **7 days**, or **90 days**. The one-minute option makes a short demonstration possible. Open settings from the timer beside the contact name or above the composer.

## Behaviour

- Either mutual follower can change the timer for their conversation. The saved setting is shared across devices and restored on reload.
- Each new message captures the conversation's duration on the server. Its deadline is independent of when it is read. A countdown ring and remaining time appear on both sides.
- Turning the timer off keeps future messages. It does not cancel the deadlines of messages already sent. The settings dialog explains this before saving.
- A financial message retains its selected duration through email verification. Its expiry starts only when verification succeeds and the message is actually created. Changing the pending duration invalidates its OTP.
- Settings have a revision number. A stale browser cannot silently overwrite a newer setting; it receives the current setting and must review it again.
- Message polling every five seconds updates the other participant's messages and timer. The countdown uses server time with a monotonic browser clock, updates each second, and resynchronizes after reconnecting or reopening the tab.
- Expired messages are excluded from responses and deleted on conversation access. The local server also removes expired rows every 30 seconds even when no chat is open. Thus a closed browser cannot extend a deadline.
- All settings writes require login, mutual following and CSRF protection. The old read endpoint now requires POST and the actual recipient. It no longer deletes a message just because it was viewed.
- Chat responses cannot be cached. Rendered messages remain HTML-escaped. This feature is not end-to-end encryption and cannot erase screenshots, copied text or independent backups.

## Upgrade and start locally

Double-click **Start AssentTag.cmd** in the project folder. It checks the database schema, starts the server and cleanup worker in the background, and opens **http://127.0.0.1:8010/**. MySQL must already be running with the project's configured connection. If the site is already running, the launcher opens it without starting a second copy. Restart an old running server after a code update.

**Open AssentTag.url** is a direct browser shortcut when the server is already running. Both files use their own folder location; the launcher also works from `Copy (2)`. They are local shortcuts, not public hosting links.

Manual equivalent:

```powershell
python manage.py prepare_chat
python manage.py run_chat_server 127.0.0.1:8010 --noreload
```

`prepare_chat` validates pre-existing legacy table columns before adopting missing migration baselines. Subsequent migrations add the message duration/deadline and the shared conversation table. Pre-existing disappearing messages receive a full 24 hours from upgrade, avoiding deletion merely because this update was installed. Untimed messages retain their contents and have no deadline.

For a production server, run `python manage.py purge_expired_messages` every minute using the hosting platform's scheduler; the local cleanup worker is part of the development server only. Visibility always checks deadlines on the server regardless of cleanup scheduling.

## Verification

```powershell
python manage.py test login image register --settings=assentag.test_settings
python tools/verify_chat_timers.py
```

Unit and database integration tests use an isolated in-memory SQLite database. The live browser check creates two temporary accounts, exercises shared settings, stale writes, Off, reloads, mobile layout and a real one-minute expiry, then removes only those test accounts and their messages. Screenshots are written to ignored `output/ui/`.
