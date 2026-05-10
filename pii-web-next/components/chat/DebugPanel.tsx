"use client";

import { useState } from "react";
import { Hash, ChevronDown, ChevronRight } from "lucide-react";

export function DebugPanel({ output }: { output: string }) {
  const [showDebug, setShowDebug] = useState(false);

  return (
    <div className="mt-4 rounded-xl border bg-card shadow-sm overflow-hidden">
      <button
        type="button"
        onClick={() => setShowDebug((p) => !p)}
        className="w-full flex items-center justify-between px-5 py-3.5 text-xs font-semibold text-muted-fg hover:bg-muted/30 transition-colors"
      >
        <span className="flex items-center gap-2">
          <Hash className="w-3.5 h-3.5" />
          Full payload (debug)
        </span>
        {showDebug ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
      </button>
      {showDebug && (
        <pre className="m-0 px-5 py-4 bg-slate-900 text-emerald-300 font-mono text-xs leading-relaxed max-h-[360px] overflow-auto whitespace-pre-wrap break-words border-t border-slate-800">
          {output}
        </pre>
      )}
    </div>
  );
}
