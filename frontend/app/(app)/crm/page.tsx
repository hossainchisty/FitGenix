"use client";
import ResourcePage, { chip } from "@/components/ResourcePage";
export default function Page() {
  return <ResourcePage title="Inquiries" path="/inquiries" addLabel="Add inquiry" hint="Follow every lead until it joins or says no."
    cols={[{ key: "name", label: "Name" }, { key: "phone", label: "Phone" }, { key: "interest", label: "Interested in" }, { key: "stage", label: "Stage", render: (r) => chip(r.stage) }, { key: "follow_up_at", label: "Follow up" }]}
    fields={[{ key: "name", label: "Name", required: true }, { key: "phone", label: "Phone" }, { key: "interest", label: "Interested in" }, { key: "stage", label: "Stage", initial: "new", options: [["new", "New"], ["contacted", "Contacted"], ["trial", "Trial"], ["won", "Won"], ["lost", "Lost"]] }, { key: "follow_up_at", label: "Follow up on", type: "date" }]} />;
}
