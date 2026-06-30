"use client";

import { FormEvent, useEffect, useState } from "react";
import { PageHeader } from "@/components/page-header";
import { apiRequest, getStoredOrganizationId, OrganizationSettings } from "@/lib/api";

export default function SettingsPage() {
  const [settings, setSettings] = useState<OrganizationSettings | null>(null);
  const [saved, setSaved] = useState(false);
  const organizationId = getStoredOrganizationId();

  useEffect(() => {
    if (!organizationId) return;
    apiRequest<OrganizationSettings>(`/settings?organization_id=${organizationId}`)
      .then(setSettings)
      .catch(() => setSettings(null));
  }, [organizationId]);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!organizationId) return;
    const form = new FormData(event.currentTarget);
    const updated = await apiRequest<OrganizationSettings>("/settings", {
      method: "PATCH",
      body: {
        organization_id: organizationId,
        ai_tone: String(form.get("ai_tone")),
        handoff_keywords: String(form.get("handoff_keywords")),
        auto_reply_enabled: form.get("auto_reply_enabled") === "on",
      },
    });
    setSettings(updated);
    setSaved(true);
  }

  return (
    <>
      <PageHeader title="Settings" description="Tune AI behavior and handoff preferences for the active organization." />
      <form onSubmit={submit} className="max-w-2xl border border-line bg-white p-5">
        <label className="block text-sm">
          AI tone
          <input
            name="ai_tone"
            defaultValue={settings?.ai_tone || "friendly and concise"}
            className="mt-1 w-full border border-line px-3 py-2"
          />
        </label>
        <label className="mt-4 block text-sm">
          Handoff keywords
          <input
            name="handoff_keywords"
            defaultValue={settings?.handoff_keywords || "human,agent,operator"}
            className="mt-1 w-full border border-line px-3 py-2"
          />
        </label>
        <label className="mt-4 flex items-center gap-2 text-sm">
          <input
            name="auto_reply_enabled"
            type="checkbox"
            defaultChecked={settings?.auto_reply_enabled ?? true}
          />
          Enable AI auto replies
        </label>
        <button className="mt-4 rounded bg-teal px-4 py-2 text-sm font-medium text-white" type="submit">
          Save settings
        </button>
        {saved ? <p className="mt-3 text-sm text-teal">Settings saved.</p> : null}
      </form>
    </>
  );
}

