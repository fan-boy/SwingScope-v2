import { Plus, Star } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { EmptyState } from "@/components/shared/empty-state";
import { WatchlistTable } from "@/components/watchlist/watchlist-table";
import { WatchlistActions } from "@/components/watchlist/watchlist-actions";
import { api, WatchlistResponse } from "@/lib/api";

async function getWatchlists(): Promise<WatchlistResponse[]> {
  try {
    return await api.watchlists.list();
  } catch {
    return [];
  }
}

export default async function WatchlistPage() {
  const watchlists = await getWatchlists();
  const primary = watchlists.find((w) => w.is_default) ?? watchlists[0] ?? null;

  const priorityCount = primary?.items.filter((i) => i.priority).length ?? 0;
  const scannedCount = primary?.items.filter((i) => i.scan_score != null).length ?? 0;

  return (
    <div className="space-y-6 max-w-5xl">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold">Watchlist</h1>
          <p className="text-sm text-muted-foreground mt-0.5">
            Tickers you're tracking
          </p>
        </div>
        {primary && <WatchlistActions watchlistId={primary.id} />}
      </div>

      {/* Stats row */}
      {primary && (
        <div className="flex items-center gap-4 text-sm text-muted-foreground">
          <span>{primary.items.length} tickers</span>
          <span>·</span>
          <span className="flex items-center gap-1">
            <Star className="w-3.5 h-3.5 text-yellow-400" />
            {priorityCount} priority
          </span>
          <span>·</span>
          <span>{scannedCount} with scan data</span>
        </div>
      )}

      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm font-medium">
              {primary?.name ?? "Watchlist"}
            </CardTitle>
            {primary?.is_default && (
              <Badge variant="outline" className="text-[10px] h-5">Default</Badge>
            )}
          </div>
        </CardHeader>
        <Separator />
        <CardContent className="p-0">
          {!primary || primary.items.length === 0 ? (
            <EmptyState
              icon={Plus}
              title="No tickers yet"
              description='Click "Add Ticker" to start tracking symbols.'
            />
          ) : (
            <WatchlistTable watchlistId={primary.id} items={primary.items} />
          )}
        </CardContent>
      </Card>
    </div>
  );
}
