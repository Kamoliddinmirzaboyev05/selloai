"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowRight, Building2, Database, MessageCircle } from "lucide-react";
import { PageHeader } from "@/components/page-header";
import { apiRequest, Organization, setStoredOrganizationId } from "@/lib/api";
import { seedDemoKnowledgeBase } from "@/lib/demo-data";

export default function OnboardingPage() {
  const router = useRouter();
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [seedDemo, setSeedDemo] = useState(true);
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    apiRequest<Organization[]>("/organizations").then(setOrganizations).catch(() => setOrganizations([]));
  }, []);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setCreating(true);
    setError(null);
    const form = new FormData(event.currentTarget);
    try {
      const organization = await apiRequest<Organization>("/organizations", {
        method: "POST",
        body: { name: String(form.get("name")) },
      });
      if (seedDemo) {
        await seedDemoKnowledgeBase(organization.id);
      }
      setStoredOrganizationId(organization.id);
      router.push("/dashboard/channels");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create organization");
    } finally {
      setCreating(false);
    }
  }

  return (
    <>
      <PageHeader
        title="Set up your workspace"
        description="Create an organization, optionally load demo FAQs, then connect your first sales channel."
      />
      <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_360px]">
        <form onSubmit={submit} className="rounded-lg border border-line bg-white p-6 shadow-sm">
          <div className="mb-5 flex items-start gap-3">
            <div className="grid h-10 w-10 place-items-center rounded-lg bg-teal text-white">
              <Building2 size={20} />
            </div>
            <div>
              <h2 className="text-base font-semibold">Create organization</h2>
              <p className="mt-1 text-sm text-zinc-600">This becomes the workspace for channels, leads, and AI knowledge.</p>
            </div>
          </div>
          <label className="block text-sm font-medium">
            Organization name
            <input
              name="name"
              className="mt-2 w-full rounded border border-line px-3 py-2"
              placeholder="Acme Sales Team"
              required
            />
          </label>
          <label className="mt-4 flex items-start gap-3 rounded-lg border border-line bg-mist p-3 text-sm">
            <input
              type="checkbox"
              checked={seedDemo}
              onChange={(event) => setSeedDemo(event.target.checked)}
              className="mt-0.5"
            />
            <span>
              <span className="block font-medium">Load demo FAQs</span>
              <span className="text-zinc-600">Adds sample hours, shipping, and pricing guidance so the AI has context immediately.</span>
            </span>
          </label>
          {error ? <p className="mt-3 text-sm text-coral">{error}</p> : null}
          <button
            className="mt-5 inline-flex items-center gap-2 rounded-lg bg-teal px-4 py-2 text-sm font-medium text-white shadow-sm disabled:opacity-60"
            type="submit"
            disabled={creating}
          >
            {creating ? "Creating..." : "Create organization"}
            <ArrowRight size={16} />
          </button>
        </form>
        <aside className="space-y-4">
          <SetupStep icon={<Building2 size={18} />} title="1. Create workspace" text="Name the business or sales team." />
          <SetupStep icon={<Database size={18} />} title="2. Add knowledge" text="Seed FAQs or add your own business facts." />
          <SetupStep icon={<MessageCircle size={18} />} title="3. Connect channels" text="Telegram is live; Instagram endpoints are ready." />
        </aside>
      </div>
      {organizations.length > 0 ? (
        <section className="mt-6 rounded-lg border border-line bg-white shadow-sm">
          <div className="border-b border-line px-4 py-3 text-sm font-semibold">Existing organizations</div>
          <div className="divide-y divide-line">
            {organizations.map((organization) => (
              <button
                key={organization.id}
                type="button"
                className="block w-full px-4 py-3 text-left text-sm hover:bg-mist"
                onClick={() => {
                  setStoredOrganizationId(organization.id);
                  router.push("/dashboard");
                }}
              >
                <span className="font-medium">{organization.name}</span>
                <span className="ml-2 text-zinc-500">{organization.slug}</span>
              </button>
            ))}
          </div>
        </section>
      ) : null}
    </>
  );
}

function SetupStep({ icon, title, text }: { icon: React.ReactNode; title: string; text: string }) {
  return (
    <div className="rounded-lg border border-line bg-white p-4 shadow-sm">
      <div className="flex items-center gap-2 text-sm font-semibold">
        <span className="text-teal">{icon}</span>
        {title}
      </div>
      <p className="mt-2 text-sm text-zinc-600">{text}</p>
    </div>
  );
}
