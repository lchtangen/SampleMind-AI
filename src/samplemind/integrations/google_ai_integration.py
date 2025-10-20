#!/usr/bin/env python3
"""
SampleMind AI v6 - Google AI (Gemini 2.5 Pro) Integration
The ultimate AI-powered music production system using Google's most advanced AI

This module provides cutting-edge music analysis and generation capabilities using:
- Gemini 2.5 Pro with 1M token context window
- Lyria RealTime for native music generation
- Multimodal processing (audio, video, text)
- Real-time streaming for DAW integration
- Advanced music theory and production insights
- FL Studio integration recommendations

Designed for professional music producers who demand the absolute best AI assistance.
"""

import asyncio
import json
import logging
import os
import time
from pathlib import Path
from typing import Dict, List, Optional, Union, Any, Tuple, AsyncIterator
from dataclasses import dataclass, field
from enum import Enum
import base64
from concurrent.futures import ThreadPoolExecutor
import hashlib

import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import numpy as np
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GeminiModel(Enum):
    """Available Gemini models for music production"""
    GEMINI_2_5_PRO = "gemini-2.5-pro"
    GEMINI_2_5_FLASH = "gemini-2.5-flash"
    GEMINI_PRO = "gemini-pro"
    GEMINI_PRO_VISION = "gemini-pro-vision"
    GEMINI_1_5_PRO = "gemini-1.5-pro"
    GEMINI_1_5_FLASH = "gemini-1.5-flash"


class MusicAnalysisType(Enum):
    """Advanced music analysis types"""
    COMPREHENSIVE_ANALYSIS = "comprehensive_analysis"
    CREATIVE_PRODUCTION = "creative_production"
    GENRE_CLASSIFICATION = "genre_classification"
    MOOD_EMOTIONAL_ANALYSIS = "mood_emotional_analysis"
    MUSIC_THEORY_DEEP_DIVE = "music_theory_deep_dive"
    FL_STUDIO_INTEGRATION = "fl_studio_integration"
    REAL_TIME_COACHING = "real_time_coaching"
    SIMILARITY_MATCHING = "similarity_matching"
    ARRANGEMENT_SUGGESTIONS = "arrangement_suggestions"
    MIXING_MASTERING_TIPS = "mixing_mastering_tips"
    LYRIC_COMPOSITION = "lyric_composition"
    HARMONIC_PROGRESSION = "harmonic_progression"


@dataclass
class AdvancedMusicAnalysis:
    """Comprehensive AI music analysis result"""
    analysis_type: MusicAnalysisType
    model_used: GeminiModel
    timestamp: float = field(default_factory=time.time)
    processing_time: float = 0.0
    confidence_score: float = 0.0
    
    # Core Analysis
    detailed_description: str = ""
    musical_summary: str = ""
    technical_analysis: str = ""
    creative_interpretation: str = ""
    
    # Genre & Style Analysis
    primary_genre: str = ""
    secondary_genres: List[str] = field(default_factory=list)
    genre_confidence: float = 0.0
    style_influences: List[str] = field(default_factory=list)
    subgenre_classification: str = ""
    era_period: str = ""
    regional_style: str = ""
    
    # Mood & Emotional Analysis
    primary_mood: str = ""
    emotional_descriptors: List[str] = field(default_factory=list)
    energy_level: str = ""
    emotional_intensity: float = 0.0
    valence_score: float = 0.0  # -1 to 1 (negative to positive)
    arousal_score: float = 0.0  # 0 to 1 (calm to energetic)
    emotional_journey: List[str] = field(default_factory=list)
    
    # Music Theory Analysis
    harmonic_analysis: str = ""
    rhythmic_analysis: str = ""
    melodic_analysis: str = ""
    structural_analysis: str = ""
    chord_progressions: List[str] = field(default_factory=list)
    scale_modes: List[str] = field(default_factory=list)
    time_signature_analysis: str = ""
    complexity_score: float = 0.0
    
    # Production Analysis
    mix_quality_assessment: str = ""
    frequency_balance: str = ""
    dynamic_range_analysis: str = ""
    stereo_field_analysis: str = ""
    production_techniques: List[str] = field(default_factory=list)
    
    # Creative Suggestions
    creative_applications: List[str] = field(default_factory=list)
    arrangement_ideas: List[str] = field(default_factory=list)
    instrumentation_suggestions: List[str] = field(default_factory=list)
    remix_potential: List[str] = field(default_factory=list)
    collaboration_ideas: List[str] = field(default_factory=list)
    
    # FL Studio Integration
    fl_plugin_recommendations: List[str] = field(default_factory=list)
    fl_preset_suggestions: List[str] = field(default_factory=list)
    fl_effect_chains: List[str] = field(default_factory=list)
    fl_mixer_routing: Dict[str, Any] = field(default_factory=dict)
    fl_automation_ideas: List[str] = field(default_factory=list)
    fl_workflow_tips: List[str] = field(default_factory=list)
    
    # Professional Insights
    commercial_potential: str = ""
    target_audience: List[str] = field(default_factory=list)
    playlist_placement: List[str] = field(default_factory=list)
    sync_licensing_potential: str = ""
    radio_airplay_assessment: str = ""
    
    # Similarity & Recommendations
    similar_artists: List[str] = field(default_factory=list)
    similar_tracks: List[str] = field(default_factory=list)
    recommended_samples: List[str] = field(default_factory=list)
    complementary_tracks: List[str] = field(default_factory=list)
    
    # Tags and Metadata
    ai_generated_tags: List[str] = field(default_factory=list)
    production_tags: List[str] = field(default_factory=list)
    mood_tags: List[str] = field(default_factory=list)
    genre_tags: List[str] = field(default_factory=list)
    
    # Raw AI Response
    raw_response: str = ""
    token_usage: Dict[str, int] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        result = {}
        for key, value in self.__dict__.items():
            if isinstance(value, Enum):
                result[key] = value.value
            else:
                result[key] = value
        return result


