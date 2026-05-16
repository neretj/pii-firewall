"""Global patterns applicable to all locales."""

import re
from ..catalog import EntityPattern
from ... import entity_types as ET


# =============================================================================
# EMAIL
# =============================================================================

GLOBAL_EMAIL = EntityPattern(
    entity_type=ET.EMAIL,
    locale="GLOBAL",
    pattern=re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
    confidence=1.0,
    description="Email addresses (RFC 5322 simplified)",
)


# =============================================================================
# IP ADDRESSES
# =============================================================================

GLOBAL_IP_V4 = EntityPattern(
    entity_type=ET.IP_ADDRESS,
    locale="GLOBAL",
    pattern=re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
    confidence=0.9,
    description="IPv4 addresses",
)

GLOBAL_IP_V6 = EntityPattern(
    entity_type=ET.IP_ADDRESS,
    locale="GLOBAL",
    pattern=re.compile(r"\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b"),
    confidence=0.95,
    description="IPv6 addresses",
)


# =============================================================================
# CREDIT CARD
# =============================================================================

GLOBAL_CREDIT_CARD = EntityPattern(
    entity_type=ET.CREDIT_CARD,
    locale="GLOBAL",
    pattern=re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b"),
    confidence=0.8,
    context_words=("card", "credit", "visa", "mastercard", "amex", "discover"),
    description="Credit card numbers (16 digits, Luhn validation recommended)",
)


# =============================================================================
# URL
# =============================================================================

GLOBAL_URL = EntityPattern(
    entity_type=ET.URL,
    locale="GLOBAL",
    pattern=re.compile(r"\b(?:https?|ftp)://[^\s/$.?#].[^\s]*\b", re.IGNORECASE),
    confidence=0.95,
    description="URLs (HTTP/HTTPS/FTP)",
)


# =============================================================================
# MAC ADDRESS
# =============================================================================

GLOBAL_MAC_ADDRESS = EntityPattern(
    entity_type=ET.MAC_ADDRESS,
    locale="GLOBAL",
    pattern=re.compile(r"\b(?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}\b"),
    confidence=0.9,
    description="MAC addresses",
)


# =============================================================================
# DOI  (Digital Object Identifier)
# Bibliographic reference — must NOT be anonymized in academic/health contexts.
# Format: 10.<registrant>/<suffix>
# Examples: 10.7417/CT.2025.5288  10.1016/j.cell.2024.01.001
# =============================================================================

GLOBAL_DOI = EntityPattern(
    entity_type=ET.DOI,
    locale="GLOBAL",
    pattern=re.compile(
        r"\b10\.\d{4,9}/[^\s\"'<>{}\[\]|\\^`]{1,200}",
        re.IGNORECASE,
    ),
    confidence=0.99,
    context_words=("doi", "doi.org", "https://doi.org"),
    description="DOI — Digital Object Identifier for academic publications",
)


# =============================================================================
# PMID  (PubMed identifier)
# Bibliographic reference — must NOT be anonymized in academic/health contexts.
# Format: pure numeric string of 1–8 digits, typically preceded by 'PMID'
# Examples: PMID: 41267587   PMID 41267587   pmid:41267587
# =============================================================================

GLOBAL_PMID = EntityPattern(
    entity_type=ET.PMID,
    locale="GLOBAL",
    pattern=re.compile(
        r"\bPMID[:\s]+\d{1,8}\b",
        re.IGNORECASE,
    ),
    confidence=0.99,
    context_words=("pmid", "pubmed", "ncbi"),
    description="PMID — PubMed identifier for biomedical literature",
)


# =============================================================================
# EXPORT
# =============================================================================

GLOBAL_PATTERNS = [
    GLOBAL_EMAIL,
    GLOBAL_IP_V4,
    GLOBAL_IP_V6,
    GLOBAL_CREDIT_CARD,
    GLOBAL_URL,
    GLOBAL_MAC_ADDRESS,
    GLOBAL_DOI,
    GLOBAL_PMID,
]
