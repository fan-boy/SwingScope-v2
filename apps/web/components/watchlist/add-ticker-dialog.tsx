"use client";

import { useState, useTransition } from "react";
import { Plus, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogClose,
} from "@/components/ui/dialog";
import { useRouter } from "next/navigation";

interface Props {
  watchlistId: string;
  open: boolean;
  onClose: () => void;
}

const TICKER_RE = /^[A-Z]{1,5}$/;

export function AddTickerDialog({ watchlistId, open, onClose }: Props) {
  const router = useRouter();
  const [symbol, setSymbol] = useState("");
  const [notes, setNotes] = useState("");
  const [priority, setPriority] = useState(false);
  const [error, setError] = useState("");
  const [isPending, startTransition] = useTransition();

  function validate(value: string): string {
    const v = value.trim().toUpperCase();
    if (!v) return "Symbol is required";
    if (!TICKER_RE.test(v)) return "Must be 1–5 uppercase letters (e.g. AAPL)";
    return "";
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const v = symbol.trim().toUpperCase();
    const err = validate(v);
    if (err) { setError(err); return; }

    startTransition(async () => {
      try {
        const res = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/api/watchlists/${watchlistId}/items`,
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ symbol: v, notes: notes || undefined, priority }),
          }
        );

        if (res.status === 409) {
          setError(`${v} is already in your watchlist`);
          return;
        }
        if (!res.ok) {
          const data = await res.json().catch(() => ({}));
          setError(data?.detail ?? "Failed to add ticker");
          return;
        }

        toast.success(`${v} added to watchlist`);
        setSymbol(""); setNotes(""); setPriority(false); setError("");
        onClose();
        router.refresh();
      } catch {
        toast.error("Network error — is the API running?");
      }
    });
  }

  return (
    <Dialog open={open} onOpenChange={(v) => { if (!v) { onClose(); setError(""); } }}>
      <DialogContent className="max-w-sm">
        <DialogHeader>
          <DialogTitle>Add Ticker</DialogTitle>
          <DialogDescription>Enter a US stock ticker symbol to track.</DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4 mt-2">
          <div className="space-y-1.5">
            <label className="text-sm font-medium" htmlFor="symbol">Symbol</label>
            <Input
              id="symbol"
              placeholder="AAPL"
              value={symbol}
              onChange={(e) => {
                const v = e.target.value.toUpperCase().replace(/[^A-Z]/g, "").slice(0, 5);
                setSymbol(v);
                setError("");
              }}
              className={error ? "border-destructive" : ""}
              autoFocus
              autoComplete="off"
            />
            {error && <p className="text-xs text-destructive">{error}</p>}
          </div>

          <div className="space-y-1.5">
            <label className="text-sm font-medium" htmlFor="notes">Notes <span className="text-muted-foreground font-normal">(optional)</span></label>
            <Input
              id="notes"
              placeholder="e.g. watching for breakout"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              maxLength={200}
            />
          </div>

          <label className="flex items-center gap-2 cursor-pointer select-none">
            <input
              type="checkbox"
              checked={priority}
              onChange={(e) => setPriority(e.target.checked)}
              className="rounded border-border"
            />
            <span className="text-sm">Mark as priority</span>
          </label>

          <div className="flex gap-2 pt-1">
            <Button type="submit" className="flex-1" disabled={isPending}>
              {isPending ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Plus className="w-4 h-4 mr-2" />}
              Add
            </Button>
            <DialogClose asChild>
              <Button type="button" variant="outline" className="flex-1" onClick={() => { onClose(); setError(""); }}>
                Cancel
              </Button>
            </DialogClose>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
