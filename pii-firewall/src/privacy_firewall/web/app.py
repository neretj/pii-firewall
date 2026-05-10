"""FastAPI backend for Privacy Firewall API.

This module provides REST API endpoints for the Privacy Firewall.
Frontend is served separately by pii-web-next (Next.js app).
"""

from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Dict

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from ..llm import MockLLMClient
from ..vault import InMemoryMappingVault
from ..firewall import PrivacyFirewall, create_firewall


class RunRequest(BaseModel):
    """Request model for /api/run endpoint."""
    text: str = Field(min_length=1)
    tenant_id: str = "tenant-demo"
    case_id: str = "case-demo"
    thread_id: str = "thread-1"
    actor_id: str = "user-demo"
    profile: str = "generic"  # generic, healthcare, finance, legal
    language: str | None = None  # auto-detect if None
    detector_backend: str = "regex"  # regex, presidio, opf, gliner, nemotron, transformers, hybrid
    token_scope: str | None = None  # thread, case, tenant
    mapping_override: dict[str, str] | None = None  # optional external mapping for rehydration


@dataclass(frozen=True)
class RuntimeKey:
    """Cache key for firewall instances."""
    profile: str
    detector_backend: str
    language: str | None
    token_scope: str | None


class RuntimeFactory:
    """Factory for creating and caching PrivacyFirewall instances."""
    
    def __init__(self) -> None:
        self._runtimes: Dict[RuntimeKey, PrivacyFirewall] = {}
        self._shared_vault = InMemoryMappingVault()

    def get(self, req: RunRequest) -> PrivacyFirewall:
        """Get or create a firewall instance for the request."""
        key = RuntimeKey(
            profile=req.profile,
            detector_backend=req.detector_backend,
            language=req.language,
            token_scope=req.token_scope,
        )
        
        if key in self._runtimes:
            return self._runtimes[key]

        fw = create_firewall(
            domain=req.profile,
            language=req.language,
            detector_backend=req.detector_backend,
            token_scope=req.token_scope,
            vault=self._shared_vault,
            llm_client=MockLLMClient(prefix="[MOCK_LLM]"),
        )
        
        self._runtimes[key] = fw
        return fw


def create_app(firewall: PrivacyFirewall | None = None) -> FastAPI:
    """Create FastAPI app with Privacy Firewall API endpoints.
    
    Args:
        firewall: Optional pre-configured firewall instance (for testing)
        
    Returns:
        FastAPI application instance
    """
    runtime_factory = RuntimeFactory()
    static_fw = firewall
    required_api_key = os.getenv("PII_FIREWALL_API_KEY")

    def validate_api_key(x_api_key: str | None) -> None:
        if required_api_key and x_api_key != required_api_key:
            raise HTTPException(status_code=401, detail="Unauthorized")

    app = FastAPI(
        title="Privacy Firewall API",
        version="2.0.0",
        description="Domain-aware multi-language anonymization API",
    )

    @app.get("/")
    def root() -> dict:
        """Root endpoint with API discovery hints."""
        return {
            "service": "pii-firewall-api",
            "status": "ok",
            "version": "2.0.0",
            "routes": {
                "health": "/health",
                "runtime_options": "/api/runtime-options",
                "run": "/api/run",
                "forget": "/api/forget",
                "docs": "/docs",
            },
        }
    
    # Enable CORS for Next.js frontend
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://localhost:3010"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    def health() -> dict:
        """Health check endpoint."""
        return {"status": "ok", "version": "2.0.0"}

    @app.get("/api/runtime-options")
    def runtime_options() -> dict:
        """Get available runtime configuration options."""
        return {
            "profile": ["generic", "healthcare", "finance", "legal"],
            "detector_backend": ["regex", "presidio", "opf", "gliner", "nemotron", "transformers", "hybrid"],
            "language": ["auto", "en", "es", "fr", "de", "it", "pt"],
            "token_scope": ["profile-default", "thread", "case", "tenant"],
            "profile_descriptions": {
                "generic": "General-purpose PII protection with safe defaults",
                "healthcare": "Keeps medical data (diagnoses, medications), redacts PII",
                "finance": "Keeps transaction amounts and financial data, redacts medical info",
                "legal": "Keeps case references and legal data with stricter entity matching"
            },
            "backend_descriptions": {
                "regex": "Locale pattern matching only (fastest, deterministic)",
                "presidio": "Fast spaCy-based NER (recommended for production)",
                "opf": "OpenAI Privacy Filter token classifier (local runtime)",
                "gliner": "Knowledgator GLiNER PII model (zero-shot labels, local runtime)",
                "nemotron": "OpenMed privacy-filter-nemotron via OPF checkpoint (55 fine-grained labels)",
                "transformers": "Domain-specific models (BioBERT, FinBERT) - slower but more accurate",
                "hybrid": "Combines both (best accuracy, slowest)"
            },
        }

    @app.post("/api/run")
    def run_pipeline(req: RunRequest, x_api_key: str | None = Header(default=None)) -> dict:
        """Run the privacy firewall pipeline on input text."""
        validate_api_key(x_api_key)
        try:
            fw = static_fw or runtime_factory.get(req)
            context = {
                "tenant_id": req.tenant_id,
                "case_id": req.case_id,
                "thread_id": req.thread_id,
                "actor_id": req.actor_id,
            }
            result = fw.secure_call(
                text=req.text,
                context=context,
                mapping=req.mapping_override,
            )
            mapping = fw.vault.get_case_mapping(req.tenant_id, req.case_id, req.thread_id)
        except HTTPException:
            raise
        except ImportError as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=500, detail="Internal processing error") from exc

        return {
            "input": {
                "text": req.text,
                "context": context,
                "config": {
                    "profile": req.profile,
                    "language": req.language or "auto-detect",
                    "detector_backend": req.detector_backend,
                    "token_scope": req.token_scope or "profile-default",
                },
            },
            "steps": {
                "detected_language": getattr(result.trace, 'language', None),
                "detected_entities": result.trace.detected_entities,
                "entities_kept": getattr(result.trace, 'entities_kept', []),
                "sanitized_text": result.sanitized_text,
                "blocked": result.trace.blocked,
                "block_reason": result.trace.block_reason,
                "llm_request": result.sanitized_text if not result.trace.blocked else None,
                "llm_response": result.model_output if not result.trace.blocked else None,
                "rehydrated_output": result.final_text if not result.trace.blocked else None,
                "mapping": mapping,
                "cleanup_warnings": result.trace.cleanup_warnings,
            },
            "trace": {
                "trace_id": result.trace.trace_id,
                "profile": result.trace.policy_mode,
                "total_replacements": len(result.trace.replacements),
            },
        }

    @app.post("/api/forget")
    def forget(req: RunRequest, x_api_key: str | None = Header(default=None)) -> dict:
        """GDPR right to be forgotten - delete all mappings for a case."""
        validate_api_key(x_api_key)
        try:
            fw = static_fw or runtime_factory.get(req)
            removed = fw.forget(
                tenant_id=req.tenant_id,
                case_id=req.case_id,
                thread_id=req.thread_id
            )
            return {"removed": removed}
        except HTTPException:
            raise
        except ImportError as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=500, detail="Internal processing error") from exc

    return app


