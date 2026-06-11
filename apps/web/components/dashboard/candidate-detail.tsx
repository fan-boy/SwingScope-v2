"use client";

import { CandidateResponse } from "@/lib/api";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription,
} from "@/components/ui/dialog";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { StockChart } from "@/components/dashboard/stock-chart";
import { ErrorBoundary } from "@/components/shared/error-boundary";

interface Props {
  candidate: CandidateResponse | null;
  open: boolean;
  onClose: () => void;
}

function Row({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between py-2">
      <span className="text-sm text-muted-foreground">{label}</span>
      <span className="text-sm font-medium">{value}</span>
    </div>
  );
}

const confidenceColor: Record<string, string> = {
  HIGH:   "border-green-500/30 text-green-400 bg-green-500/10",
  MEDIUM: "border-yellow-500/30 text-yellow-400 bg-yellow-500/10",
  LOW:    "border-red-500/30 text-red-400 bg-red-500/10",
};

export function CandidateDetail({ candidate: c, open, onClose }: Props) {
  if (!c) return null;

  const riskPerShare = (c.entry - c.stop).toFixed(2);
  const rewardPerShare = (c.target1 - c.entry).toFixed(2);

  return (
    <Dialog open={open} onOpenChange={(v) => { if (!v) onClose(); }}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-md bg-muted flex items-center justify-center text-sm font-bold">
              {c.symbol.slice(0, 2)}
            </div>
            <div>
              <DialogTitle className="text-xl">{c.symbol}</DialogTitle>
              <DialogDescription>
                Scan date {c.run_date} · {c.direction}
              </DialogDescription>
            </div>
            <Badge
              variant="outline"
              className={`ml-auto ${confidenceColor[c.confidence] ?? ""}`}
            >
              {c.confidence}
            </Badge>
          </div>
        </DialogHeader>

        <Separator />

        {/* Score breakdown */}
        <div className="space-y-0.5">
          <p className="text-xs uppercase tracking-wider text-muted-foreground mb-2">Score</p>
          <div className="flex items-end gap-2">
            <span className="text-3xl font-bold">{c.score.toFixed(1)}</span>
            <span className="text-muted-foreground text-sm mb-1">/ 100</span>
          </div>
          <div className="w-full bg-muted rounded-full h-1.5 mt-2">
            <div
              className="h-1.5 rounded-full bg-primary transition-all"
              style={{ width: `${c.score}%` }}
            />
          </div>
        </div>

        <Separator />

        {/* Trade levels */}
        <div>
          <p className="text-xs uppercase tracking-wider text-muted-foreground mb-3">Trade Levels</p>
          <div className="divide-y divide-border">
            <Row label="Entry" value={`$${c.entry.toFixed(2)}`} />
            <Row
              label="Stop"
              value={<span className="text-red-400">${c.stop.toFixed(2)}</span>}
            />
            <Row
              label="Target"
              value={<span className="text-green-400">${c.target1.toFixed(2)}</span>}
            />
            <Row label="R/R Ratio" value={`${c.rr_ratio.toFixed(1)}:1`} />
            <Row label="Risk / share" value={`$${riskPerShare}`} />
            <Row label="Reward / share" value={`$${rewardPerShare}`} />
          </div>
        </div>

        <Separator />

        {/* Technical setup */}
        {c.technical_setup && (
          <div>
            <p className="text-xs uppercase tracking-wider text-muted-foreground mb-2">
              Technical Setup
            </p>
            <p className="text-sm text-muted-foreground leading-relaxed">
              {c.technical_setup}
            </p>
          </div>
        )}

        {/* Chart */}
        <ErrorBoundary>
          <StockChart symbol={c.symbol} ideaEntry={c.entry} ideaStop={c.stop} />
        </ErrorBoundary>

        <p className="text-[11px] text-muted-foreground border-t border-border pt-3 mt-1">
          ⚠️ For informational purposes only. Not financial advice.
        </p>
      </DialogContent>
    </Dialog>
  );
}
