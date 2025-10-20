#!/usr/bin/env python3
"""
SampleMind AI v6 - OpenAI Integration Module
Advanced music production AI using OpenAI GPT-4o

This module provides comprehensive music analysis, production coaching,
and creative assistance powered by OpenAI's most advanced models.
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import base64
import hashlib

import openai
from openai import OpenAI, AsyncOpenAI
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OpenAIModel(Enum):
    """Available OpenAI models for music production"""
    GPT_5 = "gpt-5"
    GPT_4O = "gpt-4o"
    GPT_4O_MINI = "gpt-4o-mini"
    GPT_4_TURBO = "gpt-4-turbo"
    GPT_4 = "gpt-4"


class MusicAnalysisType(Enum):
    """Types of music analysis available"""
    QUICK_ANALYSIS = "quick_analysis"
    COMPREHENSIVE_ANALYSIS = "comprehensive_analysis"
    PRODUCTION_COACHING = "production_coaching"
    CREATIVE_SUGGESTIONS = "creative_suggestions"
    FL_STUDIO_OPTIMIZATION = "fl_studio_optimization"
    MIXING_MASTERING = "mixing_mastering"
    GENRE_CLASSIFICATION = "genre_classification"
    HARMONIC_ANALYSIS = "harmonic_analysis"
    RHYTHM_ANALYSIS = "rhythm_analysis"
    ARRANGEMENT_ADVICE = "arrangement_advice"


@dataclass
class OpenAIMusicAnalysis:
    """Comprehensive music analysis result from OpenAI"""
    analysis_type: MusicAnalysisType
    model_used: str
    timestamp: float = field(default_factory=time.time)
    
    # Core Analysis
    summary: str = ""
    detailed_analysis: Dict[str, Any] = field(default_factory=dict)
    
    # Production Insights
    production_tips: List[str] = field(default_factory=list)
    fl_studio_recommendations: List[str] = field(default_factory=list)
    effect_suggestions: List[Dict[str, Any]] = field(default_factory=list)
    
    # Creative Suggestions
    creative_ideas: List[str] = field(default_factory=list)
    arrangement_suggestions: List[str] = field(default_factory=list)
    
    # Technical Analysis
    harmonic_analysis: Dict[str, Any] = field(default_factory=dict)
    rhythmic_analysis: Dict[str, Any] = field(default_factory=dict)
    spectral_analysis: Dict[str, Any] = field(default_factory=dict)
    
    # Scores and Ratings
    creativity_score: float = 0.0
    production_quality_score: float = 0.0
    commercial_potential_score: float = 0.0
    
    # Metadata
    tokens_used: int = 0
    processing_time: float = 0.0
    confidence_score: float = 0.0


class AdvancedMusicPromptEngine:
    """Advanced prompt engineering for music production"""
    
    def __init__(self):
        self.base_prompts = self._load_base_prompts()
        self.context_enhancers = self._load_context_enhancers()
    
    def create_analysis_prompt(
        self, 
        audio_features: Dict[str, Any],
        analysis_type: MusicAnalysisType,
        user_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create sophisticated prompt for music analysis"""
        
        base_prompt = self.base_prompts.get(analysis_type, self.base_prompts[MusicAnalysisType.COMPREHENSIVE_ANALYSIS])
        
        # Build feature description
        feature_description = self._format_audio_features(audio_features)
        
        # Add user context if provided
        context_addition = ""
        if user_context:
            context_addition = self._format_user_context(user_context)
        
        # Combine into final prompt
        final_prompt = f"""
{base_prompt}

AUDIO ANALYSIS DATA:
{feature_description}

{context_addition}

Please provide a comprehensive response in JSON format with the following structure:
{{
    "summary": "Brief overview of the track",
    "detailed_analysis": {{
        "tempo_analysis": "Analysis of tempo and rhythm",
        "harmonic_content": "Key, mode, chord progressions",
        "spectral_characteristics": "Frequency content analysis",
        "dynamics": "Energy and dynamic range analysis"
    }},
    "production_tips": ["Tip 1", "Tip 2", "Tip 3"],
    "fl_studio_recommendations": ["FL Studio specific advice"],
    "effect_suggestions": [
        {{"effect": "Effect Name", "parameters": {{}}, "reason": "Why this effect"}}
    ],
    "creative_ideas": ["Creative suggestion 1", "Creative suggestion 2"],
    "arrangement_suggestions": ["Arrangement advice"],
    "scores": {{
        "creativity": 0.0,
        "production_quality": 0.0,
        "commercial_potential": 0.0
    }},
    "confidence": 0.95
}}
        """
        
        return final_prompt.strip()
    
    def _load_base_prompts(self) -> Dict[MusicAnalysisType, str]:
        """Load base prompts for different analysis types"""
        return {
            MusicAnalysisType.QUICK_ANALYSIS: """
You are an expert music producer and audio engineer. Provide a quick but insightful analysis of this audio track.
Focus on the most important elements: tempo, key, energy, and immediate production opportunities.
            """,
            
            MusicAnalysisType.COMPREHENSIVE_ANALYSIS: """
You are a world-class music producer, audio engineer, and creative consultant with 20+ years of experience.
Analyze this audio track comprehensively, considering all musical, technical, and creative aspects.
Provide detailed insights that would help both beginners and professionals improve their production.
            """,
            
            MusicAnalysisType.PRODUCTION_COACHING: """
You are a personal music production coach and mentor. Your goal is to help the user improve their production skills.
Analyze this track and provide specific, actionable advice for enhancing the production quality.
Focus on practical tips they can implement immediately in their DAW.
            """,
            
            MusicAnalysisType.FL_STUDIO_OPTIMIZATION: """
You are an FL Studio expert and certified trainer. Analyze this track specifically for FL Studio optimization.
Provide detailed recommendations for plugins, routing, effects chains, and workflow improvements.
Include specific FL Studio plugin names and parameter suggestions.
            """,
            
            MusicAnalysisType.CREATIVE_SUGGESTIONS: """
You are a creative music consultant and innovation expert. Your role is to inspire and guide creative decisions.
Analyze this track and provide innovative ideas for enhancement, arrangement, and creative development.
Think outside the box while maintaining musical coherence.
            """,
            
            MusicAnalysisType.MIXING_MASTERING: """
You are a professional mixing and mastering engineer. Analyze this track for technical excellence.
Provide specific recommendations for EQ, compression, spatial processing, and mastering considerations.
Focus on achieving professional sound quality and competitive loudness.
            """
        }
    
    def _load_context_enhancers(self) -> Dict[str, str]:
        """Load context enhancers for different scenarios"""
        return {
            "beginner": "Explain technical terms and provide educational context.",
            "intermediate": "Assume moderate knowledge but explain advanced concepts.",
            "expert": "Use professional terminology and advanced techniques.",
            "live_performance": "Focus on live performance considerations.",
            "studio_recording": "Emphasize studio recording techniques.",
            "home_studio": "Consider home studio limitations and solutions."
        }
    
    def _format_audio_features(self, features: Dict[str, Any]) -> str:
        """Format audio features for prompt inclusion"""
        formatted = []
        
        # Basic properties
        if 'duration' in features:
            formatted.append(f"Duration: {features['duration']:.2f} seconds")
        if 'sample_rate' in features:
            formatted.append(f"Sample Rate: {features['sample_rate']} Hz")
        
        # Musical features
        if 'tempo' in features:
            formatted.append(f"Tempo: {features['tempo']:.1f} BPM")
        if 'key' in features:
            formatted.append(f"Key: {features['key']}")
        if 'mode' in features:
            formatted.append(f"Mode: {features['mode']}")
        
        # Spectral features
        if 'spectral_centroid' in features and features['spectral_centroid']:
            avg_centroid = np.mean(features['spectral_centroid'])
            formatted.append(f"Spectral Centroid: {avg_centroid:.1f} Hz")
        
        if 'rms_energy' in features and features['rms_energy']:
            avg_rms = np.mean(features['rms_energy'])
            formatted.append(f"Average RMS Energy: {avg_rms:.3f}")
        
        # Harmonic content
        if 'pitch_class_distribution' in features:
            formatted.append(f"Pitch Class Distribution: {features['pitch_class_distribution']}")
        
        return "\n".join(formatted)
    
    def _format_user_context(self, context: Dict[str, Any]) -> str:
        """Format user context for prompt inclusion"""
        formatted = ["USER CONTEXT:"]
        
        if 'skill_level' in context:
            formatted.append(f"Skill Level: {context['skill_level']}")
        if 'genre_preference' in context:
            formatted.append(f"Genre Focus: {context['genre_preference']}")
        if 'production_goal' in context:
            formatted.append(f"Production Goal: {context['production_goal']}")
        if 'equipment' in context:
            formatted.append(f"Equipment: {context['equipment']}")
        
        return "\n".join(formatted)


