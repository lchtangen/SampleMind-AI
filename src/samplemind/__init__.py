#!/usr/bin/env python3
"""
SampleMind AI v6 - Professional Music Production Suite
The ultimate AI-powered music analysis and production platform

This package provides comprehensive audio analysis, AI-powered insights,
and professional music production tools through a beautiful CLI interface.

Main Components:
- Core Audio Engine: Advanced audio processing with LibROSA
- AI Manager: Unified interface for OpenAI GPT-5 and Google AI
- Audio Loader: Professional-grade audio file loading
- CLI Interface: Beautiful interactive terminal interface

Usage:
    from samplemind.core.engine import AudioEngine
    from samplemind.integrations.ai_manager import SampleMindAIManager
    from samplemind.interfaces.cli.menu import SampleMindCLI
"""

__version__ = "6.0.0"
__author__ = "SampleMind AI Team"
__description__ = "Professional AI-powered music production suite"

# Core imports
from .core.engine.audio_engine import AudioEngine, AudioFeatures, AnalysisLevel
from .core.loader import AdvancedAudioLoader, LoadingStrategy, AudioFormat
from .integrations.ai_manager import SampleMindAIManager, AnalysisType, AIProvider

# Make key classes available at package level
__all__ = [
    # Core classes
    "AudioEngine",
    "AudioFeatures", 
    "AnalysisLevel",
    "AdvancedAudioLoader",
    "LoadingStrategy",
    "AudioFormat",
    
    # AI classes
    "SampleMindAIManager",
    "AnalysisType",
    "AIProvider",
    
    # Package info
    "__version__",
    "__author__",
    "__description__"
]

def get_version():
    """Get SampleMind AI version"""
    return __version__

def get_info():
    """Get package information"""
    return {
        "name": "SampleMind AI",
        "version": __version__,
        "description": __description__,
        "author": __author__
    }