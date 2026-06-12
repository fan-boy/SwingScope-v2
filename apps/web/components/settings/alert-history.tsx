import { CheckCircle, XCircle, AlertTriangle, Info } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { EmptyState } from "@/components/shared/empty-state";

interface LogEntry {
  id: string;
  level: string;
  event: string;
  message: string;
  meta: Record<string, unknown> | null;
  created_at: string;
}

function LevelIcon({ level }: { level: string }) {
  if (level === "ERROR") return <XCircle className="w-4 h-4 text-red-400 shrink-0" />;
  if (level === "WARN") return <AlertTriangle className="w-4 h-4 text-yellow-400 shrink-0" />;
  return <CheckCircle className="w-4 h-4 text-green-400 shrink-0" />;
}

function eventLabel(event: string) {
  return {
    "alert.sent": "Email sent",
    "alert.failed": "Send failed",
    "alert.skipped": "Skipped",
    "alert.not_configured": "Not configured",
  }[event] ?? event;
}

export function AlertHistory({ logs }: { logs: LogEntry[] }) {
  if (!logs.length) {
    return (
      <Card>
        <CardContent className="p-0">
          <EmptyState
            icon={Info}
            title="No alert history yet"
            description="History will appear after the first scan runs."
          />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardContent className="p-0 divide-y divide-border">
        {logs.map((log) => (
          <div key={log.id} className="flex items-start gap-3 px-4 py-3">
            <LevelIcon level={log.level} />
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium">{eventLabel(log.event)}</span>
                {log.meta?.candidates != null && (
                  <span className="text-xs text-muted-foreground">
                    {String(log.meta.candidates as string | number)} candidates
                  </span>
                )}
              </div>
              <p className="text-xs text-muted-foreground mt-0.5 truncate">{log.message}</p>
            </div>
            <span className="text-xs text-muted-foreground shrink-0 mt-0.5">
              {new Date(log.created_at).toLocaleString([], {
                month: "short", day: "numeric",
                hour: "2-digit", minute: "2-digit",
              })}
            </span>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
