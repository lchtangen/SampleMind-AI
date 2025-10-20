#!/bin/bash

# SampleMind AI v6 - OpenAI API Setup Script
# Sets up OpenAI GPT-4o for ultimate music production AI

echo "🎵 SampleMind AI v6 - OpenAI API Setup"
echo "====================================="
echo ""
echo "🔑 Setting up OpenAI (GPT-5) API for music production..."
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}📋 OPENAI API SETUP INSTRUCTIONS:${NC}"
echo ""
echo "1. 🌐 Go to: https://platform.openai.com/api-keys"
echo "2. 🔐 Sign in with your OpenAI account"
echo "3. ➕ Click 'Create new secret key'"
echo "4. 📋 Copy your API key (starts with sk-)"
echo "5. 🔒 Keep it secure - this gives access to your account!"
echo ""

# Create API key storage directory
mkdir -p ~/.samplemind/config
mkdir -p ~/.samplemind/logs

echo -e "${YELLOW}🔐 Please enter your OpenAI API Key:${NC}"
read -s -p "API Key: " OPENAI_API_KEY
echo ""

if [ -z "$OPENAI_API_KEY" ]; then
    echo -e "${RED}❌ No API key provided. Exiting...${NC}"
    exit 1
fi

# Validate API key format
if [[ ! $OPENAI_API_KEY =~ ^sk-[a-zA-Z0-9]{48,}$ ]]; then
    echo -e "${YELLOW}⚠️  Warning: API key format doesn't match expected pattern${NC}"
    echo -e "${YELLOW}   Expected: sk-... (at least 51 characters)${NC}"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${RED}❌ Setup cancelled${NC}"
        exit 1
    fi
fi

# Save API key securely
echo "OPENAI_API_KEY=\"$OPENAI_API_KEY\"" > ~/.samplemind/config/openai.env
chmod 600 ~/.samplemind/config/openai.env

echo ""
echo -e "${GREEN}✅ API Key saved securely to ~/.samplemind/config/openai.env${NC}"
echo ""

# Create environment file for the project
cat > .env << EOF
# SampleMind AI v6 - Environment Configuration
# OpenAI API Configuration
OPENAI_API_KEY=$OPENAI_API_KEY

# Music AI Configuration
DEFAULT_MODEL=gpt-5
MUSIC_MODEL=gpt-5
MAX_TOKENS=4096
TEMPERATURE=0.7

# Application Settings
ENVIRONMENT=development
LOG_LEVEL=INFO
CACHE_ENABLED=true
BATCH_PROCESSING=true

# FL Studio Integration
FL_STUDIO_INTEGRATION=true
REAL_TIME_ANALYSIS=true
STREAMING_ENABLED=true

# Rate Limiting
MAX_REQUESTS_PER_MINUTE=60
ENABLE_COST_OPTIMIZATION=true

# Multi-API Support
PRIMARY_API=openai
FALLBACK_API=google_ai
API_ROTATION_ENABLED=false
EOF

echo -e "${GREEN}✅ Environment file created: .env${NC}"
echo ""

# Test API connection
echo -e "${BLUE}🧪 Testing OpenAI API connection...${NC}"

# Install required packages for testing
python3 -m pip install openai python-dotenv requests --break-system-packages --quiet

# Create test script
cat > test_openai_api.py << 'EOF'
#!/usr/bin/env python3
import os
import openai
from dotenv import load_dotenv
import sys
import json

def test_openai_api():
    # Load environment variables
    load_dotenv()
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ No API key found in environment")
        return False
    
    try:
        # Configure the API
        client = openai.OpenAI(api_key=api_key)
        
        # Test with music-specific prompt
        test_prompt = """
        You are an AI music production expert. Analyze this sample and provide creative insights:
        
        Audio Analysis:
        - Tempo: 128 BPM
        - Key: C Major
        - Duration: 30 seconds
        - Genre: Electronic House
        - Spectral Centroid: 2500 Hz
        - RMS Energy: High dynamics
        
        Provide 3 creative FL Studio production tips for this sample in JSON format.
        """
        
        print("🎵 Testing OpenAI with music production prompt...")
        
        response = client.chat.completions.create(
            model="gpt-5",
            messages=[
                {"role": "system", "content": "You are an expert music producer and FL Studio specialist."},
                {"role": "user", "content": test_prompt}
            ],
            max_tokens=500,
            temperature=0.7
        )
        
        print("✅ API Connection Successful!")
        print(f"🎹 Model: {response.model}")
        print(f"🎶 Response Preview: {response.choices[0].message.content[:200]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ API Test Failed: {e}")
        return False

if __name__ == "__main__":
    success = test_openai_api()
    sys.exit(0 if success else 1)
EOF

# Run the test
python3 test_openai_api.py

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}🎉 OPENAI API SETUP SUCCESSFUL!${NC}"
    echo ""
    echo -e "${PURPLE}🎼 SampleMind AI is now powered by:${NC}"
    echo -e "   ${CYAN}• GPT-5${NC} - Advanced reasoning and creativity"
    echo -e "   ${CYAN}• 128K Context${NC} - Comprehensive analysis"
    echo -e "   ${CYAN}• Multimodal Processing${NC} - Audio, text, images"
    echo -e "   ${CYAN}• Real-time Responses${NC} - Fast music analysis"
    echo ""
    echo -e "${YELLOW}💡 Next Steps:${NC}"
    echo "1. Run: cd /Users/lchtangen/Projects/samplemind-ai-v6"
    echo "2. Run: python3 -m pip install -r requirements.txt"
    echo "3. Run: python3 src/samplemind/interfaces/cli/main.py --help"
    echo ""
    echo -e "${GREEN}🚀 Your AI music production system is ready!${NC}"
else
    echo ""
    echo -e "${RED}❌ API setup failed. Please check your API key and try again.${NC}"
    echo ""
    echo -e "${YELLOW}💡 Troubleshooting:${NC}"
    echo "1. Verify your API key at: https://platform.openai.com/api-keys"
    echo "2. Ensure your OpenAI account has billing enabled"
    echo "3. Check API quotas and rate limits"
fi

# Cleanup test file
rm -f test_openai_api.py

echo ""
echo -e "${PURPLE}🎵 SampleMind AI v6 OpenAI Setup Complete! 🎵${NC}"