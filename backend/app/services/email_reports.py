"""HTML email monthly summaries — requires SMTP env to actually send."""

import logging
from datetime import datetime

from app.core.config import settings

logger = logging.getLogger(__name__)


def build_monthly_report_html(
    *,
    business_name: str,
    month_label: str,
    total_revenue: int,
    order_count: int,
    pending_balance: int,
) -> str:
    name = business_name or "Your business"
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Monthly report</title></head>
<body style="font-family:system-ui,sans-serif;background:#f4f4f5;padding:24px;">
  <div style="max-width:560px;margin:0 auto;background:#fff;border-radius:12px;padding:28px;">
    <h1 style="font-size:20px;margin:0 0 8px;">{name}</h1>
    <p style="color:#64748b;margin:0 0 24px;">{month_label} summary</p>
    <table style="width:100%;border-collapse:collapse;">
      <tr><td style="padding:8px 0;">Collected revenue</td><td style="text-align:right;font-weight:600;">₦{total_revenue:,}</td></tr>
      <tr><td style="padding:8px 0;">Orders</td><td style="text-align:right;font-weight:600;">{order_count}</td></tr>
      <tr><td style="padding:8px 0;">Pending balances</td><td style="text-align:right;font-weight:600;">₦{pending_balance:,}</td></tr>
    </table>
  </div>
</body></html>"""


def send_monthly_report_stub(to_email: str, html: str) -> bool:
    if not settings.SMTP_HOST:
        logger.info(
            "SMTP not configured — report for %s generated at %s",
            to_email,
            datetime.utcnow().isoformat(),
        )
        return False
    logger.info("Would send email to %s (%d bytes)", to_email, len(html))
    return True
