"use client";

import { useEffect, useState } from "react";
import { PageHeader } from "@/components/page-header";
import { apiRequest, Customer, getStoredOrganizationId } from "@/lib/api";

export default function CustomersPage() {
  const [customers, setCustomers] = useState<Customer[]>([]);
  const organizationId = getStoredOrganizationId();

  useEffect(() => {
    if (!organizationId) return;
    apiRequest<Customer[]>(`/customers?organization_id=${organizationId}`)
      .then(setCustomers)
      .catch(() => setCustomers([]));
  }, [organizationId]);

  return (
    <>
      <PageHeader title="Customers" description="Lead records created from connected messaging channels." />
      <section className="overflow-hidden border border-line bg-white">
        <table className="w-full border-collapse text-left text-sm">
          <thead className="bg-mist text-xs uppercase text-zinc-500">
            <tr>
              <th className="px-4 py-3">Name</th>
              <th className="px-4 py-3">Username</th>
              <th className="px-4 py-3">External ID</th>
              <th className="px-4 py-3">Created</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-line">
            {customers.map((customer) => (
              <tr key={customer.id}>
                <td className="px-4 py-3">{customer.name || "Unknown"}</td>
                <td className="px-4 py-3">{customer.username || "-"}</td>
                <td className="px-4 py-3">{customer.external_id}</td>
                <td className="px-4 py-3">{new Date(customer.created_at).toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </>
  );
}

