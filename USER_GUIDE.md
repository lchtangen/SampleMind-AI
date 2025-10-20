# 📚 User Guide - SampleMind AI v6

## Table of Contents

1. [Getting Started](#getting-started)
2. [CLI Interface](#cli-interface)
3. [Web Application](#web-application)
4. [DAW Integration](#daw-integration)
5. [Sample Organization](#sample-organization)
6. [AI Features](#ai-features)
7. [Advanced Workflows](#advanced-workflows)
8. [Troubleshooting](#troubleshooting)

## Getting Started

### First Run

```bash
# Initialize your sample library
samplemind init ~/Music/Samples

# Quick analysis test
samplemind analyze path/to/sample.wav

# Start web interface
samplemind web --open
```

## CLI Interface

### Basic Commands

#### Analyze Single Sample

```bash
# Basic analysis
samplemind analyze kick.wav

# Detailed analysis with AI
samplemind analyze kick.wav --detailed --model smart

# Save results to file
samplemind analyze kick.wav --output results.json
```

**Output Example:**
```
🎵 Analysis Results for kick.wav
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 Classification
   Genre: Hip-Hop (94% confidence)
   Instrument: Kick Drum (99% confidence)
   Mood: Energetic, Powerful

🎼 Musical Properties
   Key: C Major
   Tempo: 128 BPM
   Duration: 0.5s

🤖 AI Analysis
   "A punchy kick drum with strong low-end presence.
   Perfect for hip-hop and trap productions."

🏷️ AI Tags
   #punchy #hip-hop #kick #electronic #powerful
```

#### Batch Processing

```bash
# Analyze entire folder
samplemind batch ~/Music/Samples --parallel

# Filter by file type
samplemind batch ~/Music/Samples --include "*.wav,*.mp3"

# Process with progress bar
samplemind batch ~/Music/Samples --progress --workers 8
```

#### Sample Organization

```bash
# Smart organization by AI
samplemind organize ~/Music/Samples --strategy smart

# Organize by mood
samplemind organize ~/Music/Samples --strategy mood

# Custom organization
samplemind organize ~/Music/Samples --template "{genre}/{mood}/{instrument}"
```

#### Search and Discovery

```bash
# Find similar samples
samplemind similar reference.wav --limit 10

# Search by description
samplemind search "dark atmospheric pad in D minor"

# Search by musical properties
samplemind search --key "C" --tempo "120-130" --duration "1-5s"
```

### Advanced CLI Features

#### AI Chat Interface

```bash
# Start interactive AI session
samplemind chat

# Quick AI query
samplemind ask "What samples would work well with a lo-fi hip-hop beat?"
```

## Web Application

### Dashboard Overview

Access the web interface at `http://localhost:8000` after running:

```bash
samplemind web
```

#### Main Features

**1. Sample Library Browser**
- **Grid View**: Visual waveform previews with metadata
- **List View**: Detailed information in table format
- **Filter Panel**: Filter by genre, mood, key, tempo, duration
- **Search Bar**: Natural language search with AI

**2. AI Assistant Panel**
- **Real-time Chat**: Ask questions about your samples
- **Smart Suggestions**: Get recommendations based on your project
- **Analysis Results**: View detailed AI analysis

**3. Quick Actions**
- **Drag & Drop Upload**: Instant analysis of new samples
- **One-Click Export**: Direct export to your DAW
- **Batch Operations**: Select multiple samples for batch actions

### Sample Management

#### Uploading Samples

**Method 1: Drag & Drop**
1. Drag audio files from your computer to the upload area
2. AI analysis starts automatically
3. Samples are added to your library with AI-generated tags

**Method 2: Folder Import**
1. Click "Import Folder" button
2. Select folder containing samples
3. Choose organization strategy
4. Monitor progress in real-time

## DAW Integration

### FL Studio Integration

#### Installation

1. Download FL Studio plugin from SampleMind dashboard
2. Copy `SampleMind.dll` to FL Studio's plugin directory
3. Restart FL Studio
4. SampleMind appears in browser under "Installed plugins"

#### Features

**Real-time Sync:**
- Project tempo detection
- Key detection from existing elements
- Automatic sample suggestions based on project

**Smart Browser:**
- AI-organized sample categories
- Search within FL Studio browser
- Drag-drop sample import
- Preview with project context

## Sample Organization

### Intelligent Organization

#### AI-Powered Strategies

**Smart Organization Algorithm:**
1. **Audio Analysis**: Extract musical and audio features
2. **AI Classification**: Genre, mood, instrument detection
3. **Clustering**: Group similar samples using machine learning
4. **Hierarchy Creation**: Build logical folder structure
5. **Metadata Enhancement**: Add AI-generated tags and descriptions

**Example Smart Organization:**
```
📁 Organized Library/
├── 📁 Drums/
│   ├── 📁 Hip-Hop/
│   │   ├── 📁 Energetic/
│   │   │   ├── 808-kick-punchy.wav
│   │   │   └── snare-crisp-128bpm.wav
│   │   └── 📁 Chill/
│   │       ├── kick-soft-vinyl.wav
│   │       └── snare-lo-fi-dusty.wav
├── 📁 Melodic/
│   ├── 📁 Chords/
│   └── 📁 Leads/
└── 📁 Atmospheric/
    ├── 📁 Pads/
    └── 📁 Textures/
```

## AI Features

### Sample Analysis

#### Comprehensive Audio Analysis

**Audio Features:**
- **Spectral Analysis**: Frequency content, brightness, warmth
- **Rhythm Analysis**: Tempo, groove, swing feel
- **Harmonic Analysis**: Key detection, chord recognition
- **Dynamic Analysis**: Loudness, compression, transients
- **Quality Analysis**: Audio fidelity, noise detection

**AI Insights:**
- **Musical Context**: How sample fits in different genres
- **Production Tips**: Suggested processing and effects
- **Layering Suggestions**: What samples work well together
- **Usage Recommendations**: When and how to use the sample

### Smart Suggestions

#### Context-Aware Recommendations

**Project-Based Suggestions:**
1. **Upload Current Project**: Share your work-in-progress
2. **Analysis**: AI understands your style and direction
3. **Recommendations**: Get samples that complement your project
4. **Reasoning**: Understand why each sample was suggested

**Mood-Based Discovery:**
- **Energy**: Energetic, calm, intense, relaxed
- **Emotion**: Happy, sad, aggressive, peaceful
- **Atmosphere**: Dark, bright, mysterious, open
- **Movement**: Driving, floating, bouncing, flowing

## Advanced Workflows

### Producer Workflows

#### Beat Making Workflow

**1. Start with AI Assistance:**
```bash
# Get AI suggestions for your genre
samplemind ask "I want to make a trap beat. What samples do I need?"
```

**2. Build Sample Kit:**
```bash
# Create project-specific kit
samplemind kit create "My Trap Beat" --genre trap --mood aggressive
```

**3. Export to DAW:**
```bash
# Export organized kit to FL Studio
samplemind kit export "My Trap Beat" --daw fl-studio --template drum-rack
```

### Educational Workflows

#### Music Production Learning

**Analyze Professional Tracks:**
```bash
# Deconstruct professional production
samplemind deconstruct professional-track.mp3 --identify-samples

# Learn from arrangement
samplemind learn arrangement professional-track.mp3 --breakdown
```

## Troubleshooting

### Common Issues

#### Installation Problems

**Issue: Ollama models not downloading**
```bash
# Check Ollama service
ollama list

# Manually download required models
ollama pull phi3:mini
ollama pull qwen2.5:7b-instruct
```

**Issue: Audio analysis fails**
```bash
# Check audio file format support
samplemind info audio-formats

# Verify audio file integrity
samplemind validate audio-file.wav
```

#### Performance Issues

**Issue: Slow analysis speed**
```bash
# Check system resources
samplemind doctor --performance

# Optimize cache settings
samplemind config cache --optimize

# Use fast models for batch processing
samplemind config set-default-model phi3:mini
```

### Getting Help

#### Built-in Help System

```bash
# General help
samplemind --help

# Command-specific help
samplemind analyze --help

# Show examples
samplemind examples
```

#### Community Support

- **Discord**: [SampleMind Community](https://discord.gg/samplemind)
- **Forum**: [forum.samplemind.ai](https://forum.samplemind.ai)
- **GitHub Issues**: [Bug reports and feature requests](https://github.com/samplemind/samplemind-ai-v6/issues)
- **Documentation**: [docs.samplemind.ai](https://docs.samplemind.ai)

---

This comprehensive user guide covers all aspects of using SampleMind AI v6, from basic sample analysis to advanced producer workflows.