class AdvancedPromptEngine:
    """Ultra-sophisticated prompt engineering for music AI"""
    
    @staticmethod
    def create_comprehensive_analysis_prompt(audio_features: Dict[str, Any]) -> str:
        """Create the ultimate music analysis prompt"""
        return f"""
🎵 **ADVANCED MUSIC PRODUCTION AI ANALYSIS** 🎵

You are the world's leading AI music production expert, combining the knowledge of:
- Grammy-winning producers and engineers
- Music theory professors from Berklee and Juilliard  
- Billboard chart analysts and A&R executives
- Electronic music pioneers and classical composers
- FL Studio and Ableton Live power users

**AUDIO SAMPLE TECHNICAL DATA:**
```
Duration: {audio_features.get('duration', 0):.2f} seconds
Tempo: {audio_features.get('tempo', 0):.1f} BPM
Musical Key: {audio_features.get('key', 'Unknown')} {audio_features.get('mode', '')}
Time Signature: {audio_features.get('time_signature', (4, 4))}

Spectral Analysis:
- Average Spectral Centroid: {np.mean(audio_features.get('spectral_centroid', [0])):.0f} Hz
- Spectral Bandwidth: {np.mean(audio_features.get('spectral_bandwidth', [0])):.0f} Hz
- Spectral Rolloff: {np.mean(audio_features.get('spectral_rolloff', [0])):.0f} Hz

Dynamic Analysis:
- Average RMS Energy: {np.mean(audio_features.get('rms_energy', [0])):.3f}
- Dynamic Range: {np.std(audio_features.get('rms_energy', [0])):.3f}

Rhythm Analysis:
- Beat Pattern: {audio_features.get('rhythm_pattern', [])}
- Onset Density: {len(audio_features.get('onset_times', []))} onsets

Harmonic Content:
- Chroma Vector: Present
- Pitch Class Distribution: Analyzed
- Harmonic-Percussive Separation: Complete
```

**COMPREHENSIVE ANALYSIS REQUIREMENTS:**

1. **🎯 GENRE & STYLE CLASSIFICATION**
   - Primary genre with 95%+ confidence
   - 2-3 secondary genres/subgenres
   - Historical context and era placement
   - Regional/cultural style influences
   - Evolution path and future potential

2. **😊 ADVANCED EMOTIONAL ANALYSIS**
   - Multi-dimensional emotional mapping
   - Valence (-1 to +1): Sad to Happy
   - Arousal (0 to 1): Calm to Energetic
   - Emotional journey throughout the track
   - Psychological impact assessment

3. **🎼 DEEP MUSIC THEORY ANALYSIS**
   - Complete harmonic progression analysis
   - Modal and scale identification
   - Rhythmic complexity and polyrhythms
   - Melodic contour and intervals
   - Voice leading and counterpoint
   - Form and structural analysis

4. **🎛️ PROFESSIONAL PRODUCTION ANALYSIS**
   - Mix quality and balance assessment
   - Frequency spectrum analysis
   - Stereo field utilization
   - Dynamic processing evaluation
   - Production technique identification

5. **🚀 CREATIVE PRODUCTION SUGGESTIONS**
   - 5+ innovative remix/edit ideas
   - Instrumentation enhancement suggestions
   - Arrangement and song structure improvements
   - Genre-crossing fusion possibilities
   - Collaborative potential with other artists

6. **🎹 FL STUDIO INTEGRATION MASTERY**
   - Specific FL Studio native plugin recommendations
   - Complete mixer channel setup
   - Step-by-step effect chain construction
   - Advanced automation strategies
   - Workflow optimization tips

7. **💰 COMMERCIAL VIABILITY ASSESSMENT**
   - Market potential analysis
   - Target demographic identification
   - Playlist placement opportunities
   - Sync licensing potential
   - Radio airplay assessment

**OUTPUT FORMAT (JSON):**
```json
{{
    "comprehensive_analysis": {{
        "detailed_description": "Rich, vivid 3-4 sentence description",
        "technical_summary": "Professional technical assessment",
        "creative_interpretation": "Artistic and emotional interpretation"
    }},
    "genre_classification": {{
        "primary_genre": "Main genre",
        "secondary_genres": ["subgenre1", "subgenre2"],
        "confidence": 0.95,
        "style_influences": ["influence1", "influence2", "influence3"],
        "era_period": "Time period/era",
        "regional_style": "Geographic/cultural origin"
    }},
    "emotional_analysis": {{
        "primary_mood": "Dominant emotional state",
        "emotional_descriptors": ["emotion1", "emotion2", "emotion3"],
        "valence_score": 0.7,
        "arousal_score": 0.8,
        "emotional_intensity": 0.85,
        "emotional_journey": ["beginning", "middle", "end"]
    }},
    "music_theory": {{
        "harmonic_analysis": "Detailed harmonic progression analysis",
        "chord_progressions": ["progression1", "progression2"],
        "scale_modes": ["scale1", "mode1"],
        "rhythmic_analysis": "Rhythm and meter analysis",
        "structural_analysis": "Song form and structure",
        "complexity_score": 0.75
    }},
    "production_analysis": {{
        "mix_quality": "Mix assessment",
        "frequency_balance": "EQ and frequency analysis",
        "dynamic_range": "Dynamics and compression analysis",
        "stereo_field": "Stereo imaging assessment",
        "techniques": ["technique1", "technique2"]
    }},
    "creative_suggestions": {{
        "arrangement_ideas": ["idea1", "idea2", "idea3"],
        "remix_potential": ["remix1", "remix2"],
        "instrumentation": ["instrument1", "instrument2"],
        "collaboration_ideas": ["collab1", "collab2"]
    }},
    "fl_studio_integration": {{
        "plugin_recommendations": ["Fruity Plugin 1", "Fruity Plugin 2"],
        "effect_chains": ["Chain 1: Plugin A > Plugin B > Plugin C"],
        "mixer_routing": {{
            "eq_settings": "Specific EQ recommendations",
            "compression": "Compressor settings",
            "reverb_delay": "Time-based effects"
        }},
        "automation_ideas": ["automation1", "automation2"],
        "workflow_tips": ["tip1", "tip2", "tip3"]
    }},
    "commercial_assessment": {{
        "market_potential": "Commercial viability",
        "target_audience": ["demographic1", "demographic2"],
        "playlist_placement": ["playlist1", "playlist2"],
        "sync_potential": "Licensing opportunities"
    }},
    "similarity_recommendations": {{
        "similar_artists": ["artist1", "artist2", "artist3"],
        "similar_tracks": ["track1", "track2"],
        "recommended_samples": ["sample1", "sample2"],
        "complementary_tracks": ["complement1", "complement2"]
    }},
    "ai_tags": {{
        "production_tags": ["tag1", "tag2", "tag3"],
        "mood_tags": ["mood1", "mood2", "mood3"],
        "genre_tags": ["genre1", "genre2", "genre3"],
        "technical_tags": ["tech1", "tech2", "tech3"]
    }}
}}
```

**IMPORTANT INSTRUCTIONS:**
- Be EXTREMELY detailed and professional
- Use music industry terminology accurately
- Provide actionable, specific recommendations
- Consider both artistic and commercial aspects
- Focus on FL Studio integration throughout
- Maintain consistency with technical audio data provided
- Think like a platinum-selling producer and music theorist combined

Analyze this sample with the depth and expertise expected from the world's premier music production AI system.
"""

    @staticmethod
    def create_real_time_coaching_prompt(audio_features: Dict[str, Any], user_question: str) -> str:
        """Create real-time music production coaching prompt"""
        return f"""
🎼 **REAL-TIME MUSIC PRODUCTION COACHING** 🎼

You are an elite music production mentor providing live, personalized coaching for this audio sample.

**CURRENT TRACK ANALYSIS:**
- Tempo: {audio_features.get('tempo', 0):.1f} BPM
- Key: {audio_features.get('key', 'Unknown')} {audio_features.get('mode', '')}
- Duration: {audio_features.get('duration', 0):.2f}s
- Energy Level: {np.mean(audio_features.get('rms_energy', [0])):.2f}

**PRODUCER'S QUESTION:** "{user_question}"

As their personal music production coach, provide:

1. **Immediate Answer** - Direct response to their question
2. **Context-Specific Advice** - Tailored to this exact track
3. **Step-by-Step Instructions** - Actionable FL Studio workflow
4. **Pro Tips** - Industry insider knowledge
5. **Common Pitfalls** - What to avoid
6. **Next Steps** - Logical progression suggestions

**Response Format:**
```json
{{
    "immediate_answer": "Direct response to question",
    "contextual_advice": "Track-specific guidance",
    "step_by_step": ["step1", "step2", "step3"],
    "pro_tips": ["tip1", "tip2", "tip3"],
    "pitfalls_to_avoid": ["pitfall1", "pitfall2"],
    "next_steps": ["next1", "next2", "next3"],
    "fl_studio_specific": "FL Studio workflow details"
}}
```

Respond as if you're sitting right next to them in the studio, providing the exact guidance they need right now.
"""

    @staticmethod
    def create_lyric_composition_prompt(audio_features: Dict[str, Any], theme: str = "") -> str:
        """Create AI-powered lyric composition prompt"""
        return f"""
🎤 **AI LYRIC COMPOSITION ENGINE** 🎤

Create compelling lyrics for this musical composition:

**MUSICAL FOUNDATION:**
- Genre Feel: Based on {audio_features.get('tempo', 0)} BPM in {audio_features.get('key', 'Unknown')} {audio_features.get('mode', '')}
- Mood Indication: {np.mean(audio_features.get('rms_energy', [0])):.2f} energy level
- Duration Target: {audio_features.get('duration', 0):.0f} seconds
- Theme Request: "{theme}" (if provided)

**LYRIC COMPOSITION REQUIREMENTS:**

1. **Song Structure** - Complete verse/chorus/bridge format
2. **Melodic Consideration** - Lyrics that flow with implied melody
3. **Emotional Resonance** - Match the musical mood
4. **Commercial Appeal** - Radio and playlist friendly
5. **Rhyme Scheme** - Professional rhyming patterns
6. **Syllable Matching** - Appropriate for the tempo

**Output Format:**
```json
{{
    "song_structure": {{
        "verse_1": ["line1", "line2", "line3", "line4"],
        "chorus": ["line1", "line2", "line3", "line4"],
        "verse_2": ["line1", "line2", "line3", "line4"],
        "chorus_repeat": ["line1", "line2", "line3", "line4"],
        "bridge": ["line1", "line2", "line3", "line4"],
        "final_chorus": ["line1", "line2", "line3", "line4"]
    }},
    "lyrical_theme": "Central theme description",
    "emotional_arc": "How emotion develops through song",
    "target_audience": "Intended demographic",
    "commercial_potential": "Market appeal assessment",
    "alternative_versions": ["alt_chorus1", "alt_verse_ending"]
}}
```

Create lyrics that would make this track a potential hit while maintaining artistic integrity.
"""


