#!/usr/bin/env python3
"""
SampleMind AI v6 - Unified AI Manager
Manages multiple AI providers (OpenAI, Google AI) with intelligent routing

This module provides a unified interface for all AI operations, automatic
failover, cost optimization, and performance monitoring across providers.
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Union
import json
import os
from pathlib import Path

# Import our AI integrations
from .openai_integration import OpenAIMusicProducer, OpenAIMusicAnalysis, MusicAnalysisType as OpenAIMusicAnalysisType
try:
    from .google_ai_integration import GoogleAIMusicProducer, AdvancedMusicAnalysis, MusicAnalysisType as GoogleMusicAnalysisType
    GOOGLE_AI_AVAILABLE = True
except ImportError:
    GOOGLE_AI_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("Google AI integration not available - some features will be limited")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AIProvider(Enum):
    """Supported AI providers"""
    OPENAI = "openai"
    GOOGLE_AI = "google_ai"


class AnalysisType(Enum):
    """Unified analysis types across all providers"""
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
class AIProviderConfig:
    """Configuration for an AI provider"""
    provider: AIProvider
    api_key: str
    enabled: bool = True
    priority: int = 1  # Lower number = higher priority
    max_requests_per_minute: int = 60
    cost_per_token: float = 0.0001
    features: List[str] = field(default_factory=list)
    
    # Performance tracking
    total_requests: int = 0
    total_tokens: int = 0
    avg_response_time: float = 0.0
    success_rate: float = 1.0
    last_error: Optional[str] = None


@dataclass
class UnifiedAnalysisResult:
    """Unified analysis result from any provider"""
    provider: AIProvider
    analysis_type: AnalysisType
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
    cost_estimate: float = 0.0


class AILoadBalancer:
    """Intelligent load balancing across AI providers"""
    
    def __init__(self, providers: List[AIProviderConfig]):
        self.providers = {p.provider: p for p in providers}
        self.request_counts = {p.provider: 0 for p in providers}
        self.last_request_time = {p.provider: 0 for p in providers}
    
    def select_provider(
        self, 
        analysis_type: AnalysisType,
        preferred_provider: Optional[AIProvider] = None
    ) -> AIProvider:
        """Select the best provider for a request"""
        
        # If specific provider requested and available, use it
        if preferred_provider and preferred_provider in self.providers:
            if self.providers[preferred_provider].enabled:
                return preferred_provider
        
        # Filter available providers
        available_providers = [
            p for p in self.providers.values() 
            if p.enabled and self._check_rate_limit(p)
        ]
        
        if not available_providers:
            raise RuntimeError("No AI providers available")
        
        # Sort by priority, then by performance
        available_providers.sort(key=lambda p: (
            p.priority,
            -p.success_rate,
            p.avg_response_time
        ))
        
        selected = available_providers[0]
        self._update_request_count(selected.provider)
        
        return selected.provider
    
    def _check_rate_limit(self, provider: AIProviderConfig) -> bool:
        """Check if provider is within rate limits"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time[provider.provider]
        
        # Reset count if more than a minute has passed
        if time_since_last > 60:
            self.request_counts[provider.provider] = 0
        
        return self.request_counts[provider.provider] < provider.max_requests_per_minute
    
    def _update_request_count(self, provider: AIProvider):
        """Update request count for rate limiting"""
        self.request_counts[provider] += 1
        self.last_request_time[provider] = time.time()


