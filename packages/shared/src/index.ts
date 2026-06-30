export const channelTypes = ["telegram", "instagram", "whatsapp", "website_chat"] as const;
export const conversationStatuses = ["open", "ai_handling", "human_handoff", "closed"] as const;

export type ChannelType = (typeof channelTypes)[number];
export type ConversationStatus = (typeof conversationStatuses)[number];

export interface ApiError {
  detail: string;
  code: string;
}

export interface OrganizationDto {
  id: string;
  name: string;
  slug: string;
}

export interface ConversationDto {
  id: string;
  status: ConversationStatus;
  customerName: string;
  channelType: ChannelType;
  lastMessageAt: string | null;
}

