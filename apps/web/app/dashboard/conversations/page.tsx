"use client";

import { FormEvent, useEffect, useState } from "react";
import { Send } from "lucide-react";
import { PageHeader } from "@/components/page-header";
import { apiRequest, Conversation, getStoredOrganizationId, Message } from "@/lib/api";

export default function ConversationsPage() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [selected, setSelected] = useState<Conversation | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const organizationId = getStoredOrganizationId();

  function refreshConversations() {
    if (!organizationId) return;
    apiRequest<Conversation[]>(`/conversations?organization_id=${organizationId}`)
      .then((items) => {
        setConversations(items);
        if (!selected && items[0]) setSelected(items[0]);
      })
      .catch(() => setConversations([]));
  }

  useEffect(refreshConversations, [organizationId, selected]);

  useEffect(() => {
    if (!organizationId || !selected) return;
    apiRequest<{ messages: Message[] }>(
      `/conversations/${selected.id}/messages?organization_id=${organizationId}`,
    )
      .then((data) => setMessages(data.messages))
      .catch(() => setMessages([]));
  }, [organizationId, selected]);

  async function reply(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!organizationId || !selected) return;
    const form = new FormData(event.currentTarget);
    await apiRequest<Message>(
      `/conversations/${selected.id}/manual-reply?organization_id=${organizationId}`,
      {
        method: "POST",
        body: { body: String(form.get("body")) },
      },
    );
    event.currentTarget.reset();
    const data = await apiRequest<{ messages: Message[] }>(
      `/conversations/${selected.id}/messages?organization_id=${organizationId}`,
    );
    setMessages(data.messages);
  }

  return (
    <>
      <PageHeader title="Conversations" description="Review AI-handled conversations and step in with manual replies." />
      <div className="grid min-h-[680px] gap-0 border border-line bg-white lg:grid-cols-[360px_1fr]">
        <aside className="border-r border-line">
          <div className="border-b border-line px-4 py-3 text-sm font-semibold">Inbox</div>
          <div className="divide-y divide-line">
            {conversations.map((conversation) => (
              <button
                key={conversation.id}
                type="button"
                className={`block w-full px-4 py-3 text-left text-sm hover:bg-mist ${
                  selected?.id === conversation.id ? "bg-mist" : ""
                }`}
                onClick={() => setSelected(conversation)}
              >
                <div className="font-medium">{conversation.customer_name || conversation.customer_id}</div>
                <div className="mt-1 flex justify-between text-xs text-zinc-500">
                  <span>{conversation.channel_type}</span>
                  <span>{conversation.status}</span>
                </div>
              </button>
            ))}
          </div>
        </aside>
        <section className="flex min-h-[680px] flex-col">
          <div className="border-b border-line px-4 py-3 text-sm font-semibold">
            {selected ? selected.customer_name || selected.customer_id : "No conversation selected"}
          </div>
          <div className="flex-1 space-y-3 overflow-auto bg-mist p-4">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`max-w-[760px] border border-line bg-white p-3 text-sm ${
                  message.direction === "outbound" ? "ml-auto" : ""
                }`}
              >
                <div className="mb-1 text-xs uppercase text-zinc-500">{message.sender_type}</div>
                <div>{message.body}</div>
              </div>
            ))}
          </div>
          <form onSubmit={reply} className="flex gap-3 border-t border-line p-4">
            <input name="body" className="flex-1 border border-line px-3 py-2 text-sm" required />
            <button className="inline-flex items-center gap-2 rounded bg-teal px-4 py-2 text-sm text-white">
              <Send size={16} />
              Send
            </button>
          </form>
        </section>
      </div>
    </>
  );
}

