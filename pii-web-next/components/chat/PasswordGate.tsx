"use client";

import { useState, useCallback } from "react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { RefreshCw, Lock, Eye, EyeOff, AlertTriangle } from "lucide-react";
import { sha256 } from "@/lib/utils/auth";
import { SESSION_KEY, CORRECT_HASH } from "@/lib/constants";

export function PasswordGate({ onUnlock }: { onUnlock: () => void }) {
  const [pwd, setPwd] = useState("");
  const [show, setShow] = useState(false);
  const [error, setError] = useState("");
  const [checking, setChecking] = useState(false);

  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      setChecking(true);
      setError("");
      const hash = await sha256(pwd);
      if (hash === CORRECT_HASH) {
        sessionStorage.setItem(SESSION_KEY, "1");
        onUnlock();
      } else {
        setError("Incorrect password. Please try again.");
        setPwd("");
      }
      setChecking(false);
    },
    [pwd, onUnlock],
  );

  return (
    <div className="min-h-screen bg-muted/40 flex items-center justify-center p-4">
      <div className="w-full max-w-sm">
        <div className="rounded-2xl border bg-card shadow-lg overflow-hidden">
          <div className="bg-primary px-8 py-8 text-center">
            <div className="w-14 h-14 rounded-2xl bg-white/10 border border-white/20 flex items-center justify-center mx-auto mb-4">
              <Lock className="w-6 h-6 text-white" />
            </div>
            <h1 className="text-white font-bold text-lg tracking-tight">PII Firewall</h1>
            <p className="text-white/70 text-sm mt-1">Enter password to continue</p>
          </div>
          <form onSubmit={handleSubmit} className="px-8 py-7 space-y-5">
            <div className="space-y-2">
              <label className="text-xs font-semibold text-muted-fg block">Password</label>
              <div className="relative">
                <input
                  type={show ? "text" : "password"}
                  value={pwd}
                  onChange={(e) => { setPwd(e.target.value); setError(""); }}
                  placeholder="••••••••••••••••"
                  autoFocus
                  autoComplete="current-password"
                  className={cn(
                    "w-full h-10 rounded-md border bg-background px-3 pr-10 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-ring transition-colors",
                    error ? "border-destructive focus:ring-destructive/30" : "border-input",
                  )}
                />
                <button
                  type="button"
                  onClick={() => setShow((s) => !s)}
                  className="absolute right-2.5 top-1/2 -translate-y-1/2 text-muted-fg hover:text-foreground transition-colors"
                  tabIndex={-1}
                >
                  {show ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
              {error && (
                <p className="text-xs text-destructive flex items-center gap-1.5">
                  <AlertTriangle className="w-3.5 h-3.5 flex-shrink-0" />
                  {error}
                </p>
              )}
            </div>
            <Button type="submit" className="w-full" disabled={!pwd || checking}>
              {checking ? (
                <><RefreshCw className="w-4 h-4 animate-spin" /> Verifying…</>
              ) : (
                <><Lock className="w-4 h-4" /> Access</>
              )}
            </Button>
          </form>
        </div>
        <p className="text-center text-xs text-muted-fg mt-4">
          Restricted Access · PII Firewall Lab
        </p>
      </div>
    </div>
  );
}
