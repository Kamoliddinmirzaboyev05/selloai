"use client";

import { FormEvent, useEffect, useState } from "react";
import { BookOpen, Database, PlusCircle } from "lucide-react";
import { PageHeader } from "@/components/page-header";
import { apiRequest, getStoredOrganizationId, KnowledgeBaseEntry } from "@/lib/api";
import { demoFaqs, seedDemoKnowledgeBase } from "@/lib/demo-data";

export default function KnowledgeBasePage() {
  const [entries, setEntries] = useState<KnowledgeBaseEntry[]>([]);
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [saving, setSaving] = useState(false);
  const [seeding, setSeeding] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const organizationId = getStoredOrganizationId();

  async function refresh() {
    if (!organizationId) return;
    try {
      const items = await apiRequest<KnowledgeBaseEntry[]>(`/knowledge-base?organization_id=${organizationId}`);
      setEntries(items);
    } catch {
      setEntries([]);
    }
  }

  useEffect(() => {
    refresh();
  }, [organizationId]);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!organizationId) return;
    setSaving(true);
    setMessage(null);
    setError(null);
    try {
      await apiRequest<KnowledgeBaseEntry>("/knowledge-base", {
        method: "POST",
        body: {
          organization_id: organizationId,
          title,
          content,
          is_active: true,
        },
      });
      setTitle("");
      setContent("");
      setMessage("Knowledge entry added.");
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not add knowledge entry");
    } finally {
      setSaving(false);
    }
  }

  async function seedDemo() {
    if (!organizationId) return;
    setSeeding(true);
    setMessage(null);
    setError(null);
    try {
      await seedDemoKnowledgeBase(organizationId);
      setMessage("Demo FAQs added.");
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not add demo FAQs");
    } finally {
      setSeeding(false);
    }
  }

  function addFirstFaq() {
    setTitle(demoFaqs[0].title);
    setContent(demoFaqs[0].content);
  }

  return (
    <>
      <PageHeader
        title="Knowledge Base"
        description="Business facts, policies, and FAQs the AI uses when answering customers."
        actions={
          <button
            type="button"
            onClick={seedDemo}
            disabled={seeding}
            className="inline-flex items-center gap-2 rounded-lg border border-line bg-white px-4 py-2 text-sm font-medium shadow-sm hover:bg-mist disabled:opacity-60"
          >
            <Database size={16} />
            {seeding ? "Adding demo..." : "Add demo FAQs"}
          </button>
        }
      />
      <div className="grid gap-6 lg:grid-cols-[420px_1fr]">
        <form onSubmit={submit} className="rounded-lg border border-line bg-white p-5 shadow-sm">
          <div className="mb-4 flex items-center gap-2 text-sm font-semibold">
            <PlusCircle size={17} className="text-teal" />
            Add FAQ or policy
          </div>
          <label className="block text-sm font-medium">
            Title
            <input
              value={title}
              onChange={(event) => setTitle(event.target.value)}
              className="mt-2 w-full rounded border border-line px-3 py-2"
              placeholder="Returns policy"
              required
            />
          </label>
          <label className="mt-4 block text-sm font-medium">
            Content
            <textarea
              value={content}
              onChange={(event) => setContent(event.target.value)}
              rows={8}
              className="mt-2 w-full rounded border border-line px-3 py-2"
              placeholder="Describe the answer Sello AI should use."
              required
            />
          </label>
          <button
            className="mt-4 rounded-lg bg-teal px-4 py-2 text-sm font-medium text-white shadow-sm disabled:opacity-60"
            type="submit"
            disabled={saving}
          >
            {saving ? "Adding..." : "Add entry"}
          </button>
          {message ? <p className="mt-3 text-sm text-teal">{message}</p> : null}
          {error ? <p className="mt-3 text-sm text-coral">{error}</p> : null}
        </form>
        <section className="rounded-lg border border-line bg-white shadow-sm">
          <div className="border-b border-line px-4 py-3 text-sm font-semibold">Entries</div>
          {entries.length === 0 ? (
            <div className="grid min-h-[360px] place-items-center px-6 py-10 text-center">
              <div>
                <div className="mx-auto grid h-12 w-12 place-items-center rounded-lg bg-[#dff3ef] text-teal">
                  <BookOpen size={22} />
                </div>
                <h2 className="mt-4 text-base font-semibold">No knowledge yet</h2>
                <p className="mx-auto mt-2 max-w-sm text-sm text-zinc-600">
                  Add the first FAQ so Sello AI can answer with business-specific context.
                </p>
                <button
                  type="button"
                  onClick={addFirstFaq}
                  className="mt-5 rounded-lg bg-teal px-4 py-2 text-sm font-medium text-white shadow-sm"
                >
                  Add first FAQ
                </button>
              </div>
            </div>
          ) : (
            <div className="divide-y divide-line">
              {entries.map((entry) => (
                <article key={entry.id} className="px-4 py-4">
                  <div className="flex items-center justify-between gap-3">
                    <h2 className="text-sm font-semibold">{entry.title}</h2>
                    <span className="rounded-full bg-[#dff3ef] px-2 py-1 text-xs text-teal">
                      {entry.is_active ? "Active" : "Inactive"}
                    </span>
                  </div>
                  <p className="mt-2 whitespace-pre-wrap text-sm leading-6 text-zinc-700">{entry.content}</p>
                </article>
              ))}
            </div>
          )}
        </section>
      </div>
    </>
  );
}
