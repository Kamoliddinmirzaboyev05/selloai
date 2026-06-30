"use client";

import { FormEvent, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { apiRequest, Organization, setStoredOrganizationId, setToken } from "@/lib/api";

export function AuthForm({ mode }: { mode: "login" | "register" }) {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    const form = new FormData(event.currentTarget);
    const payload =
      mode === "register"
        ? {
            email: String(form.get("email")),
            full_name: String(form.get("full_name")),
            password: String(form.get("password")),
          }
        : {
            email: String(form.get("email")),
            password: String(form.get("password")),
          };

    try {
      const response = await apiRequest<{ access_token: string }>(`/auth/${mode}`, {
        method: "POST",
        body: payload,
        token: null,
      });
      setToken(response.access_token);
      const organizations = await apiRequest<Organization[]>("/organizations", {
        token: response.access_token,
      });
      if (organizations.length > 0) {
        setStoredOrganizationId(organizations[0].id);
        router.push("/dashboard");
        return;
      }
      router.push("/dashboard/onboarding");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Authentication failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="grid min-h-screen place-items-center bg-[radial-gradient(circle_at_top_left,#dff3ef,transparent_34%),#f4f6f8] px-4">
      <form onSubmit={submit} className="w-full max-w-sm rounded-lg border border-line bg-white p-6 shadow-sm">
        <div className="mb-6">
          <div className="text-xl font-semibold">Sello AI</div>
          <p className="mt-1 text-sm text-zinc-600">
            {mode === "register" ? "Create your operator account." : "Sign in to your workspace."}
          </p>
        </div>
        <div className="space-y-4">
          {mode === "register" ? (
            <label className="block text-sm">
              Full name
              <input name="full_name" className="mt-1 w-full border border-line px-3 py-2" required />
            </label>
          ) : null}
          <label className="block text-sm">
            Email
            <input
              name="email"
              type="email"
              className="mt-1 w-full rounded border border-line px-3 py-2"
              required
            />
          </label>
          <label className="block text-sm">
            Password
            <input
              name="password"
              type="password"
              minLength={8}
              className="mt-1 w-full rounded border border-line px-3 py-2"
              required
            />
          </label>
        </div>
        {error ? <p className="mt-4 text-sm text-coral">{error}</p> : null}
        <button
          type="submit"
          disabled={loading}
          className="mt-6 w-full rounded bg-teal px-4 py-2 text-sm font-medium text-white disabled:opacity-60"
        >
          {loading ? "Working..." : mode === "register" ? "Create account" : "Sign in"}
        </button>
        <p className="mt-4 text-center text-sm text-zinc-600">
          {mode === "register" ? "Already registered?" : "New to Sello AI?"}{" "}
          <Link className="font-medium text-teal" href={mode === "register" ? "/login" : "/register"}>
            {mode === "register" ? "Sign in" : "Create account"}
          </Link>
        </p>
      </form>
    </main>
  );
}