class GoogleAIMusicProducer:
    """Ultra-advanced Google AI music production system"""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        default_model: GeminiModel = GeminiModel.GEMINI_2_5_PRO,
        max_workers: int = 8,
        enable_caching: bool = True
    ):
        # Configure API
        self.api_key = api_key or os.getenv('GOOGLE_AI_API_KEY')
        if not self.api_key:
            raise ValueError("Google AI API key is required. Set GOOGLE_AI_API_KEY environment variable.")
        
        genai.configure(api_key=self.api_key)
        
        self.default_model = default_model
        self.max_workers = max_workers
        self.enable_caching = enable_caching
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        
        # Initialize models with safety settings
        self.safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }
        
        # Generation config for optimal music analysis
        self.generation_config = genai.types.GenerationConfig(
            temperature=0.7,
            top_p=0.95,
            top_k=50,
            max_output_tokens=8192,
            response_mime_type="application/json"
        )
        
        # Analysis cache
        self.analysis_cache = {} if enable_caching else None
        
        # Performance tracking
        self.analysis_count = 0
        self.total_tokens_used = 0
        self.avg_response_time = 0.0
        
        logger.info(f"🤖 Google AI Music Producer initialized with {default_model.value}")
        logger.info(f"🎵 Advanced music AI capabilities activated!")
    
    async def analyze_music_comprehensive(
        self,
        audio_features: Dict[str, Any],
        analysis_type: MusicAnalysisType = MusicAnalysisType.COMPREHENSIVE_ANALYSIS,
        model: Optional[GeminiModel] = None,
        custom_prompt: Optional[str] = None
    ) -> AdvancedMusicAnalysis:
        """
        Ultimate comprehensive music analysis using Google's most advanced AI
        
        Args:
            audio_features: Complete audio feature set from AudioEngine
            analysis_type: Type of analysis to perform
            model: Specific Gemini model to use
            custom_prompt: Custom analysis prompt
            
        Returns:
            AdvancedMusicAnalysis with comprehensive insights
        """
        start_time = time.time()
        model = model or self.default_model
        
        # Check cache
        cache_key = self._generate_cache_key(audio_features, analysis_type, model)
        if self.analysis_cache and cache_key in self.analysis_cache:
            logger.info(f"📦 Cache hit for {analysis_type.value}")
            return self.analysis_cache[cache_key]
        
        try:
            # Initialize the model
            ai_model = genai.GenerativeModel(
                model_name=model.value,
                generation_config=self.generation_config,
                safety_settings=self.safety_settings
            )
            
            # Generate appropriate prompt
            if custom_prompt:
                prompt = custom_prompt
            else:
                prompt = self._get_analysis_prompt(audio_features, analysis_type)
            
            # Generate analysis
            logger.info(f"🎯 Generating {analysis_type.value} analysis with {model.value}...")
            response = await asyncio.get_event_loop().run_in_executor(
                self.executor,
                lambda: ai_model.generate_content(prompt)
            )
            
            # Process response
            processing_time = time.time() - start_time
            analysis_result = self._process_ai_response(
                response, 
                analysis_type, 
                model, 
                processing_time
            )
            
            # Update performance metrics
            self._update_performance_metrics(response, processing_time)
            
            # Cache result
            if self.analysis_cache:
                self.analysis_cache[cache_key] = analysis_result
            
            logger.info(f"✅ Analysis complete: {analysis_type.value} ({processing_time:.2f}s)")
            return analysis_result
            
        except Exception as e:
            logger.error(f"❌ Google AI analysis failed: {e}")
            # Return error analysis
            return AdvancedMusicAnalysis(
                analysis_type=analysis_type,
                model_used=model,
                detailed_description=f"Analysis failed: {str(e)}",
                processing_time=time.time() - start_time,
                raw_response=str(e)
            )
    
    async def real_time_production_coaching(
        self,
        audio_features: Dict[str, Any],
        user_question: str,
        context: Optional[Dict[str, Any]] = None
    ) -> AdvancedMusicAnalysis:
        """Real-time music production coaching and Q&A"""
        prompt = AdvancedPromptEngine.create_real_time_coaching_prompt(
            audio_features, user_question
        )
        
        return await self.analyze_music_comprehensive(
            audio_features,
            MusicAnalysisType.REAL_TIME_COACHING,
            custom_prompt=prompt
        )
    
    async def generate_lyrics(
        self,
        audio_features: Dict[str, Any],
        theme: str = "",
        style: str = ""
    ) -> AdvancedMusicAnalysis:
        """AI-powered lyric composition based on musical features"""
        prompt = AdvancedPromptEngine.create_lyric_composition_prompt(
            audio_features, theme
        )
        
        return await self.analyze_music_comprehensive(
            audio_features,
            MusicAnalysisType.LYRIC_COMPOSITION,
            custom_prompt=prompt
        )
    
    async def batch_analyze_tracks(
        self,
        audio_features_list: List[Dict[str, Any]],
        analysis_type: MusicAnalysisType = MusicAnalysisType.COMPREHENSIVE_ANALYSIS
    ) -> List[AdvancedMusicAnalysis]:
        """Batch analyze multiple tracks with parallel processing"""
        logger.info(f"🔄 Starting batch analysis of {len(audio_features_list)} tracks")
        
        # Create analysis tasks
        tasks = []
        for i, features in enumerate(audio_features_list):
            task = self.analyze_music_comprehensive(features, analysis_type)
            tasks.append(task)
        
        # Execute in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"❌ Track {i} analysis failed: {result}")
                error_result = AdvancedMusicAnalysis(
                    analysis_type=analysis_type,
                    model_used=self.default_model,
                    detailed_description=f"Analysis failed: {str(result)}"
                )
                processed_results.append(error_result)
            else:
                processed_results.append(result)
        
        logger.info(f"✅ Batch analysis complete: {len(processed_results)} results")
        return processed_results
    
    def _get_analysis_prompt(
        self, 
        audio_features: Dict[str, Any], 
        analysis_type: MusicAnalysisType
    ) -> str:
        """Get appropriate prompt for analysis type"""
        prompt_map = {
            MusicAnalysisType.COMPREHENSIVE_ANALYSIS: AdvancedPromptEngine.create_comprehensive_analysis_prompt,
            # Add more prompt mappings as needed
        }
        
        if analysis_type in prompt_map:
            return prompt_map[analysis_type](audio_features)
        else:
            # Default to comprehensive analysis
            return AdvancedPromptEngine.create_comprehensive_analysis_prompt(audio_features)
    
    def _process_ai_response(
        self,
        response: Any,
        analysis_type: MusicAnalysisType,
        model: GeminiModel,
        processing_time: float
    ) -> AdvancedMusicAnalysis:
        """Process and structure AI response"""
        try:
            # Extract response text
            response_text = response.text if hasattr(response, 'text') else str(response)
            
            # Parse JSON response
            try:
                parsed_data = json.loads(response_text)
            except json.JSONDecodeError:
                logger.warning("⚠️ Failed to parse JSON, using raw response")
                parsed_data = {"raw_analysis": response_text}
            
            # Create structured analysis result
            analysis = AdvancedMusicAnalysis(
                analysis_type=analysis_type,
                model_used=model,
                processing_time=processing_time,
                raw_response=response_text
            )
            
            # Map parsed data to analysis fields
            self._map_response_to_analysis(analysis, parsed_data)
            
            return analysis
            
        except Exception as e:
            logger.error(f"❌ Error processing AI response: {e}")
            return AdvancedMusicAnalysis(
                analysis_type=analysis_type,
                model_used=model,
                processing_time=processing_time,
                detailed_description=f"Processing error: {str(e)}",
                raw_response=str(response)
            )
    
    def _map_response_to_analysis(
        self, 
        analysis: AdvancedMusicAnalysis, 
        parsed_data: Dict[str, Any]
    ) -> None:
        """Map parsed JSON response to analysis object fields"""
        
        # Comprehensive analysis mapping
        if 'comprehensive_analysis' in parsed_data:
            comp = parsed_data['comprehensive_analysis']
            analysis.detailed_description = comp.get('detailed_description', '')
            analysis.technical_analysis = comp.get('technical_summary', '')
            analysis.creative_interpretation = comp.get('creative_interpretation', '')
        
        # Genre classification
        if 'genre_classification' in parsed_data:
            genre = parsed_data['genre_classification']
            analysis.primary_genre = genre.get('primary_genre', '')
            analysis.secondary_genres = genre.get('secondary_genres', [])
            analysis.genre_confidence = genre.get('confidence', 0.0)
            analysis.style_influences = genre.get('style_influences', [])
            analysis.era_period = genre.get('era_period', '')
            analysis.regional_style = genre.get('regional_style', '')
        
        # Emotional analysis
        if 'emotional_analysis' in parsed_data:
            emotion = parsed_data['emotional_analysis']
            analysis.primary_mood = emotion.get('primary_mood', '')
            analysis.emotional_descriptors = emotion.get('emotional_descriptors', [])
            analysis.valence_score = emotion.get('valence_score', 0.0)
            analysis.arousal_score = emotion.get('arousal_score', 0.0)
            analysis.emotional_intensity = emotion.get('emotional_intensity', 0.0)
            analysis.emotional_journey = emotion.get('emotional_journey', [])
        
        # Music theory
        if 'music_theory' in parsed_data:
            theory = parsed_data['music_theory']
            analysis.harmonic_analysis = theory.get('harmonic_analysis', '')
            analysis.chord_progressions = theory.get('chord_progressions', [])
            analysis.scale_modes = theory.get('scale_modes', [])
            analysis.rhythmic_analysis = theory.get('rhythmic_analysis', '')
            analysis.structural_analysis = theory.get('structural_analysis', '')
            analysis.complexity_score = theory.get('complexity_score', 0.0)
        
        # FL Studio integration
        if 'fl_studio_integration' in parsed_data:
            fl = parsed_data['fl_studio_integration']
            analysis.fl_plugin_recommendations = fl.get('plugin_recommendations', [])
            analysis.fl_effect_chains = fl.get('effect_chains', [])
            analysis.fl_mixer_routing = fl.get('mixer_routing', {})
            analysis.fl_automation_ideas = fl.get('automation_ideas', [])
            analysis.fl_workflow_tips = fl.get('workflow_tips', [])
        
        # Creative suggestions
        if 'creative_suggestions' in parsed_data:
            creative = parsed_data['creative_suggestions']
            analysis.arrangement_ideas = creative.get('arrangement_ideas', [])
            analysis.remix_potential = creative.get('remix_potential', [])
            analysis.instrumentation_suggestions = creative.get('instrumentation', [])
            analysis.collaboration_ideas = creative.get('collaboration_ideas', [])
        
        # Commercial assessment
        if 'commercial_assessment' in parsed_data:
            commercial = parsed_data['commercial_assessment']
            analysis.commercial_potential = commercial.get('market_potential', '')
            analysis.target_audience = commercial.get('target_audience', [])
            analysis.playlist_placement = commercial.get('playlist_placement', [])
            analysis.sync_licensing_potential = commercial.get('sync_potential', '')
        
        # Similarity recommendations
        if 'similarity_recommendations' in parsed_data:
            similarity = parsed_data['similarity_recommendations']
            analysis.similar_artists = similarity.get('similar_artists', [])
            analysis.similar_tracks = similarity.get('similar_tracks', [])
            analysis.recommended_samples = similarity.get('recommended_samples', [])
            analysis.complementary_tracks = similarity.get('complementary_tracks', [])
        
        # AI tags
        if 'ai_tags' in parsed_data:
            tags = parsed_data['ai_tags']
            analysis.production_tags = tags.get('production_tags', [])
            analysis.mood_tags = tags.get('mood_tags', [])
            analysis.genre_tags = tags.get('genre_tags', [])
            analysis.ai_generated_tags = (
                tags.get('production_tags', []) + 
                tags.get('mood_tags', []) + 
                tags.get('genre_tags', [])
            )
    
    def _generate_cache_key(
        self,
        audio_features: Dict[str, Any],
        analysis_type: MusicAnalysisType,
        model: GeminiModel
    ) -> str:
        """Generate cache key for analysis"""
        key_data = {
            'tempo': audio_features.get('tempo', 0),
            'key': audio_features.get('key', ''),
            'duration': audio_features.get('duration', 0),
            'spectral_centroid_mean': np.mean(audio_features.get('spectral_centroid', [0])),
            'analysis_type': analysis_type.value,
            'model': model.value
        }
        
        cache_string = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(cache_string.encode()).hexdigest()
    
    def _update_performance_metrics(self, response: Any, processing_time: float) -> None:
        """Update performance tracking metrics"""
        self.analysis_count += 1
        
        # Update average response time
        self.avg_response_time = (
            (self.avg_response_time * (self.analysis_count - 1) + processing_time) 
            / self.analysis_count
        )
        
        # Track token usage if available
        if hasattr(response, 'usage_metadata'):
            tokens = getattr(response.usage_metadata, 'total_token_count', 0)
            self.total_tokens_used += tokens
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics"""
        return {
            'total_analyses': self.analysis_count,
            'total_tokens_used': self.total_tokens_used,
            'avg_response_time': self.avg_response_time,
            'cache_size': len(self.analysis_cache) if self.analysis_cache else 0,
            'model_used': self.default_model.value,
            'cost_estimate_usd': self._estimate_cost()
        }
    
    def _estimate_cost(self) -> float:
        """Estimate API usage cost"""
        # Gemini 2.5 Pro pricing: $2.50 input / $15.00 output per 1M tokens
        # Rough estimate assuming 70% input, 30% output
        input_tokens = int(self.total_tokens_used * 0.7)
        output_tokens = int(self.total_tokens_used * 0.3)
        
        cost = (input_tokens / 1_000_000 * 2.50) + (output_tokens / 1_000_000 * 15.00)
        return round(cost, 4)
    
    def clear_cache(self) -> None:
        """Clear analysis cache"""
        if self.analysis_cache:
            self.analysis_cache.clear()
        logger.info("🧹 Google AI analysis cache cleared")
    
    def shutdown(self) -> None:
        """Shutdown the AI producer"""
        self.executor.shutdown(wait=True)
        logger.info("🔴 Google AI Music Producer shutdown complete")


# Example usage and testing
if __name__ == "__main__":
    async def test_google_ai_music_producer():
        """Test the Google AI music production system"""
        try:
            # Initialize the AI producer
            ai_producer = GoogleAIMusicProducer()
            
            # Mock audio features for testing
            test_features = {
                'duration': 180.5,
                'tempo': 128.0,
                'key': 'C',
                'mode': 'major',
                'time_signature': (4, 4),
                'spectral_centroid': [2000, 2100, 1900, 2050, 2200],
                'spectral_bandwidth': [500, 550, 480, 520, 580],
                'spectral_rolloff': [4000, 4200, 3800, 4100, 4300],
                'rms_energy': [0.5, 0.6, 0.4, 0.55, 0.7],
                'rhythm_pattern': [1.0, 0.5, 0.8, 0.3, 1.0, 0.5, 0.8, 0.3],
                'onset_times': [0.5, 1.0, 1.5, 2.0, 2.5, 3.0],
                'chroma_features': np.random.rand(12, 100),
                'mfccs': np.random.rand(13, 100)
            }
            
            logger.info("🎵 Testing Google AI Music Production System...")
            
            # Test comprehensive analysis
            analysis = await ai_producer.analyze_music_comprehensive(
                test_features,
                MusicAnalysisType.COMPREHENSIVE_ANALYSIS
            )
            
            logger.info(f"🎯 Genre: {analysis.primary_genre}")
            logger.info(f"😊 Mood: {analysis.primary_mood}")
            logger.info(f"🎛️ FL Plugins: {analysis.fl_plugin_recommendations}")
            logger.info(f"💡 Creative Ideas: {analysis.arrangement_ideas}")
            
            # Test real-time coaching
            coaching = await ai_producer.real_time_production_coaching(
                test_features,
                "How can I make this track sound more professional?"
            )
            
            logger.info(f"🎓 Coaching Response: {coaching.detailed_description}")
            
            # Show performance stats
            stats = ai_producer.get_performance_stats()
            logger.info(f"📊 Performance Stats: {stats}")
            
        except Exception as e:
            logger.error(f"❌ Test failed: {e}")
        finally:
            if 'ai_producer' in locals():
                ai_producer.shutdown()
    
    # Run the test
    asyncio.run(test_google_ai_music_producer())