class OpenAIMusicProducer:
    """
    Advanced OpenAI-powered music production assistant
    
    Provides comprehensive music analysis, production coaching, and creative assistance
    using OpenAI's GPT-4o and other advanced models.
    """
    
    def __init__(
        self,
        api_key: str,
        default_model: OpenAIModel = OpenAIModel.GPT_5,
        max_retries: int = 3,
        timeout: float = 30.0
    ):
        self.api_key = api_key
        self.default_model = default_model
        self.max_retries = max_retries
        self.timeout = timeout
        
        # Initialize clients
        self.client = OpenAI(api_key=api_key)
        self.async_client = AsyncOpenAI(api_key=api_key)
        
        # Initialize prompt engine
        self.prompt_engine = AdvancedMusicPromptEngine()
        
        # Caching and optimization
        self.analysis_cache = {}
        self.usage_stats = {
            'total_requests': 0,
            'total_tokens': 0,
            'avg_response_time': 0.0,
            'cache_hits': 0
        }
        
        logger.info(f"🎵 OpenAI Music Producer initialized with {default_model.value}")
    
    async def analyze_music_comprehensive(
        self,
        audio_features: Dict[str, Any],
        analysis_type: MusicAnalysisType = MusicAnalysisType.COMPREHENSIVE_ANALYSIS,
        model: Optional[OpenAIModel] = None,
        user_context: Optional[Dict[str, Any]] = None,
        use_cache: bool = True
    ) -> OpenAIMusicAnalysis:
        """
        Perform comprehensive music analysis using OpenAI
        
        Args:
            audio_features: Dictionary of extracted audio features
            analysis_type: Type of analysis to perform
            model: OpenAI model to use (defaults to instance default)
            user_context: Additional context about user and goals
            use_cache: Whether to use response caching
            
        Returns:
            OpenAIMusicAnalysis object with comprehensive results
        """
        start_time = time.time()
        model = model or self.default_model
        
        # Generate cache key
        cache_key = self._generate_cache_key(audio_features, analysis_type, model)
        
        # Check cache
        if use_cache and cache_key in self.analysis_cache:
            self.usage_stats['cache_hits'] += 1
            logger.info("📦 Using cached analysis result")
            return self.analysis_cache[cache_key]
        
        try:
            # Create sophisticated prompt
            prompt = self.prompt_engine.create_analysis_prompt(
                audio_features, analysis_type, user_context
            )
            
            # Make API request with model-specific parameters
            completion_kwargs = {
                "model": model.value,
                "messages": [
                    {
                        "role": "system", 
                        "content": "You are an expert music producer, audio engineer, and creative consultant."
                    },
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
                "response_format": {"type": "json_object"}
            }
            
            # Use correct parameter based on model
            if model == OpenAIModel.GPT_5:
                completion_kwargs["max_completion_tokens"] = 4000
            else:
                completion_kwargs["max_tokens"] = 4000
            
            response = await self.async_client.chat.completions.create(**completion_kwargs)
            
            # Parse response
            content = response.choices[0].message.content
            analysis_data = json.loads(content)
            
            # Create analysis object
            analysis = OpenAIMusicAnalysis(
                analysis_type=analysis_type,
                model_used=model.value,
                summary=analysis_data.get('summary', ''),
                detailed_analysis=analysis_data.get('detailed_analysis', {}),
                production_tips=analysis_data.get('production_tips', []),
                fl_studio_recommendations=analysis_data.get('fl_studio_recommendations', []),
                effect_suggestions=analysis_data.get('effect_suggestions', []),
                creative_ideas=analysis_data.get('creative_ideas', []),
                arrangement_suggestions=analysis_data.get('arrangement_suggestions', []),
                harmonic_analysis=analysis_data.get('detailed_analysis', {}).get('harmonic_content', {}),
                rhythmic_analysis=analysis_data.get('detailed_analysis', {}).get('tempo_analysis', {}),
                spectral_analysis=analysis_data.get('detailed_analysis', {}).get('spectral_characteristics', {}),
                creativity_score=analysis_data.get('scores', {}).get('creativity', 0.0),
                production_quality_score=analysis_data.get('scores', {}).get('production_quality', 0.0),
                commercial_potential_score=analysis_data.get('scores', {}).get('commercial_potential', 0.0),
                tokens_used=response.usage.total_tokens,
                processing_time=time.time() - start_time,
                confidence_score=analysis_data.get('confidence', 0.0)
            )
            
            # Cache result
            if use_cache:
                self.analysis_cache[cache_key] = analysis
            
            # Update usage stats
            self._update_usage_stats(response.usage.total_tokens, time.time() - start_time)
            
            logger.info(f"🎯 OpenAI analysis complete ({analysis.processing_time:.2f}s, {analysis.tokens_used} tokens)")
            return analysis
            
        except Exception as e:
            logger.error(f"❌ OpenAI analysis failed: {e}")
            raise
    
    def analyze_music_sync(
        self,
        audio_features: Dict[str, Any],
        analysis_type: MusicAnalysisType = MusicAnalysisType.COMPREHENSIVE_ANALYSIS,
        model: Optional[OpenAIModel] = None,
        user_context: Optional[Dict[str, Any]] = None
    ) -> OpenAIMusicAnalysis:
        """Synchronous version of music analysis"""
        return asyncio.run(self.analyze_music_comprehensive(
            audio_features, analysis_type, model, user_context
        ))
    
    async def get_production_coaching(
        self,
        audio_features: Dict[str, Any],
        current_issues: List[str],
        skill_level: str = "intermediate"
    ) -> OpenAIMusicAnalysis:
        """Get personalized production coaching"""
        user_context = {
            'skill_level': skill_level,
            'current_issues': current_issues,
            'production_goal': 'Improve production skills'
        }
        
        return await self.analyze_music_comprehensive(
            audio_features,
            MusicAnalysisType.PRODUCTION_COACHING,
            user_context=user_context
        )
    
    async def get_fl_studio_optimization(
        self,
        audio_features: Dict[str, Any],
        current_plugins: List[str] = None
    ) -> OpenAIMusicAnalysis:
        """Get FL Studio specific optimization advice"""
        user_context = {
            'daw': 'FL Studio',
            'current_plugins': current_plugins or [],
            'production_goal': 'Optimize FL Studio workflow'
        }
        
        return await self.analyze_music_comprehensive(
            audio_features,
            MusicAnalysisType.FL_STUDIO_OPTIMIZATION,
            user_context=user_context
        )
    
    async def batch_analyze(
        self,
        audio_features_list: List[Dict[str, Any]],
        analysis_type: MusicAnalysisType = MusicAnalysisType.COMPREHENSIVE_ANALYSIS,
        max_concurrent: int = 5
    ) -> List[OpenAIMusicAnalysis]:
        """Batch analyze multiple tracks with concurrency control"""
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def analyze_with_semaphore(features):
            async with semaphore:
                return await self.analyze_music_comprehensive(features, analysis_type)
        
        tasks = [analyze_with_semaphore(features) for features in audio_features_list]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"❌ Batch analysis failed for item {i}: {result}")
                # Create empty analysis for failed items
                empty_analysis = OpenAIMusicAnalysis(analysis_type=analysis_type, model_used=self.default_model.value)
                processed_results.append(empty_analysis)
            else:
                processed_results.append(result)
        
        return processed_results
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics and performance metrics"""
        return {
            **self.usage_stats,
            'cache_size': len(self.analysis_cache),
            'cache_hit_rate': self.usage_stats['cache_hits'] / max(1, self.usage_stats['total_requests'])
        }
    
    def clear_cache(self):
        """Clear analysis cache"""
        self.analysis_cache.clear()
        logger.info("🧹 OpenAI analysis cache cleared")
    
    def _generate_cache_key(
        self, 
        audio_features: Dict[str, Any], 
        analysis_type: MusicAnalysisType,
        model: OpenAIModel
    ) -> str:
        """Generate cache key for analysis request"""
        # Create a hash from features and parameters
        key_data = {
            'tempo': audio_features.get('tempo', 0),
            'key': audio_features.get('key', ''),
            'duration': audio_features.get('duration', 0),
            'analysis_type': analysis_type.value,
            'model': model.value
        }
        
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _update_usage_stats(self, tokens_used: int, response_time: float):
        """Update usage statistics"""
        self.usage_stats['total_requests'] += 1
        self.usage_stats['total_tokens'] += tokens_used
        
        # Update running average response time
        prev_avg = self.usage_stats['avg_response_time']
        prev_count = self.usage_stats['total_requests'] - 1
        self.usage_stats['avg_response_time'] = (prev_avg * prev_count + response_time) / self.usage_stats['total_requests']
    
    async def close(self):
        """Clean up resources"""
        await self.async_client.close()
        logger.info("🔴 OpenAI Music Producer closed")


# Utility functions for integration
def create_openai_producer_from_env() -> OpenAIMusicProducer:
    """Create OpenAI producer from environment variables"""
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    api_key = os.getenv('OPENAI_API_KEY')
    
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in environment variables")
    
    return OpenAIMusicProducer(api_key=api_key)


# Example usage
if __name__ == "__main__":
    async def example_usage():
        # Example audio features (would come from audio_engine.py)
        sample_features = {
            'tempo': 128.0,
            'key': 'C',
            'mode': 'major',
            'duration': 180.0,
            'sample_rate': 44100,
            'spectral_centroid': [2500.0] * 100,
            'rms_energy': [0.5] * 100,
            'pitch_class_distribution': [0.1] * 12
        }
        
        try:
            # Create producer (would use real API key)
            # producer = create_openai_producer_from_env()
            
            # Example analysis
            # analysis = await producer.analyze_music_comprehensive(
            #     sample_features, 
            #     MusicAnalysisType.FL_STUDIO_OPTIMIZATION
            # )
            
            logger.info("🎵 OpenAI Music Producer example complete!")
            
        except Exception as e:
            logger.error(f"❌ Example failed: {e}")
    
    # Run example
    # asyncio.run(example_usage())
    logger.info("🎼 OpenAI Integration Module Ready!")