/**
 * Thin API client for the FastAPI backend.
 * Used in server components — no auth headers yet (add later).
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    next: { revalidate: 60 }, // ISR — revalidate every 60s
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`API ${res.status}: ${text}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  watchlists: {
    list: () => apiFetch<WatchlistResponse[]>("/api/watchlists/"),
    get: (id: string) => apiFetch<WatchlistResponse>(`/api/watchlists/${id}`),
    addItem: (id: string, body: { symbol: string; notes?: string; priority?: boolean }) =>
      apiFetch<WatchlistItemResponse>(`/api/watchlists/${id}/items`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
        next: { revalidate: 0 },
      }),
    removeItem: (id: string, itemId: string) =>
      fetch(`${API_BASE}/api/watchlists/${id}/items/${itemId}`, { method: "DELETE" }),
    updateItem: (id: string, itemId: string, body: { notes?: string; priority?: boolean }) =>
      apiFetch<WatchlistItemResponse>(`/api/watchlists/${id}/items/${itemId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
        next: { revalidate: 0 },
      }),
  },
  scans: {
    latest: () => apiFetch<ScanRunResponse>("/api/scans/latest"),
    get: (id: string) => apiFetch<ScanRunResponse>(`/api/scans/${id}`),
    list: () => apiFetch<ScanRunResponse[]>("/api/scans/"),
    run: (body?: RunScanRequest) =>
      apiFetch<ScanRunResponse>("/api/scans/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: body ? JSON.stringify(body) : undefined,
        next: { revalidate: 0 },
      }),
  },
};

// ── Response types (mirror FastAPI schemas) ───────────────────────────────

export interface CandidateResponse {
  id: string;
  symbol: string;
  score: number;
  confidence: "HIGH" | "MEDIUM" | "LOW";
  entry: number;
  stop: number;
  target1: number;
  rr_ratio: number;
  direction: string;
  technical_score: number;
  technical_setup: string | null;
  status: string;
  run_date: string;
}

export interface ScanRunResponse {
  id: string;
  run_date: string;
  status: string;
  market_regime: string | null;
  tickers_scanned: number;
  candidates_found: number;
  duration_ms: number | null;
  is_mocked: boolean;
  created_at: string;
  candidates: CandidateResponse[];
}

// ── Watchlist types ───────────────────────────────────────────────────────

export interface WatchlistItemResponse {
  id: string;
  symbol: string;
  notes: string | null;
  priority: boolean;
  scan_score: number | null;
  scan_confidence: "HIGH" | "MEDIUM" | "LOW" | null;
  scan_status: string | null;
}

export interface WatchlistResponse {
  id: string;
  name: string;
  description: string | null;
  is_default: boolean;
  items: WatchlistItemResponse[];
}

export interface RunScanRequest {
  config?: Record<string, unknown>;
  universe?: string[];
}
