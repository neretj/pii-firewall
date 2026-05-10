# regex Audit Results

- Generated: 2026-04-28T21:57:06.033378+00:00
- Backend: regex
- Profile: generic

## Summary

| Language | Queries | HTTP Failures | Unavailable Failures | Structured Expected | Structured Fully Sanitized |
|---|---:|---:|---:|---:|---:|
| es | 10 | 0 | 0 | 6 | 6 |
| en | 10 | 0 | 0 | 6 | 6 |
| fr | 10 | 0 | 0 | 6 | 3 |
| de | 10 | 0 | 0 | 7 | 7 |
| it | 10 | 0 | 0 | 4 | 3 |
| pt | 10 | 0 | 0 | 6 | 6 |

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
- idx 7: ['+33612345678']
- idx 9: ['1850312345678']

### de

HTTP failures: none
Structured PII sanitization gaps: none detected

### it

HTTP failures: none
Structured PII still present after sanitize:
- idx 7: ['+393123456789']

### pt

HTTP failures: none
Structured PII sanitization gaps: none detected
