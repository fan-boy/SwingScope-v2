"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { RefreshCw } from "lucide-react";
import { getScannerConfig } from "@/components/settings/scanner-filters-form";

export function TriggerScanButton() {
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  async function handleScan() {
    setLoading(true);
    try {
      const config = getScannerConfig();
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/api/scans/run`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ config }),
        }
      );
      if (!res.ok) throw new Error("Scan failed");
      const data = await res.json();
      toast.success(`Scan complete — ${data.candidates_found ?? 0} candidates found`);
      router.refresh();
    } catch {
      toast.error("Failed to run scan");
    } finally {
      setLoading(false);
    }
  }

  return (
    <Button variant="outline" size="sm" onClick={handleScan} disabled={loading}>
      <RefreshCw className={`w-3.5 h-3.5 mr-1.5 ${loading ? "animate-spin" : ""}`} />
      {loading ? "Scanning…" : "Run Scan"}
    </Button>
  );
}
