"use client";

import { signOut, useSession } from "next-auth/react";
import { Menu, LogOut, User, ChevronDown } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
  SheetClose,
} from "@/components/ui/sheet";
import { MobileSidebarContent } from "./app-sidebar";
import { useState } from "react";

interface AppHeaderProps {
  title: string;
}

export function AppHeader({ title }: AppHeaderProps) {
  const { data: session } = useSession();
  const [sheetOpen, setSheetOpen] = useState(false);

  return (
    <header className="h-14 border-b border-border bg-background flex items-center justify-between px-4 md:px-6 shrink-0">
      {/* Mobile menu trigger */}
      <div className="flex items-center gap-3">
        <Sheet open={sheetOpen} onOpenChange={setSheetOpen}>
          <SheetTrigger asChild>
            <Button variant="ghost" size="icon" className="md:hidden">
              <Menu className="w-5 h-5" />
              <span className="sr-only">Open menu</span>
            </Button>
          </SheetTrigger>
          <SheetContent side="left" className="w-64 p-5">
            <SheetHeader>
              <SheetTitle className="sr-only">Navigation</SheetTitle>
            </SheetHeader>
            <MobileSidebarContent onNavigate={() => setSheetOpen(false)} />
          </SheetContent>
        </Sheet>

        <h1 className="text-sm font-semibold text-foreground">{title}</h1>
      </div>

      {/* Right side — user menu */}
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="ghost" size="sm" className="gap-2 text-muted-foreground hover:text-foreground">
            <div className="w-6 h-6 rounded-full bg-primary/20 flex items-center justify-center">
              <User className="w-3.5 h-3.5 text-primary" />
            </div>
            <span className="hidden sm:block text-xs max-w-[140px] truncate">
              {session?.user?.email ?? "Account"}
            </span>
            <ChevronDown className="w-3.5 h-3.5" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" className="w-52">
          <DropdownMenuLabel>
            <span className="block text-xs font-normal text-muted-foreground truncate">
              {session?.user?.email}
            </span>
          </DropdownMenuLabel>
          <DropdownMenuSeparator />
          <DropdownMenuItem
            onClick={() => signOut({ callbackUrl: "/login" })}
            className="text-destructive focus:text-destructive gap-2 cursor-pointer"
          >
            <LogOut className="w-4 h-4" />
            Sign out
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </header>
  );
}
