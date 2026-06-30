"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { PageHeader } from "@/components/page-header";
import { apiRequest, Conversation, Customer, getStoredOrganizationId, Organization } from "@/lib/api";

export default function DashboardPage() {
  const [orgs, setOrgs] = useState<Organization[]>([]);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [customers, setCustomers] = useState<Customer[]>([]);

  useEffect(() => {
    apiRequest<Organization[]>("/organizations").then(setOrgs).catch(() => setOrgs([]));
    const organizationId = getStoredOrganizationId();
    if (organizationId) {
      apiRequest<Conversation[]>(`/conversations?organization_id=${organizationId}`)
        .then(setConversations)
        .catch(() => setConversations([]));
      apiRequest<Customer[]>(`/customers?organization_id=${organizationId}`)
        .then(setCustomers)
        .catch(() => setCustomers([]));
    }
  }, []);

  return (
    <>
      <PageHeader
        title="Dashboard"
        description="Monitor AI-assisted sales conversations, connected channels, and customer activity."
        actions={
          <Link className="rounded bg-teal px-4 py-2 text-sm font-medium text-white" href="/dashboard/conversations">
            Open inbox
          </Link>
        }
      />
      <div className="grid gap-4 md:grid-cols-3">
        <Metric label="Organizations" value={orgs.length} />
        <Metric label="Conversations" value={conversations.length} />
        <Metric label="Customers" value={customers.length} />
      </div>
      <section className="mt-8 border border-line bg-white">
        <div className="border-b border-line px-4 py-3 text-sm font-semibold">Recent conversations</div>
        <div className="divide-y divide-line">
          {conversations.slice(0, 8).map((conversation) => (
            <Link
              href="/dashboard/conversations"
              key={conversation.id}
              className="flex items-center justify-between px-4 py-3 text-sm hover:bg-mist"
            >
              <span>{conversation.customer_name || conversation.customer_id}</span>
              <span className="text-zinc-500">{conversation.status}</span>
            </Link>
          ))}
          {conversations.length === 0 ? (
            <div className="px-4 py-8 text-sm text-zinc-500">No conversations yet.</div>
          ) : null}
        </div>
      </section>
    </>
  );
}

function Metric({ label, value }: { label: string; value: number }) {
  return (
    <div className="border border-line bg-white p-4">
      <div className="text-sm text-zinc-500">{label}</div>
      <div className="mt-2 text-3xl font-semibold">{value}</div>
    </div>
  );
}

