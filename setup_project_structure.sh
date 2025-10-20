#!/bin/bash

# SampleMind AI v6 - Project Structure Creator
# Creates the complete directory structure for the project

echo "🏗️ Creating SampleMind AI v6 Project Structure..."

BASE_DIR="/Users/lchtangen/Projects/samplemind-ai-v6"
cd "$BASE_DIR"

# Create main source structure
mkdir -p src/samplemind/{ai/{cloud,hybrid,local,models},core/{database,engine,models,security,utils,workers},interfaces/{cli/{commands},api/{middleware,models,routes},gui/{electron,web},plugins/{au,fl_studio,vst3}},integrations/{cloud_storage,daw,social}}

# Create __init__.py files
find src -type d -exec touch {}/__init__.py \;

# Create test structure
mkdir -p tests/{unit/{ai,core,interfaces},integration,e2e,performance,fixtures/{audio_samples,configs,mock_responses}}

# Create configuration directories
mkdir -p config/{database,environments,logging,models}

# Create data directories
mkdir -p data/{dev,prod,test}/{cache,logs,samples,chromadb,mongodb,ollama,redis}

# Create deployment directories
mkdir -p deployment/{docker,kubernetes/{configmaps,deployments,ingress,monitoring,secrets,services},scripts,terraform/{environments,modules/{eks,rds,vpc}}}

# Create frontend directories
mkdir -p frontend/{electron/{assets,main,renderer},web/{docs,public,src/{app,components,hooks,lib,styles,types}}}

# Create monitoring directories
mkdir -p monitoring/{alerts,exporters,grafana/{dashboards,provisioning/{dashboards,datasources}}}

# Create docs directories
mkdir -p docs/{api,assets/{examples,images,videos},deployment,developer_guide,tutorials,user_guide}

# Create tools directories
mkdir -p tools/{automation,linting,scripts,templates}

# Create GitHub directories
mkdir -p .github/{ISSUE_TEMPLATE,workflows}

# Create VSCode directory
mkdir -p .vscode

echo "✅ Project structure created successfully!"
echo "📁 Directory structure:"
tree src -I '__pycache__|*.pyc' || find src -type d | head -20

echo ""
echo "🎯 Ready to implement audio engine and core functionality!"