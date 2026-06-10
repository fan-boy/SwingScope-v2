import { Separator } from "@/components/ui/separator";
import { AlertSettingsForm } from "@/components/settings/alert-settings-form";
import { AlertHistory } from "@/components/settings/alert-history";
import { api } from "@/lib/api";

async function getAlertSettings() {
  try {
    const res = await fetch(
      `${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/api/alerts/settings`,
      { next: { revalidate: 0 } }
    );
    if (!res.ok) return null;
    return res.json();
  } catch { return null; }
}

async function getAlertHistory() {
  try {
    const res = await fetch(
      `${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/api/alerts/history?limit=10`,
      { next: { revalidate: 0 } }
    );
    if (!res.ok) return [];
    return res.json();
  } catch { return []; }
}

export default async function SettingsPage() {
  const [alertSettings, history] = await Promise.all([
    getAlertSettings(),
    getAlertHistory(),
  ]);

  return (
    <div className="space-y-8 max-w-2xl">
      <div>
        <h1 className="text-xl font-semibold">Settings</h1>
        <p className="text-sm text-muted-foreground mt-0.5">Manage alerts and scan schedule</p>
      </div>

      <Separator />

      <section className="space-y-4">
        <div>
          <h2 className="text-base font-semibold">Email Alerts</h2>
          <p className="text-sm text-muted-foreground mt-0.5">
            Get a daily summary after each scan. Configure SMTP in your server <code className="text-xs bg-muted px-1 py-0.5 rounded">.env</code>.
          </p>
        </div>
        <AlertSettingsForm initialSettings={alertSettings} />
      </section>

      <Separator />

      <section className="space-y-4">
        <div>
          <h2 className="text-base font-semibold">Alert History</h2>
          <p className="text-sm text-muted-foreground mt-0.5">Recent email delivery log</p>
        </div>
        <AlertHistory logs={history} />
      </section>
    </div>
  );
}
