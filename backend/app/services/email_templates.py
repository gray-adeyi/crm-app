from datetime import date, time


def _fmt_date(d: date | None) -> str:
    if not d:
        return "—"
    return d.strftime("%d %B %Y")


def _fmt_time(t: time | None) -> str:
    if not t:
        return "—"
    # Windows strftime doesn't support %-I; use %I then strip leading zero.
    return t.strftime("%I:%M %p").lstrip("0") if hasattr(t, "strftime") else str(t)


def build_order_created_email_html(
    *,
    business_name: str | None,
    customer_name: str,
    product_name: str,
    quantity: int,
    amount_paid: int,
    balance: int,
    delivery_date: date | None,
    delivery_time: time | None,
    order_status: str,
    fulfillment_type: str = "delivery",
    delivery_address: str | None = None,
    payment_label: str | None = None,
    headline: str | None = None,
) -> str:
    name = business_name or "Your business"
    ft = (fulfillment_type or "delivery").lower()
    mode = "Pickup" if ft == "pickup" else "Delivery"
    title = headline or f"New Order — {mode}"
    intro = (
        "A new pickup order is ready to prepare. Coordinate collection with your customer."
        if ft == "pickup"
        else "You have a delivery order scheduled. Please confirm address, timing, and payment."
    )
    addr_row = ""
    if ft == "delivery" and delivery_address:
        addr_row = f'<tr><td style="padding:10px 0;color:#334155;">Delivery address</td><td style="padding:10px 0;text-align:right;font-weight:600;color:#0f172a;">{delivery_address}</td></tr>'
    pay_row = ""
    if payment_label:
        pay_row = f'<tr><td style="padding:10px 0;color:#334155;">Payment status</td><td style="padding:10px 0;text-align:right;font-weight:600;color:#0f172a;">{payment_label}</td></tr>'
    dl_rows = ""
    if ft == "delivery":
        dl_rows = f"""<tr><td style="padding:10px 0;color:#334155;">Delivery Date</td><td style="padding:10px 0;text-align:right;font-weight:600;color:#0f172a;">{_fmt_date(delivery_date)}</td></tr>
        <tr><td style="padding:10px 0;color:#334155;">Delivery Time</td><td style="padding:10px 0;text-align:right;font-weight:600;color:#0f172a;">{_fmt_time(delivery_time)}</td></tr>"""
    return f"""<!DOCTYPE html>
<html>
  <head><meta charset="utf-8" /><title>New order</title></head>
  <body style="font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;background:#f4f4f5;padding:24px;">
    <div style="max-width:640px;margin:0 auto;background:#ffffff;border-radius:14px;padding:28px;border:1px solid #e4e4e7;">
      <div style="margin-bottom:18px;">
        <div style="font-size:14px;color:#64748b;">{name}</div>
        <h1 style="font-size:20px;margin:6px 0 0;color:#0f172a;">{title}</h1>
        <p style="margin:10px 0 0;color:#475569;font-size:14px;">
          {intro}
        </p>
      </div>

      <table style="width:100%;border-collapse:collapse;font-size:14px;">
        <tr><td style="padding:10px 0;color:#334155;">Customer</td><td style="padding:10px 0;text-align:right;font-weight:600;color:#0f172a;">{customer_name}</td></tr>
        <tr><td style="padding:10px 0;color:#334155;">Product</td><td style="padding:10px 0;text-align:right;font-weight:600;color:#0f172a;">{product_name}</td></tr>
        <tr><td style="padding:10px 0;color:#334155;">Quantity</td><td style="padding:10px 0;text-align:right;font-weight:600;color:#0f172a;">{int(quantity)}</td></tr>
        <tr><td style="padding:10px 0;color:#334155;">Amount Paid</td><td style="padding:10px 0;text-align:right;font-weight:600;color:#0f172a;">₦{int(amount_paid):,}</td></tr>
        <tr><td style="padding:10px 0;color:#334155;">Balance</td><td style="padding:10px 0;text-align:right;font-weight:600;color:#0f172a;">₦{int(balance):,}</td></tr>
        {pay_row}
        {addr_row}
        {dl_rows}
        <tr><td style="padding:10px 0;color:#334155;">Order Status</td><td style="padding:10px 0;text-align:right;font-weight:600;color:#0f172a;">{order_status}</td></tr>
      </table>
    </div>
  </body>
</html>"""


