import { TrendingUp, ShieldCheck, Clock, Radar, ArrowUpRight } from "lucide-react";
import { MetricCard } from "@/components/shared/metric-card";
import { EmptyState } from "@/components/shared/empty-state";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";

// Placeholder data — replace with real DB queries
const CANDIDATES = [
  { symbol: "NVDA", score: 82, confidence: "HIGH", entry: 875, stop: 848, target: 929, regime: "BULLISH" },
  { symbol: "AAPL", score: 78, confidence: "HIGH", entry: 192.5, stop: 187.2, target: 203.1, regime: "BULLISH" },
  { symbol: "MSFT", score: 71, confidence: "MEDIUM", entry: 422.3, stop: 411, target: 444.9, regime: "BULLISH" },
  { symbol: "V", score: 65, confidence: "MEDIUM", entry: 278, stop: 270.5, target: 293, regime: "NEUTRAL" },
];

const PENDING = [
  { symbol: "AMD", score: 68, note: "Awaiting volume confirmation" },
  { symbol: "META", score: 61, note: "Earnings in 4 days — watch risk" },
];

const REGIME = { label: "Bullish", color: "text-green-400", border: "border-green-500/20 bg-green-500/5", detail: "SPY + QQQ both above 20 EMA" };

const confidenceColor: Record<string, string> = {
  HIGH: "border-green-500/30 text-green-400 bg-green-500/10",
  MEDIUM: "border-yellow-500/30 text-yellow-400 bg-yellow-500/10",
  LOW: "border-red-500/30 text-red-400 bg-red-500/10",
};

export default function DashboardPage() {
  return (
    <div className="space-y-6 max-w-6xl">

      {/* Page title */}
      <div>
        <h1 className="text-xl font-semibold">Dashboard</h1>
        <p className="text-sm text-muted-foreground mt-0.5">
          {new Date().toLocaleDateString("en-US", { weekday: "long", month: "long", day: "numeric" })}
        </p>
      </div>

      {/* Metric row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <MetricCard
          title="Top Candidates"
          value={CANDIDATES.length}
          sub="Scored above threshold"
          icon={TrendingUp}
          trend="up"
        />
        <MetricCard
          title="Market Regime"
          value={REGIME.label}
          sub={REGIME.detail}
          icon={Radar}
          trend="up"
        />
        <MetricCard
          title="Pending Approvals"
          value={PENDING.length}
          sub="Needs review"
          icon={ShieldCheck}
          trend="neutral"
        />
        <MetricCard
          title="Last Scan"
          value="—"
          sub="No scan run today"
          icon={Clock}
          trend="neutral"
        />
      </div>

      {/* Main content */}
      <Tabs defaultValue="candidates">
        <TabsList className="bg-muted/50">
          <TabsTrigger value="candidates">Top Candidates</TabsTrigger>
          <TabsTrigger value="pending">Pending Approvals</TabsTrigger>
          <TabsTrigger value="scans">Recent Scans</TabsTrigger>
        </TabsList>

        {/* Tab: Top Candidates */}
        <TabsContent value="candidates">
          <Card>
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm font-medium">Today's Candidates</CardTitle>
                <Badge variant="outline" className={REGIME.border + " " + REGIME.color + " border text-xs"}>
                  🟢 {REGIME.label}
                </Badge>
              </div>
            </CardHeader>
            <Separator />
            <CardContent className="p-0">
              {CANDIDATES.length === 0 ? (
                <EmptyState
                  icon={TrendingUp}
                  title="No candidates yet"
                  description="Run a scan to generate today's trade ideas."
                />
              ) : (
                <div className="divide-y divide-border">
                  {CANDIDATES.map((c) => (
                    <div key={c.symbol} className="flex items-center justify-between px-6 py-4 hover:bg-accent/30 transition-colors group cursor-pointer">
                      <div className="flex items-center gap-4">
                        <div className="w-10 h-10 rounded-md bg-muted flex items-center justify-center text-xs font-bold">
                          {c.symbol.slice(0, 2)}
                        </div>
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="font-semibold text-sm">{c.symbol}</span>
                            <Badge variant="outline" className={`text-[10px] h-4 px-1.5 ${confidenceColor[c.confidence]}`}>
                              {c.confidence}
                            </Badge>
                          </div>
                          <p className="text-xs text-muted-foreground mt-0.5">
                            Entry ${c.entry} · Stop ${c.stop} · Target ${c.target}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-3">
                        <div className="text-right hidden sm:block">
                          <p className="text-xs text-muted-foreground">Score</p>
                          <p className="text-sm font-bold text-green-400">{c.score}</p>
                        </div>
                        <ArrowUpRight className="w-4 h-4 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tab: Pending Approvals */}
        <TabsContent value="pending">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium">Pending Approvals</CardTitle>
            </CardHeader>
            <Separator />
            <CardContent className="p-0">
              {PENDING.length === 0 ? (
                <EmptyState
                  icon={ShieldCheck}
                  title="Nothing to review"
                  description="All candidates have been actioned."
                />
              ) : (
                <div className="divide-y divide-border">
                  {PENDING.map((p) => (
                    <div key={p.symbol} className="flex items-center justify-between px-6 py-4 hover:bg-accent/30 transition-colors">
                      <div className="flex items-center gap-4">
                        <div className="w-10 h-10 rounded-md bg-muted flex items-center justify-center text-xs font-bold">
                          {p.symbol.slice(0, 2)}
                        </div>
                        <div>
                          <span className="font-semibold text-sm">{p.symbol}</span>
                          <p className="text-xs text-muted-foreground mt-0.5">{p.note}</p>
                        </div>
                      </div>
                      <span className="text-sm font-bold text-yellow-400">{p.score}</span>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tab: Recent Scans */}
        <TabsContent value="scans">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium">Recent Scans</CardTitle>
            </CardHeader>
            <Separator />
            <CardContent>
              <EmptyState
                icon={Clock}
                title="No scans yet"
                description="Scans run automatically after market close or can be triggered manually."
              />
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

    </div>
  );
}
