"use client";

import { FormEvent, useEffect, useState } from "react";
import { PageHeader } from "@/components/page-header";
import { apiRequest, getStoredOrganizationId, KnowledgeBaseEntry } from "@/lib/api";

export default function KnowledgeBasePage() {
  const [entries, setEntries] = useState<KnowledgeBaseEntry[]>([]);
  const organizationId = getStoredOrganizationId();

  function refresh() {
    if (!organizationId) return;
    apiRequest<KnowledgeBaseEntry[]>(`/knowledge-base?organization_id=${organizationId}`)
      .then(setEntries)
      .catch(() => setEntries([]));
  }

  useEffect(refresh, [organizationId]);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!organizationId) return;
    const form = new FormData(event.currentTarget);
    await apiRequest<KnowledgeBaseEntry>("/knowledge-base", {
      method: "POST",
      body: {
        organization_id: organizationId,
        title: String(form.get("title")),
        content: String(form.get("content")),
        is_active: true,
      },
    });
    event.currentTarget.reset();
    refresh();
  }

  return (
    <>
      <PageHeader title="Knowledge Base" description="Business facts the AI uses when answering customers." />
      <div className="grid gap-6 lg:grid-cols-[420px_1fr]">
        <form onSubmit={submit} className="border border-line bg-white p-5">
          <label className="block text-sm">
            Title
            <input name="title" className="mt-1 w-full border border-line px-3 py-2" required />
          </label>
          <label className="mt-4 block text-sm">
            Content
            <textarea name="content" rows={8} className="mt-1 w-full border border-line px-3 py-2" required />
          </label>
          <button className="mt-4 rounded bg-teal px-4 py-2 text-sm font-medium text-white" type="submit">
            Add entry
          </button>
        </form>
        <section className="border border-line bg-white">
          <div className="border-b border-line px-4 py-3 text-sm font-semibold">Entries</div>
          <div className="divide-y divide-line">
            {entries.map((entry) => (
              <article key={entry.id} className="px-4 py-3">
                <div className="flex items-center justify-between gap-3">
                  <h2 className="text-sm font-semibold">{entry.title}</h2>
                  <span className="text-xs text-zinc-500">{entry.is_active ? "Active" : "Inactive"}</span>
                </div>
                <p className="mt-2 whitespace-pre-wrap text-sm text-zinc-700">{entry.content}</p>
              </article>
            ))}
          </div>
        </section>
      </div>
    </>
  );
}

