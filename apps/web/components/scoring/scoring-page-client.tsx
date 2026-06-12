"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";

const STORAGE_KEY = "swingscope_scoring_weights";

// ── Types ────────────────────────────────────────────────────────────────────

interface ScoringWeights {
  // Weights (must sum to 100)
  weight_trend: number;
  weight_volume: number;
  weight_breakout: number;
  // Trend sub-scores
  trend_above_ma20: number;       // pts for price > MA20
  trend_above_ma50: number;       // pts for price > MA50
  trend_ma20_above_ma50: number;  // pts for MA20 > MA50
  trend_ma50_above_ma200: number; // pts for MA50 > MA200
  // Volume thresholds
  volume_base_rv: number;         // relative volume for 50pts
  // Breakout
  breakout_pct: number;           // % from high = in breakout zone
  // Confidence
  confidence_high: number;        // score >= this = HIGH
  confidence_medium: number;      // score >= this = MEDIUM
}

const DEFAULT_WEIGHTS: ScoringWeights = {
  weight_trend: 40,
  weight_volume: 30,
  weight_breakout: 30,
  trend_above_ma20: 40,
  trend_above_ma50: 30,
  trend_ma20_above_ma50: 20,
  trend_ma50_above_ma200: 10,
  volume_base_rv: 2.0,
  breakout_pct: 3,
  confidence_high: 75,
  confidence_medium: 55,
};

function loadWeights(): ScoringWeights {
  if (typeof window === "undefined") return DEFAULT_WEIGHTS;
  try {
    const s = localStorage.getItem(STORAGE_KEY);
    return s ? { ...DEFAULT_WEIGHTS, ...JSON.parse(s) } : DEFAULT_WEIGHTS;
  } catch { return DEFAULT_WEIGHTS; }
}

// ── Score preview calculator ──────────────────────────────────────────────────

interface PreviewInputs {
  close: number; ma20: number; ma50: number; ma200: number;
  relVol: number; pctFromHigh20: number;
}

function calcScore(w: ScoringWeights, inp: PreviewInputs) {
  // Trend
  let trend = 0;
  if (inp.close > inp.ma20) trend += w.trend_above_ma20;
  if (inp.close > inp.ma50) trend += w.trend_above_ma50;
  if (inp.ma20 > inp.ma50) trend += w.trend_ma20_above_ma50;
  if (inp.ma50 > inp.ma200) trend += w.trend_ma50_above_ma200;
  trend = Math.min(100, trend);

  // Volume: 0x→0, base_rv→50, 2*base_rv→100
  const volume = Math.min(100, (inp.relVol / (w.volume_base_rv * 2)) * 100);

  // Breakout
  let breakout = 0;
  const pct = inp.pctFromHigh20;
  if (pct >= 0) breakout = 100;
  else if (Math.abs(pct) <= w.breakout_pct / 100) breakout = 100 - (Math.abs(pct) / (w.breakout_pct / 100)) * 50;
  else breakout = Math.max(0, 30 - Math.abs(pct) * 200);

  const total = Math.min(100, (w.weight_trend / 100) * trend + (w.weight_volume / 100) * volume + (w.weight_breakout / 100) * breakout);
  const confidence = total >= w.confidence_high ? "HIGH" : total >= w.confidence_medium ? "MEDIUM" : "LOW";
  return { trend: Math.round(trend), volume: Math.round(volume), breakout: Math.round(breakout), total: Math.round(total), confidence };
}

// ── Sub-components ────────────────────────────────────────────────────────────

function ScoreBar({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-xs">
        <span className="text-muted-foreground">{label}</span>
        <span className="font-medium tabular-nums">{value}/100</span>
      </div>
      <div className="h-2 bg-muted rounded-full overflow-hidden">
        <div className={`h-full rounded-full transition-all ${color}`} style={{ width: `${value}%` }} />
      </div>
    </div>
  );
}

function WeightRow({ label, desc, field, value, onChange, min = 0, max = 100, step = 1 }: {
  label: string; desc: string; field: string; value: number;
  onChange: (v: number) => void; min?: number; max?: number; step?: number;
}) {
  return (
    <div className="flex items-start gap-4 py-3 border-b border-border last:border-0">
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium">{label}</p>
        <p className="text-xs text-muted-foreground mt-0.5">{desc}</p>
      </div>
      <div className="flex items-center gap-2 shrink-0">
        <Input
          type="number" min={min} max={max} step={step}
          value={value}
          onChange={e => onChange(parseFloat(e.target.value) || 0)}
          className="w-20 h-8 text-sm text-right tabular-nums"
        />
      </div>
    </div>
  );
}

