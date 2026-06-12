import { Suspense } from "react";
import { TrendingUp, ShieldCheck, Clock, Radar } from "lucide-react";
import { MetricCard } from "@/components/shared/metric-card";
import { EmptyState } from "@/components/shared/empty-state";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import { CandidatesTable, CandidatesTableSkeleton } from "@/components/dashboard/candidates-table";
import { TriggerScanButton } from "@/components/dashboard/trigger-scan-button";
import { api, ScanRunResponse } from "@/lib/api";

// ── Helpers ──────────────────────────────────────────────────────────────

function regimeBadge(regime: string | null) {
  if (!regime) return null;
  const styles: Record<string, string> = {
    BULLISH:  "border-green-500/30 text-green-400 bg-green-500/10",
    NEUTRAL:  "border-yellow-500/30 text-yellow-400 bg-yellow-500/10",
    RISK_OFF: "border-red-500/30 text-red-400 bg-red-500/10",
  };
  const icons: Record<string, string> = { BULLISH: "🟢", NEUTRAL: "🟡", RISK_OFF: "🔴" };
  return (
    <Badge variant="outline" className={styles[regime] ?? ""}>
      {icons[regime] ?? ""} {regime}
    </Badge>
  );
}

function formatDuration(ms: number | null) {
  if (!ms) return "—";
  return ms < 1000 ? `${ms}ms` : `${(ms / 1000).toFixed(1)}s`;
}

function formatTime(iso: string) {
  return new Date(iso).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

// ── Server data fetch ─────────────────────────────────────────────────────

async function getLatestScan(): Promise<ScanRunResponse | null> {
  try {
    return await api.scans.latest();
  } catch {
    return null;
  }
}

// ── Page ──────────────────────────────────────────────────────────────────

export default async function DashboardPage() {
  const scan = await getLatestScan();
  const candidates = scan?.candidates ?? [];

  return (
    <div className="space-y-6 max-w-6xl">
      {/* Page header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold">Dashboard</h1>
          <p className="text-sm text-muted-foreground mt-0.5">
            {new Date().toLocaleDateString("en-US", {
              weekday: "long", month: "long", day: "numeric",
            })}
          </p>
        </div>
        <div className="flex items-center gap-2">
          {scan?.is_mocked && (
            <Badge variant="outline" className="border-yellow-500/30 text-yellow-400 text-xs">
              Mock data
            </Badge>
          )}
          <TriggerScanButton />
        </div>
      </div>

      {/* Metric cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <MetricCard
          title="Top Candidates"
          value={scan ? candidates.length : undefined}
          sub={scan ? `${scan.tickers_scanned} tickers scanned` : "No scan yet"}
          icon={TrendingUp}
          trend={candidates.length > 0 ? "up" : "neutral"}
          loading={false}
        />
        <Card>
          <div className="flex flex-col p-6 pb-2 space-y-1.5">
            <div className="flex items-center justify-between">
              <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                Market Regime
              </p>
              <Radar className="w-4 h-4 text-muted-foreground" />
            </div>
          </div>
          <CardContent className="pt-0">
            {scan?.market_regime
              ? regimeBadge(scan.market_regime)
              : <p className="text-2xl font-bold">—</p>
            }
            {scan?.market_regime && (
              <p className="text-xs text-muted-foreground mt-1">
                {scan.market_regime === "BULLISH"
                  ? "SPY & QQQ above MA20"
                  : scan.market_regime === "NEUTRAL"
                  ? "Mixed signals"
                  : "Risk-off environment"
                }
              </p>
            )}
          </CardContent>
        </Card>
        <MetricCard
          title="Pending Review"
          value={candidates.filter(c => c.status === "NEW").length || (scan ? 0 : undefined)}
          sub="Awaiting your review"
          icon={ShieldCheck}
          trend="neutral"
          loading={false}
        />
        <MetricCard
          title="Last Scan"
          value={scan ? formatTime(scan.created_at) : undefined}
          sub={scan ? `Took ${formatDuration(scan.duration_ms)}` : "Never run"}
          icon={Clock}
          trend="neutral"
          loading={false}
        />
      </div>

      {/* Candidates table */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm font-medium">
              Top Candidates
              {candidates.length > 0 && (
                <span className="ml-2 text-xs font-normal text-muted-foreground">
                  {candidates.length} ranked
                </span>
              )}
            </CardTitle>
            {scan && regimeBadge(scan.market_regime)}
          </div>
        </CardHeader>
        <Separator />
        <CardContent className="p-0">
          {!scan ? (
            <EmptyState
              icon={Clock}
              title="No scan data"
              description="Run a scan from the API to generate candidates."
            />
          ) : candidates.length === 0 ? (
            <EmptyState
              icon={TrendingUp}
              title="No candidates found"
              description="No stocks passed the filter criteria in the last scan."
            />
          ) : (
            <CandidatesTable candidates={candidates} />
          )}
        </CardContent>
      </Card>

      {scan && (
        <p className="text-xs text-muted-foreground">
          Last updated {new Date(scan.created_at).toLocaleString()} ·
          Scan ID {scan.id.slice(0, 8)}…
        </p>
      )}
    </div>
  );
}
