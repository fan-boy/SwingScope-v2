"use client";

import { useEffect, useState } from "react";
import {
  ComposedChart,
  Bar,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import type { ChartCandle, ChartMetrics, ChartResponse } from "@/lib/api";

interface StockChartProps {
  symbol: string;
  ideaEntry?: number;
  ideaStop?: number;
}

// ── Helpers ──────────────────────────────────────────────────

function fmt(v: number) {
  return `$${v.toFixed(2)}`;
}

function toBarValue(c: ChartCandle) {
  return c.close >= c.open ? [c.open, c.close] : [c.close, c.open];
}

function CandleBar(props: any) {
  const { x, y, width, height, payload } = props;
  if (!payload) return null;
  const isBullish = payload.close >= payload.open;
  const fill = isBullish ? "#22c55e" : "#ef4444";
  const wickX = x + width / 2;
  return (
    <g>
      <line x1={wickX} y1={props.background?.y ?? y} x2={wickX} y2={y} stroke={fill} strokeWidth={1} />
      <rect x={x + 1} y={y} width={Math.max(width - 2, 2)} height={Math.abs(height)} fill={fill} />
      <line
        x1={wickX}
        y1={y + Math.abs(height)}
        x2={wickX}
        y2={(props.background?.y ?? y) + (props.background?.height ?? 0)}
        stroke={fill}
        strokeWidth={1}
      />
    </g>
  );
}

function MetricCard({
  label,
  value,
  sub,
  color,
}: {
  label: string;
  value: string;
  sub?: string;
  color?: string;
}) {
  return (
    <div className="rounded-lg bg-muted/50 px-4 py-3 text-center">
      <p className="text-xs text-muted-foreground mb-1">{label}</p>
      <p className={`text-lg font-bold tabular-nums ${color ?? "text-foreground"}`}>{value}</p>
      {sub && <p className="text-xs text-muted-foreground mt-0.5">{sub}</p>}
    </div>
  );
}

const CustomTooltip = ({ active, payload }: any) => {
  if (!active || !payload?.length) return null;
  const d = payload[0]?.payload as ChartCandle;
  if (!d) return null;
  return (
    <div className="rounded-lg border border-border bg-card p-3 text-xs shadow-lg space-y-1 min-w-[160px]">
      <p className="font-semibold text-foreground mb-2">{d.date}</p>
      <p>O: <span className="text-foreground font-medium">{fmt(d.open)}</span></p>
      <p>H: <span className="text-green-400 font-medium">{fmt(d.high)}</span></p>
      <p>L: <span className="text-red-400 font-medium">{fmt(d.low)}</span></p>
      <p>C: <span className="text-foreground font-medium">{fmt(d.close)}</span></p>
      <p className="text-muted-foreground">Vol: {(d.volume / 1_000_000).toFixed(2)}M</p>
      {d.ma20 != null && <p className="text-blue-400">MA20: {fmt(d.ma20)}</p>}
      {d.ma50 != null && <p className="text-yellow-400">MA50: {fmt(d.ma50)}</p>}
      {d.ma200 != null && <p className="text-purple-400">MA200: {fmt(d.ma200)}</p>}
    </div>
  );
};

// ── Component ────────────────────────────────────────────────

export function StockChart({ symbol, ideaEntry, ideaStop }: StockChartProps) {
  const [data, setData] = useState<ChartResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    fetch(`/api/chart/${symbol}`)
      .then((r) => (r.ok ? r.json() : Promise.reject("No data")))
      .then(setData)
      .catch(() => setError("Could not load chart data"))
      .finally(() => setLoading(false));
  }, [symbol]);

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <Skeleton className="h-5 w-40" />
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="grid grid-cols-4 gap-3">
            {[...Array(4)].map((_, i) => (
              <Skeleton key={i} className="h-16 rounded-lg" />
            ))}
          </div>
          <Skeleton className="h-72 w-full" />
          <Skeleton className="h-16 w-full" />
        </CardContent>
      </Card>
    );
  }

  if (error || !data) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center h-32">
          <p className="text-sm text-muted-foreground">{error ?? "No chart data"}</p>
        </CardContent>
      </Card>
    );
  }

  const { candles, metrics } = data;

  const prices = candles.flatMap((c) => [c.low, c.high]);
  const minPrice = Math.min(...prices) * 0.998;
  const maxPrice = Math.max(...prices) * 1.002;

  const tickIndexes = new Set(
    candles
      .map((_, i) => i)
      .filter((i) => i % 10 === 0 || i === candles.length - 1),
  );

  const relVolColor =
    metrics.rel_vol >= 2
      ? "text-green-400"
      : metrics.rel_vol >= 1
        ? "text-foreground"
        : "text-muted-foreground";

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base">{symbol} — 60-Day Chart</CardTitle>
          <span className="text-xs text-muted-foreground">Daily OHLCV · MA overlays</span>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Metrics strip */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <MetricCard
            label="Rel. Volume"
            value={`${metrics.rel_vol}×`}
            sub="vs 20-day avg"
            color={relVolColor}
          />
          <MetricCard
            label="ATR (14)"
            value={metrics.atr14 != null ? fmt(metrics.atr14) : "—"}
            sub="avg true range"
          />
          <MetricCard
            label="Stop Distance"
            value={metrics.stop_distance != null ? fmt(metrics.stop_distance) : "—"}
            sub="1.5× ATR estimate"
            color="text-red-400"
          />
          <MetricCard
            label="Breakout Level"
            value={fmt(metrics.breakout_level)}
            sub="20-day high"
            color="text-green-400"
          />
        </div>

        {/* Price chart */}
        <ResponsiveContainer width="100%" height={280}>
          <ComposedChart data={candles} margin={{ top: 4, right: 8, bottom: 0, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
            <XAxis
              dataKey="date"
              tick={{ fontSize: 10, fill: "#888" }}
              tickLine={false}
              axisLine={false}
              tickFormatter={(v, i) => (tickIndexes.has(i) ? v.slice(5) : "")}
              interval={0}
            />
            <YAxis
              domain={[minPrice, maxPrice]}
              tick={{ fontSize: 10, fill: "#888" }}
              tickLine={false}
              axisLine={false}
              tickFormatter={(v) => `$${v.toFixed(0)}`}
              width={48}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend
              wrapperStyle={{ fontSize: 11 }}
              formatter={(v) =>
                v === "close"
                  ? "Price"
                  : v === "ma20"
                    ? "MA20"
                    : v === "ma50"
                      ? "MA50"
                      : v === "ma200"
                        ? "MA200"
                        : v
              }
            />

            {/* Candle bodies as range bars */}
            <Bar
              dataKey={(c: ChartCandle) => toBarValue(c)}
              name="close"
              shape={<CandleBar />}
              isAnimationActive={false}
            />

            {/* MA overlays */}
            <Line
              dataKey="ma20"
              name="ma20"
              stroke="#3b82f6"
              strokeWidth={1.5}
              dot={false}
              connectNulls
              isAnimationActive={false}
            />
            <Line
              dataKey="ma50"
              name="ma50"
              stroke="#eab308"
              strokeWidth={1.5}
              dot={false}
              connectNulls
              isAnimationActive={false}
            />
            <Line
              dataKey="ma200"
              name="ma200"
              stroke="#a855f7"
              strokeWidth={1.5}
              dot={false}
              connectNulls
              isAnimationActive={false}
            />

            {/* Breakout level reference */}
            <ReferenceLine
              y={metrics.breakout_level}
              stroke="#22c55e"
              strokeDasharray="4 4"
              strokeWidth={1}
              label={{ value: "Breakout", fill: "#22c55e", fontSize: 10, position: "insideTopRight" }}
            />

            {/* Entry/stop from trade idea */}
            {ideaEntry && (
              <ReferenceLine
                y={ideaEntry}
                stroke="#60a5fa"
                strokeDasharray="4 4"
                strokeWidth={1}
                label={{ value: "Entry", fill: "#60a5fa", fontSize: 10, position: "insideTopRight" }}
              />
            )}
            {ideaStop && (
              <ReferenceLine
                y={ideaStop}
                stroke="#f87171"
                strokeDasharray="4 4"
                strokeWidth={1}
                label={{ value: "Stop", fill: "#f87171", fontSize: 10, position: "insideBottomRight" }}
              />
            )}
          </ComposedChart>
        </ResponsiveContainer>

        {/* Volume chart */}
        <ResponsiveContainer width="100%" height={70}>
          <ComposedChart data={candles} margin={{ top: 0, right: 8, bottom: 0, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
            <XAxis dataKey="date" hide />
            <YAxis
              tick={{ fontSize: 9, fill: "#888" }}
              tickLine={false}
              axisLine={false}
              tickFormatter={(v) => `${(v / 1_000_000).toFixed(0)}M`}
              width={48}
            />
            <Bar dataKey="volume" name="Volume" fill="#6366f1" opacity={0.6} isAnimationActive={false} />
          </ComposedChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
