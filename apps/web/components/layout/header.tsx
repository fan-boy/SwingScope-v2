"use client";

import { signOut, useSession } from "next-auth/react";
import { Button } from "@/components/ui/button";
import { LogOut } from "lucide-react";

export function Header({ title }: { title?: string }) {
  const { data: session } = useSession();

  return (
    <header className="h-14 border-b border-border flex items-center justify-between px-6 bg-background">
      <span className="text-sm text-muted-foreground">
        {title ?? "SwingScope"}
      </span>
      <div className="flex items-center gap-3">
        {session?.user?.email && (
          <span className="text-xs text-muted-foreground hidden sm:block">
            {session.user.email}
          </span>
        )}
        <Button
          variant="ghost"
          size="sm"
          onClick={() => signOut({ callbackUrl: "/login" })}
          className="gap-2 text-muted-foreground hover:text-foreground"
        >
          <LogOut className="w-4 h-4" />
          Sign out
        </Button>
      </div>
    </header>
  );
}
