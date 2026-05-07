"""Generate lightweight PDF blobs for emailed monthly reports."""

from io import BytesIO


def monthly_report_pdf_bytes(*, business_name: str, period_label: str, metrics: dict) -> bytes:
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
    except ImportError:  # pragma: no cover
        tex = BytesIO()
        tex.write(b"ReportLab not installed.")
        return tex.getvalue()

    buff = BytesIO()
    pdf = canvas.Canvas(buff, pagesize=letter)
    width, height = letter
    y = height - 48
    title = business_name or "Vendora business"
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(40, y, title)
    y -= 24
    pdf.setFont("Helvetica", 11)
    pdf.drawString(40, y, f"Monthly business report — {period_label}")
    y -= 32
    lines = [
        f"Total collected revenue (month): ₦{metrics.get('revenue_month', 0):,}",
        f"Outstanding balances: ₦{metrics.get('pending_balance', 0):,}",
        f"Total customers: {metrics.get('total_customers', 0)}",
        f"Total orders (month): {metrics.get('orders_month', 0)}",
        f"Paid orders (month): {metrics.get('orders_paid', 0)}",
        f"Partial orders (month): {metrics.get('orders_partial', 0)}",
        f"Cancelled orders (month): {metrics.get('orders_cancelled', 0)}",
        f"Low stock SKU count: {metrics.get('low_stock', 0)}",
        f"Subscription status: {metrics.get('subscription_status', '-')}",
        f"Subscription plan: {metrics.get('plan', '-')}",
    ]
    for ln in lines:
        pdf.drawString(40, y, ln[:120])
        y -= 16
        if y < 60:
            pdf.showPage()
            y = height - 48
            pdf.setFont("Helvetica", 11)
    pdf.save()
    buff.seek(0)
    return buff.read()
