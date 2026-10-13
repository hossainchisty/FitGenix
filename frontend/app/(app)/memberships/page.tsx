"use client";
import ResourcePage, { chip, money } from "@/components/ResourcePage";
export default function Page() {
  return <ResourcePage title="Sell membership" path="/member-packages" addLabel="Sell package" hint="Pick a member and a package. End date and price are calculated for you."
    cols={[{ key: "member_name", label: "Member" }, { key: "package_name", label: "Package" }, { key: "start_date", label: "Start" }, { key: "end_date", label: "End" }, { key: "price", label: "Price", render: (r) => money(r.price) }, { key: "paid", label: "Paid", render: (r) => money(r.paid || 0) }, { key: "status", label: "Status", render: (r) => chip(r.status) }]}
    fields={[{ key: "member", label: "Member", required: true, from: { path: "/members", label: (r) => `${r.code} ${r.name}` } }, { key: "package", label: "Package", required: true, from: { path: "/packages", label: (r) => r.name } }, { key: "start_date", label: "Start date", type: "date" }, { key: "discount", label: "Discount (Tk.)", type: "number" }]} />;
}
