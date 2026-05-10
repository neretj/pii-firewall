# gliner Audit Results

- Generated: 2026-04-28T21:55:33.876887+00:00
- Backend: gliner
- Profile: generic

## Summary

| Language | Queries | HTTP Failures | Unavailable Failures | Structured Expected | Structured Fully Sanitized |
|---|---:|---:|---:|---:|---:|
| es | 10 | 0 | 0 | 6 | 6 |
| en | 10 | 0 | 0 | 6 | 6 |
| fr | 10 | 0 | 0 | 6 | 4 |
| de | 10 | 0 | 0 | 7 | 7 |
| it | 10 | 0 | 0 | 4 | 4 |
| pt | 10 | 0 | 0 | 6 | 3 |

## Detailed Findings

### es

HTTP failures: none
Structured PII sanitization gaps: none detected

### en

HTTP failures: none
Structured PII sanitization gaps: none detected

### fr

HTTP failures: none
Structured PII still present after sanitize:
- idx 1: ['2850312345678']
- idx 9: ['1850312345678']

### de

HTTP failures: none
Structured PII sanitization gaps: none detected

### it

HTTP failures: none
Structured PII sanitization gaps: none detected

### pt

HTTP failures: none
Structured PII still present after sanitize:
- idx 1: ['123.456.789-00']
- idx 6: ['12345-6 78901-2']
- idx 9: ['987.654.321-00']
