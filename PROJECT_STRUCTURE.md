# 📁 SampleMind AI v6 - Project Structure Guide

## 🚀 Quick Navigation

### 📖 **Documentation & Getting Started**
- `README.md` - **START HERE** - Main project overview and features
- `INSTALLATION_GUIDE.md` - Complete installation instructions
- `USER_GUIDE.md` - Comprehensive usage guide
- `MODERN_DEV_SETUP.md` - AI-enhanced development environment setup

### ⚡ **Quick Setup Scripts**
- `scripts/setup-modern-dev.sh` - Full development environment setup
- `scripts/setup-samplemind-ai-dev.sh` - Basic Python project setup
- `scripts/quick-start.sh` - Quick project startup
- `scripts/performance-optimize.sh` - System performance optimization
- `scripts/quick-performance-fix.sh` - Quick performance fixes

### 🔧 **Configuration**
- `pyproject.toml` - Poetry dependencies and project configuration
- `docker-compose.yml` - Docker services orchestration
- `Dockerfile` - Container build configuration
- `Makefile` - Common development tasks

### 💻 **Core Application**
- `src/samplemind/` - Main application source code
  - `ai/` - AI models and processing (local, cloud, hybrid)
  - `core/` - Core engine, database, security
  - `interfaces/` - CLI, API, GUI interfaces
  - `integrations/` - DAW plugins and external services

### 🌐 **Frontend Applications**
- `frontend/web/` - Web application
- `frontend/electron/` - Desktop application

### 🧪 **Testing**
- `tests/unit/` - Unit tests
- `tests/integration/` - Integration tests
- `tests/e2e/` - End-to-end tests
- `tests/performance/` - Performance tests

### 🚀 **Deployment**
- `deployment/docker/` - Docker configurations
- `deployment/kubernetes/` - Kubernetes manifests
- `deployment/terraform/` - Infrastructure as code

### 📊 **Monitoring & Observability**
- `monitoring/grafana/` - Grafana dashboards and configuration
- `monitoring/alerts/` - Alert configurations

### 📚 **Extended Documentation**
- `docs/api/` - API documentation
- `docs/developer_guide/` - Developer guides
- `docs/assets/` - Documentation assets (images, examples)

### 🗂️ **Data Storage**
- `data/dev/` - Development data and cache
- `data/prod/` - Production data structures
- `data/test/` - Testing data

### 🛠️ **Development Tools**
- `tools/` - Development utilities and scripts
- `config/` - Application configuration files
- `.vscode/` - VS Code settings
- `.github/` - GitHub workflows and templates

## 🎯 Common Tasks

### First Time Setup
1. Read `README.md` for project overview
2. Follow `INSTALLATION_GUIDE.md` for setup
3. Run `scripts/setup-modern-dev.sh` for full dev environment

### Daily Development
1. Activate environment: `source .venv/bin/activate`
2. Start services: `docker-compose up -d`
3. Run application: `make dev` or `poetry run samplemind`

### Documentation
- User documentation: `USER_GUIDE.md`
- API reference: `docs/api/README.md`
- Development guide: `docs/developer_guide/README.md`

---

**💡 Tip**: This project structure follows modern Python standards with Poetry, Docker, and comprehensive testing. All documentation is organized by purpose for easy navigation.