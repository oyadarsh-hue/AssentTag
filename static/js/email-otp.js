/* Countdown is presentation only: Django checks expiry, attempts and resend limits. */
(() => {
  const card = document.querySelector('[data-otp-remaining]');
  if (!card) return;
  const countdown = document.getElementById('otp-countdown');
  const input = document.getElementById('email-otp');
  const verify = document.getElementById('otp-verify');
  const resend = document.getElementById('otp-resend');
  const start = Date.now();
  const lifetime = Number(card.dataset.otpRemaining) || 0;
  const cooldown = Number(card.dataset.resendRemaining) || 0;
  let announced = false;
  const update = () => {
    const elapsed = Math.floor((Date.now() - start) / 1000);
    const left = Math.max(0, lifetime - elapsed);
    const wait = Math.max(0, cooldown - elapsed);
    resend.disabled = wait > 0;
    resend.textContent = wait > 0 ? `Resend OTP in ${wait}s` : 'Resend OTP';
    if (left > 0) {
      // Avoid announcing every second to screen readers.
      countdown.setAttribute('aria-live', 'off');
      countdown.textContent = `Code expires in ${Math.floor(left / 60)}:${String(left % 60).padStart(2, '0')}`;
    } else {
      input.disabled = true; verify.disabled = true;
      if (!announced) {
        countdown.setAttribute('aria-live', 'polite');
        countdown.textContent = lifetime > 0 ? 'OTP expired. Select Resend OTP for a new code.' : 'Select Resend OTP to receive a new code.';
        card.classList.add('at-otp-expired'); announced = true;
      }
    }
  };
  update();
  const timer = setInterval(() => {
    update();
    if (Date.now() - start >= Math.max(lifetime, cooldown) * 1000) clearInterval(timer);
  }, 1000);
  document.addEventListener('visibilitychange', update);
})();
