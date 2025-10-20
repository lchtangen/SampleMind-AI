#!/bin/bash

# Modern Development Setup Script for SampleMind AI v6
# This script automates the entire setup process from MODERN_DEV_SETUP.md

set -e  # Exit on any error

echo "🚀 Starting Modern Development Setup for SampleMind AI v6"
echo "========================================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to install Homebrew if not present
install_homebrew() {
    if ! command_exists brew; then
        print_status "Installing Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        eval "$(/usr/local/bin/brew shellenv)"
    else
        print_success "Homebrew already installed"
    fi
}

# Phase 1: Core AI-Enhanced Terminal Stack
install_terminal_tools() {
    print_status "Installing Core AI-Enhanced Terminal Stack..."
    
    # Core tools
    brew install --quiet starship zoxide fzf ripgrep bat eza atuin fig || true
    
    # AI Development Essentials
    brew install --quiet ollama llamafile litellm || true
    
    # Modern DevOps tools
    brew install --quiet lazygit lazydocker k9s dive ctop glow fx httpie curlie || true
    
    print_success "Terminal tools installation completed"
}

# Phase 2: Modern Zsh Setup
setup_zsh() {
    print_status "Setting up Modern Zsh configuration..."
    
    # Install Oh My Zsh if not present
    if [ ! -d "$HOME/.oh-my-zsh" ]; then
        print_status "Installing Oh My Zsh..."
        sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" "" --unattended
    fi
    
    # Install Powerlevel10k theme
    if [ ! -d "${ZSH_CUSTOM:-$HOME/.oh-my-zsh/custom}/themes/powerlevel10k" ]; then
        print_status "Installing Powerlevel10k theme..."
        git clone --depth=1 https://github.com/romkatv/powerlevel10k.git ${ZSH_CUSTOM:-$HOME/.oh-my-zsh/custom}/themes/powerlevel10k
    fi
    
    # Install essential plugins
    local plugins=(
        "zsh-autosuggestions:https://github.com/zsh-users/zsh-autosuggestions"
        "zsh-syntax-highlighting:https://github.com/zsh-users/zsh-syntax-highlighting"
        "fast-syntax-highlighting:https://github.com/zdharma-continuum/fast-syntax-highlighting"
        "zsh-autocomplete:https://github.com/marlonrichert/zsh-autocomplete"
    )
    
    for plugin in "${plugins[@]}"; do
        IFS=':' read -r name url <<< "$plugin"
        local plugin_path="${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/$name"
        if [ ! -d "$plugin_path" ]; then
            print_status "Installing plugin: $name"
            git clone "$url" "$plugin_path"
        fi
    done
    
    print_success "Zsh setup completed"
}

# Phase 3: Update Zsh Configuration
update_zshrc() {
    print_status "Updating .zshrc configuration..."
    
    # Create backup
    cp ~/.zshrc ~/.zshrc.backup.$(date +%Y%m%d_%H%M%S) 2>/dev/null || true
    
    # Create new .zshrc with modern configuration
    cat > ~/.zshrc << 'EOF'
# Enable Powerlevel10k instant prompt
if [[ -r "${XDG_CACHE_HOME:-$HOME/.cache}/p10k-instant-prompt-${(%):-%n}.zsh" ]]; then
  source "${XDG_CACHE_HOME:-$HOME/.cache}/p10k-instant-prompt-${(%):-%n}.zsh"
fi

# Oh My Zsh configuration
export ZSH="$HOME/.oh-my-zsh"
ZSH_THEME="powerlevel10k/powerlevel10k"

# Plugins
plugins=(
  git
  zsh-autosuggestions
  zsh-syntax-highlighting
  fast-syntax-highlighting
  zsh-autocomplete
  docker
  python
  poetry
  npm
  node
)

source $ZSH/oh-my-zsh.sh

# Initialize modern tools
eval "$(starship init zsh 2>/dev/null || true)"
eval "$(zoxide init zsh)"
eval "$(atuin init zsh)"
eval "$(fig init zsh 2>/dev/null || true)"

# AI Development aliases
alias smai='cd ~/Projects/samplemind-ai.v6/samplemind-ai-v6'
alias ai='aider --model gpt-4o 2>/dev/null || echo "aider not installed"'
alias chat='ollama run qwen2.5:7b-instruct 2>/dev/null || echo "ollama not running"'
alias lg='lazygit'
alias ld='lazydocker'

# Modern replacements
alias ls='eza --icons --git 2>/dev/null || ls'
alias ll='eza -l --icons --git 2>/dev/null || ls -l'
alias la='eza -la --icons --git 2>/dev/null || ls -la'
alias cat='bat 2>/dev/null || cat'
alias cd='z'
alias grep='rg 2>/dev/null || grep'
alias find='fd 2>/dev/null || find'
alias top='btop 2>/dev/null || top'
alias du='dust 2>/dev/null || du'
alias df='duf 2>/dev/null || df'
alias ping='gping 2>/dev/null || ping'

# AI Environment
export OPENAI_API_KEY=$(cat ~/.config/openai/key 2>/dev/null || echo "")
export ANTHROPIC_API_KEY=$(cat ~/.config/anthropic/key 2>/dev/null || echo "")
export OLLAMA_HOST=http://localhost:11434

# Development Environment
export EDITOR="cursor 2>/dev/null || code 2>/dev/null || vim"
export BROWSER="open"
export PYTHONDONTWRITEBYTECODE=1
export PYTHONUNBUFFERED=1
export POETRY_VENV_IN_PROJECT=1
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

# Ensure Homebrew tools are in PATH
export PATH="/usr/local/bin:$PATH"

# Docker optimizations for Intel MacBook Pro
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1
export BUILDKIT_PROGRESS=plain
export DOCKER_CLI_EXPERIMENTAL=enabled
export DOCKER_SCAN_SUGGEST=false
export DOCKER_DEFAULT_PLATFORM=linux/amd64

# Load Powerlevel10k configuration
[[ ! -f ~/.p10k.zsh ]] || source ~/.p10k.zsh

# Docker CLI completions
fpath=(/Users/lchtangen/.docker/completions $fpath)
autoload -Uz compinit
compinit
EOF

    print_success ".zshrc updated successfully"
}

