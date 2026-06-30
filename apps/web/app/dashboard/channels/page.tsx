"use client";

import { FormEvent, useEffect, useState } from "react";
import { Cable } from "lucide-react";
import { PageHeader } from "@/components/page-header";
import { apiRequest, Channel, getStoredOrganizationId } from "@/lib/api";

export default function ChannelsPage() {
  const [channels, setChannels] = useState<Channel[]>([]);
  const [message, setMessage] = useState<string | null>(null);
  const organizationId = getStoredOrganizationId();

  function refresh() {
    if (!organizationId) return;
    apiRequest<Channel[]>(`/channels?organization_id=${organizationId}`)
      .then(setChannels)
      .catch(() => setChannels([]));
  }

  useEffect(refresh, [organizationId]);

  async function connectTelegram(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!organizationId) return;
    const form = new FormData(event.currentTarget);
    const response = await apiRequest<{ webhook_path: string }>("/channels/telegram/connect", {
      method: "POST",
      body: { organization_id: organizationId, bot_token: String(form.get("bot_token")) },
    });
    setMessage(`Telegram connected. Webhook path: ${response.webhook_path}`);
    refresh();
  }

  return (
    <>
      <PageHeader title="Channels" description="Connect customer messaging channels and monitor integration status." />
      <div className="grid gap-6 lg:grid-cols-[420px_1fr]">
        <form onSubmit={connectTelegram} className="border border-line bg-white p-5">
          <div className="mb-4 flex items-center gap-2 text-sm font-semibold">
            <Cable size={17} />
            Telegram bot
          </div>
          <label className="block text-sm">
            Bot token
            <input name="bot_token" className="mt-1 w-full border border-line px-3 py-2" required />
          </label>
          <button className="mt-4 rounded bg-teal px-4 py-2 text-sm font-medium text-white" type="submit">
            Connect Telegram
          </button>
          {message ? <p className="mt-3 text-sm text-zinc-600">{message}</p> : null}
        </form>
        <section className="border border-line bg-white">
          <div className="border-b border-line px-4 py-3 text-sm font-semibold">Connected channels</div>
          <div className="divide-y divide-line">
            {channels.map((channel) => (
              <div key={channel.id} className="grid grid-cols-4 gap-3 px-4 py-3 text-sm">
                <span className="font-medium">{channel.display_name}</span>
                <span>{channel.type}</span>
                <span>{channel.status}</span>
                <span className="text-zinc-500">{channel.external_id}</span>
              </div>
            ))}
            <div className="px-4 py-4 text-sm text-zinc-600">
              Instagram: OAuth and webhook skeleton available in the API.
            </div>
          </div>
        </section>
      </div>
    </>
  );
}

