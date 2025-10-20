# 📦 Installation Guide - SampleMind AI v6

## Quick Start

### One-Line Installation (Recommended)

```bash
# macOS/Linux - Install everything automatically
curl -fsSL https://install.samplemind.ai | bash

# Windows (PowerShell)
iwr -useb https://install.samplemind.ai/windows.ps1 | iex
```

### Manual Installation

```bash
# 1. Install Python dependencies
pip install samplemind-ai[complete]

# 2. Install and start Ollama
curl -fsSL https://ollama.ai/install.sh | sh
ollama serve &

# 3. Download AI models
samplemind setup --install-models

# 4. Verify installation
samplemind doctor
```

## System Requirements

### Minimum Requirements

| Component | Requirement |
|-----------|-------------|
| **OS** | macOS 12+, Ubuntu 20.04+, Windows 11 |
| **Python** | 3.11+ |
| **RAM** | 8GB (16GB recommended) |
| **Storage** | 20GB free space |
| **Internet** | Required for cloud AI and updates |

### Recommended Specifications

| Component | Recommendation |
|-----------|----------------|
| **CPU** | Apple M1/M2, Intel i7/i9, AMD Ryzen 7+ |
| **RAM** | 32GB+ for large libraries |
| **Storage** | SSD with 100GB+ free space |
| **GPU** | Apple Silicon, NVIDIA RTX (optional) |

## Installation Methods

### Method 1: From Source

```bash
# Clone repository
git clone https://github.com/samplemind/samplemind-ai-v6.git
cd samplemind-ai-v6

# Install Poetry (dependency manager)
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies
poetry install

# Install AI models
poetry run samplemind setup --install-models

# Run SampleMind AI
poetry run samplemind
```

### Method 2: Docker Container

```bash
# Pull and run SampleMind AI
docker run -d \
  --name samplemind \
  -p 8000:8000 \
  -v samplemind_data:/data \
  samplemind/samplemind-ai:latest

# Or use Docker Compose
docker-compose up -d
```

## AI Models Setup

### Automatic Model Installation

```bash
# Install recommended model set
samplemind setup --install-models

# Install specific model sets
samplemind setup --models fast      # Fast models only
samplemind setup --models complete  # All models
samplemind setup --models minimal   # Minimal set
```

### Manual Model Installation

```bash
# Start Ollama service
ollama serve &

# Install ultra-fast models (2-4GB total)
ollama pull phi3:mini        # 2.2GB - Ultra-fast classification
ollama pull gemma2:2b        # 1.6GB - Quick analysis

# Install intelligent models (8-12GB total)
ollama pull qwen2.5:7b-instruct  # 4.4GB - Complex analysis
ollama pull llama3.1:8b          # 4.7GB - Creative tasks

# Verify installations
ollama list
samplemind ai test
```

## Platform-Specific Instructions

### macOS Installation

```bash
# Install Homebrew
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install dependencies
brew install python@3.11 portaudio ffmpeg

# Install SampleMind AI
pip3 install samplemind-ai[complete]
```

### Ubuntu/Linux Installation

```bash
# Install dependencies
sudo apt update
sudo apt install -y python3.11 python3.11-pip build-essential \
    libasound2-dev libportaudio2 portaudio19-dev ffmpeg

# Install SampleMind AI
pip3 install samplemind-ai[complete]
```

### Windows Installation

```powershell
# Install dependencies via Chocolatey
choco install python nodejs git

# Install SampleMind AI
pip install samplemind-ai[complete]
```

## Verification & Testing

### Installation Verification

```bash
# Check installation
samplemind --version
samplemind doctor

# Expected output:
# SampleMind AI v6.0.0
# ✅ Python 3.11.5
# ✅ Audio libraries installed
# ✅ Ollama service running
# ✅ AI models available
# ✅ Configuration valid
```

### System Health Check

```bash
# Comprehensive system check
samplemind doctor --full

# Test audio processing
samplemind test audio

# Test AI models
samplemind ai test --comprehensive
```

## Configuration

### Environment Configuration

```bash
# Create configuration directory
mkdir -p ~/.samplemind

# Basic configuration file
samplemind config init

# Interactive configuration
samplemind config setup --interactive
```

### Configuration File

```yaml
# ~/.samplemind/config.yaml
application:
  environment: production
  log_level: INFO
  data_directory: ~/.samplemind/data
  cache_directory: ~/.samplemind/cache

audio:
  sample_rate: 44100
  supported_formats: [wav, mp3, aiff, flac]
  max_file_size: 100MB
  processing_quality: high

ai:
  default_model: auto
  local_models_path: ~/.samplemind/models
  enable_cloud_fallback: true
  max_analysis_time: 30s

api:
  host: localhost
  port: 8000
  cors_enabled: true
  rate_limiting: true

database:
  mongodb_url: mongodb://localhost:27017/samplemind
  redis_url: redis://localhost:6379/0
  vector_db_path: ~/.samplemind/chromadb
```

## Troubleshooting

### Common Issues

#### Audio Libraries Missing

```bash
# macOS
brew install portaudio

# Ubuntu
sudo apt install libasound2-dev portaudio19-dev

# Windows
# Install Visual C++ Build Tools
```

#### Ollama Connection Issues

```bash
# Check if Ollama is running
ps aux | grep ollama

# Start Ollama service
ollama serve &

# Test connection
curl http://localhost:11434/api/tags
```

#### Model Download Failures

```bash
# Check disk space
df -h

# Manual model download
ollama pull phi3:mini --verbose

# Clear model cache if corrupted
ollama rm phi3:mini
ollama pull phi3:mini
```

## Next Steps

After successful installation:

1. Read the [User Guide](USER_GUIDE.md) for usage instructions
2. Check the [API Documentation](API_DOCUMENTATION.md) for integration
3. Join the [Discord Community](https://discord.gg/samplemind) for support

**Need Help?**
- 📧 Email: support@samplemind.ai
- 💬 Discord: [SampleMind Community](https://discord.gg/samplemind)
- 🐛 Issues: [GitHub Issues](https://github.com/samplemind/samplemind-ai-v6/issues)
