"use client";

import { useState } from "react";
import { CandidateResponse } from "@/lib/api";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { CandidateDetail } from "@/components/dashboard/candidate-detail";

// ── Helpers ──────────────────────────────────────────────────────────────

function confidenceBadge(c: string) {
  const styles: Record<string, string> = {
    HIGH:   "border-green-500/30 text-green-400 bg-green-500/10",
    MEDIUM: "border-yellow-500/30 text-yellow-400 bg-yellow-500/10",
    LOW:    "border-red-500/30 text-red-400 bg-red-500/10",
  };
  return (
    <Badge variant="outline" className={`text-[10px] h-5 px-1.5 ${styles[c] ?? ""}`}>
      {c}
    </Badge>
  );
}

function maStatus(setup: string | null) {
  if (!setup) return <span className="text-muted-foreground text-xs">—</span>;
  const hasMA50 = setup.includes("MA50");
  return (
    <span className="text-xs text-muted-foreground">
      {hasMA50 ? "MA20 ✓ MA50 ✓" : "MA20 ✓"}
    </span>
  );
}

function scoreColor(score: number) {
  if (score >= 75) return "text-green-400 font-bold";
  if (score >= 55) return "text-yellow-400 font-semibold";
  return "text-muted-foreground";
}

function breakoutBadge(setup: string | null) {
  if (!setup) return <span className="text-xs text-muted-foreground">—</span>;
  if (setup.includes("Above 20-day high")) {
    return <Badge variant="outline" className="text-[10px] border-green-500/30 text-green-400 bg-green-500/10">Breakout</Badge>;
  }
  const match = setup.match(/([\d.]+)% from/);
  if (match) {
    return <span className="text-xs text-muted-foreground">{match[1]}% below</span>;
  }
  return <span className="text-xs text-muted-foreground">—</span>;
}

// ── Skeleton rows ─────────────────────────────────────────────────────────

export function CandidatesTableSkeleton() {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          {["Symbol", "Price", "Score", "Confidence", "Rel Vol", "MA Status", "Breakout"].map(h => (
            <TableHead key={h}>{h}</TableHead>
          ))}
        </TableRow>
      </TableHeader>
      <TableBody>
        {[...Array(8)].map((_, i) => (
          <TableRow key={i}>
            {[...Array(7)].map((_, j) => (
              <TableCell key={j}><Skeleton className="h-4 w-16" /></TableCell>
            ))}
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

// ── Main table ─────────────────────────────────────────────────────────────

interface Props {
  candidates: CandidateResponse[];
}

export function CandidatesTable({ candidates }: Props) {
  const [selected, setSelected] = useState<CandidateResponse | null>(null);

  if (candidates.length === 0) return null;

  return (
    <>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Symbol</TableHead>
            <TableHead>Price</TableHead>
            <TableHead>Score</TableHead>
            <TableHead>Confidence</TableHead>
            <TableHead>Rel Vol</TableHead>
            <TableHead>MA Status</TableHead>
            <TableHead>Breakout</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {candidates.map((c) => (
            <TableRow
              key={c.id}
              className="cursor-pointer"
              onClick={() => setSelected(c)}
            >
              <TableCell className="font-semibold">{c.symbol}</TableCell>
              <TableCell>${c.entry.toFixed(2)}</TableCell>
              <TableCell>
                <span className={scoreColor(c.score)}>{c.score.toFixed(1)}</span>
              </TableCell>
              <TableCell>{confidenceBadge(c.confidence)}</TableCell>
              <TableCell>
                {/* rel volume extracted from technical_setup */}
                {(() => {
                  const m = c.technical_setup?.match(/Rel vol ([\d.]+)x/);
                  return m
                    ? <span className="text-xs">{m[1]}×</span>
                    : <span className="text-xs text-muted-foreground">—</span>;
                })()}
              </TableCell>
              <TableCell>{maStatus(c.technical_setup)}</TableCell>
              <TableCell>{breakoutBadge(c.technical_setup)}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>

      <CandidateDetail
        candidate={selected}
        open={!!selected}
        onClose={() => setSelected(null)}
      />
    </>
  );
}
