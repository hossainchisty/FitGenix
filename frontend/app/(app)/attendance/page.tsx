"use client";
import ResourcePage, { when } from "@/components/ResourcePage";
export default function Page() {
  return <ResourcePage title="Attendance" path="/attendance" addLabel="Check in member" hint="Members need an active package to check in."
    cols={[{ key: "checked_in_at", label: "Checked in", render: (r) => when(r.checked_in_at) }, { key: "member_name", label: "Member" }, { key: "source", label: "Source" }]}
    fields={[{ key: "member", label: "Member", required: true, from: { path: "/members", label: (r) => `${r.code} ${r.name}` } }]} />;
}
