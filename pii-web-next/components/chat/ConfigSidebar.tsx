import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { SectionHeader } from "@/components/shared/SectionHeader";
import { MetricCard } from "@/components/shared/MetricCard";
import {FieldSelect } from "@/components/shared/FieldSelect";
import { DEMO_PROMPTS_BY_LANGUAGE } from "@/lib/constants";
import type { PipelineForm } from "@/lib/types";

interface ConfigSidebarProps {
  form: PipelineForm;
  onChange: (key: keyof PipelineForm, value: string) => void;
  continuity: { total: number; repeated: number };
  loading: boolean;
  setDraft: (text: string) => void;
}

export function ConfigSidebar({ form, onChange, continuity, loading, setDraft }: ConfigSidebarProps) {
  return (
    <aside className="border-r bg-muted/30 p-5 flex flex-col gap-6 overflow-y-auto max-h-[780px]">
      <section>
        <SectionHeader>Execution settings</SectionHeader>
        <div className="grid grid-cols-2 gap-3">
          <FieldSelect
            label="Profile"
            value={form.profile}
            onValueChange={(v) => onChange("profile", v)}
            options={[
              { value: "generic", label: "Generic" },
              { value: "healthcare", label: "Healthcare" },
              { value: "finance", label: "Finance" },
              { value: "legal", label: "Legal" },
            ]}
          />
          <FieldSelect
            label="Detection engine"
            value={form.detector_backend}
            onValueChange={(v) => onChange("detector_backend", v)}
            options={[
              { value: "regex", label: "Regex" },
              { value: "presidio", label: "Presidio" },
              { value: "opf", label: "OpenAI Privacy Filter" },
              { value: "gliner", label: "GLiNER PII" },
              { value: "nemotron", label: "Nemotron Privacy Filter" },
              { value: "transformers", label: "Transformers" },
              { value: "hybrid", label: "Hybrid" },
            ]}
          />
          <FieldSelect
            label="Language"
            value={form.language}
            onValueChange={(v) => onChange("language", v)}
            options={[
              { value: "auto", label: "Auto-detect" },
              { value: "es", label: "Español" },
              { value: "en", label: "English" },
              { value: "fr", label: "Français" },
              { value: "de", label: "Deutsch" },
              { value: "it", label: "Italiano" },
              { value: "pt", label: "Português" },
            ]}
          />
        </div>
      </section>

      <Separator />

      <section>
        <SectionHeader>Context metrics</SectionHeader>
        <div className="grid grid-cols-2 gap-2">
          <MetricCard label="Total tokens" value={continuity.total} sub="entities detected" />
          <MetricCard label="Reused tokens" value={continuity.repeated} sub="across turns" />
        </div>
      </section>

      <Separator />

      <section>
        <SectionHeader>Test scenarios</SectionHeader>
        <div className="grid grid-cols-4 gap-1.5">
          {(DEMO_PROMPTS_BY_LANGUAGE[form.language] || DEMO_PROMPTS_BY_LANGUAGE.es).map((prompt, idx) => (
            <Button
              key={prompt}
              variant="outline"
              size="sm"
              disabled={loading}
              onClick={() => setDraft(prompt)}
              title={prompt}
              className="h-8 text-xs font-semibold"
            >
              #{idx + 1}
            </Button>
          ))}
        </div>
      </section>
    </aside>
  );
}
