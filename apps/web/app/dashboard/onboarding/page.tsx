"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { PageHeader } from "@/components/page-header";
import { apiRequest, Organization, setStoredOrganizationId } from "@/lib/api";

export default function OnboardingPage() {
  const router = useRouter();
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiRequest<Organization[]>("/organizations").then(setOrganizations).catch(() => setOrganizations([]));
  }, []);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    try {
      const organization = await apiRequest<Organization>("/organizations", {
        method: "POST",
        body: { name: String(form.get("name")) },
      });
      setStoredOrganizationId(organization.id);
      router.push("/dashboard/channels");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create organization");
    }
  }

  return (
    <>
      <PageHeader title="Onboarding" description="Create or select the organization this dashboard manages." />
      <div className="grid gap-6 lg:grid-cols-[1fr_1fr]">
        <form onSubmit={submit} className="border border-line bg-white p-5">
          <label className="block text-sm">
            Organization name
            <input name="name" className="mt-1 w-full border border-line px-3 py-2" required />
          </label>
          {error ? <p className="mt-3 text-sm text-coral">{error}</p> : null}
          <button className="mt-4 rounded bg-teal px-4 py-2 text-sm font-medium text-white" type="submit">
            Create organization
          </button>
        </form>
        <section className="border border-line bg-white">
          <div className="border-b border-line px-4 py-3 text-sm font-semibold">Your organizations</div>
          <div className="divide-y divide-line">
            {organizations.map((organization) => (
              <button
                key={organization.id}
                type="button"
                className="block w-full px-4 py-3 text-left text-sm hover:bg-mist"
                onClick={() => {
                  setStoredOrganizationId(organization.id);
                  router.push("/dashboard");
                }}
              >
                <span className="font-medium">{organization.name}</span>
                <span className="ml-2 text-zinc-500">{organization.slug}</span>
              </button>
            ))}
          </div>
        </section>
      </div>
    </>
  );
}

