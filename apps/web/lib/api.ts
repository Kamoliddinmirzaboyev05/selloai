"use client";

const API_URL =
  process.env.NEXT_PUBLIC_API_URL ||
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  "http://localhost:8000/api/v1";
const API_BASE_URL = API_URL.endsWith("/api/v1")
  ? API_URL
  : `${API_URL.replace(/\/$/, "")}/api/v1`;
const TOKEN_KEY = "sello_access_token";
const ORG_KEY = "sello_organization_id";

export type ApiMethod = "GET" | "POST" | "PATCH" | "DELETE";

export interface User {
  id: string;
  email: string;
  full_name: string;
}

export interface Organization {
  id: string;
  name: string;
  slug: string;
}

export interface Channel {
  id: string;
  organization_id: string;
  type: string;
  status: string;
  display_name: string;
  external_id: string | null;
}

export interface Conversation {
  id: string;
  organization_id: string;
  channel_id: string;
  customer_id: string;
  status: string;
  customer_name: string | null;
  channel_type: string | null;
  last_message_at: string | null;
}

export interface Message {
  id: string;
  direction: "inbound" | "outbound";
  sender_type: string;
  body: string;
  created_at: string;
}

export interface Customer {
  id: string;
  external_id: string;
  name: string | null;
  username: string | null;
  created_at: string;
}

export interface KnowledgeBaseEntry {
  id: string;
  organization_id: string;
  title: string;
  content: string;
  is_active: boolean;
}

export interface OrganizationSettings {
  organization_id: string;
  ai_tone: string;
  handoff_keywords: string;
  auto_reply_enabled: boolean;
}

export function getToken() {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string) {
  window.localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken() {
  window.localStorage.removeItem(TOKEN_KEY);
}

export function getStoredOrganizationId() {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(ORG_KEY);
}

export function setStoredOrganizationId(id: string) {
  window.localStorage.setItem(ORG_KEY, id);
}

export function clearStoredOrganizationId() {
  window.localStorage.removeItem(ORG_KEY);
}

export async function apiRequest<T>(
  path: string,
  options: { method?: ApiMethod; body?: unknown; token?: string | null } = {},
): Promise<T> {
  const token = options.token ?? getToken();
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: options.method || "GET",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: options.body ? JSON.stringify(options.body) : undefined,
    cache: "no-store",
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Request failed" }));
    throw new Error(error.detail || "Request failed");
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}