function ConfidenceBadge({ level }: { level: string }) {
  if (level === "HIGH") return <Badge className="bg-green-500/20 text-green-400 border-green-500/30">HIGH</Badge>;
  if (level === "MEDIUM") return <Badge className="bg-yellow-500/20 text-yellow-400 border-yellow-500/30">MEDIUM</Badge>;
  return <Badge className="bg-muted text-muted-foreground">LOW</Badge>;
}

// ── Main Component ─────────────────────────────────────────────────────────────

export function ScoringPageClient() {
  const [weights, setWeights] = useState<ScoringWeights>(DEFAULT_WEIGHTS);
  const [preview, setPreview] = useState<PreviewInputs>({
    close: 150, ma20: 145, ma50: 140, ma200: 130, relVol: 1.2, pctFromHigh20: -0.01,
  });

  useEffect(() => { setWeights(loadWeights()); }, []);

  function update(key: keyof ScoringWeights, value: number) {
    setWeights(prev => ({ ...prev, [key]: value }));
  }

  function updatePreview(key: keyof PreviewInputs, value: number) {
    setPreview(prev => ({ ...prev, [key]: value }));
  }

  function handleSave() {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(weights));
    toast.success("Scoring weights saved");
  }

  function handleReset() {
    setWeights(DEFAULT_WEIGHTS);
    localStorage.removeItem(STORAGE_KEY);
    toast.success("Reset to defaults");
  }

  const score = calcScore(weights, preview);
  const weightSum = weights.weight_trend + weights.weight_volume + weights.weight_breakout;

  return (
    <div className="max-w-4xl space-y-6">
      <div>
        <h1 className="text-xl font-semibold">Scoring Algorithm</h1>
        <p className="text-sm text-muted-foreground mt-0.5">
          Understand how candidates are scored and tune the weights to your style.
        </p>
      </div>

      {/* How it works */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">How Scoring Works</CardTitle>
          <CardDescription>Each candidate gets a 0–100 score from three components</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {[
              {
                title: "📈 Trend Score",
                weight: weights.weight_trend,
                color: "bg-blue-500",
                points: [
                  `+${weights.trend_above_ma20}pts — Price above MA20`,
                  `+${weights.trend_above_ma50}pts — Price above MA50`,
                  `+${weights.trend_ma20_above_ma50}pts — MA20 > MA50`,
                  `+${weights.trend_ma50_above_ma200}pts — MA50 > MA200`,
                ],
                note: "Measures trend strength across timeframes."
              },
              {
                title: "📊 Volume Score",
                weight: weights.weight_volume,
                color: "bg-purple-500",
                points: [
                  `0x vol = 0pts`,
                  `${weights.volume_base_rv}x vol = 50pts`,
                  `${weights.volume_base_rv * 2}x+ vol = 100pts`,
                ],
                note: "Higher-than-average volume signals conviction."
              },
              {
                title: "🎯 Breakout Score",
                weight: weights.weight_breakout,
                color: "bg-green-500",
                points: [
                  `Above 20-day high = 100pts`,
                  `Within ${weights.breakout_pct}% of high = 50–100pts`,
                  `Below zone = 0–30pts`,
                ],
                note: "Proximity to breakout levels indicates momentum."
              },
            ].map(({ title, weight, color, points, note }) => (
              <div key={title} className="rounded-lg border border-border p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <p className="text-sm font-semibold">{title}</p>
                  <Badge variant="outline">{weight}% weight</Badge>
                </div>
                <div className="h-1.5 bg-muted rounded-full">
                  <div className={`h-full rounded-full ${color}`} style={{ width: `${weight}%` }} />
                </div>
                <ul className="space-y-1">
                  {points.map(p => (
                    <li key={p} className="text-xs text-muted-foreground flex gap-1.5">
                      <span className="text-foreground/40">·</span>{p}
                    </li>
                  ))}
                </ul>
                <p className="text-xs text-muted-foreground italic">{note}</p>
              </div>
            ))}
          </div>

          <div className="rounded-md bg-muted/40 px-4 py-3 text-sm space-y-1">
            <p><strong>Final Score</strong> = (Trend × {weights.weight_trend}%) + (Volume × {weights.weight_volume}%) + (Breakout × {weights.weight_breakout}%)</p>
            <p className="text-muted-foreground text-xs">Confidence: <strong>HIGH</strong> ≥ {weights.confidence_high} · <strong>MEDIUM</strong> ≥ {weights.confidence_medium} · <strong>LOW</strong> below that</p>
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Weight Editor */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-base">Tune Weights</CardTitle>
                <CardDescription>Adjust how much each component matters</CardDescription>
              </div>
              {weightSum !== 100 && (
                <Badge variant="outline" className="border-red-500/30 text-red-400">
                  Weights sum to {weightSum} (need 100)
                </Badge>
              )}
            </div>
          </CardHeader>
          <CardContent className="space-y-0">
            <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-2">Component Weights (must sum to 100)</p>
            <WeightRow label="Trend Weight (%)" desc="Importance of MA alignment" field="weight_trend" value={weights.weight_trend} onChange={v => update("weight_trend", v)} />
            <WeightRow label="Volume Weight (%)" desc="Importance of volume expansion" field="weight_volume" value={weights.weight_volume} onChange={v => update("weight_volume", v)} />
            <WeightRow label="Breakout Weight (%)" desc="Importance of breakout proximity" field="weight_breakout" value={weights.weight_breakout} onChange={v => update("weight_breakout", v)} />

            <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide mt-4 mb-2">Trend Sub-scores</p>
            <WeightRow label="Price above MA20" desc="Points awarded" field="trend_above_ma20" value={weights.trend_above_ma20} onChange={v => update("trend_above_ma20", v)} />
            <WeightRow label="Price above MA50" desc="Points awarded" field="trend_above_ma50" value={weights.trend_above_ma50} onChange={v => update("trend_above_ma50", v)} />
            <WeightRow label="MA20 > MA50" desc="Points awarded" field="trend_ma20_above_ma50" value={weights.trend_ma20_above_ma50} onChange={v => update("trend_ma20_above_ma50", v)} />
            <WeightRow label="MA50 > MA200" desc="Points awarded" field="trend_ma50_above_ma200" value={weights.trend_ma50_above_ma200} onChange={v => update("trend_ma50_above_ma200", v)} />

            <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide mt-4 mb-2">Volume & Breakout</p>
            <WeightRow label="Volume baseline (x)" desc="This rel-vol = 50pts" field="volume_base_rv" value={weights.volume_base_rv} onChange={v => update("volume_base_rv", v)} min={0.1} max={5} step={0.1} />
            <WeightRow label="Breakout zone (%)" desc="% from high = in zone" field="breakout_pct" value={weights.breakout_pct} onChange={v => update("breakout_pct", v)} min={0.5} max={20} step={0.5} />

            <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide mt-4 mb-2">Confidence Thresholds</p>
            <WeightRow label="HIGH confidence (≥)" desc="Minimum score for HIGH" field="confidence_high" value={weights.confidence_high} onChange={v => update("confidence_high", v)} />
            <WeightRow label="MEDIUM confidence (≥)" desc="Minimum score for MEDIUM" field="confidence_medium" value={weights.confidence_medium} onChange={v => update("confidence_medium", v)} />
          </CardContent>
        </Card>

        {/* Live Preview */}
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Live Score Preview</CardTitle>
              <CardDescription>Adjust inputs to see how a stock would score</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-3">
                {([
                  ["Close Price", "close", 0.01],
                  ["MA20", "ma20", 0.01],
                  ["MA50", "ma50", 0.01],
                  ["MA200", "ma200", 0.01],
                  ["Rel. Volume (x)", "relVol", 0.1],
                  ["% from 20d High", "pctFromHigh20", 0.001],
                ] as [string, keyof PreviewInputs, number][]).map(([label, key, step]) => (
                  <div key={key} className="space-y-1">
                    <label className="text-xs text-muted-foreground">{label}</label>
                    <Input type="number" step={step} value={preview[key]}
                      onChange={e => updatePreview(key, parseFloat(e.target.value) || 0)}
                      className="h-8 text-sm tabular-nums" />
                  </div>
                ))}
              </div>

              <Separator />

              <div className="space-y-3">
                <ScoreBar label="Trend Score" value={score.trend} color="bg-blue-500" />
                <ScoreBar label="Volume Score" value={score.volume} color="bg-purple-500" />
                <ScoreBar label="Breakout Score" value={score.breakout} color="bg-green-500" />
              </div>

              <Separator />

              <div className="flex items-center justify-between">
                <div>
                  <p className="text-3xl font-bold tabular-nums">{score.total}<span className="text-lg text-muted-foreground font-normal">/100</span></p>
                  <p className="text-xs text-muted-foreground mt-0.5">Final Score</p>
                </div>
                <ConfidenceBadge level={score.confidence} />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-4 space-y-3">
              <div className="flex gap-2">
                <Button onClick={handleSave} size="sm" disabled={weightSum !== 100} className="flex-1">
                  {weightSum !== 100 ? `Weights must sum to 100 (${weightSum})` : "Save Weights"}
                </Button>
                <Button onClick={handleReset} size="sm" variant="outline">Reset</Button>
              </div>
              <p className="text-xs text-muted-foreground">
                Saved weights are used for the score preview only. Scanner weights are configured in Settings → Scanner Filters.
              </p>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
