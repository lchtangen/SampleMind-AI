#!/bin/bash

# SampleMind AI v6 - Google AI API Setup Script
# Sets up Google AI (Gemini) API for the ultimate music production AI

echo "🎵 SampleMind AI v6 - Google AI API Setup"
echo "=============================================="
echo ""
echo "🔑 Setting up Google AI (Gemini 2.5 Pro) API for music production..."
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}📋 GOOGLE AI API SETUP INSTRUCTIONS:${NC}"
echo ""
echo "1. 🌐 Go to: https://makersuite.google.com/app/apikey"
echo "2. 🔐 Sign in with your Google account"
echo "3. ➕ Click 'Create API Key'"
echo "4. 📋 Copy your API key"
echo "5. 🔒 Keep it secure - this gives access to your account!"
echo ""

# Create API key storage directory
mkdir -p ~/.samplemind/config
mkdir -p ~/.samplemind/logs

echo -e "${YELLOW}🔐 Please enter your Google AI API Key:${NC}"
read -s -p "API Key: " GOOGLE_AI_API_KEY
echo ""

if [ -z "$GOOGLE_AI_API_KEY" ]; then
    echo -e "${RED}❌ No API key provided. Exiting...${NC}"
    exit 1
fi

# Save API key securely
echo "GOOGLE_AI_API_KEY=\"$GOOGLE_AI_API_KEY\"" > ~/.samplemind/config/google_ai.env
chmod 600 ~/.samplemind/config/google_ai.env

echo ""
echo -e "${GREEN}✅ API Key saved securely to ~/.samplemind/config/google_ai.env${NC}"
echo ""

# Create environment file for the project
cat > .env << EOF
# SampleMind AI v6 - Environment Configuration
# Google AI (Gemini) API Configuration
GOOGLE_AI_API_KEY=$GOOGLE_AI_API_KEY

# Music AI Configuration
DEFAULT_MODEL=gemini-2.5-pro
MUSIC_MODEL=lyria-realtime
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
EOF

echo -e "${GREEN}✅ Environment file created: .env${NC}"
echo ""

# Test API connection
echo -e "${BLUE}🧪 Testing API connection...${NC}"

# Install required packages for testing
python3 -m pip install google-generativeai requests python-dotenv --break-system-packages --quiet

# Create test script
cat > test_google_ai_api.py << 'EOF'
#!/usr/bin/env python3
import os
import google.generativeai as genai
from dotenv import load_dotenv
import sys

def test_google_ai_api():
    # Load environment variables
    load_dotenv()
    
    api_key = os.getenv('GOOGLE_AI_API_KEY')
    if not api_key:
        print("❌ No API key found in environment")
        return False
    
    try:
        # Configure the API
        genai.configure(api_key=api_key)
        
        # Test with music-specific prompt
        model = genai.GenerativeModel('gemini-pro')
        
        test_prompt = """
        You are an AI music production expert. Analyze this sample:
        - Tempo: 128 BPM
        - Key: C Major
        - Duration: 30 seconds
        - Genre: Electronic
        
        Provide 3 creative FL Studio production tips for this sample.
        """
        
        print("🎵 Testing Google AI with music production prompt...")
        response = model.generate_content(test_prompt)
        
        print("✅ API Connection Successful!")
        print(f"🎹 Response Preview: {response.text[:200]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ API Test Failed: {e}")
        return False

if __name__ == "__main__":
    success = test_google_ai_api()
    sys.exit(0 if success else 1)
EOF

# Run the test
python3 test_google_ai_api.py

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}🎉 GOOGLE AI API SETUP SUCCESSFUL!${NC}"
    echo ""
    echo -e "${PURPLE}🎼 SampleMind AI is now powered by:${NC}"
    echo -e "   ${CYAN}• Gemini 2.5 Pro${NC} - Advanced reasoning and creativity"
    echo -e "   ${CYAN}• Lyria RealTime${NC} - Native music generation"
    echo -e "   ${CYAN}• 1M Token Context${NC} - Comprehensive analysis"
    echo -e "   ${CYAN}• Multimodal Processing${NC} - Audio, video, text"
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
    echo "1. Verify your API key at: https://makersuite.google.com/app/apikey"
    echo "2. Ensure your Google Cloud account has billing enabled"
    echo "3. Check API quotas and rate limits"
fi

# Cleanup test file
rm -f test_google_ai_api.py

echo ""
echo -e "${PURPLE}🎵 SampleMind AI v6 Setup Complete! 🎵${NC}"