"use client";
import ResourcePage, { chip } from "@/components/ResourcePage";
export default function Page() {
  return <ResourcePage title="Members" path="/members" addLabel="Add member" deletable hint="Removing a member archives them; payment history is kept."
    cols={[{ key: "code", label: "ID" }, { key: "name", label: "Name" }, { key: "phone", label: "Phone" }, { key: "active_until", label: "Active until", render: (r) => r.active_until || "No active package" }, { key: "status", label: "Status", render: (r) => chip(r.status) }]}
    fields={[{ key: "name", label: "Full name", required: true }, { key: "phone", label: "Phone" }, { key: "email", label: "Email", type: "email" }, { key: "gender", label: "Gender", options: [["male", "Male"], ["female", "Female"], ["other", "Other"]] }, { key: "notes", label: "Notes" }]} />;
}