def build_low_stock_email_html(
    *,
    business_name: str | None,
    product_name: str,
    remaining: int,
    threshold: int,
    restock_tip: int,
    peak_quantity: int,
) -> str:
    name = business_name or "Your business"
    peak_line = (
        f'<tr><td style="padding:10px 0;color:#334155;">Peak stock</td><td style="padding:10px 0;text-align:right;font-weight:600;color:#0f172a;">{int(peak_quantity)}</td></tr>'
        if peak_quantity
        else ""
    )
    return f"""<!DOCTYPE html>
<html>
  <head><meta charset="utf-8" /><title>Low stock alert</title></head>
  <body style="font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;background:#f4f4f5;padding:24px;">
    <div style="max-width:640px;margin:0 auto;background:#ffffff;border-radius:14px;padding:28px;border:1px solid #e4e4e7;">
      <div style="font-size:14px;color:#64748b;">{name}</div>
      <h1 style="font-size:20px;margin:6px 0 0;color:#0f172a;">Low Stock Alert — Restock Needed</h1>
      <p style="margin:12px 0 0;color:#475569;font-size:14px;">
        Your inventory for <strong>{product_name}</strong> is running low<span style="color:#94a3b8;"> (~10% of peak or below threshold).</span>
      </p>
      <table style="width:100%;border-collapse:collapse;font-size:14px;margin-top:16px;">
        <tr><td style="padding:10px 0;color:#334155;">Remaining Units</td><td style="padding:10px 0;text-align:right;font-weight:600;color:#0f172a;">{int(remaining)}</td></tr>
        {peak_line}
        <tr><td style="padding:10px 0;color:#334155;">Threshold Level</td><td style="padding:10px 0;text-align:right;font-weight:600;color:#0f172a;">{int(threshold)}</td></tr>
        <tr><td style="padding:10px 0;color:#334155;">Recommended restock amount</td><td style="padding:10px 0;text-align:right;font-weight:600;color:#0f172a;">{int(max(restock_tip, 1))} units</td></tr>
      </table>
      <p style="margin:16px 0 0;color:#475569;font-size:14px;">Please restock this item soon to avoid stockout.</p>
    </div>
  </body>
</html>"""


def build_vendor_welcome_email_html(*, dashboard_url: str, user_email: str) -> str:
    return f"""<!DOCTYPE html>
<html>
  <head><meta charset="utf-8" /><meta name="viewport" content="width=device-width, initial-scale=1" /><title>Welcome to Vendora</title></head>
  <body style="margin:0;background:#0f172a;font-family:Inter,system-ui,-apple-system,Segoe UI,Roboto,sans-serif;">
    <div style="padding:32px 16px;">
      <div style="max-width:600px;margin:0 auto;border-radius:20px;overflow:hidden;background:#fff;box-shadow:0 25px 60px rgba(15,23,42,.35);">
        <div style="padding:28px 28px 20px;background:linear-gradient(135deg,#4f46e5,#7c3aed);color:#fff;">
          <p style="margin:0;font-size:13px;letter-spacing:.08em;text-transform:uppercase;opacity:.85;">Vendora CRM</p>
          <h1 style="margin:10px 0 0;font-size:24px;line-height:1.25;">Welcome to Vendora 🚀</h1>
          <p style="margin:12px 0 0;font-size:15px;line-height:1.6;opacity:.95;">
            Thanks for joining from <strong>{user_email}</strong>. You now have a full premium trial to run your online business with confidence.
          </p>
        </div>
        <div style="padding:28px;color:#0f172a;font-size:15px;line-height:1.65;">
          <p style="margin:0 0 14px;">Vendora helps online vendors track sales, customers, inventory, and deliveries in one premium workspace — similar to the clarity you expect from Stripe or Shopify admin.</p>
          <ul style="margin:0;padding-left:20px;color:#334155;">
            <li><strong>Orders &amp; payments</strong> — partial payments, balances, delivery windows, and pickup workflows.</li>
            <li><strong>Customers</strong> — relationship history and fast lookup.</li>
            <li><strong>Inventory</strong> — live stock, low-stock intelligence, and movement history.</li>
            <li><strong>Analytics</strong> — revenue, outstanding balances, and operational widgets.</li>
            <li><strong>Automations</strong> — smart email reminders, monthly reports, and alerts to your vendor inbox.</li>
          </ul>
          <p style="margin:18px 0 0;">Your <strong>30-day trial</strong> unlocks every premium capability. When you are ready, pick a plan that fits your growth — billing is handled securely via Paystack.</p>
          <div style="margin:28px 0;text-align:center;">
            <a href="{dashboard_url}" style="display:inline-block;padding:14px 26px;border-radius:999px;background:#4f46e5;color:#fff;font-weight:600;text-decoration:none;">Open your dashboard</a>
          </div>
          <div style="padding:18px;border-radius:14px;background:#f8fafc;border:1px solid #e2e8f0;">
            <p style="margin:0;font-size:14px;color:#475569;"><strong>Next steps:</strong> finish onboarding, import a few products, and create your first order. Our monthly insights land automatically in this inbox.</p>
          </div>
          <p style="margin:24px 0 0;font-size:13px;color:#94a3b8;">Need help? Reply to this message or contact support from the in-app billing center.</p>
        </div>
      </div>
    </div>
  </body>
</html>"""


