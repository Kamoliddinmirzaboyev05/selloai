import { apiRequest, KnowledgeBaseEntry } from "@/lib/api";

export const demoFaqs = [
  {
    title: "Store hours",
    content:
      "We are open Monday to Friday from 9 AM to 6 PM. Weekend appointments can be arranged for qualified leads.",
  },
  {
    title: "Shipping and delivery",
    content:
      "Orders ship within two business days. Local delivery is available for priority customers in the city.",
  },
  {
    title: "Pricing questions",
    content:
      "Ask what product or service the customer is interested in, then offer to share a tailored quote or connect them with a human sales operator.",
  },
];

export async function seedDemoKnowledgeBase(organizationId: string) {
  return Promise.all(
    demoFaqs.map((entry) =>
      apiRequest<KnowledgeBaseEntry>("/knowledge-base", {
        method: "POST",
        body: {
          organization_id: organizationId,
          title: entry.title,
          content: entry.content,
          is_active: true,
        },
      }),
    ),
  );
}
