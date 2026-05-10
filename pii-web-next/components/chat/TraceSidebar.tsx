import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { SectionHeader } from "@/components/shared/SectionHeader";
import type { PipelineRunResponse } from "@/lib/types";

type ChatTurn = {
  id: string;
  userText: string;
  response: PipelineRunResponse;
};

interface TraceSidebarProps {
  selectedTurn: ChatTurn | null;
  continuity: {
    rows: Array<{ token: string; original: string; turns: number[] }>;
  };
}

export function TraceSidebar({ selectedTurn, continuity }: TraceSidebarProps) {
  return (
    <aside className="border-l bg-muted/30 p-5 overflow-y-auto max-h-[780px] flex flex-col gap-5">
      <SectionHeader>Selected turn trace</SectionHeader>

      {!selectedTurn ? (
        <p className="text-xs text-muted-fg text-center py-8">
          Select a turn to inspect anonymization details.
        </p>
      ) : (
        <>
          <div className="space-y-1.5">
            {[
              { label: "Trace ID", value: selectedTurn.response.trace.trace_id.slice(0, 8), mono: true },
              {
                label: "Status",
                value: selectedTurn.response.steps.blocked ? "Blocked" : "Allowed",
                ok: !selectedTurn.response.steps.blocked,
              },
            ].map(({ label, value, mono, ok }) => (
              <div key={label} className="flex items-center justify-between rounded-md border bg-card px-3 py-2 text-xs">
                <span className="text-muted-fg font-medium">{label}</span>
                <span
                  className={cn(
                    "font-semibold",
                    mono && "font-mono",
                    ok === false && "text-destructive",
                    ok === true && "text-emerald-600",
                  )}
                >
                  {value}
                </span>
              </div>
            ))}
          </div>

          <Separator />

          <div>
            <p className="panel-label mb-2 text-[10px] font-bold uppercase tracking-widest text-muted-fg">
              Sanitized text
            </p>
            <pre className="rounded-md bg-slate-900 text-emerald-300 text-[11.5px] font-mono p-3 max-h-[110px] overflow-y-auto whitespace-pre-wrap break-words leading-relaxed">
              {selectedTurn.response.steps.sanitized_text}
            </pre>
          </div>

          <Separator />

          <div>
            <p className="text-[10px] font-bold uppercase tracking-widest text-muted-fg mb-2">
              Detected entities
            </p>
            {selectedTurn.response.steps.detected_entities.length === 0 ? (
              <p className="text-xs text-muted-fg text-center py-3">No entities in this turn.</p>
            ) : (
              <div className="space-y-1.5">
                {selectedTurn.response.steps.detected_entities.map((entity: any, idx: number) => (
                  <div key={`${entity.text}-${idx}`} className="flex items-center gap-2 rounded-md border bg-card px-2.5 py-2 text-xs min-w-0">
                    <Badge variant="accent" className="flex-shrink-0 text-[10px]">{entity.entity_type}</Badge>
                    <span className="font-medium truncate flex-1">{entity.text}</span>
                    <span className="text-[10px] text-muted-fg bg-muted px-1.5 py-0.5 rounded flex-shrink-0">
                      {entity.source}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>

          <Separator />

          <div>
            <p className="text-[10px] font-bold uppercase tracking-widest text-muted-fg mb-2">
              Current mapping
            </p>
            {Object.entries(selectedTurn.response.steps.mapping).length === 0 ? (
              <p className="text-xs text-muted-fg text-center py-3">No stored mappings.</p>
            ) : (
              <div className="space-y-1">
                {Object.entries(selectedTurn.response.steps.mapping)
                  .sort(([a], [b]) => a.localeCompare(b))
                  .map(([token, original]) => (
                    <div key={token} className="grid gap-2 rounded-md border bg-card px-2.5 py-2 text-xs min-w-0" style={{ gridTemplateColumns: "110px 1fr" }}>
                      <code className="font-mono text-[11px] text-primary font-semibold truncate">{token}</code>
                      <span className="text-foreground/80 truncate">{original as string}</span>
                    </div>
                  ))}
              </div>
            )}
          </div>

          <Separator />

          <div>
            <p className="text-[10px] font-bold uppercase tracking-widest text-muted-fg mb-2">
              Continuity index
            </p>
            {continuity.rows.length === 0 ? (
              <p className="text-xs text-muted-fg text-center py-3">No data yet.</p>
            ) : (
              <div className="space-y-1">
                {continuity.rows.map((row) => (
                  <div key={`c-${row.token}`} className="grid gap-2 rounded-md border bg-card px-2.5 py-2 text-xs min-w-0 items-center" style={{ gridTemplateColumns: "110px 1fr auto" }}>
                    <code className="font-mono text-[11px] text-primary font-semibold truncate">{row.token}</code>
                    <span className="text-foreground/80 truncate">{row.original}</span>
                    <div className="flex gap-0.5 flex-shrink-0">
                      {row.turns.map((t) => (
                        <span key={t} className="w-4 h-4 rounded-full bg-primary/10 border border-primary/30 text-primary text-[9px] font-bold flex items-center justify-center">
                          {t}
                        </span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </>
      )}
    </aside>
  );
}
