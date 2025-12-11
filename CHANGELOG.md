# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-12-11

### Added
- Multi-layered OSINT pipeline with polyglot architecture (Go, Python, Node.js)
- FastAPI backend with asynchronous data gathering orchestration
- Go-based API gateway with per-IP rate limiting
- Node.js CLI interface for user-friendly report generation
- Redis integration for caching and user-agent pooling
- Multiple OSINT sources:
  - Deep Search (web search integration)
  - Domain Checker (domain analysis)
  - Search Engine (search engine integration)
  - Social Media (social media footprint detection)
  - Vulnerability Database (vulnerability scanning)
- Pydantic model-based data normalization
- Docker and Docker Compose support for containerized deployment
- Comprehensive error handling and graceful degradation
- Test suite with pytest and coverage reporting

### Features
- Parallel data collection from multiple sources
- Normalized output with DigitalFootprintReport model
- Rate limiting and timeout management
- Environment-based configuration (API keys, Redis URL)
- Comprehensive logging

---

## Initial Release

This is the first stable release of OSINT-CLI, a production-oriented proof-of-concept OSINT pipeline demonstrating polyglot microservice architecture for digital footprint analysis.
