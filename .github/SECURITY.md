# Security Policy

## Supported Versions

| Project | Supported |
| ------- | --------- |
| OCRBridge packages | Latest minor release |
| OCR service 2.x.x | Yes |
| OCR service < 2.0 | No |

## Reporting a Vulnerability

If you discover a security vulnerability, report it responsibly:

1. Do not open a public GitHub issue for security vulnerabilities.
2. Email the maintainers with details of the vulnerability.
3. Include steps to reproduce the issue.
4. Allow reasonable time for the issue to be addressed before public disclosure.

## Service Deployment Notes

- Enable API key authentication in production with `API_KEY_ENABLED=true`.
- Store API keys in environment variables, never in code.
- Configure Redis for shared multi-worker rate limiting with `RATE_LIMIT_STORAGE_URI`.
- Run behind a reverse proxy with HTTPS/TLS termination.
- Restrict CORS origins to known domains.
- Use specific container image tags instead of `latest`.
