import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function WatchlistPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Watchlist</h1>
        <p className="text-muted-foreground text-sm mt-1">Tickers you're tracking</p>
      </div>
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Your Tickers</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground text-sm">No tickers added yet.</p>
        </CardContent>
      </Card>
    </div>
  );
}