def build_saas_monthly_report_html(*, user, metrics: dict, month_label: str) -> str:
    brand = user.business_name or "Your business"
    bestsellers = metrics.get("bestsellers") or []
    rows = ""
    for name, qty in bestsellers:
        rows += f'<tr><td style="padding:8px 0;border-bottom:1px solid #f1f5f9;">{name}</td><td style="padding:8px 0;border-bottom:1px solid #f1f5f9;text-align:right;font-weight:600;">{int(qty or 0)}</td></tr>'
    if not rows:
        rows = '<tr><td colspan="2" style="padding:12px 0;color:#94a3b8;">No product movement recorded this month.</td></tr>'

    low_rows = ""
    for row in metrics.get("low_stock_rows") or []:
        low_rows += f'<tr><td style="padding:8px 0;border-bottom:1px solid #f1f5f9;">{row["name"]}</td><td style="padding:8px 0;border-bottom:1px solid #f1f5f9;text-align:right;">{row["qty"]}</td></tr>'
    if not low_rows:
        low_rows = '<tr><td colspan="2" style="padding:12px 0;color:#94a3b8;">No low-stock SKUs flagged.</td></tr>'

    trial_note = (
        "Trial active — enjoy every premium module."
        if metrics.get("trial_active")
        else "Subscription required after trial — upgrade anytime in Billing."
    )

    return f"""<!DOCTYPE html>
<html>
  <head><meta charset="utf-8" /><title>Monthly report</title></head>
  <body style="margin:0;background:#f4f4f5;padding:24px;font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;">
    <div style="max-width:640px;margin:0 auto;background:#fff;border-radius:16px;padding:32px;border:1px solid #e2e8f0;">
      <p style="margin:0;font-size:13px;color:#6366f1;font-weight:600;letter-spacing:.08em;text-transform:uppercase;">Vendora Intelligence</p>
      <h1 style="margin:8px 0 4px;font-size:22px;color:#0f172a;">{brand}</h1>
      <p style="margin:0;color:#64748b;">{month_label} performance digest</p>
      <p style="margin:16px 0 0;font-size:14px;color:#475569;">{trial_note} A detailed PDF is attached for your records.</p>

      <div style="margin-top:24px;display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px;">
        <div style="padding:16px;border-radius:12px;background:#f8fafc;">
          <p style="margin:0;font-size:12px;color:#64748b;">Collected revenue</p>
          <p style="margin:6px 0 0;font-size:20px;font-weight:700;color:#0f172a;">₦{metrics.get("revenue_month", 0):,}</p>
        </div>
        <div style="padding:16px;border-radius:12px;background:#f8fafc;">
          <p style="margin:0;font-size:12px;color:#64748b;">Outstanding balances</p>
          <p style="margin:6px 0 0;font-size:20px;font-weight:700;color:#0f172a;">₦{metrics.get("pending_balance", 0):,}</p>
        </div>
      </div>

      <table style="width:100%;margin-top:24px;font-size:14px;border-collapse:collapse;">
        <tr><td style="padding:6px 0;">Customers</td><td style="text-align:right;font-weight:600;">{metrics.get("total_customers", 0)}</td></tr>
        <tr><td style="padding:6px 0;">Orders (month)</td><td style="text-align:right;font-weight:600;">{metrics.get("orders_month", 0)}</td></tr>
        <tr><td style="padding:6px 0;">Paid orders</td><td style="text-align:right;font-weight:600;">{metrics.get("orders_paid", 0)}</td></tr>
        <tr><td style="padding:6px 0;">Partial payments</td><td style="text-align:right;font-weight:600;">{metrics.get("orders_partial", 0)}</td></tr>
        <tr><td style="padding:6px 0;">Cancelled orders</td><td style="text-align:right;font-weight:600;">{metrics.get("orders_cancelled", 0)}</td></tr>
        <tr><td style="padding:6px 0;">Low stock SKU</td><td style="text-align:right;font-weight:600;">{metrics.get("low_stock", 0)}</td></tr>
      </table>

      <h2 style="margin:28px 0 8px;font-size:15px;color:#0f172a;">Best sellers</h2>
      <table style="width:100%;font-size:13px;color:#475569">{rows}</table>

      <h2 style="margin:24px 0 8px;font-size:15px;color:#0f172a;">Low stock spotlight</h2>
      <table style="width:100%;font-size:13px;color:#475569">{low_rows}</table>

      <p style="margin:28px 0 0;font-size:12px;color:#94a3b8;">Plan: <strong>{metrics.get("plan", "-")}</strong> • Status: <strong>{metrics.get("subscription_status", "-")}</strong></p>
    </div>
  </body>
</html>"""


