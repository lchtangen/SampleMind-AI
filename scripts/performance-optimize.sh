#!/bin/bash

# Mac Performance Optimization Script
# Optimizes terminal, chat, and overall system performance

echo "🚀 Optimizing Mac Performance for Development"
echo "============================================="

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# 1. Terminal Performance Optimizations
optimize_terminal() {
    print_status "Optimizing terminal performance..."
    
    # Disable terminal animations
    defaults write com.apple.dock expose-animation-duration -float 0.1
    defaults write com.apple.dock springboard-show-duration -float 0.1
    defaults write com.apple.dock springboard-hide-duration -float 0.1
    
    # Optimize shell startup
    echo "export HISTSIZE=1000" >> ~/.zshrc
    echo "export SAVEHIST=1000" >> ~/.zshrc
    echo "export HISTFILE=~/.zsh_history" >> ~/.zshrc
    echo "setopt SHARE_HISTORY" >> ~/.zshrc
    
    # Disable unnecessary shell features for speed
    echo "unsetopt AUTO_CD" >> ~/.zshrc
    echo "unsetopt AUTO_PUSHD" >> ~/.zshrc
    
    print_success "Terminal optimizations applied"
}

# 2. System Performance Optimizations
optimize_system() {
    print_status "Optimizing system performance..."
    
    # Disable animations
    defaults write com.apple.dock expose-animation-duration -float 0.1
    defaults write com.apple.dock springboard-show-duration -float 0.1
    defaults write com.apple.dock springboard-hide-duration -float 0.1
    defaults write com.apple.dock autohide-delay -float 0
    defaults write com.apple.dock autohide-time-modifier -float 0.1
    
    # Optimize window animations
    defaults write NSGlobalDomain NSWindowResizeTime -float 0.001
    defaults write NSGlobalDomain NSAutomaticWindowAnimationsEnabled -bool false
    
    # Optimize finder
    defaults write com.apple.finder DisableAllAnimations -bool true
    defaults write com.apple.finder ShowPathbar -bool false
    defaults write com.apple.finder ShowSidebar -bool false
    
    # Optimize dock
    defaults write com.apple.dock minimize-to-application -bool true
    defaults write com.apple.dock show-recents -bool false
    
    print_success "System optimizations applied"
}

# 3. Memory and CPU Optimizations
optimize_memory() {
    print_status "Optimizing memory and CPU usage..."
    
    # Create performance-focused shell configuration
    cat > ~/.zshrc.fast << 'EOF'
# Fast shell configuration for development
export HISTSIZE=500
export SAVEHIST=500
export HISTFILE=~/.zsh_history
setopt SHARE_HISTORY

# Disable slow features
unsetopt AUTO_CD
unsetopt AUTO_PUSHD
unsetopt AUTO_MENU
unsetopt MENU_COMPLETE

# Fast completions
autoload -Uz compinit
compinit -d ~/.cache/.zcompdump

# Essential aliases only
alias ls='ls -G'
alias ll='ls -la'
alias grep='grep --color=auto'

# Fast prompt
PS1='%n@%m:%~$ '

# Essential PATH
export PATH="/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH"

# Development environment
export PYTHONDONTWRITEBYTECODE=1
export PYTHONUNBUFFERED=1
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1
EOF

    print_success "Memory optimizations applied"
}

# 4. Network Optimizations
optimize_network() {
    print_status "Optimizing network performance..."
    
    # Optimize DNS
    echo "nameserver 8.8.8.8" | sudo tee -a /etc/resolv.conf > /dev/null
    echo "nameserver 1.1.1.1" | sudo tee -a /etc/resolv.conf > /dev/null
    
    # Optimize TCP settings
    sudo sysctl -w net.inet.tcp.slow_start_after_idle=0
    sudo sysctl -w net.inet.tcp.mssdflt=1448
    
    print_success "Network optimizations applied"
}

# 5. Development Environment Optimizations
optimize_dev_env() {
    print_status "Optimizing development environment..."
    
    # Create fast Python environment
    echo "export PYTHONDONTWRITEBYTECODE=1" >> ~/.zshrc
    echo "export PYTHONUNBUFFERED=1" >> ~/.zshrc
    echo "export PIP_NO_CACHE_DIR=1" >> ~/.zshrc
    
    # Optimize Git
    echo "export GIT_TERMINAL_PROGRESS=0" >> ~/.zshrc
    echo "git config --global core.preloadindex true" >> ~/.zshrc
    echo "git config --global core.fscache true" >> ~/.zshrc
    
    # Optimize Docker
    echo "export DOCKER_BUILDKIT=1" >> ~/.zshrc
    echo "export COMPOSE_DOCKER_CLI_BUILD=1" >> ~/.zshrc
    
    print_success "Development environment optimized"
}

# 6. Create Fast Startup Script
create_fast_startup() {
    print_status "Creating fast startup configuration..."
    
    cat > ~/bin/fast-dev << 'EOF'
#!/bin/bash
# Fast development environment startup

# Use fast shell config
export ZSH_DISABLE_COMPFIX=true
source ~/.zshrc.fast

# Start essential services
brew services start ollama 2>/dev/null || true

# Navigate to project
cd ~/Projects/samplemind-ai.v6/samplemind-ai-v6

echo "🚀 Fast development environment ready!"
echo "Use 'fast-dev' to start this optimized environment"
EOF

    chmod +x ~/bin/fast-dev
    
    # Add to PATH if not present
    if [[ ":$PATH:" != *":$HOME/bin:"* ]]; then
        echo 'export PATH="$HOME/bin:$PATH"' >> ~/.zshrc
    fi
    
    print_success "Fast startup script created"
}

# 7. Performance Monitoring
setup_monitoring() {
    print_status "Setting up performance monitoring..."
    
    # Create performance check script
    cat > ~/bin/check-performance << 'EOF'
#!/bin/bash
echo "🔍 Performance Check"
echo "==================="
echo "CPU Usage: $(top -l 1 | grep "CPU usage" | awk '{print $3}' | cut -d'%' -f1)%"
echo "Memory Usage: $(memory_pressure | grep "System-wide memory free percentage" | awk '{print $5}' | cut -d'%' -f1)%"
echo "Disk Usage: $(df -h / | awk 'NR==2 {print $5}' | cut -d'%' -f1)%"
echo "Active Processes: $(ps aux | wc -l)"
echo "Network Connections: $(netstat -an | wc -l)"
EOF

    chmod +x ~/bin/check-performance
    
    print_success "Performance monitoring setup complete"
}

# Main execution
main() {
    echo "Starting performance optimization..."
    
    optimize_terminal
    optimize_system
    optimize_memory
    optimize_network
    optimize_dev_env
    create_fast_startup
    setup_monitoring
    
    echo ""
    echo "🎉 Performance optimization complete!"
    echo "====================================="
    echo ""
    echo "Quick commands:"
    echo "  fast-dev          - Start optimized development environment"
    echo "  check-performance - Check system performance"
    echo "  source ~/.zshrc.fast - Use fast shell configuration"
    echo ""
    echo "Restart your terminal for all changes to take effect."
    echo ""
}

main "$@" 