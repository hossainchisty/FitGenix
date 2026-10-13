"use client";
import ResourcePage, { money } from "@/components/ResourcePage";
export default function Page() {
  return <ResourcePage title="Packages" path="/packages" addLabel="Add package" hint="The membership plans you sell to members. Owners and managers can edit."
    cols={[{ key: "name", label: "Name" }, { key: "duration_days", label: "Days" }, { key: "price", label: "Price", render: (r) => money(r.price) }, { key: "visit_limit", label: "Visit limit", render: (r) => r.visit_limit ?? "Unlimited" }]}
    fields={[{ key: "name", label: "Package name", required: true }, { key: "duration_days", label: "Duration (days)", type: "number", required: true }, { key: "price", label: "Price (Tk.)", type: "number", required: true }, { key: "visit_limit", label: "Visit limit (optional)", type: "number" }]} />;
}
