import { jsPDF } from "jspdf";
import * as XLSX from "xlsx";

function orderTotal(order) {
  return Number(order.total_price ?? order.price ?? 0);
}

export function exportCustomersPdf(customers, title = "Customers") {
  const doc = new jsPDF();
  doc.setFontSize(15);
  doc.text(title, 14, 18);
  doc.setFontSize(9);
  doc.setTextColor(100);
  doc.text(`Generated ${new Date().toLocaleString()}`, 14, 26);
  doc.setTextColor(0);
  let y = 36;
  customers.forEach((c) => {
    const line = `${c.name} · ${c.phone}${c.instagram_handle ? " · @" + c.instagram_handle : ""}`;
    const split = doc.splitTextToSize(line, 180);
    split.forEach((t) => {
      if (y > 285) {
        doc.addPage();
        y = 16;
      }
      doc.text(t, 14, y);
      y += 5;
    });
    y += 2;
  });
  doc.save("customers-export.pdf");
}

export function exportOrdersPdf(orders, customers, title = "Orders") {
  const nameById = Object.fromEntries(customers.map((c) => [c.id, c.name]));
  const doc = new jsPDF();
  doc.setFontSize(15);
  doc.text(title, 14, 18);
  doc.setFontSize(9);
  doc.setTextColor(100);
  doc.text(`Generated ${new Date().toLocaleString()}`, 14, 26);
  doc.setTextColor(0);
  let y = 36;
  orders.forEach((o) => {
    const line = `#${o.id} ${o.product} · ${nameById[o.customer_id] || "Customer"} · ₦${orderTotal(o).toLocaleString()} · ${o.status}`;
    const split = doc.splitTextToSize(line, 180);
    split.forEach((t) => {
      if (y > 285) {
        doc.addPage();
        y = 16;
      }
      doc.text(t, 14, y);
      y += 5;
    });
    y += 2;
  });
  doc.save("orders-export.pdf");
}

export function exportOrdersXlsx(orders) {
  const rows = orders.map((o) => ({
    id: o.id,
    product: o.product,
    total_price: orderTotal(o),
    amount_paid: o.amount_paid,
    balance: o.balance,
    status: o.status,
    customer_id: o.customer_id,
    payment_method: o.payment_method || "",
    notes: o.notes || "",
    created_at: o.created_at || ""
  }));
  const ws = XLSX.utils.json_to_sheet(rows);
  const wb = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(wb, ws, "Orders");
  XLSX.writeFile(wb, "orders-export.xlsx");
}

export function exportCustomersXlsx(customers) {
  const ws = XLSX.utils.json_to_sheet(customers);
  const wb = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(wb, ws, "Customers");
  XLSX.writeFile(wb, "customers-export.xlsx");
}

export function exportRevenueReportPdf(dashboard) {
  const doc = new jsPDF();
  doc.setFontSize(15);
  doc.text("Revenue report", 14, 18);
  doc.setFontSize(10);
  let y = 30;
  const lines = [
    `Total collected revenue: ₦${Number(dashboard.total_revenue || 0).toLocaleString()}`,
    `Gross order value: ₦${Number(dashboard.gross_sales || 0).toLocaleString()}`,
    `Outstanding balances: ₦${Number(dashboard.outstanding_balance || 0).toLocaleString()}`,
    `This month collected: ₦${Number(dashboard.monthly_revenue || 0).toLocaleString()}`,
    `Orders — pending: ${dashboard.orders_pending}, partial: ${dashboard.orders_partial}, paid: ${dashboard.orders_paid}`
  ];
  lines.forEach((t) => {
    doc.text(t, 14, y);
    y += 8;
  });
  doc.save("revenue-report.pdf");
}

/**
 * PDF invoice/receipt branded with seller profile (business_name, email, phone, address).
 * @param {object} options docTitle/fileSlug/customization
 */
export function downloadOrderInvoice(order, customerName, business, options = {}) {
  const doc = new jsPDF();
  const tp = orderTotal(order);
  const docTitle = options.docTitle || "Invoice";
  const slug = options.fileSlug || "invoice";
  const brand = business?.business_name || docTitle || "Vendor";
  doc.setFontSize(16);
  doc.text(docTitle === "Receipt" ? `Receipt · ${brand}` : brand, 14, 20);
  if (business?.logo_url) {
    doc.setFontSize(8);
    doc.setTextColor(100);
    doc.text("Branded logo configured in Settings (URL on file)", 14, 26);
    doc.setTextColor(0);
  }
  doc.setFontSize(10);
  let y = business?.logo_url ? 36 : 30;
  const numLabel = docTitle === "Receipt" ? `Receipt no.` : `Invoice no.`;
  doc.text(`${numLabel} ${slug.toUpperCase()}-${String(order.id).padStart(5, "0")}`, 14, y);
  y += 8;
  doc.text(`Date: ${new Date(order.created_at || Date.now()).toLocaleDateString()}`, 14, y);
  y += 10;
  if (business?.email) {
    doc.text(`Email: ${business.email}`, 14, y);
    y += 8;
  }
  if (business?.business_phone) {
    doc.text(`Phone: ${business.business_phone}`, 14, y);
    y += 8;
  }
  if (business?.business_address) {
    const parts = doc.splitTextToSize(String(business.business_address), 180);
    doc.text(parts, 14, y);
    y += Math.max(14, parts.length * 5 + 4);
  }
  doc.text(`Bill to: ${customerName}`, 14, y);
  y += 10;
  doc.text(`Product / service: ${order.product}`, 14, y);
  y += 10;
  doc.text(`Total: ₦${tp.toLocaleString()}`, 14, y);
  y += 10;
  doc.text(`Amount paid: ₦${Number(order.amount_paid || 0).toLocaleString()}`, 14, y);
  y += 10;
  doc.text(`Balance due: ₦${Number(order.balance || 0).toLocaleString()}`, 14, y);
  y += 10;
  doc.text(`Status: ${order.status}`, 14, y);
  y += 10;
  if (order.fulfillment_type) {
    doc.text(`Fulfillment: ${order.fulfillment_type}`, 14, y);
    y += 10;
  }
  if (order.delivery_address) {
    doc.text(`Delivery address: ${order.delivery_address}`, 14, y);
    y += 10;
  }
  if (order.payment_method) doc.text(`Payment method: ${order.payment_method}`, 14, y);
  doc.save(`${slug}-${order.id}.pdf`);
}

export function downloadOrderReceipt(order, customerName, business) {
  return downloadOrderInvoice(order, customerName, business, {
    docTitle: "Receipt",
    fileSlug: "receipt"
  });
}