def build_activity_digest_email_html(*, user, acts, txs, month_label: str) -> str:
    brand = user.business_name or "Your business"
    bullets_a = "".join(
        [
            f'<li>{a.summary or a.action} — <span style="color:#64748b">{a.entity_type}</span></li>'
            for a in acts[:25]
        ]
    )
    if not bullets_a:
        bullets_a = "<li>No recorded edits this month.</li>"
    bullets_t = "".join([f"<li>{t.summary}</li>" for t in txs[:25]])
    if not bullets_t:
        bullets_t = "<li>No billing or transaction ledger entries captured.</li>"

    return f"""<!DOCTYPE html>
<html>
  <head><meta charset="utf-8" /><title>Activity digest</title></head>
  <body style="margin:0;background:#f4f4f5;padding:24px;font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;">
    <div style="max-width:640px;margin:0 auto;background:#fff;border-radius:16px;padding:32px;border:1px solid #e2e8f0;">
      <p style="margin:0;font-size:13px;color:#64748b;">{brand}</p>
      <h1 style="margin:10px 0 0;font-size:22px;color:#0f172a;">Monthly activity recap</h1>
      <p style="margin:10px 0 0;color:#475569;font-size:14px;">Operational trail for <strong>{month_label}</strong> — mirrored from your CRM audit feeds.</p>
      <div style="margin-top:28px;">
        <h2 style="font-size:15px;color:#0f172a;">Records & edits</h2>
        <ul style="margin:10px 0 0;padding-left:18px;line-height:1.6;color:#334155;font-size:14px;">{bullets_a}</ul>
      </div>
      <div style="margin-top:24px;">
        <h2 style="font-size:15px;color:#0f172a;">Transactions</h2>
        <ul style="margin:10px 0 0;padding-left:18px;line-height:1.6;color:#334155;font-size:14px;">{bullets_t}</ul>
      </div>
      <p style="margin-top:28px;font-size:12px;color:#94a3b8;">Need deeper exports? Upgrade to Enterprise for advanced workflows.</p>
    </div>
  </body>
</html>"""


def build_verification_otp_email_html(
    *,
    company_name: str | None,
    email: str,
    otp_code: str,
    expires_minutes: int,
    support_email: str,
    app_url: str,
) -> str:
    brand = company_name or "Vendora"
    return f"""<!DOCTYPE html>
<html>
  <head><meta charset="utf-8" /><title>Verify your email</title></head>
  <body style="margin:0;background:#f4f4f5;padding:32px;font-family:system-ui,-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0"><tr><td align="center">
      <div style="max-width:520px;text-align:left;background:#ffffff;border-radius:16px;padding:36px 32px;box-shadow:0 25px 50px -12px rgba(15,23,42,0.08);border:1px solid #e2e8f0;">
        <p style="margin:0;font-size:13px;color:#64748b;letter-spacing:0.06em;text-transform:uppercase;">Vendora</p>
        <h1 style="margin:14px 0 0;font-size:24px;font-weight:650;color:#0f172a;">Confirm your inbox</h1>
        <p style="margin:14px 0 0;line-height:1.6;color:#475569;font-size:15px;">
          Hi — you are almost inside <strong>{brand}</strong>. Use this one-time code to verify <strong>{email}</strong> and activate your CRM workspace.
        </p>
        <div style="margin:28px 0;text-align:center;">
          <div style="display:inline-block;padding:14px 32px;background:linear-gradient(135deg,#4f46e5,#6366f1);color:#ffffff;font-size:28px;font-weight:700;border-radius:12px;letter-spacing:0.4em;font-family:'SF Mono',ui-monospace,monospace;">
            {otp_code}
          </div>
        </div>
        <p style="margin:0;font-size:13px;color:#94a3b8;">
          Expires in <strong>{expires_minutes} minutes</strong>. If you did not request this, you can safely ignore this message.
        </p>
        <hr style="margin:28px 0;border:none;border-top:1px solid #e2e8f0;" />
        <p style="margin:0;font-size:13px;color:#475569;line-height:1.6;">
          Need help? <a href="mailto:{support_email}" style="color:#4f46e5;">{support_email}</a><br/>
          <a href="{app_url}" style="color:#4f46e5;text-decoration:none;">Open dashboard</a>
        </p>
      </div>
    </td></tr></table>
  </body>
</html>"""
