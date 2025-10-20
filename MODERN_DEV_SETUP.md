# 🚀 AI-First Modern Dev Setup (SampleMind AI v6)

## 1. Prerequisites

### Homebrew (Universal Package Manager)
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

---

## 2. Terminal & Shell: AI-Enhanced Stack

### Install All Core Tools (One Command)
```bash
brew install starship zoxide fzf ripgrep bat eza atuin fig ollama aider lazygit lazydocker k9s dive ctop glow fx httpie curlie trivy syft grype gitleaks semgrep osv-scanner checkov btop bandwhich dust duf gping hyperfine
brew install --cask cursor
```
- **Optional:** For GPU-accelerated/AI terminals:  
  `brew install --cask warp`  
  `brew install ghostty`

---

## 3. Modern Zsh & Shell Configuration

### Oh My Zsh, Powerlevel10k, Plugins
```bash
sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" "" --unattended
git clone --depth=1 https://github.com/romkatv/powerlevel10k.git ${ZSH_CUSTOM:-$HOME/.oh-my-zsh/custom}/themes/powerlevel10k
for repo in \
  zsh-users/zsh-autosuggestions \
  zsh-users/zsh-syntax-highlighting \
  zdharma-continuum/fast-syntax-highlighting \
  marlonrichert/zsh-autocomplete; do
  git clone https://github.com/$repo ${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/$(basename $repo)
done
```

### Recommended `.zshrc` (idempotent, high-performance)
```bash
export ZSH="$HOME/.oh-my-zsh"
ZSH_THEME="powerlevel10k/powerlevel10k"
plugins=(git zsh-autosuggestions zsh-syntax-highlighting fast-syntax-highlighting zsh-autocomplete docker python poetry npm node)
source $ZSH/oh-my-zsh.sh

eval "$(starship init zsh 2>/dev/null || true)"
eval "$(zoxide init zsh)"
eval "$(atuin init zsh)"
eval "$(fig init zsh 2>/dev/null || true)"

# AI/Dev Aliases
alias smai='cd ~/Projects/samplemind-ai.v6/samplemind-ai-v6'
alias ai='aider --model gpt-4o'
alias chat='ollama run qwen2.5:7b-instruct'
alias code='cursor'
alias lg='lazygit'
alias ld='lazydocker'
alias ls='eza --icons --git'
alias ll='eza -l --icons --git'
alias la='eza -la --icons --git'
alias cat='bat'
alias cd='z'
alias grep='rg'
alias find='fd'
alias top='btop'
alias du='dust'
alias df='duf'
alias ping='gping'

# AI Environment
export OPENAI_API_KEY=$(cat ~/.config/openai/key 2>/dev/null)
export ANTHROPIC_API_KEY=$(cat ~/.config/anthropic/key 2>/dev/null)
export OLLAMA_HOST=http://localhost:11434

# Dev Environment
export EDITOR="cursor"
export BROWSER="open"
export PYTHONDONTWRITEBYTECODE=1
export PYTHONUNBUFFERED=1
export POETRY_VENV_IN_PROJECT=1
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1
export PATH="$HOME/bin:/usr/local/bin:$PATH"
```

---

## 4. AI-First Development Environment

### Cursor IDE (AI-Native)
```bash
brew install --cask cursor
cursor --install-extension continue.continue github.copilot ms-python.python charliermarsh.ruff ms-python.black-formatter bradlc.vscode-tailwindcss ms-toolsai.jupyter ms-python.isort tabnine.tabnine-vscode codeium.codeium
```

### AI Coding Assistants
```bash
pip install --upgrade aider-chat
npm install -g @githubnext/github-copilot-cli
```

---

## 5. Python: Fast, Modern, Reproducible

```bash
# UV (Rust-based pip, 10x faster)
curl -LsSf https://astral.sh/uv/install.sh | sh
# Rye (modern Python project mgmt)
curl -sSf https://rye-up.com/get | bash
# PDM (modern dependency mgmt)
curl -sSL https://raw.githubusercontent.com/pdm-project/pdm/main/install-pdm.py | python3 -
```

---

## 6. AI Model Management

```bash
brew services start ollama
ollama pull phi3.5:3.8b-mini-instruct-q4_K_M
ollama pull qwen2.5-coder:7b-instruct-q4_K_M
ollama pull deepseek-coder-v2:16b-lite-instruct
ollama pull llama3.1:8b-instruct-q4_K_M
ollama pull codellama:7b-code-q4_K_M
ollama pull nomic-embed-text
ollama pull mxbai-embed-large
ollama pull wizard-vicuna:13b-uncensored
ollama pull dolphin-mixtral:8x7b
```

---

## 7. Project Setup (SampleMind AI)

```bash
cd ~/Projects/samplemind-ai.v6/samplemind-ai-v6
uv venv .venv --python 3.12
source .venv/bin/activate
uv pip install poetry
poetry install
```

---

## 8. AI-Enhanced Git & DevOps

```bash
npm install -g aicommits @commitlint/cli @commitlint/config-conventional
aicommits config set OPENAI_API_KEY=$(cat ~/.config/openai/key)
pip install git-sim
```

---

## 9. Security & Performance

```bash
pip install bandit safety pip-audit py-spy memray scalene line_profiler
```

---

## 10. Smart Functions & Health

Add to `~/.zshrc` or `~/.zsh_functions`:
```bash
ai_analyze() { aider --model gpt-4o --message "Analyze this audio file: $1 and suggest optimizations"; }
ai_debug() { ollama run qwen2.5-coder:7b "Debug this error: $(cat $1)"; }
ai_optimize() { aider --model claude-3-sonnet --message "Optimize this code for performance: $1"; }
ai_test() { aider --model gpt-4o --message "Generate comprehensive tests for: $1"; }
smai_health() {
  echo "🤖 SampleMind AI Health Check"
  docker ps --format "table {{.Names}}\t{{.Status}}"
  ollama ps
  echo "Memory: $(free -h 2>/dev/null | awk '/^Mem:/ {print $3 "/" $2}' || echo 'N/A')"
  command -v nvidia-smi >/dev/null 2>&1 && echo "GPU: $(nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader,nounits)%"
}
```

---

## 11. Verification & Health Check

```bash
ollama --version && echo "✅ Ollama ready"
aider --version && echo "✅ Aider ready"
cursor --version && echo "✅ Cursor ready"
cd ~/Projects/samplemind-ai.v6/samplemind-ai-v6
source .venv/bin/activate
python -c "import torch; print(f'PyTorch: {torch.__version__}')"
python -c "import transformers; print(f'Transformers: {transformers.__version__}')"
hyperfine 'python -c \"import samplemind; print(\\"Ready\\")\"'
ollama run phi3.5 "Hello, can you help with Python coding?"
```

---

**This setup is designed for maximum speed, automation, and future extensibility. All steps are safe to re-run and will not duplicate installations or configs.**