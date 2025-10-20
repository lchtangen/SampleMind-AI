# Security Policy

## Supported Versions

We release patches for security vulnerabilities. Currently supported versions:

| Version | Supported          |
| ------- | ------------------ |
| 6.0.x   | :white_check_mark: |
| < 6.0   | :x:                |

## Reporting a Vulnerability

We take the security of SampleMind AI seriously. If you believe you have found a security vulnerability, please report it to us as described below.

### Please Do NOT:

- Open a public GitHub issue
- Disclose the vulnerability publicly before it has been addressed

### Please DO:

1. **Email us directly** at: security@samplemind.ai (or lchtangen@gmail.com)
2. **Include the following information:**
   - Type of vulnerability
   - Full paths of source file(s) related to the vulnerability
   - Location of the affected source code (tag/branch/commit or direct URL)
   - Step-by-step instructions to reproduce the issue
   - Proof-of-concept or exploit code (if possible)
   - Impact of the vulnerability, including how an attacker might exploit it

### What to Expect:

- **Acknowledgment**: We will acknowledge receipt of your vulnerability report within 48 hours
- **Communication**: We will keep you informed about the progress of fixing the vulnerability
- **Credit**: We will credit you in the security advisory (unless you prefer to remain anonymous)
- **Timeline**: We aim to patch critical vulnerabilities within 7 days, and moderate vulnerabilities within 30 days

## Security Best Practices for Users

### API Keys & Secrets

- **Never commit API keys** to version control
- Use environment variables or `.env` files (which are gitignored)
- Rotate API keys regularly
- Use separate keys for development and production

### Audio File Processing

- **Validate file types** before processing
- Be cautious when processing audio files from untrusted sources
- SampleMind AI runs locally, but malicious audio files could potentially exploit vulnerabilities in audio processing libraries

### Network Security

- When using cloud AI features, ensure you're on a trusted network
- Consider using a VPN when processing sensitive audio content
- Review which AI models have internet access in your configuration

### Docker Security

- Keep Docker images updated
- Don't run containers as root (our images use non-root users by default)
- Review docker-compose.yml before deploying

## Known Security Considerations

### Local AI Models

- Models are downloaded from Ollama's official registry
- Verify model checksums when possible
- Be aware that AI models can have biases or unexpected behaviors

### File System Access

- SampleMind AI requires read access to your sample directories
- Write access is only needed for cache and database directories
- Review file permissions in production deployments

### Dependencies

- We regularly update dependencies to patch known vulnerabilities
- Run `pip audit` or `safety check` to scan for vulnerable dependencies
- See `requirements.txt` and `pyproject.toml` for full dependency list

## Security Updates

Security updates will be released as patch versions (e.g., 6.0.1, 6.0.2) and announced via:

- GitHub Security Advisories
- Release notes in CHANGELOG.md
- Discord announcements (#security channel)
- Email notifications to registered users (opt-in)

## Compliance

SampleMind AI is designed with privacy in mind:

- **Local-first**: Audio processing happens on your machine
- **No telemetry**: We don't collect usage data by default
- **GDPR-friendly**: No personal data is transmitted to our servers
- **Open source**: Full transparency - audit the code yourself

## Contact

For security concerns, contact:
- **Email**: security@samplemind.ai or lchtangen@gmail.com
- **PGP Key**: Available on request
- **Response time**: Within 48 hours

---

**Thank you for helping keep SampleMind AI and our users safe!** 🔒

