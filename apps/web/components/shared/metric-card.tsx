import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import type { LucideIcon } from "lucide-react";

interface MetricCardProps {
  title: string;
  value?: string | number;
  sub?: string;
  icon?: LucideIcon;
  trend?: "up" | "down" | "neutral";
  loading?: boolean;
  className?: string;
}

export function MetricCard({ title, value, sub, icon: Icon, trend, loading, className }: MetricCardProps) {
  const trendColor = {
    up: "text-green-400",
    down: "text-red-400",
    neutral: "text-muted-foreground",
  }[trend ?? "neutral"];

  return (
    <Card className={cn("bg-card", className)}>
      <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
        <CardTitle className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
          {title}
        </CardTitle>
        {Icon && <Icon className="w-4 h-4 text-muted-foreground" />}
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="space-y-2">
            <Skeleton className="h-7 w-20" />
            <Skeleton className="h-3 w-28" />
          </div>
        ) : (
          <>
            <p className={cn("text-2xl font-bold tracking-tight", trendColor)}>
              {value ?? "—"}
            </p>
            {sub && (
              <p className="text-xs text-muted-foreground mt-1">{sub}</p>
            )}
          </>
        )}
      </CardContent>
    </Card>
  );
}
