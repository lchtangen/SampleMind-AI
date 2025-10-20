#!/bin/bash

# Quick Performance Fix for Mac Terminal and Chat
# Run this immediately for instant performance improvements

echo "⚡ Quick Performance Fix"
echo "======================="

# 1. Immediate terminal speed improvements
echo "Optimizing terminal speed..."

# Create a minimal fast .zshrc
cat > ~/.zshrc.fast << 'EOF'
# Fast terminal configuration
export HISTSIZE=100
export SAVEHIST=100
export HISTFILE=~/.zsh_history

# Disable slow features
unsetopt AUTO_CD
unsetopt AUTO_PUSHD
unsetopt AUTO_MENU

# Fast prompt
PS1='%n@%m:%~$ '

# Essential PATH
export PATH="/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH"

# Development optimizations
export PYTHONDONTWRITEBYTECODE=1
export PYTHONUNBUFFERED=1
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1
export GIT_TERMINAL_PROGRESS=0
EOF

# 2. System performance tweaks
echo "Applying system optimizations..."

# Disable animations
defaults write com.apple.dock expose-animation-duration -float 0.1
defaults write com.apple.dock springboard-show-duration -float 0.1
defaults write com.apple.dock springboard-hide-duration -float 0.1
defaults write com.apple.dock autohide-delay -float 0
defaults write com.apple.dock autohide-time-modifier -float 0.1

# Optimize window animations
defaults write NSGlobalDomain NSWindowResizeTime -float 0.001
defaults write NSGlobalDomain NSAutomaticWindowAnimationsEnabled -bool false

# 3. Create fast startup command
mkdir -p ~/bin
cat > ~/bin/fast << 'EOF'
#!/bin/bash
# Quick fast terminal startup
export ZSH_DISABLE_COMPFIX=true
source ~/.zshrc.fast
cd ~/Projects/samplemind-ai.v6/samplemind-ai-v6
echo "⚡ Fast terminal ready!"
EOF

chmod +x ~/bin/fast

# 4. Add to PATH
echo 'export PATH="$HOME/bin:$PATH"' >> ~/.zshrc

# 5. Optimize Git
git config --global core.preloadindex true
git config --global core.fscache true

echo ""
echo "✅ Quick performance fix applied!"
echo ""
echo "To use fast terminal:"
echo "  source ~/.zshrc.fast"
echo "  or run: fast"
echo ""
echo "Restart terminal for full effect." 