import { jsPDF } from "jspdf";
import * as XLSX from "xlsx";

function money(n) {
  return `₦${Number(n || 0).toLocaleString()}`;
}

export function exportReportSummaryPdf(summary, businessName) {
  const doc = new jsPDF();
  const brand = businessName || "Vendora";
  doc.setFontSize(16);
  doc.text(`${brand} — Business report`, 14, 20);
  doc.setFontSize(9);
  doc.setTextColor(100);
  doc.text(`Range ${summary.range_start} → ${summary.range_end} · Generated ${new Date().toLocaleString()}`, 14, 28);
  doc.setTextColor(0);

  let y = 42;
  const lines = [
    `Total collected revenue ${money(summary.total_revenue)}`,
    `Monthly (calendar) ${money(summary.monthly_revenue)} · Weekly ${money(summary.weekly_revenue)} · YTD slice ${money(summary.yearly_revenue)}`,
    `Gross order value ${money(summary.gross_order_value)}`,
    `Pending balances ${money(summary.pending_balance_total)}`,
    `Paid captured ${money(summary.paid_revenue)} · Partial ${money(summary.partial_revenue)}`,
    `Orders analyzed ${summary.order_count} · Average order ${money(summary.average_order_value)}`,
    summary.delivery_success_rate != null
      ? `Delivery success estimate ${summary.delivery_success_rate}%`
      : "Delivery success — insufficient delivery rows in filter"
  ];
  lines.forEach((ln) => {
    doc.splitTextToSize(ln, 182).forEach((row) => {
      if (y > 280) {
        doc.addPage();
        y = 16;
      }
      doc.text(row, 14, y);
      y += 6;
    });
    y += 2;
  });
  doc.save(`vendora-report-${summary.range_start}-${summary.range_end}.pdf`);
}

export function exportReportSummaryXlsx(summary) {
  const rows = [];
  rows.push(["Metric", "Value"]);
  rows.push(["Range start", summary.range_start]);
  rows.push(["Range end", summary.range_end]);
  rows.push(["Total revenue", summary.total_revenue]);
  rows.push(["Monthly revenue", summary.monthly_revenue]);
  rows.push(["Weekly revenue", summary.weekly_revenue]);
  rows.push(["Yearly (slice)", summary.yearly_revenue]);
  rows.push(["Gross orders", summary.gross_order_value]);
  rows.push(["Pending balances", summary.pending_balance_total]);
  rows.push(["Paid revenue", summary.paid_revenue]);
  rows.push(["Partial revenue", summary.partial_revenue]);
  rows.push(["Order count", summary.order_count]);
  rows.push(["AOV", summary.average_order_value]);
  summary.bestsellers?.forEach((b) => {
    rows.push([`Bestseller: ${b.product}`, `${b.units_sold} units / ${b.revenue}`]);
  });
  summary.top_customers?.forEach((c) => {
    rows.push([`Customer: ${c.name}`, `${c.revenue}`]);
  });
  const ws = XLSX.utils.aoa_to_sheet(rows);
  const wb = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(wb, ws, "Summary");
  XLSX.writeFile(wb, `vendora-report-${summary.range_start}-${summary.range_end}.xlsx`);
}