# Phase 4: AI Development Tools
install_ai_tools() {
    print_status "Installing AI Development Tools..."
    
    # Install Cursor IDE
    brew install --cask cursor 2>/dev/null || print_warning "Cursor installation failed"
    
    # Install Python-based AI tools
    pip3 install --user aider-chat 2>/dev/null || print_warning "aider installation failed"
    
    # Install GitHub Copilot CLI
    npm install -g @githubnext/github-copilot-cli 2>/dev/null || print_warning "GitHub Copilot CLI installation failed"
    
    print_success "AI tools installation completed"
}

# Phase 5: Advanced Python Environment
setup_python_env() {
    print_status "Setting up Advanced Python Environment..."
    
    # Install UV (Rust-based Python package manager)
    if ! command_exists uv; then
        print_status "Installing UV..."
        curl -LsSf https://astral.sh/uv/install.sh | sh
    fi
    
    # Install Rye
    if ! command_exists rye; then
        print_status "Installing Rye..."
        curl -sSf https://rye-up.com/get | bash
    fi
    
    # Install PDM
    if ! command_exists pdm; then
        print_status "Installing PDM..."
        curl -sSL https://raw.githubusercontent.com/pdm-project/pdm/main/install-pdm.py | python3 -
    fi
    
    print_success "Python environment setup completed"
}

# Phase 6: AI Model Management
setup_ai_models() {
    print_status "Setting up AI Models..."
    
    # Start Ollama if not running
    if ! pgrep -x "ollama" > /dev/null; then
        print_status "Starting Ollama..."
        brew services start ollama 2>/dev/null || print_warning "Ollama service start failed"
    fi
    
    # Pull essential models (in background to avoid blocking)
    print_status "Pulling AI models (this may take a while)..."
    {
        ollama pull phi3.5:3.8b-mini-instruct-q4_K_M 2>/dev/null || true
        ollama pull qwen2.5:7b-instruct-q4_K_M 2>/dev/null || true
        ollama pull llama3.1:8b-instruct-q4_K_M 2>/dev/null || true
    } &
    
    print_success "AI models setup initiated"
}

# Phase 7: Container & Orchestration
setup_containers() {
    print_status "Setting up Container & Orchestration tools..."
    
    # Install Docker tools
    brew install --quiet docker docker-compose kubectl kubectx kubens helm kustomize stern skaffold 2>/dev/null || true
    
    # Install container security tools
    brew install --quiet trivy syft grype 2>/dev/null || true
    
    print_success "Container tools setup completed"
}

# Phase 8: SampleMind AI Project Setup
setup_samplemind_project() {
    print_status "Setting up SampleMind AI Project..."
    
    cd ~/Projects/samplemind-ai.v6/samplemind-ai-v6
    
    # Setup Python virtual environment with UV
    if [ ! -d ".venv" ]; then
        print_status "Creating Python virtual environment..."
        uv venv .venv --python 3.12 2>/dev/null || python3 -m venv .venv
    fi
    
    # Activate virtual environment and install dependencies
    source .venv/bin/activate
    
    # Install Poetry if not present
    if ! command_exists poetry; then
        print_status "Installing Poetry..."
        pip install poetry
    fi
    
    # Install project dependencies
    if [ -f "pyproject.toml" ]; then
        print_status "Installing project dependencies..."
        poetry install --no-dev 2>/dev/null || print_warning "Poetry install failed"
    fi
    
    print_success "SampleMind AI project setup completed"
}

