import random
import string

import resend

from app.core.config import settings

resend.api_key = settings.resend_api_key


def generate_otp() -> str:
    return "".join(random.choices(string.digits, k=6))


def _build_otp_email(otp: str, full_name: str | None = None) -> str:
    name = full_name or "there"
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Verify your Substrate account</title>
</head>
<body style="margin:0;padding:0;background-color:#f8fafc;font-family:'Inter',Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background-color:#f8fafc;padding:40px 0;">
    <tr>
      <td align="center">
        <table width="560" cellpadding="0" cellspacing="0" style="background-color:#ffffff;border-radius:12px;border:1px solid #e2e8f0;overflow:hidden;">

          <!-- Header -->
          <tr>
            <td style="background-color:#4f46e5;padding:32px 40px;">
              <p style="margin:0;font-size:20px;font-weight:700;color:#ffffff;letter-spacing:-0.3px;">
                &#9632; Substrate
              </p>
              <p style="margin:6px 0 0;font-size:13px;color:#c7d2fe;">
                The memory layer for multi-agent AI
              </p>
            </td>
          </tr>

          <!-- Body -->
          <tr>
            <td style="padding:40px;">
              <p style="margin:0 0 8px;font-size:24px;font-weight:700;color:#0f172a;letter-spacing:-0.4px;">
                Verify your email
              </p>
              <p style="margin:0 0 32px;font-size:15px;color:#64748b;line-height:1.6;">
                Hi {name}, welcome to Substrate! Use the code below to verify
                your email address. It expires in <strong>10 minutes</strong>.
              </p>

              <!-- OTP Box -->
              <table width="100%" cellpadding="0" cellspacing="0">
                <tr>
                  <td align="center">
                    <div style="display:inline-block;background-color:#f1f5f9;border:2px dashed #cbd5e1;border-radius:12px;padding:24px 48px;margin-bottom:32px;">
                      <p style="margin:0;font-size:42px;font-weight:800;color:#4f46e5;letter-spacing:12px;font-family:'Courier New',monospace;">
                        {otp}
                      </p>
                    </div>
                  </td>
                </tr>
              </table>

              <p style="margin:0 0 24px;font-size:14px;color:#64748b;line-height:1.6;">
                Enter this code on the verification page to activate your
                account and start building with Substrate.
              </p>

              <!-- CTA Button -->
              <table width="100%" cellpadding="0" cellspacing="0">
                <tr>
                  <td align="center" style="padding-bottom:32px;">
                    <a href="{settings.frontend_url}/verify-email"
                       style="display:inline-block;background-color:#4f46e5;color:#ffffff;
                              font-size:14px;font-weight:600;text-decoration:none;
                              padding:12px 32px;border-radius:8px;">
                      Verify my account →
                    </a>
                  </td>
                </tr>
              </table>

              <!-- Divider -->
              <hr style="border:none;border-top:1px solid #e2e8f0;margin:0 0 24px;" />

              <!-- What's next -->
              <p style="margin:0 0 12px;font-size:13px;font-weight:600;color:#0f172a;">
                What happens next?
              </p>
              <table width="100%" cellpadding="0" cellspacing="0">
                <tr>
                  <td style="padding:6px 0;">
                    <p style="margin:0;font-size:13px;color:#64748b;">
                      &#10003; &nbsp;Register your AI agents
                    </p>
                  </td>
                </tr>
                <tr>
                  <td style="padding:6px 0;">
                    <p style="margin:0;font-size:13px;color:#64748b;">
                      &#10003; &nbsp;Publish and subscribe to context
                    </p>
                  </td>
                </tr>
                <tr>
                  <td style="padding:6px 0;">
                    <p style="margin:0;font-size:13px;color:#64748b;">
                      &#10003; &nbsp;Watch your agents work together live
                    </p>
                  </td>
                </tr>
              </table>

              <hr style="border:none;border-top:1px solid #e2e8f0;margin:24px 0;" />

              <p style="margin:0;font-size:12px;color:#94a3b8;line-height:1.6;">
                If you didn't create a Substrate account, you can safely ignore
                this email. This code will expire automatically in 10 minutes.
              </p>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="background-color:#f8fafc;padding:20px 40px;border-top:1px solid #e2e8f0;">
              <p style="margin:0;font-size:12px;color:#94a3b8;text-align:center;">
                &#9632; Substrate &nbsp;·&nbsp; The memory layer for multi-agent AI
                <br/>
                <a href="{settings.frontend_url}"
                   style="color:#4f46e5;text-decoration:none;">
                  substrate-frontend.vercel.app
                </a>
              </p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""


async def send_otp_email(
    email: str,
    otp: str,
    full_name: str | None = None
) -> bool:
    try:
        resend.Emails.send({
            "from": f"{settings.from_name} <{settings.from_email}>",
            "to": [email],
            "subject": f"{otp} is your Substrate verification code",
            "html": _build_otp_email(otp, full_name),
        })
        return True
    except Exception as e:
        print(f"Failed to send OTP email: {e}")
        return False