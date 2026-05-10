# Security Policy

## Supported versions

| Version | Supported |
|---|---|
| 0.1.x | ✅ Yes |

---

## Reporting a vulnerability

**Please do not file public GitHub issues for security vulnerabilities.**

To report a security issue, email **security@neretj.dev** with:

1. A description of the vulnerability
2. Steps to reproduce (proof of concept if possible)
3. Potential impact (data exposure, bypass of PII detection, etc.)
4. Any suggested mitigations

You will receive an acknowledgement within **48 hours** and a full response within **7 days**.

If the issue is confirmed, we will:
- Release a patch as soon as possible
- Credit you in the release notes (unless you prefer anonymity)

---

## Threat model

PII Firewall is a **defense-in-depth layer**, not a security boundary. It aims to reduce the probability of sensitive data reaching third-party LLM providers, but should not be the sole control for highly regulated data.

**In scope:**
- Incomplete PII detection (false negatives) for supported entity types
- Vault data exposure (e.g., unauthorized access to token→original mappings)
- Injection attacks that bypass the anonymization pipeline
- GDPR data leakage through the `forget()` mechanism not working correctly

**Out of scope:**
- PII in languages or formats not covered by any supported backend (these are known limitations, not vulnerabilities)
- Privacy of audit logs stored by the caller's infrastructure
- Vulnerabilities in upstream dependencies (report those to the respective project)

---

## Security design notes

- The in-memory vault (`InMemoryMappingVault`) stores mappings only in process memory; nothing is written to disk unless `SQLiteMappingVault` is explicitly chosen.
- Tenant isolation is enforced at the data layer: the same token in different `tenant_id` namespaces never shares a mapping.
- No data is sent to any external service by default; all processing is local.
- The `forget()` method irreversibly removes all vault mappings for the given scope, satisfying GDPR Art. 17.
