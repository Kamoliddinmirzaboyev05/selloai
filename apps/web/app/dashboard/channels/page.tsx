"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { CheckCircle2, Instagram, Loader2, Send } from "lucide-react";
import { PageHeader } from "@/components/page-header";
import {
  apiRequest,
  Channel,
  getStoredOrganizationId,
  getToken,
  InstagramOAuthLoginResponse,
  Organization,
  setStoredOrganizationId,
} from "@/lib/api";

export default function ChannelsPage() {
  const router = useRouter();
  const [channels, setChannels] = useState<Channel[]>([]);
  const [organizationId, setOrganizationId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [connectingTelegram, setConnectingTelegram] = useState(false);
  const [connectingInstagram, setConnectingInstagram] = useState(false);

  async function refreshChannels(activeOrganizationId = organizationId) {
    if (!activeOrganizationId) return;
    try {
      const channelItems = await apiRequest<Channel[]>(`/channels?organization_id=${activeOrganizationId}`);
      setChannels(channelItems);
    } catch {
      setChannels([]);
    }
  }

  useEffect(() => {
    let cancelled = false;

    async function loadChannels() {
      if (!getToken()) {
        router.replace("/login");
        return;
      }

      setLoading(true);
      setError(null);
      try {
        const organizations = await apiRequest<Organization[]>("/organizations");
        if (cancelled) return;
        if (organizations.length === 0) {
          router.replace("/dashboard/onboarding");
          return;
        }

        const storedOrganizationId = getStoredOrganizationId();
        const activeOrganization =
          organizations.find((organization) => organization.id === storedOrganizationId) || organizations[0];
        setStoredOrganizationId(activeOrganization.id);
        setOrganizationId(activeOrganization.id);
        await refreshChannels(activeOrganization.id);

        const instagramStatus = new URLSearchParams(window.location.search).get("instagram");
        if (instagramStatus === "connected") {
          setMessage("Instagram connected successfully.");
        } else if (instagramStatus === "no_instagram_business_account") {
          setError("Meta OAuth finished, but no Instagram Business Account was found on the selected Facebook Pages.");
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Could not load channels.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    loadChannels();
    return () => {
      cancelled = true;
    };
  }, [router]);

  async function connectTelegram(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!organizationId) {
      router.replace("/dashboard/onboarding");
      return;
    }
    setConnectingTelegram(true);
    setMessage(null);
    setError(null);
    const form = new FormData(event.currentTarget);
    try {
      const response = await apiRequest<{ webhook_path: string }>("/channels/telegram/connect", {
        method: "POST",
        body: { organization_id: organizationId, bot_token: String(form.get("bot_token")) },
      });
      setMessage(`Telegram connected. Webhook path: ${response.webhook_path}`);
      refreshChannels(organizationId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not connect Telegram");
    } finally {
      setConnectingTelegram(false);
    }
  }

  async function connectInstagram() {
    if (!organizationId) {
      router.replace("/dashboard/onboarding");
      return;
    }

    setConnectingInstagram(true);
    setMessage(null);
    setError(null);
    try {
      const response = await apiRequest<InstagramOAuthLoginResponse>(
        `/integrations/instagram/oauth/login?organization_id=${encodeURIComponent(organizationId)}`,
      );
      window.location.assign(response.authorization_url);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not start Instagram connection.");
      setConnectingInstagram(false);
    }
  }

  const telegramChannel = channels.find((channel) => channel.type === "telegram");
  const instagramChannel = channels.find((channel) => channel.type === "instagram");
  const instagramNeedsReconnect =
    instagramChannel?.status === "needs_reconnect" || instagramChannel?.status === "error";

  if (loading) {
    return (
      <div className="grid min-h-[60vh] place-items-center">
        <div className="inline-flex items-center gap-2 rounded-lg border border-line bg-white px-5 py-4 text-sm text-zinc-600 shadow-sm">
          <Loader2 size={16} className="animate-spin text-teal" />
          Loading channels...
        </div>
      </div>
    );
  }

  return (
    <>
      <PageHeader title="Channels" description="Connect customer messaging channels and monitor integration status." />
      {message ? <p className="mb-4 rounded border border-[#bfe7df] bg-[#edf8f5] px-3 py-2 text-sm text-teal">{message}</p> : null}
      {error ? <p className="mb-4 rounded border border-[#f0c8c2] bg-[#fff4f2] px-3 py-2 text-sm text-coral">{error}</p> : null}
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
              disabled={connectingTelegram}
            >
              {connectingTelegram ? <Loader2 size={16} className="animate-spin" /> : <Send size={16} />}
              {connectingTelegram ? "Connecting..." : "Connect Telegram"}
            </button>
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
            <StatusBadge
              active={Boolean(instagramChannel) && !instagramNeedsReconnect}
              label={instagramNeedsReconnect ? "Reconnect required" : instagramChannel ? "Connected" : "Ready"}
            />
          </div>
          <div className="mt-5 space-y-3 border-t border-line pt-5 text-sm">
            <FeatureRow text="Meta OAuth connection" />
            <FeatureRow text="Webhook verification endpoint" />
            <FeatureRow text="DM and comment event dispatch" />
            {organizationId ? (
              <button
                className="mt-2 inline-flex items-center gap-2 rounded-lg bg-teal px-4 py-2 text-sm font-medium text-white shadow-sm disabled:opacity-60"
                type="button"
                onClick={connectInstagram}
                disabled={connectingInstagram || (Boolean(instagramChannel) && !instagramNeedsReconnect)}
              >
                {connectingInstagram ? <Loader2 size={16} className="animate-spin" /> : <Instagram size={16} />}
                {instagramChannel && !instagramNeedsReconnect
                  ? "Instagram connected"
                  : connectingInstagram
                    ? "Opening Meta..."
                    : instagramNeedsReconnect
                      ? "Reconnect Instagram"
                      : "Connect Instagram"}
              </button>
            ) : null}
            {instagramChannel && !instagramNeedsReconnect ? (
              <p className="rounded border border-[#bfe7df] bg-[#edf8f5] px-3 py-2 text-sm text-teal">
                Connected as {instagramChannel.display_name}.
              </p>
            ) : null}
            {instagramNeedsReconnect ? (
              <p className="rounded border border-[#f0c8c2] bg-[#fff4f2] px-3 py-2 text-sm text-coral">
                The saved Meta token needs a fresh OAuth connection.
              </p>
            ) : null}
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
