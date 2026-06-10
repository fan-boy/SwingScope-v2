"use client";

import { useState, useTransition } from "react";
import { useRouter } from "next/navigation";
import { Send, Loader2, CheckCircle, XCircle, AlertTriangle } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

interface AlertSettings {
  email_enabled: boolean;
  email_to: string;
  smtp_configured: boolean;
  scheduler_enabled: boolean;
  scan_cron_schedule: string;
}

interface Props {
  initialSettings: AlertSettings | null;
}

export function AlertSettingsForm({ initialSettings }: Props) {
  const router = useRouter();
  const [settings, setSettings] = useState<AlertSettings>(
    initialSettings ?? {
      email_enabled: false,
      email_to: "",
      smtp_configured: false,
      scheduler_enabled: false,
      scan_cron_schedule: "30 23 * * 1-5",
    }
  );
  const [isSaving, startSaving] = useTransition();
  const [isResending, startResend] = useTransition();

  async function handleSave() {
    startSaving(async () => {
      try {
        const res = await fetch(`${API_BASE}/api/alerts/settings`, {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            email_enabled: settings.email_enabled,
            email_to: settings.email_to,
            scan_cron_schedule: settings.scan_cron_schedule,
          }),
        });
        if (!res.ok) throw new Error(await res.text());
        toast.success("Settings saved");
        router.refresh();
      } catch (e: any) {
        toast.error(`Failed to save: ${e.message}`);
      }
    });
  }

  async function handleResend() {
    startResend(async () => {
      try {
        const res = await fetch(`${API_BASE}/api/alerts/resend`, { method: "POST" });
        const data = await res.json();
        if (data.sent) {
          toast.success(`Summary sent to ${data.to} (${data.candidates} candidates)`);
        } else if (data.reason === "smtp_not_configured") {
          toast.warning("SMTP not configured — set env vars on the server");
        } else if (data.reason === "no_completed_scans") {
          toast.warning("No completed scans found — run a scan first");
        } else {
          toast.info(`Not sent: ${data.reason}`);
        }
        router.refresh();
      } catch {
        toast.error("Failed to resend");
      }
    });
  }

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-medium">Email Configuration</CardTitle>
          <div className="flex items-center gap-2">
            {settings.smtp_configured
              ? <Badge variant="outline" className="text-[10px] border-green-500/30 text-green-400 bg-green-500/10 gap-1"><CheckCircle className="w-3 h-3" />SMTP ready</Badge>
              : <Badge variant="outline" className="text-[10px] border-yellow-500/30 text-yellow-400 bg-yellow-500/10 gap-1"><AlertTriangle className="w-3 h-3" />SMTP not configured</Badge>
            }
          </div>
        </div>
      </CardHeader>
      <Separator />
      <CardContent className="pt-4 space-y-5">
        {/* Enable toggle */}
        <label className="flex items-center justify-between cursor-pointer">
          <div>
            <p className="text-sm font-medium">Enable email alerts</p>
            <p className="text-xs text-muted-foreground mt-0.5">Send a summary after each scan</p>
          </div>
          <button
            role="switch"
            aria-checked={settings.email_enabled}
            onClick={() => setSettings(s => ({ ...s, email_enabled: !s.email_enabled }))}
            className={`relative inline-flex h-5 w-9 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring ${settings.email_enabled ? "bg-primary" : "bg-muted"}`}
          >
            <span className={`pointer-events-none inline-block h-4 w-4 rounded-full bg-white shadow-lg ring-0 transition-transform ${settings.email_enabled ? "translate-x-4" : "translate-x-0"}`} />
          </button>
        </label>

        {/* Recipient */}
        <div className="space-y-1.5">
          <label className="text-sm font-medium" htmlFor="email_to">Recipient email</label>
          <Input
            id="email_to"
            type="email"
            placeholder="you@example.com"
            value={settings.email_to}
            onChange={e => setSettings(s => ({ ...s, email_to: e.target.value }))}
            disabled={!settings.email_enabled}
          />
        </div>

        {/* Cron */}
        <div className="space-y-1.5">
          <label className="text-sm font-medium" htmlFor="cron">Scan schedule <span className="text-xs font-normal text-muted-foreground">(cron, UTC)</span></label>
          <Input
            id="cron"
            placeholder="30 23 * * 1-5"
            value={settings.scan_cron_schedule}
            onChange={e => setSettings(s => ({ ...s, scan_cron_schedule: e.target.value }))}
          />
          <p className="text-xs text-muted-foreground">
            Default: <code className="bg-muted px-1 rounded">30 23 * * 1-5</code> = 11:30 PM UTC Mon–Fri (≈6:30 PM ET)
          </p>
        </div>

        <Separator />

        {/* Actions */}
        <div className="flex gap-2 flex-wrap">
          <Button onClick={handleSave} disabled={isSaving} className="gap-2">
            {isSaving && <Loader2 className="w-4 h-4 animate-spin" />}
            Save settings
          </Button>
          <Button
            variant="outline"
            onClick={handleResend}
            disabled={isResending}
            className="gap-2"
          >
            {isResending
              ? <Loader2 className="w-4 h-4 animate-spin" />
              : <Send className="w-4 h-4" />
            }
            Resend last summary
          </Button>
        </div>

        {!settings.smtp_configured && (
          <p className="text-xs text-muted-foreground bg-muted/50 rounded-md p-3">
            Add <code>SMTP_HOST</code>, <code>SMTP_USERNAME</code>, <code>SMTP_PASSWORD</code>, and <code>ALERT_EMAIL_TO</code> to your server <code>.env</code> to enable email delivery.
          </p>
        )}
      </CardContent>
    </Card>
  );
}
