"""Email OTP sending via Resend."""
from __future__ import annotations

import os
import asyncio
import logging
import random

import resend

logger = logging.getLogger("labos.email")


def generate_otp() -> str:
    """Cryptographically-random 6-digit OTP."""
    return f"{random.SystemRandom().randint(0, 999999):06d}"


def _clean(name: str) -> str:
    return os.environ.get(name, "").strip().strip('"').strip("'")


def _otp_email_html(name: str, code: str) -> str:
    display_name = (name or "there").split(" ")[0]
    return f"""
<!doctype html>
<html>
<body style="margin:0;padding:0;background:#0a0a0a;font-family:Helvetica,Arial,sans-serif;color:#ffffff;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#0a0a0a;padding:40px 20px;">
    <tr>
      <td align="center">
        <table role="presentation" width="560" cellpadding="0" cellspacing="0" style="background:#141414;border:1px solid rgba(255,255,255,0.1);max-width:560px;">
          <tr>
            <td style="padding:32px 40px;border-bottom:1px solid rgba(255,255,255,0.08);">
              <div style="font-family:Helvetica,Arial,sans-serif;font-weight:800;font-size:22px;letter-spacing:-0.5px;color:#ffffff;">
                LABOS<span style="color:#FF7A00;">.</span>
              </div>
              <div style="color:#a3a3a3;font-size:11px;letter-spacing:2px;text-transform:uppercase;margin-top:4px;">
                Virtual IT Studio
              </div>
            </td>
          </tr>
          <tr>
            <td style="padding:40px;">
              <h1 style="margin:0 0 16px;font-size:26px;line-height:1.2;color:#ffffff;font-weight:800;letter-spacing:-0.5px;">
                Verify your email, {display_name}.
              </h1>
              <p style="margin:0 0 24px;color:#a3a3a3;font-size:15px;line-height:1.6;">
                Enter this 6-digit code on the verification screen to activate your LABOS account. The code expires in 10 minutes.
              </p>
              <div style="background:#0a0a0a;border:1px solid rgba(255,122,0,0.4);padding:24px;text-align:center;margin-bottom:24px;">
                <div style="font-family:Menlo,Consolas,monospace;font-size:36px;letter-spacing:12px;font-weight:700;color:#FF7A00;">
                  {code}
                </div>
              </div>
              <p style="margin:0;color:#737373;font-size:13px;line-height:1.6;">
                Didn't request this? You can safely ignore this email — nobody can access your account without the code.
              </p>
            </td>
          </tr>
          <tr>
            <td style="padding:24px 40px;border-top:1px solid rgba(255,255,255,0.08);color:#525252;font-size:12px;">
              © LABOS Technologies · Crafted with focus
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>
""".strip()


async def send_otp_email(to_email: str, name: str, code: str) -> None:
    """Fire the OTP email through Resend (non-blocking)."""
    api_key = _clean("RESEND_API_KEY")
    sender = _clean("SENDER_EMAIL") or "onboarding@resend.dev"

    if not api_key or "placeholder" in api_key.lower():
        raise RuntimeError(
            "Resend is not configured. Set RESEND_API_KEY in backend/.env "
            "(get one at https://resend.com/api-keys)."
        )

    resend.api_key = api_key
    params = {
        "from": f"LABOS Technologies <{sender}>",
        "to": [to_email],
        "subject": f"Your LABOS verification code: {code}",
        "html": _otp_email_html(name, code),
    }
    try:
        result = await asyncio.to_thread(resend.Emails.send, params)
        logger.info("OTP email sent to %s (resend id=%s)", to_email, result.get("id"))
    except Exception as e:
        logger.error("Resend send failed for %s: %s", to_email, e)
        raise
