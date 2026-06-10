"use client";

import { useState } from "react";
import { Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { AddTickerDialog } from "@/components/watchlist/add-ticker-dialog";

interface Props {
  watchlistId: string;
}

export function WatchlistActions({ watchlistId }: Props) {
  const [open, setOpen] = useState(false);

  return (
    <>
      <Button size="sm" onClick={() => setOpen(true)} className="gap-2">
        <Plus className="w-4 h-4" />
        Add Ticker
      </Button>
      <AddTickerDialog
        watchlistId={watchlistId}
        open={open}
        onClose={() => setOpen(false)}
      />
    </>
  );
}
