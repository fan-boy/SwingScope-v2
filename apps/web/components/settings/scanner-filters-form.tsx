"use client";

import { useState, useEffect } from "react";
import { toast } from "sonner";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

const STORAGE_KEY = "swingscope_scanner_config";

export interface ScannerFilterConfig {
  min_price: number;
  min_avg_dollar_volume: number;
  min_relative_volume: number;
  require_above_ma20: boolean;
  require_above_ma50: boolean;
  require_ma20_above_ma50: boolean;
  min_final_score: number;
  max_candidates: number;
}

const DEFAULTS: ScannerFilterConfig = {
  min_price: 5,
  min_avg_dollar_volume: 10_000_000,
  min_relative_volume: 0.5,
  require_above_ma20: true,
  require_above_ma50: false,
  require_ma20_above_ma50: false,
  min_final_score: 30,
  max_candidates: 20,
};

export function getScannerConfig(): ScannerFilterConfig {
  if (typeof window === "undefined") return DEFAULTS;
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    return stored ? { ...DEFAULTS, ...JSON.parse(stored) } : DEFAULTS;
  } catch {
    return DEFAULTS;
  }
}

export function ScannerFiltersForm() {
  const [cfg, setCfg] = useState<ScannerFilterConfig>(DEFAULTS);

  useEffect(() => {
    setCfg(getScannerConfig());
  }, []);

  function update(key: keyof ScannerFilterConfig, value: number | boolean) {
    setCfg(prev => ({ ...prev, [key]: value }));
  }

  function handleSave() {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(cfg));
    toast.success("Filter settings saved — will apply on next scan");
  }

  function handleReset() {
    setCfg(DEFAULTS);
    localStorage.removeItem(STORAGE_KEY);
    toast.success("Filters reset to defaults");
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Scanner Filters</CardTitle>
        <CardDescription>Applied when you run a scan. Stricter = fewer but higher-quality candidates.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-5">
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-1.5">
            <label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Min Price ($)</label>
            <Input type="number" min="0" step="1" value={cfg.min_price}
              onChange={e => update("min_price", parseFloat(e.target.value))} />
          </div>
          <div className="space-y-1.5">
            <label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Min Avg Daily Volume ($)</label>
            <Input type="number" min="0" step="1000000" value={cfg.min_avg_dollar_volume}
              onChange={e => update("min_avg_dollar_volume", parseFloat(e.target.value))} />
            <p className="text-xs text-muted-foreground">e.g. 10000000 = $10M</p>
          </div>
          <div className="space-y-1.5">
            <label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Min Relative Volume</label>
            <Input type="number" min="0" step="0.1" value={cfg.min_relative_volume}
              onChange={e => update("min_relative_volume", parseFloat(e.target.value))} />
            <p className="text-xs text-muted-foreground">0.5 = 50% of avg volume</p>
          </div>
          <div className="space-y-1.5">
            <label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Min Score (0–100)</label>
            <Input type="number" min="0" max="100" step="5" value={cfg.min_final_score}
              onChange={e => update("min_final_score", parseFloat(e.target.value))} />
          </div>
          <div className="space-y-1.5">
            <label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Max Candidates</label>
            <Input type="number" min="1" max="50" step="1" value={cfg.max_candidates}
              onChange={e => update("max_candidates", parseInt(e.target.value))} />
          </div>
        </div>

        <div className="space-y-2">
          <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Moving Average Rules</p>
          {[
            { key: "require_above_ma20" as const, label: "Price above MA20", desc: "Only show stocks in short-term uptrend" },
            { key: "require_above_ma50" as const, label: "Price above MA50", desc: "Only show stocks in medium-term uptrend" },
            { key: "require_ma20_above_ma50" as const, label: "MA20 > MA50", desc: "Require bullish MA crossover" },
          ].map(({ key, label, desc }) => (
            <label key={key} className="flex items-center gap-3 cursor-pointer">
              <input type="checkbox" checked={cfg[key] as boolean}
                onChange={e => update(key, e.target.checked)}
                className="w-4 h-4 rounded border-input" />
              <div>
                <p className="text-sm font-medium">{label}</p>
                <p className="text-xs text-muted-foreground">{desc}</p>
              </div>
            </label>
          ))}
        </div>

        <div className="flex gap-2">
          <Button size="sm" onClick={handleSave}>Save Filters</Button>
          <Button size="sm" variant="outline" onClick={handleReset}>Reset to Defaults</Button>
        </div>
      </CardContent>
    </Card>
  );
}