class SampleMindAIManager:
    """
    Unified AI Manager for SampleMind AI v6
    
    Manages multiple AI providers with intelligent routing, automatic failover,
    cost optimization, and performance monitoring.
    """
    
    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or Path.home() / ".samplemind" / "config" / "ai_config.json"
        self.providers: Dict[AIProvider, Any] = {}  # Will hold actual provider instances
        self.provider_configs: Dict[AIProvider, AIProviderConfig] = {}
        self.load_balancer: Optional[AILoadBalancer] = None
        
        # Performance tracking
        self.global_stats = {
            'total_requests': 0,
            'total_tokens': 0,
            'total_cost': 0.0,
            'avg_response_time': 0.0,
            'provider_usage': {},
            'error_count': 0
        }
        
        # Initialize from config or environment
        self._initialize_providers()
        
        logger.info(f"🤖 SampleMind AI Manager initialized with {len(self.providers)} providers")
    
    def _initialize_providers(self):
        """Initialize AI providers from config or environment"""
        
        # Try to load from config file first
        if self.config_path.exists():
            self._load_from_config()
        else:
            # Initialize from environment variables
            self._initialize_from_env()
        
        # Create load balancer
        if self.provider_configs:
            self.load_balancer = AILoadBalancer(list(self.provider_configs.values()))
    
    def _initialize_from_env(self):
        """Initialize providers from environment variables"""
        from dotenv import load_dotenv
        load_dotenv()
        
        # OpenAI Setup
        openai_key = os.getenv('OPENAI_API_KEY')
        if openai_key:
            try:
                from .openai_integration import OpenAIMusicProducer
                
                config = AIProviderConfig(
                    provider=AIProvider.OPENAI,
                    api_key=openai_key,
                    priority=1,
                    max_requests_per_minute=60,
                    cost_per_token=0.00003,  # GPT-5 pricing (estimated)
                    features=['comprehensive_analysis', 'production_coaching', 'fl_studio_optimization']
                )
                
                self.provider_configs[AIProvider.OPENAI] = config
                self.providers[AIProvider.OPENAI] = OpenAIMusicProducer(api_key=openai_key)
                logger.info("✅ OpenAI provider initialized")
                
            except Exception as e:
                logger.error(f"❌ Failed to initialize OpenAI: {e}")
        
        # Google AI Setup
        google_key = os.getenv('GOOGLE_AI_API_KEY')
        if google_key and GOOGLE_AI_AVAILABLE:
            try:
                from .google_ai_integration import GoogleAIMusicProducer
                
                config = AIProviderConfig(
                    provider=AIProvider.GOOGLE_AI,
                    api_key=google_key,
                    priority=2,
                    max_requests_per_minute=60,
                    cost_per_token=0.000015,  # Gemini pricing
                    features=['comprehensive_analysis', 'music_generation', 'creative_suggestions']
                )
                
                self.provider_configs[AIProvider.GOOGLE_AI] = config
                self.providers[AIProvider.GOOGLE_AI] = GoogleAIMusicProducer(api_key=google_key)
                logger.info("✅ Google AI provider initialized")
                
            except Exception as e:
                logger.error(f"❌ Failed to initialize Google AI: {e}")
        
        # Save configuration
        self._save_config()
    
    def _load_from_config(self):
        """Load provider configurations from JSON file"""
        try:
            with open(self.config_path, 'r') as f:
                config_data = json.load(f)
            
            for provider_data in config_data.get('providers', []):
                provider = AIProvider(provider_data['provider'])
                config = AIProviderConfig(**provider_data)
                self.provider_configs[provider] = config
                
                # Initialize actual provider instance
                if provider == AIProvider.OPENAI:
                    from .openai_integration import OpenAIMusicProducer
                    self.providers[provider] = OpenAIMusicProducer(api_key=config.api_key)
                elif provider == AIProvider.GOOGLE_AI and GOOGLE_AI_AVAILABLE:
                    from .google_ai_integration import GoogleAIMusicProducer
                    self.providers[provider] = GoogleAIMusicProducer(api_key=config.api_key)
            
            logger.info(f"📁 Loaded configuration for {len(self.provider_configs)} providers")
            
        except Exception as e:
            logger.error(f"❌ Failed to load config: {e}")
            self._initialize_from_env()
    
    def _save_config(self):
        """Save current configuration to JSON file"""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            config_data = {
                'providers': [
                    {
                        'provider': config.provider.value,
                        'enabled': config.enabled,
                        'priority': config.priority,
                        'max_requests_per_minute': config.max_requests_per_minute,
                        'cost_per_token': config.cost_per_token,
                        'features': config.features
                        # Note: API keys are not saved for security
                    }
                    for config in self.provider_configs.values()
                ]
            }
            
            with open(self.config_path, 'w') as f:
                json.dump(config_data, f, indent=2)
            
            logger.info(f"💾 Configuration saved to {self.config_path}")
            
        except Exception as e:
            logger.error(f"❌ Failed to save config: {e}")
    
    async def analyze_music(
        self,
        audio_features: Dict[str, Any],
        analysis_type: AnalysisType = AnalysisType.COMPREHENSIVE_ANALYSIS,
        preferred_provider: Optional[AIProvider] = None,
        user_context: Optional[Dict[str, Any]] = None,
        enable_fallback: bool = True
    ) -> UnifiedAnalysisResult:
        """
        Perform music analysis with intelligent provider selection
        
        Args:
            audio_features: Audio features from audio engine
            analysis_type: Type of analysis to perform
            preferred_provider: Preferred AI provider (optional)
            user_context: Additional context for analysis
            enable_fallback: Whether to try backup providers on failure
            
        Returns:
            UnifiedAnalysisResult with comprehensive analysis
        """
        start_time = time.time()
        
        if not self.load_balancer:
            raise RuntimeError("No AI providers configured")
        
        # Select provider
        selected_provider = self.load_balancer.select_provider(analysis_type, preferred_provider)
        
        try:
            # Perform analysis with selected provider
            result = await self._analyze_with_provider(
                selected_provider, audio_features, analysis_type, user_context
            )
            
            # Update success metrics
            self._update_provider_stats(selected_provider, result.tokens_used, 
                                      result.processing_time, True)
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Analysis failed with {selected_provider.value}: {e}")
            
            # Update failure metrics
            self._update_provider_stats(selected_provider, 0, time.time() - start_time, False)
            
            # Try fallback if enabled
            if enable_fallback:
                for provider in self.providers:
                    if provider != selected_provider:
                        try:
                            logger.info(f"🔄 Trying fallback provider: {provider.value}")
                            result = await self._analyze_with_provider(
                                provider, audio_features, analysis_type, user_context
                            )
                            self._update_provider_stats(provider, result.tokens_used,
                                                      result.processing_time, True)
                            return result
                        except Exception as fallback_error:
                            logger.error(f"❌ Fallback failed with {provider.value}: {fallback_error}")
                            continue
            
            # All providers failed
            raise RuntimeError(f"All AI providers failed. Last error: {e}")
    
    async def _analyze_with_provider(
        self,
        provider: AIProvider,
        audio_features: Dict[str, Any],
        analysis_type: AnalysisType,
        user_context: Optional[Dict[str, Any]]
    ) -> UnifiedAnalysisResult:
        """Perform analysis with specific provider"""
        
        if provider == AIProvider.OPENAI:
            # Convert to OpenAI analysis type
            openai_type = self._convert_to_openai_type(analysis_type)
            
            # Get OpenAI analysis
            openai_result = await self.providers[provider].analyze_music_comprehensive(
                audio_features, openai_type, user_context=user_context
            )
            
            # Convert to unified result
            return self._convert_openai_result(openai_result)
            
        elif provider == AIProvider.GOOGLE_AI and GOOGLE_AI_AVAILABLE:
            # Convert to Google AI analysis type
            google_type = self._convert_to_google_type(analysis_type)
            
            # Get Google AI analysis
            google_result = await self.providers[provider].analyze_music_comprehensive(
                audio_features, google_type, custom_prompt=None
            )
            
            # Convert to unified result
            return self._convert_google_result(google_result)
        
        else:
            raise ValueError(f"Provider {provider} not supported or available")
    
    def _convert_to_openai_type(self, analysis_type: AnalysisType) -> OpenAIMusicAnalysisType:
        """Convert unified analysis type to OpenAI type"""
        mapping = {
            AnalysisType.QUICK_ANALYSIS: OpenAIMusicAnalysisType.QUICK_ANALYSIS,
            AnalysisType.COMPREHENSIVE_ANALYSIS: OpenAIMusicAnalysisType.COMPREHENSIVE_ANALYSIS,
            AnalysisType.PRODUCTION_COACHING: OpenAIMusicAnalysisType.PRODUCTION_COACHING,
            AnalysisType.CREATIVE_SUGGESTIONS: OpenAIMusicAnalysisType.CREATIVE_SUGGESTIONS,
            AnalysisType.FL_STUDIO_OPTIMIZATION: OpenAIMusicAnalysisType.FL_STUDIO_OPTIMIZATION,
            AnalysisType.MIXING_MASTERING: OpenAIMusicAnalysisType.MIXING_MASTERING,
        }
        return mapping.get(analysis_type, OpenAIMusicAnalysisType.COMPREHENSIVE_ANALYSIS)
    
    def _convert_to_google_type(self, analysis_type: AnalysisType):
        """Convert unified analysis type to Google AI type"""
        if not GOOGLE_AI_AVAILABLE:
            return None
        
        mapping = {
            AnalysisType.QUICK_ANALYSIS: GoogleMusicAnalysisType.QUICK_ANALYSIS,
            AnalysisType.COMPREHENSIVE_ANALYSIS: GoogleMusicAnalysisType.COMPREHENSIVE_ANALYSIS,
            AnalysisType.CREATIVE_SUGGESTIONS: GoogleMusicAnalysisType.CREATIVE_ENHANCEMENT,
            # Add more mappings as needed
        }
        return mapping.get(analysis_type, GoogleMusicAnalysisType.COMPREHENSIVE_ANALYSIS)
    
    def _convert_openai_result(self, openai_result: OpenAIMusicAnalysis) -> UnifiedAnalysisResult:
        """Convert OpenAI result to unified format"""
        return UnifiedAnalysisResult(
            provider=AIProvider.OPENAI,
            analysis_type=AnalysisType.COMPREHENSIVE_ANALYSIS,  # Map back from OpenAI type
            model_used=openai_result.model_used,
            timestamp=openai_result.timestamp,
            summary=openai_result.summary,
            detailed_analysis=openai_result.detailed_analysis,
            production_tips=openai_result.production_tips,
            fl_studio_recommendations=openai_result.fl_studio_recommendations,
            effect_suggestions=openai_result.effect_suggestions,
            creative_ideas=openai_result.creative_ideas,
            arrangement_suggestions=openai_result.arrangement_suggestions,
            harmonic_analysis=openai_result.harmonic_analysis,
            rhythmic_analysis=openai_result.rhythmic_analysis,
            spectral_analysis=openai_result.spectral_analysis,
            creativity_score=openai_result.creativity_score,
            production_quality_score=openai_result.production_quality_score,
            commercial_potential_score=openai_result.commercial_potential_score,
            tokens_used=openai_result.tokens_used,
            processing_time=openai_result.processing_time,
            confidence_score=openai_result.confidence_score,
            cost_estimate=openai_result.tokens_used * self.provider_configs[AIProvider.OPENAI].cost_per_token
        )
    
    def _convert_google_result(self, google_result) -> UnifiedAnalysisResult:
        """Convert Google AI result to unified format"""
        if not GOOGLE_AI_AVAILABLE:
            raise RuntimeError("Google AI not available")
        
        # Convert Google AI result to unified format
        # This would need to be implemented based on Google AI integration structure
        return UnifiedAnalysisResult(
            provider=AIProvider.GOOGLE_AI,
            analysis_type=AnalysisType.COMPREHENSIVE_ANALYSIS,
            model_used=google_result.model_used,
            # Map other fields...
        )
    
    def _update_provider_stats(
        self, 
        provider: AIProvider, 
        tokens_used: int, 
        response_time: float, 
        success: bool
    ):
        """Update provider performance statistics"""
        config = self.provider_configs[provider]
        
        config.total_requests += 1
        config.total_tokens += tokens_used
        
        # Update running average response time
        prev_avg = config.avg_response_time
        prev_count = config.total_requests - 1
        if prev_count > 0:
            config.avg_response_time = (prev_avg * prev_count + response_time) / config.total_requests
        else:
            config.avg_response_time = response_time
        
        # Update success rate
        if success:
            config.success_rate = (config.success_rate * prev_count + 1.0) / config.total_requests
        else:
            config.success_rate = (config.success_rate * prev_count) / config.total_requests
            self.global_stats['error_count'] += 1
        
        # Update global stats
        self.global_stats['total_requests'] += 1
        self.global_stats['total_tokens'] += tokens_used
        self.global_stats['total_cost'] += tokens_used * config.cost_per_token
        
        if provider.value not in self.global_stats['provider_usage']:
            self.global_stats['provider_usage'][provider.value] = 0
        self.global_stats['provider_usage'][provider.value] += 1
    
    def get_provider_status(self) -> Dict[str, Any]:
        """Get status of all providers"""
        status = {}
        for provider, config in self.provider_configs.items():
            status[provider.value] = {
                'enabled': config.enabled,
                'priority': config.priority,
                'total_requests': config.total_requests,
                'total_tokens': config.total_tokens,
                'avg_response_time': config.avg_response_time,
                'success_rate': config.success_rate,
                'last_error': config.last_error,
                'estimated_cost': config.total_tokens * config.cost_per_token
            }
        return status
    
    def get_global_stats(self) -> Dict[str, Any]:
        """Get global usage statistics"""
        return {
            **self.global_stats,
            'providers_configured': len(self.providers),
            'providers_enabled': sum(1 for c in self.provider_configs.values() if c.enabled)
        }
    
    def set_provider_enabled(self, provider: AIProvider, enabled: bool):
        """Enable or disable a provider"""
        if provider in self.provider_configs:
            self.provider_configs[provider].enabled = enabled
            logger.info(f"🔧 Provider {provider.value} {'enabled' if enabled else 'disabled'}")
            self._save_config()
    
    def set_provider_priority(self, provider: AIProvider, priority: int):
        """Set provider priority (lower = higher priority)"""
        if provider in self.provider_configs:
            self.provider_configs[provider].priority = priority
            logger.info(f"🔧 Provider {provider.value} priority set to {priority}")
            self._save_config()
    
    async def close(self):
        """Clean up all provider connections"""
        for provider in self.providers.values():
            if hasattr(provider, 'close'):
                await provider.close()
        logger.info("🔴 AI Manager closed")


# Utility functions
def create_ai_manager_from_env() -> SampleMindAIManager:
    """Create AI manager with environment configuration"""
    return SampleMindAIManager()


# Example usage
if __name__ == "__main__":
    async def example_usage():
        try:
            # Create AI manager
            ai_manager = SampleMindAIManager()
            
            # Example audio features
            sample_features = {
                'tempo': 128.0,
                'key': 'C',
                'mode': 'major',
                'duration': 180.0,
                'sample_rate': 44100,
                'spectral_centroid': [2500.0] * 100,
                'rms_energy': [0.5] * 100
            }
            
            # Perform analysis
            result = await ai_manager.analyze_music(
                sample_features,
                AnalysisType.FL_STUDIO_OPTIMIZATION
            )
            
            print(f"✅ Analysis complete with {result.provider.value}")
            print(f"🎯 Summary: {result.summary[:100]}...")
            
            # Get statistics
            stats = ai_manager.get_global_stats()
            print(f"📊 Global Stats: {stats}")
            
            await ai_manager.close()
            
        except Exception as e:
            logger.error(f"❌ Example failed: {e}")
    
    # Run example
    # asyncio.run(example_usage())
    logger.info("🤖 AI Manager Module Ready!")