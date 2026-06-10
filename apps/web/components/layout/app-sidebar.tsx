"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, Star, Settings, TrendingUp, Activity } from "lucide-react";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";

const navItems = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/watchlist", label: "Watchlist", icon: Star },
  { href: "/settings", label: "Settings", icon: Settings },
];

function NavLinks({ onNavigate }: { onNavigate?: () => void }) {
  const pathname = usePathname();
  return (
    <nav className="flex-1 p-3 space-y-0.5">
      {navItems.map(({ href, label, icon: Icon }) => (
        <Link
          key={href}
          href={href}
          onClick={onNavigate}
          className={cn(
            "flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors",
            pathname === href
              ? "bg-accent text-foreground font-medium"
              : "text-muted-foreground hover:text-foreground hover:bg-accent/50"
          )}
        >
          <Icon className="w-4 h-4 shrink-0" />
          {label}
        </Link>
      ))}
    </nav>
  );
}

export function AppSidebar() {
  return (
    <aside className="fixed left-0 top-0 h-screen w-60 border-r border-border bg-card flex flex-col z-30">
      {/* Logo */}
      <div className="flex items-center gap-2.5 px-5 h-14 border-b border-border shrink-0">
        <div className="w-7 h-7 rounded-md bg-primary flex items-center justify-center">
          <TrendingUp className="w-4 h-4 text-primary-foreground" />
        </div>
        <span className="font-semibold text-sm tracking-tight">SwingScope</span>
        <Badge variant="outline" className="ml-auto text-[10px] py-0 h-5 border-primary/30 text-primary">
          v2
        </Badge>
      </div>

      {/* Nav */}
      <NavLinks />

      {/* Footer */}
      <div className="p-3 border-t border-border shrink-0">
        <div className="flex items-center gap-2 px-3 py-2">
          <Activity className="w-3.5 h-3.5 text-green-400" />
          <span className="text-xs text-muted-foreground">Market open</span>
        </div>
      </div>
    </aside>
  );
}

// Mobile version — used inside Sheet
export function MobileSidebarContent({ onNavigate }: { onNavigate?: () => void }) {
  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center gap-2.5 pb-4 border-b border-border mb-2">
        <div className="w-7 h-7 rounded-md bg-primary flex items-center justify-center">
          <TrendingUp className="w-4 h-4 text-primary-foreground" />
        </div>
        <span className="font-semibold text-sm">SwingScope</span>
      </div>
      <NavLinks onNavigate={onNavigate} />
    </div>
  );
}
