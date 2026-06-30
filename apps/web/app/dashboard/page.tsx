"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowRight, Building2, MessageSquare, RadioTower, Users } from "lucide-react";
import { PageHeader } from "@/components/page-header";
import {
  apiRequest,
  Channel,
  Conversation,
  Customer,
  getStoredOrganizationId,
  getToken,
  KnowledgeBaseEntry,
  Organization,
  setStoredOrganizationId,
} from "@/lib/api";

export default function DashboardPage() {
  const router = useRouter();
  const [orgs, setOrgs] = useState<Organization[]>([]);
  const [activeOrganization, setActiveOrganization] = useState<Organization | null>(null);
  const [channels, setChannels] = useState<Channel[]>([]);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [knowledgeEntries, setKnowledgeEntries] = useState<KnowledgeBaseEntry[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadDashboard() {
      if (!getToken()) {
        router.replace("/login");
        return;
      }

      try {
        const organizations = await apiRequest<Organization[]>("/organizations");
        setOrgs(organizations);
        if (organizations.length === 0) {
          router.replace("/dashboard/onboarding");
          return;
        }

        const storedOrganizationId = getStoredOrganizationId();
        const activeOrganization =
          organizations.find((organization) => organization.id === storedOrganizationId) || organizations[0];
        setActiveOrganization(activeOrganization);
        setStoredOrganizationId(activeOrganization.id);

        const [channelItems, conversationItems, customerItems, knowledgeItems] = await Promise.all([
          apiRequest<Channel[]>(`/channels?organization_id=${activeOrganization.id}`).catch(() => []),
          apiRequest<Conversation[]>(`/conversations?organization_id=${activeOrganization.id}`).catch(() => []),
          apiRequest<Customer[]>(`/customers?organization_id=${activeOrganization.id}`).catch(() => []),
          apiRequest<KnowledgeBaseEntry[]>(`/knowledge-base?organization_id=${activeOrganization.id}`).catch(() => []),
        ]);
        setChannels(channelItems);
        setConversations(conversationItems);
        setCustomers(customerItems);
        setKnowledgeEntries(knowledgeItems);
      } catch {
        router.replace("/login");
      } finally {
        setLoading(false);
      }
    }

    loadDashboard();
  }, [router]);

  if (loading) {
    return (
      <div className="grid min-h-[60vh] place-items-center">
        <div className="rounded-lg border border-line bg-white px-5 py-4 text-sm text-zinc-600 shadow-sm">
          Loading workspace...
        </div>
      </div>
    );
  }

  return (
    <>
      <PageHeader
        title="Dashboard"
        description="Monitor AI-assisted sales conversations, channel readiness, and customer activity."
        actions={
          <Link
            className="inline-flex items-center gap-2 rounded-lg bg-teal px-4 py-2 text-sm font-medium text-white shadow-sm"
            href="/dashboard/conversations"
          >
            Open inbox
            <ArrowRight size={16} />
          </Link>
        }
      />
      <section className="mb-6 overflow-hidden rounded-lg border border-line bg-white shadow-sm">
        <div className="grid gap-0 lg:grid-cols-[1.4fr_1fr]">
          <div className="p-6">
            <div className="mb-3 inline-flex rounded-full bg-[#e2f4f0] px-3 py-1 text-xs font-medium text-teal">
              Active workspace
            </div>
            <h2 className="text-xl font-semibold">{activeOrganization?.name || "Workspace"}</h2>
            <p className="mt-2 max-w-2xl text-sm text-zinc-600">
              Add knowledge, connect Telegram, and let Sello AI handle first-response sales conversations.
            </p>
            <div className="mt-5 flex flex-wrap gap-3">
              <Link className="rounded-lg border border-line px-4 py-2 text-sm hover:bg-mist" href="/dashboard/knowledge-base">
                Add knowledge
              </Link>
              <Link className="rounded-lg border border-line px-4 py-2 text-sm hover:bg-mist" href="/dashboard/channels">
                Connect channels
              </Link>
            </div>
          </div>
          <div className="border-t border-line bg-mist p-6 lg:border-l lg:border-t-0">
            <div className="text-sm font-semibold">Setup checklist</div>
            <div className="mt-4 space-y-3">
              <ChecklistItem label="Organization created" done={orgs.length > 0} />
              <ChecklistItem label="Knowledge base ready" done={knowledgeEntries.length > 0} />
              <ChecklistItem label="Channel connected" done={channels.length > 0} />
            </div>
          </div>
        </div>
      </section>
      <div className="grid gap-4 md:grid-cols-3">
        <Metric icon={<Building2 size={18} />} label="Organizations" value={orgs.length} />
        <Metric icon={<MessageSquare size={18} />} label="Conversations" value={conversations.length} />
        <Metric icon={<Users size={18} />} label="Customers" value={customers.length} />
      </div>
      <section className="mt-8 rounded-lg border border-line bg-white shadow-sm">
        <div className="flex items-center justify-between border-b border-line px-4 py-3">
          <div className="text-sm font-semibold">Recent conversations</div>
          <RadioTower size={16} className="text-zinc-400" />
        </div>
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
            <div className="px-4 py-10 text-center">
              <div className="mx-auto grid h-10 w-10 place-items-center rounded-lg bg-mist text-teal">
                <MessageSquare size={19} />
              </div>
              <div className="mt-3 text-sm font-medium">No conversations yet</div>
              <p className="mx-auto mt-1 max-w-sm text-sm text-zinc-600">
                Connect Telegram to start receiving messages, or add demo knowledge so the AI is ready when traffic arrives.
              </p>
            </div>
          ) : null}
        </div>
      </section>
    </>
  );
}

function Metric({ icon, label, value }: { icon: React.ReactNode; label: string; value: number }) {
  return (
    <div className="rounded-lg border border-line bg-white p-4 shadow-sm">
      <div className="flex items-center justify-between">
        <div className="text-sm text-zinc-500">{label}</div>
        <div className="text-teal">{icon}</div>
      </div>
      <div className="mt-2 text-3xl font-semibold">{value}</div>
    </div>
  );
}

function ChecklistItem({ label, done }: { label: string; done: boolean }) {
  return (
    <div className="flex items-center justify-between text-sm">
      <span>{label}</span>
      <span className={`rounded-full px-2 py-1 text-xs ${done ? "bg-[#dff3ef] text-teal" : "bg-white text-zinc-500"}`}>
        {done ? "Done" : "Pending"}
      </span>
    </div>
  );
}
