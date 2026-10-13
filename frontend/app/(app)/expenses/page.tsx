"use client";
import ResourcePage, { money } from "@/components/ResourcePage";
export default function Page() {
  return <ResourcePage title="Expenses" path="/expenses" addLabel="Add expense" hint="Visible to owners and managers only."
    cols={[{ key: "paid_on", label: "Date" }, { key: "category", label: "Category" }, { key: "amount", label: "Amount", render: (r) => money(r.amount) }, { key: "note", label: "Note" }]}
    fields={[{ key: "category", label: "Category (rent, salary...)", required: true }, { key: "amount", label: "Amount (Tk.)", type: "number", required: true }, { key: "paid_on", label: "Date", type: "date" }, { key: "note", label: "Note" }]} />;
}
