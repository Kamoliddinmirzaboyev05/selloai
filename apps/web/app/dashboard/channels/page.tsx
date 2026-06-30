"use client";

import { FormEvent, useEffect, useState } from "react";
import { CheckCircle2, Instagram, Loader2, Send } from "lucide-react";
import { PageHeader } from "@/components/page-header";
import { apiRequest, Channel, getStoredOrganizationId } from "@/lib/api";

export default function ChannelsPage() {
  const [channels, setChannels] = useState<Channel[]>([]);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [connecting, setConnecting] = useState(false);
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
    setConnecting(true);
    setMessage(null);
    setError(null);
    const form = new FormData(event.currentTarget);
    try {
      const response = await apiRequest<{ webhook_path: string }>("/channels/telegram/connect", {
        method: "POST",
        body: { organization_id: organizationId, bot_token: String(form.get("bot_token")) },
      });
      setMessage(`Telegram connected. Webhook path: ${response.webhook_path}`);
      refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not connect Telegram");
    } finally {
      setConnecting(false);
    }
  }

  const telegramChannel = channels.find((channel) => channel.type === "telegram");

  return (
    <>
      <PageHeader title="Channels" description="Connect customer messaging channels and monitor integration status." />
      <div className="grid gap-5 lg:grid-cols-2">
        <section className="rounded-lg border border-line bg-white p-5 shadow-sm">
          <div className="flex items-start justify-between gap-4">
            <div className="flex items-start gap-3">
              <div className="grid h-10 w-10 place-items-center rounded-lg bg-[#dff3ef] text-teal">
                <Send size={20} />
              </div>
              <div>
                <h2 className="text-base font-semibold">Telegram</h2>
                <p className="mt-1 text-sm text-zinc-600">Fully supported for MVP auto-replies and manual operator replies.</p>
              </div>
            </div>
            <StatusBadge active={Boolean(telegramChannel)} label={telegramChannel ? "Active" : "Ready"} />
          </div>
          <form onSubmit={connectTelegram} className="mt-5 border-t border-line pt-5">
            <label className="block text-sm font-medium">
              Bot token
              <input
                name="bot_token"
                className="mt-2 w-full rounded border border-line px-3 py-2"
                placeholder="123456789:AA..."
                required
              />
            </label>
            <button
              className="mt-4 inline-flex items-center gap-2 rounded-lg bg-teal px-4 py-2 text-sm font-medium text-white shadow-sm disabled:opacity-60"
              type="submit"
              disabled={connecting}
            >
              {connecting ? <Loader2 size={16} className="animate-spin" /> : <Send size={16} />}
              {connecting ? "Connecting..." : "Connect Telegram"}
            </button>
            {message ? <p className="mt-3 rounded border border-[#bfe7df] bg-[#edf8f5] px-3 py-2 text-sm text-teal">{message}</p> : null}
            {error ? <p className="mt-3 rounded border border-[#f0c8c2] bg-[#fff4f2] px-3 py-2 text-sm text-coral">{error}</p> : null}
          </form>
        </section>
        <section className="rounded-lg border border-line bg-white p-5 shadow-sm">
          <div className="flex items-start justify-between gap-4">
            <div className="flex items-start gap-3">
              <div className="grid h-10 w-10 place-items-center rounded-lg bg-[#f4e9f2] text-coral">
                <Instagram size={20} />
              </div>
              <div>
                <h2 className="text-base font-semibold">Instagram</h2>
                <p className="mt-1 text-sm text-zinc-600">Meta OAuth, webhook verification, DM, and comment handlers are scaffolded.</p>
              </div>
            </div>
            <StatusBadge active={false} label="Skeleton" />
          </div>
          <div className="mt-5 space-y-3 border-t border-line pt-5 text-sm">
            <FeatureRow text="OAuth callback placeholder" />
            <FeatureRow text="Webhook verification endpoint" />
            <FeatureRow text="DM and comment event dispatch" />
          </div>
        </section>
      </div>
      <section className="mt-6 rounded-lg border border-line bg-white shadow-sm">
        <div className="border-b border-line px-4 py-3 text-sm font-semibold">Connected channels</div>
        <div className="divide-y divide-line">
          {channels.length === 0 ? (
            <div className="px-4 py-8 text-sm text-zinc-500">No live channels connected yet.</div>
          ) : null}
          {channels.map((channel) => (
            <div key={channel.id} className="grid gap-3 px-4 py-3 text-sm md:grid-cols-4">
              <span className="font-medium">{channel.display_name}</span>
              <span>{channel.type}</span>
              <span>{channel.status}</span>
              <span className="text-zinc-500">{channel.external_id}</span>
            </div>
          ))}
        </div>
      </section>
    </>
  );
}

function StatusBadge({ active, label }: { active: boolean; label: string }) {
  return (
    <span className={`rounded-full px-3 py-1 text-xs font-medium ${active ? "bg-[#dff3ef] text-teal" : "bg-mist text-zinc-600"}`}>
      {label}
    </span>
  );
}

function FeatureRow({ text }: { text: string }) {
  return (
    <div className="flex items-center gap-2 text-zinc-700">
      <CheckCircle2 size={16} className="text-teal" />
      {text}
    </div>
  );
}
