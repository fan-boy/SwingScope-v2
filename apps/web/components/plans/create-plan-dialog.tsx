"use client";

import { useState, useTransition } from "react";
import { useRouter } from "next/navigation";
import { Plus, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { CandidateResponse } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogClose } from "@/components/ui/dialog";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

interface Props {
  open: boolean;
  onClose: () => void;
  prefill?: Partial<CandidateResponse>;
}

export function CreatePlanDialog({ open, onClose, prefill }: Props) {
  const router = useRouter();
  const [isPending, start] = useTransition();
  const [form, setForm] = useState({
    symbol: prefill?.symbol ?? "",
    entry: prefill?.entry?.toFixed(2) ?? "",
    stop: prefill?.stop?.toFixed(2) ?? "",
    target1: prefill?.target1?.toFixed(2) ?? "",
    target2: "",
    quantity: "",
    risk_amount: "",
    notes: "",
  });
  const [errors, setErrors] = useState<Record<string, string>>({});

  function field(name: keyof typeof form) {
    return {
      value: form[name],
      onChange: (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
        setForm(f => ({ ...f, [name]: e.target.value }));
        setErrors(e2 => { const n = { ...e2 }; delete n[name]; return n; });
      },
    };
  }

  function validate(): boolean {
    const e: Record<string, string> = {};
    if (!form.symbol.trim()) e.symbol = "Required";
    if (!form.entry || isNaN(+form.entry) || +form.entry <= 0) e.entry = "Must be > 0";
    if (!form.stop || isNaN(+form.stop) || +form.stop <= 0) e.stop = "Must be > 0";
    if (!form.target1 || isNaN(+form.target1) || +form.target1 <= 0) e.target1 = "Must be > 0";
    if (form.quantity && (isNaN(+form.quantity) || +form.quantity <= 0)) e.quantity = "Must be > 0";
    if (form.risk_amount && (isNaN(+form.risk_amount) || +form.risk_amount <= 0)) e.risk_amount = "Must be > 0";
    setErrors(e);
    return Object.keys(e).length === 0;
  }

  function rr() {
    const e = +form.entry, s = +form.stop, t = +form.target1;
    if (!e || !s || !t) return null;
    const risk = Math.abs(e - s), reward = Math.abs(t - e);
    if (!risk) return null;
    return (reward / risk).toFixed(2);
  }

  async function handleSubmit(ev: React.FormEvent) {
    ev.preventDefault();
    if (!validate()) return;
    start(async () => {
      try {
        const res = await fetch(`${API_BASE}/api/trade-plans/`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            symbol: form.symbol.toUpperCase().trim(),
            direction: "LONG",
            entry: +form.entry, stop: +form.stop, target1: +form.target1,
            target2: form.target2 ? +form.target2 : undefined,
            quantity: form.quantity ? +form.quantity : undefined,
            risk_amount: form.risk_amount ? +form.risk_amount : undefined,
            notes: form.notes || undefined,
            candidate_id: prefill?.id ?? undefined,
          }),
        });
        if (!res.ok) { const d = await res.json().catch(() => ({})); throw new Error(d.detail ?? "Failed"); }
        toast.success(`Trade plan created for ${form.symbol.toUpperCase()}`);
        onClose();
        router.refresh();
      } catch (e: any) { toast.error(e.message); }
    });
  }

  const rrVal = rr();

  return (
    <Dialog open={open} onOpenChange={v => { if (!v) onClose(); }}>
      <DialogContent className="max-w-md max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Create Trade Plan</DialogTitle>
          <DialogDescription>Plan starts as a draft. You'll approve it before execution.</DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4 mt-2">
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <label className="text-sm font-medium">Symbol</label>
              <Input placeholder="AAPL" className={errors.symbol ? "border-destructive" : ""} {...field("symbol")} />
              {errors.symbol && <p className="text-xs text-destructive">{errors.symbol}</p>}
            </div>
            <div className="space-y-1.5">
              <label className="text-sm font-medium">Direction</label>
              <Input value="LONG" disabled className="opacity-60" />
            </div>
          </div>

          <div className="grid grid-cols-3 gap-3">
            {(["entry", "stop", "target1"] as const).map(k => (
              <div key={k} className="space-y-1.5">
                <label className="text-sm font-medium capitalize">{k === "target1" ? "Target" : k}</label>
                <Input type="number" step="0.01" placeholder="0.00"
                  className={errors[k] ? "border-destructive" : ""} {...field(k)} />
                {errors[k] && <p className="text-xs text-destructive">{errors[k]}</p>}
              </div>
            ))}
          </div>

          {rrVal && (
            <p className="text-sm text-muted-foreground">
              R/R ratio: <span className={+rrVal >= 2 ? "text-green-400 font-semibold" : "text-yellow-400"}>{rrVal}:1</span>
            </p>
          )}

          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <label className="text-sm font-medium">Shares <span className="text-xs text-muted-foreground">(optional)</span></label>
              <Input type="number" step="1" placeholder="100" {...field("quantity")} />
              {errors.quantity && <p className="text-xs text-destructive">{errors.quantity}</p>}
            </div>
            <div className="space-y-1.5">
              <label className="text-sm font-medium">Max risk $ <span className="text-xs text-muted-foreground">(optional)</span></label>
              <Input type="number" step="1" placeholder="500" {...field("risk_amount")} />
              {errors.risk_amount && <p className="text-xs text-destructive">{errors.risk_amount}</p>}
            </div>
          </div>

          <div className="space-y-1.5">
            <label className="text-sm font-medium">Notes <span className="text-xs text-muted-foreground">(optional)</span></label>
            <Textarea placeholder="Thesis, setup notes, invalidation conditions..." rows={3} {...field("notes")} />
          </div>

          <div className="flex gap-2 pt-1">
            <Button type="submit" className="flex-1" disabled={isPending}>
              {isPending && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
              Create Plan
            </Button>
            <DialogClose asChild>
              <Button type="button" variant="outline" className="flex-1">Cancel</Button>
            </DialogClose>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
