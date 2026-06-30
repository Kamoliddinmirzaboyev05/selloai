"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  Bot,
  BookOpen,
  Cable,
  LayoutDashboard,
  LogOut,
  MessageSquare,
  Settings,
  Users,
} from "lucide-react";
import { clearStoredOrganizationId, clearToken } from "@/lib/api";

const navItems = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/dashboard/conversations", label: "Conversations", icon: MessageSquare },
  { href: "/dashboard/customers", label: "Customers", icon: Users },
  { href: "/dashboard/knowledge-base", label: "Knowledge Base", icon: BookOpen },
  { href: "/dashboard/channels", label: "Channels", icon: Cable },
  { href: "/dashboard/settings", label: "Settings", icon: Settings },
];

export function DashboardShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();

  function logout() {
    clearToken();
    clearStoredOrganizationId();
    router.push("/login");
  }

  return (
    <div className="min-h-screen bg-[#eef2f3] text-ink">
      <aside className="fixed inset-y-0 left-0 hidden w-64 border-r border-line bg-white/95 lg:block">
        <div className="flex h-16 items-center gap-3 border-b border-line px-5">
          <div className="grid h-9 w-9 place-items-center rounded-lg bg-teal text-white shadow-sm">
            <Bot size={20} />
          </div>
          <div>
            <div className="text-sm font-semibold">Sello AI</div>
            <div className="text-xs text-zinc-500">Sales assistant</div>
          </div>
        </div>
        <nav className="space-y-1 p-3">
          {navItems.map((item) => {
            const Icon = item.icon;
            const active = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition ${
                  active ? "bg-teal text-white shadow-sm" : "text-zinc-700 hover:bg-mist"
                }`}
              >
                <Icon size={17} />
                {item.label}
              </Link>
            );
          })}
        </nav>
        <button
          type="button"
          onClick={logout}
          className="absolute bottom-4 left-3 right-3 flex items-center gap-3 rounded-lg px-3 py-2 text-sm text-zinc-700 hover:bg-mist"
        >
          <LogOut size={17} />
          Sign out
        </button>
      </aside>
      <main className="lg:pl-64">
        <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">{children}</div>
      </main>
    </div>
  );
}
