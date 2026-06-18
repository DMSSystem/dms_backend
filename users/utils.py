# users/utils.py
import logging
from django.core.mail import EmailMultiAlternatives
from django.conf import settings

logger = logging.getLogger(__name__)


# ── HTML Email Template ─────────────────────────────────────

def build_otp_email_html(user, otp_code):
    """Returns a branded HTML email body for OTP verification."""
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>DMS Verification</title>
</head>
<body style="margin:0;padding:0;background-color:#f4f6f9;font-family:Arial,sans-serif;">

  <table width="100%" cellpadding="0" cellspacing="0" style="background-color:#f4f6f9;padding:40px 0;">
    <tr>
      <td align="center">
        <table width="600" cellpadding="0" cellspacing="0"
               style="background-color:#ffffff;border-radius:12px;
                      overflow:hidden;box-shadow:0 4px 16px rgba(0,0,0,0.08);
                      max-width:600px;width:100%;">

          <!-- Header -->
          <tr>
            <td style="background:linear-gradient(135deg,#1A3A6B 0%,#2E4F8A 60%,#3A6BBF 100%);
                       padding:36px 40px;text-align:center;">
              <div style="font-size:28px;margin-bottom:6px;">🏫</div>
              <h1 style="margin:0;color:#ffffff;font-size:26px;font-weight:bold;
                         letter-spacing:0.5px;">
                Dormitory Management System
              </h1>
              <p style="margin:8px 0 0;color:#ccd9f0;font-size:14px;">
                Secure Account Verification
              </p>
            </td>
          </tr>

          <!-- Body -->
          <tr>
            <td style="padding:40px 40px 24px;">
              <p style="margin:0 0 16px;font-size:16px;color:#222222;">
                Hello <strong>{user.full_name}</strong>,
              </p>
              <p style="margin:0 0 24px;font-size:15px;color:#444444;line-height:1.7;">
                {'Welcome to the DMS! To activate your account and get started, please verify your email address using the code below.' if not user.is_verified else 'You requested a new verification code. Use the code below to verify your account.'}
              </p>

              <!-- OTP Box -->
              <table width="100%" cellpadding="0" cellspacing="0">
                <tr>
                  <td align="center" style="padding:8px 0 32px;">
                    <p style="margin:0 0 12px;font-size:13px;color:#666666;
                               text-transform:uppercase;letter-spacing:1px;">
                      Your verification code
                    </p>
                    <div style="display:inline-block;background:#f0f4ff;
                                border:2px dashed #2E4F8A;border-radius:12px;
                                padding:20px 48px;">
                      <span style="font-size:42px;font-weight:bold;
                                   letter-spacing:12px;color:#1A3A6B;
                                   font-family:'Courier New',monospace;">
                        {otp_code}
                      </span>
                    </div>
                    <p style="margin:14px 0 0;font-size:13px;color:#e05a2b;font-weight:bold;">
                      ⏱ This code expires in <strong>10 minutes</strong>
                    </p>
                  </td>
                </tr>
              </table>

              <!-- Role-specific message -->
              {'<p style="margin:0 0 24px;font-size:15px;color:#444444;line-height:1.7;">Once verified, you will be able to <strong>view your child\'s leave-out records, dormitory status, and receive important notifications</strong> from the school.</p>' if user.role == 'parent' else '<p style="margin:0 0 24px;font-size:15px;color:#444444;line-height:1.7;">Once verified, you will be able to <strong>manage leave-out requests, submit maintenance reports, record inspections, and view duty rosters</strong>.</p>'}

              <!-- Security note -->
              <table width="100%" cellpadding="0" cellspacing="0">
                <tr>
                  <td style="background:#fff8f0;border-left:4px solid #e05a2b;
                              border-radius:0 8px 8px 0;padding:14px 18px;margin-bottom:24px;">
                    <p style="margin:0;font-size:13px;color:#7a3a10;line-height:1.6;">
                      🔒 <strong>Security tip:</strong> Never share this code with anyone,
                      including school staff. The DMS team will never ask for your OTP.
                    </p>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- Divider -->
          <tr>
            <td style="padding:0 40px;">
              <hr style="border:none;border-top:1px solid #eeeeee;margin:0;"/>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="padding:24px 40px 36px;text-align:center;">
              <p style="margin:0 0 6px;font-size:13px;color:#888888;">
                If you did not create an account on the DMS, please ignore this email.
              </p>
              <p style="margin:0;font-size:13px;color:#888888;">
                &copy; {__import__('datetime').date.today().year} Dormitory Management System &nbsp;|&nbsp;
                <span style="color:#2E4F8A;">Egerton University</span>
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


def build_otp_email_text(user, otp_code):
    """Plain text fallback for email clients that don't render HTML."""
    return f"""
Hello {user.full_name},

Your DMS verification code is: {otp_code}

This code expires in 10 minutes.

Do not share this code with anyone.

If you did not create a DMS account, please ignore this email.

— Dormitory Management System
""".strip()


# ── Send functions ──────────────────────────────────────────

def send_otp_email(user, otp_code):
    """
    Send a branded HTML OTP email to the user.
    Falls back to plain text for clients that don't support HTML.
    """
    subject = "DMS — Your Verification Code"
    from_email = settings.DEFAULT_FROM_EMAIL
    to = [user.email]

    text_content = build_otp_email_text(user, otp_code)
    html_content = build_otp_email_html(user, otp_code)

    try:
        msg = EmailMultiAlternatives(subject, text_content, from_email, to)
        msg.attach_alternative(html_content, "text/html")
        msg.send()
        logger.info(f"OTP email sent to {user.email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send OTP email to {user.email}: {e}")
        return False

def send_otp(user, method='email'):
    """Always sends via email. method param kept for future extensibility."""
    otp_code = user.generate_otp()
    success = send_otp_email(user, otp_code)
    return success, otp_code