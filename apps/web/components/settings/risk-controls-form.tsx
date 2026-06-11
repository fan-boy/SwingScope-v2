"use client";

import { useState } from "react";
import { toast } from "sonner";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Separator } from "@/components/ui/separator";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

interface RiskSettings {
  kill_switch_active: boolean;
  max_risk_per_trade_pct: number;
  max_daily_loss_pct: number;
  max_concurrent_positions: number;
  max_new_positions_per_day: number;
  block_trades_near_earnings: boolean;
  account_size_usd: number;
}

interface Props {
  initialSettings: RiskSettings | null;
}

export function RiskControlsForm({ initialSettings }: Props) {
  const s = initialSettings;
  const [killSwitch, setKillSwitch] = useState(s?.kill_switch_active ?? false);
  const [maxRiskPct, setMaxRiskPct] = useState(String(s?.max_risk_per_trade_pct ?? 2.0));
  const [maxDailyPct, setMaxDailyPct] = useState(String(s?.max_daily_loss_pct ?? 5.0));
  const [maxPositions, setMaxPositions] = useState(String(s?.max_concurrent_positions ?? 5));
  const [maxNewDay, setMaxNewDay] = useState(String(s?.max_new_positions_per_day ?? 3));
  const [blockEarnings, setBlockEarnings] = useState(s?.block_trades_near_earnings ?? true);
  const [accountSize, setAccountSize] = useState(String(s?.account_size_usd ?? 100000));
  const [saving, setSaving] = useState(false);
  const [togglingKill, setTogglingKill] = useState(false);

  async function patch(data: Partial<RiskSettings>) {
    const res = await fetch(`${API_BASE}/api/settings`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error("Failed to save");
  }

  async function toggleKillSwitch() {
    setTogglingKill(true);
    try {
      const next = !killSwitch;
      await patch({ kill_switch_active: next });
      setKillSwitch(next);
      toast[next ? "warning" : "success"](
        next ? "Kill switch activated — trading halted" : "Kill switch deactivated — trading enabled"
      );
    } catch {
      toast.error("Failed to toggle kill switch");
    } finally {
      setTogglingKill(false);
    }
  }

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    try {
      await patch({
        max_risk_per_trade_pct: parseFloat(maxRiskPct),
        max_daily_loss_pct: parseFloat(maxDailyPct),
        max_concurrent_positions: parseInt(maxPositions),
        max_new_positions_per_day: parseInt(maxNewDay),
        block_trades_near_earnings: blockEarnings,
        account_size_usd: parseFloat(accountSize),
      });
      toast.success("Risk controls saved");
    } catch {
      toast.error("Failed to save risk controls");
    } finally {
      setSaving(false);
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Risk Controls</CardTitle>
        <CardDescription>Safeguards applied before any order is submitted</CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Kill switch */}
        <div className="flex items-center justify-between gap-4">
          <div>
            <p className="text-sm font-medium">Kill Switch</p>
            <p className="text-xs text-muted-foreground">Immediately halts all order submissions</p>
          </div>
          <Button
            variant={killSwitch ? "destructive" : "outline"}
            size="sm"
            onClick={toggleKillSwitch}
            disabled={togglingKill}
            className={killSwitch ? "" : "border-green-500/50 text-green-500 hover:bg-green-500/10"}
          >
            {togglingKill ? "…" : killSwitch ? "⛔ KILL SWITCH ON" : "✅ Trading Enabled"}
          </Button>
        </div>

        {killSwitch && (
          <div className="rounded-md bg-destructive/10 border border-destructive/30 px-3 py-2 text-sm text-destructive font-medium">
            ⛔ Kill switch active. No orders can be sent.
          </div>
        )}

        <Separator />

        {/* Risk config */}
        <form onSubmit={handleSave} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                Max Risk / Trade (%)
              </label>
              <Input type="number" min="0.1" max="20" step="0.1" value={maxRiskPct}
                onChange={e => setMaxRiskPct(e.target.value)} />
              <p className="text-xs text-muted-foreground">% of account per trade</p>
            </div>
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                Max Daily Loss (%)
              </label>
              <Input type="number" min="0.1" max="50" step="0.1" value={maxDailyPct}
                onChange={e => setMaxDailyPct(e.target.value)} />
              <p className="text-xs text-muted-foreground">Halt trading if exceeded</p>
            </div>
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                Max Open Positions
              </label>
              <Input type="number" min="1" max="50" step="1" value={maxPositions}
                onChange={e => setMaxPositions(e.target.value)} />
            </div>
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                Max New / Day
              </label>
              <Input type="number" min="1" max="20" step="1" value={maxNewDay}
                onChange={e => setMaxNewDay(e.target.value)} />
            </div>
            <div className="space-y-1.5 col-span-2">
              <label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                Account Size (USD)
              </label>
              <Input type="number" min="1000" step="1000" value={accountSize}
                onChange={e => setAccountSize(e.target.value)} />
              <p className="text-xs text-muted-foreground">Used for risk % calculations</p>
            </div>
          </div>

          <label className="flex items-center gap-3 cursor-pointer">
            <input type="checkbox" checked={blockEarnings}
              onChange={e => setBlockEarnings(e.target.checked)}
              className="w-4 h-4 rounded border-input" />
            <div>
              <p className="text-sm font-medium">Block trades near earnings</p>
              <p className="text-xs text-muted-foreground">Reject plans when an earnings event is detected</p>
            </div>
          </label>

          <Button type="submit" size="sm" disabled={saving}>
            {saving ? "Saving…" : "Save Risk Controls"}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
