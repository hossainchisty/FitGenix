"use client";
import ResourcePage, { money, when } from "@/components/ResourcePage";
export default function Page() {
  return <ResourcePage title="Payments" path="/payments" addLabel="Take payment"
    cols={[{ key: "paid_at", label: "When", render: (r) => when(r.paid_at) }, { key: "member_name", label: "Member" }, { key: "amount", label: "Amount", render: (r) => money(r.amount) }, { key: "method", label: "Method" }, { key: "reference", label: "Reference" }]}
    fields={[{ key: "member", label: "Member", required: true, from: { path: "/members", label: (r) => `${r.code} ${r.name}` } }, { key: "member_package", label: "For membership (optional)", from: { path: "/member-packages", label: (r) => `${r.member_name}: ${r.package_name} (ends ${r.end_date})` } }, { key: "amount", label: "Amount (Tk.)", type: "number", required: true }, { key: "method", label: "Method", initial: "cash", options: [["cash", "Cash"], ["bkash", "bKash"], ["nagad", "Nagad"], ["card", "Card"], ["bank", "Bank"]] }, { key: "reference", label: "Transaction ID (optional)" }]} />;
}
