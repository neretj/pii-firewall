import { ShieldCheck } from "lucide-react";

export function AppHeader() {
  return (
    <header className="flex items-start justify-between gap-4 mb-5 px-1">
      <div>
        <h1 className="text-xl font-bold tracking-tight flex items-center gap-2">
          <ShieldCheck className="w-5 h-5 text-primary" />
          PII Firewall · Chat Lab
        </h1>
        <p className="text-sm text-muted-fg mt-1 max-w-xl">
          Simulate multi-turn conversations to verify persistent entity mapping and
          secure context rehydration.
        </p>
      </div>
    </header>
  );
}
