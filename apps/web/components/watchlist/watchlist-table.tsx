"use client";

import { useState, useTransition } from "react";
import { useRouter } from "next/navigation";
import { Trash2, Star, StarOff, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { WatchlistItemResponse } from "@/lib/api";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const confidenceColor: Record<string, string> = {
  HIGH:   "border-green-500/30 text-green-400 bg-green-500/10",
  MEDIUM: "border-yellow-500/30 text-yellow-400 bg-yellow-500/10",
  LOW:    "border-red-500/30 text-red-400 bg-red-500/10",
};

export function WatchlistTableSkeleton() {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          {["Symbol", "Score", "Confidence", "Status", "Notes", ""].map((h, i) => (
            <TableHead key={i}>{h}</TableHead>
          ))}
        </TableRow>
      </TableHeader>
      <TableBody>
        {[...Array(5)].map((_, i) => (
          <TableRow key={i}>
            {[...Array(6)].map((_, j) => (
              <TableCell key={j}><Skeleton className="h-4 w-16" /></TableCell>
            ))}
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

interface Props {
  watchlistId: string;
  items: WatchlistItemResponse[];
}

export function WatchlistTable({ watchlistId, items }: Props) {
  const router = useRouter();
  const [pending, setPending] = useState<string | null>(null);

  async function handleRemove(item: WatchlistItemResponse) {
    setPending(item.id);
    try {
      const res = await fetch(`${API_BASE}/api/watchlists/${watchlistId}/items/${item.id}`, {
        method: "DELETE",
      });
      if (!res.ok) throw new Error("Failed");
      toast.success(`${item.symbol} removed`);
      router.refresh();
    } catch {
      toast.error("Failed to remove ticker");
    } finally {
      setPending(null);
    }
  }

  async function handleTogglePriority(item: WatchlistItemResponse) {
    setPending(item.id + "-priority");
    try {
      const res = await fetch(`${API_BASE}/api/watchlists/${watchlistId}/items/${item.id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ priority: !item.priority }),
      });
      if (!res.ok) throw new Error("Failed");
      toast.success(item.priority ? `${item.symbol} removed from priority` : `${item.symbol} marked as priority`);
      router.refresh();
    } catch {
      toast.error("Failed to update");
    } finally {
      setPending(null);
    }
  }

  // Sort: priority first, then alphabetical
  const sorted = [...items].sort((a, b) => {
    if (a.priority !== b.priority) return a.priority ? -1 : 1;
    return a.symbol.localeCompare(b.symbol);
  });

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Symbol</TableHead>
          <TableHead>Score</TableHead>
          <TableHead>Confidence</TableHead>
          <TableHead>Scan Status</TableHead>
          <TableHead>Notes</TableHead>
          <TableHead className="w-20 text-right">Actions</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {sorted.map((item) => (
          <TableRow key={item.id} className={item.priority ? "bg-primary/5" : ""}>
            <TableCell>
              <div className="flex items-center gap-2">
                {item.priority && (
                  <span className="text-yellow-400 text-xs">★</span>
                )}
                <span className="font-semibold">{item.symbol}</span>
              </div>
            </TableCell>
            <TableCell>
              {item.scan_score != null
                ? <span className={item.scan_score >= 75 ? "text-green-400 font-bold" : item.scan_score >= 55 ? "text-yellow-400" : "text-muted-foreground"}>
                    {item.scan_score.toFixed(1)}
                  </span>
                : <span className="text-muted-foreground text-xs">—</span>
              }
            </TableCell>
            <TableCell>
              {item.scan_confidence
                ? <Badge variant="outline" className={`text-[10px] h-5 ${confidenceColor[item.scan_confidence] ?? ""}`}>{item.scan_confidence}</Badge>
                : <span className="text-muted-foreground text-xs">—</span>
              }
            </TableCell>
            <TableCell>
              {item.scan_status
                ? <span className="text-xs text-muted-foreground">{item.scan_status}</span>
                : <span className="text-muted-foreground text-xs">Not scanned</span>
              }
            </TableCell>
            <TableCell>
              <span className="text-xs text-muted-foreground truncate max-w-[160px] block">
                {item.notes ?? "—"}
              </span>
            </TableCell>
            <TableCell>
              <div className="flex items-center justify-end gap-1">
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-7 w-7 text-muted-foreground hover:text-yellow-400"
                  onClick={() => handleTogglePriority(item)}
                  disabled={pending === item.id + "-priority"}
                  title={item.priority ? "Remove priority" : "Mark priority"}
                >
                  {pending === item.id + "-priority"
                    ? <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    : item.priority
                    ? <Star className="w-3.5 h-3.5 fill-yellow-400 text-yellow-400" />
                    : <Star className="w-3.5 h-3.5" />
                  }
                </Button>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-7 w-7 text-muted-foreground hover:text-destructive"
                  onClick={() => handleRemove(item)}
                  disabled={pending === item.id}
                  title="Remove"
                >
                  {pending === item.id
                    ? <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    : <Trash2 className="w-3.5 h-3.5" />
                  }
                </Button>
              </div>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