# Phase 9: Security & Performance Tools
install_security_tools() {
    print_status "Installing Security & Performance Tools..."
    
    # Security tools
    brew install --quiet gitleaks semgrep osv-scanner checkov 2>/dev/null || true
    
    # Performance monitoring tools
    brew install --quiet btop iotop bandwhich dust duf gping hyperfine 2>/dev/null || true
    
    # Python security tools
    pip3 install --user bandit safety pip-audit 2>/dev/null || true
    
    # Python profiling tools
    pip3 install --user py-spy memray scalene line_profiler 2>/dev/null || true
    
    print_success "Security & performance tools installed"
}

# Phase 10: Create AI Development Functions
create_ai_functions() {
    print_status "Creating AI Development Functions..."
    
    # Create functions file
    cat > ~/.zsh_functions << 'EOF'
# AI analyze function
ai_analyze() {
    local file="$1"
    if command_exists aider; then
        aider --model gpt-4o --message "Analyze this audio file: $file and suggest optimizations"
    else
        echo "aider not installed. Install with: pip install aider-chat"
    fi
}

# AI debug function
ai_debug() {
    local error_log="$1"
    if command_exists ollama; then
        ollama run qwen2.5:7b-instruct "Debug this error: $(cat $error_log)"
    else
        echo "ollama not running. Start with: brew services start ollama"
    fi
}

# AI optimize function
ai_optimize() {
    local code_file="$1"
    if command_exists aider; then
        aider --model claude-3-sonnet --message "Optimize this code for performance: $code_file"
    else
        echo "aider not installed. Install with: pip install aider-chat"
    fi
}

# AI test function
ai_test() {
    local module="$1"
    if command_exists aider; then
        aider --model gpt-4o --message "Generate comprehensive tests for: $module"
    else
        echo "aider not installed. Install with: pip install aider-chat"
    fi
}

# SampleMind health check
smai_health() {
    echo "🤖 SampleMind AI Health Check"
    echo "=============================="
    docker ps --format "table {{.Names}}\t{{.Status}}" 2>/dev/null || echo "Docker not running"
    ollama ps 2>/dev/null || echo "Ollama not running"
    echo "Memory: $(free -h 2>/dev/null | awk '/^Mem:/ {print $3 "/" $2}' || echo 'N/A')"
    if command -v nvidia-smi >/dev/null 2>&1; then
        echo "GPU: $(nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader,nounits)%"
    fi
}
EOF

    # Source functions in .zshrc
    echo "source ~/.zsh_functions" >> ~/.zshrc
    
    print_success "AI development functions created"
}

# Phase 11: Verification & Health Check
verify_setup() {
    print_status "Verifying setup..."
    
    echo "🔍 Checking installed tools:"
    
    local tools=("starship" "zoxide" "atuin" "fig" "rg" "bat" "eza" "ollama" "cursor")
    for tool in "${tools[@]}"; do
        if command_exists "$tool"; then
            print_success "✅ $tool"
        else
            print_warning "❌ $tool (not found)"
        fi
    done
    
    echo ""
    echo "🔍 Checking SampleMind AI project:"
    cd ~/Projects/samplemind-ai.v6/samplemind-ai-v6
    if [ -d ".venv" ]; then
        print_success "✅ Python virtual environment"
    else
        print_warning "❌ Python virtual environment (not found)"
    fi
    
    if [ -f "pyproject.toml" ]; then
        print_success "✅ Poetry configuration"
    else
        print_warning "❌ Poetry configuration (not found)"
    fi
    
    echo ""
    print_success "Setup verification completed"
}

# Main execution
main() {
    echo "🚀 Starting comprehensive modern development setup..."
    echo "This will take several minutes. Please be patient."
    echo ""
    
    install_homebrew
    install_terminal_tools
    setup_zsh
    update_zshrc
    install_ai_tools
    setup_python_env
    setup_ai_models
    setup_containers
    setup_samplemind_project
    install_security_tools
    create_ai_functions
    verify_setup
    
    echo ""
    echo "🎉 Modern Development Setup Complete!"
    echo "====================================="
    echo ""
    echo "Next steps:"
    echo "1. Restart your terminal or run: source ~/.zshrc"
    echo "2. Configure Powerlevel10k: p10k configure"
    echo "3. Set up API keys in ~/.config/openai/key and ~/.config/anthropic/key"
    echo "4. Start Ollama: brew services start ollama"
    echo "5. Test AI tools: ollama run phi3.5 'Hello, can you help with Python coding?'"
    echo ""
    echo "SampleMind AI project is ready at: ~/Projects/samplemind-ai.v6/samplemind-ai-v6"
    echo ""
}

# Run main function
main "$@" 