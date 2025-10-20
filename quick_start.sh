#!/bin/bash

# SampleMind AI v6 - Quick Start Script
# Professional AI Music Production Suite

echo "🎵 SampleMind AI v6 - Quick Start Setup"
echo "======================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Check Python version
echo -e "${BLUE}🐍 Checking Python version...${NC}"
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
    echo -e "${GREEN}✅ Python ${PYTHON_VERSION} found${NC}"
else
    echo -e "${RED}❌ Python 3 not found. Please install Python 3.8 or higher.${NC}"
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "main.py" ] || [ ! -f "pyproject.toml" ]; then
    echo -e "${RED}❌ Please run this script from the SampleMind AI v6 project directory${NC}"
    exit 1
fi

echo ""
echo -e "${CYAN}📦 Installing Python dependencies...${NC}"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}🔨 Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
echo -e "${YELLOW}🔌 Activating virtual environment...${NC}"
source venv/bin/activate

# Upgrade pip
echo -e "${YELLOW}⬆️ Upgrading pip...${NC}"
pip install --upgrade pip

# Install dependencies
echo -e "${YELLOW}📥 Installing core dependencies...${NC}"
pip install -r requirements.txt

echo ""
echo -e "${GREEN}✅ Dependencies installed successfully!${NC}"

# Check for API keys
echo ""
echo -e "${CYAN}🔑 Checking API configuration...${NC}"

NEEDS_OPENAI=false
NEEDS_GOOGLE=false

if [ ! -f ".env" ] || ! grep -q "OPENAI_API_KEY" .env; then
    NEEDS_OPENAI=true
fi

if [ ! -f ".env" ] || ! grep -q "GOOGLE_AI_API_KEY" .env; then
    NEEDS_GOOGLE=true
fi

if [ "$NEEDS_OPENAI" = true ] && [ "$NEEDS_GOOGLE" = true ]; then
    echo -e "${YELLOW}⚠️ No API keys configured${NC}"
    echo ""
    echo "Choose an option:"
    echo "1. Setup OpenAI API (GPT-5) - Recommended"
    echo "2. Setup Google AI API (Gemini 2.5 Pro)"
    echo "3. Setup both APIs"
    echo "4. Skip for now"
    echo ""
    read -p "Enter choice (1-4): " choice
    
    case $choice in
        1)
            echo -e "${BLUE}🚀 Running OpenAI setup...${NC}"
            chmod +x setup_openai_api.sh
            ./setup_openai_api.sh
            ;;
        2)
            echo -e "${BLUE}🚀 Running Google AI setup...${NC}"
            chmod +x setup_google_ai_api.sh
            ./setup_google_ai_api.sh
            ;;
        3)
            echo -e "${BLUE}🚀 Running OpenAI setup...${NC}"
            chmod +x setup_openai_api.sh
            ./setup_openai_api.sh
            echo ""
            echo -e "${BLUE}🚀 Running Google AI setup...${NC}"
            chmod +x setup_google_ai_api.sh
            ./setup_google_ai_api.sh
            ;;
        4)
            echo -e "${YELLOW}⏭️ Skipping API setup${NC}"
            ;;
        *)
            echo -e "${RED}❌ Invalid choice${NC}"
            ;;
    esac
elif [ "$NEEDS_OPENAI" = true ]; then
    echo -e "${YELLOW}⚠️ OpenAI API not configured${NC}"
    echo "Run: ./setup_openai_api.sh"
elif [ "$NEEDS_GOOGLE" = true ]; then
    echo -e "${YELLOW}⚠️ Google AI API not configured${NC}"
    echo "Run: ./setup_google_ai_api.sh"
else
    echo -e "${GREEN}✅ API keys already configured${NC}"
fi

echo ""
echo -e "${PURPLE}🎉 SampleMind AI v6 Setup Complete!${NC}"
echo ""
echo -e "${CYAN}🚀 Ready to start! Choose how to run:${NC}"
echo ""
echo "1. Interactive Menu (Recommended):"
echo -e "   ${GREEN}python main.py${NC}"
echo ""
echo "2. Quick Analysis:"
echo -e "   ${GREEN}python main.py analyze your_audio_file.wav${NC}"
echo ""
echo "3. Batch Processing:"
echo -e "   ${GREEN}python main.py batch ./your_music_folder${NC}"
echo ""
echo "4. Show Help:"
echo -e "   ${GREEN}python main.py --help${NC}"
echo ""
echo -e "${BLUE}📋 Additional Commands:${NC}"
echo -e "   ${CYAN}python main.py --setup-openai${NC}  # Setup OpenAI API"
echo -e "   ${CYAN}python main.py --setup-google${NC}  # Setup Google AI API"
echo ""
echo -e "${YELLOW}💡 Pro Tip: The interactive menu provides the best experience!${NC}"
echo ""

# Ask if user wants to start now
read -p "🎵 Start SampleMind AI now? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${GREEN}🚀 Starting SampleMind AI v6...${NC}"
    echo ""
    python main.py
fi

echo ""
echo -e "${PURPLE}🎵 Thank you for using SampleMind AI v6! 🎵${NC}"