export type PipelineProfile = "generic" | "healthcare" | "finance" | "legal";

export type DetectorBackend =
  | "regex"
  | "presidio"
  | "opf"
  | "gliner"
  | "nemotron"
  | "transformers"
  | "hybrid";

export type PipelineLanguage = "auto" | "es" | "en" | "fr" | "de" | "it" | "pt";

export type PipelineBaseFields = {
  text: string;
  tenant_id: string;
  case_id: string;
  thread_id: string;
  actor_id: string;
};

export type PipelineForm = PipelineBaseFields & {
  profile: PipelineProfile;
  detector_backend: DetectorBackend;
  language: PipelineLanguage;
};

export type PipelineConfig = {
  profile: PipelineProfile;
  detector_backend: DetectorBackend;
  language: Exclude<PipelineLanguage, "auto"> | "auto-detect";
};

export type PipelineRequest = PipelineBaseFields & {
  profile: PipelineProfile;
  detector_backend: DetectorBackend;
  language: Exclude<PipelineLanguage, "auto"> | null;
};

export type DetectedEntity = {
  entity_type: string;
  text: string;
  confidence: number;
  source: string;
};

export type PipelineRunResponse = {
  input: {
    text: string;
    context: {
      tenant_id: string;
      case_id: string;
      thread_id: string;
      actor_id: string;
    };
    config: PipelineConfig;
  };
  steps: {
    detected_entities: DetectedEntity[];
    sanitized_text: string;
    blocked: boolean;
    block_reason: string | null;
    llm_request: string | null;
    llm_response: string | null;
    rehydrated_output: string | null;
    mapping: Record<string, string>;
  };
  trace: {
    trace_id: string;
    profile: string;
    k_anonymity_score: number;
    total_replacements: number;
  };
};
