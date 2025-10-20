#!/usr/bin/env python3
"""
Pytest configuration and fixtures for SampleMind AI testing
Provides comprehensive test fixtures for audio processing, AI integration, and database testing
"""

import pytest
import asyncio
import tempfile
import shutil
import numpy as np
import soundfile as sf
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List
from unittest.mock import AsyncMock, MagicMock

# Add src to Python path for testing
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from samplemind.core.engine.audio_engine import AudioEngine, AnalysisLevel, AudioFeatures
from samplemind.integrations.openai_integration import OpenAIMusicProducer, OpenAIModel


# ============================================================================
# Scope Configuration
# ============================================================================

def pytest_configure(config):
    """Configure pytest environment"""
    # Ensure test directories exist
    test_root = Path(__file__).parent
    for subdir in ["fixtures", "temp", "reports"]:
        (test_root / subdir).mkdir(exist_ok=True)


def pytest_unconfigure(config):
    """Cleanup after all tests"""
    test_root = Path(__file__).parent
    temp_dir = test_root / "temp"
    if temp_dir.exists():
        shutil.rmtree(temp_dir)


# ============================================================================
# Test Data Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def test_audio_samples():
    """Generate synthetic audio samples for testing"""
    test_root = Path(__file__).parent
    fixtures_dir = test_root / "fixtures"
    fixtures_dir.mkdir(exist_ok=True)
    
    samples = {}
    
    # Sample 1: 120 BPM C major track
    sample_rate = 44100
    duration = 3.0  # 3 seconds
    t = np.linspace(0, duration, int(sample_rate * duration))
    
    # Create C major chord progression
    c_major = [261.63, 329.63, 392.00]  # C, E, G
    signal = np.zeros_like(t)
    for freq in c_major:
        signal += 0.3 * np.sin(2 * np.pi * freq * t)
    
    # Add 120 BPM rhythm
    beat_freq = 2.0  # 120 BPM = 2 beats per second
    rhythm = 0.2 * np.sin(2 * np.pi * beat_freq * t) * np.sin(2 * np.pi * 60 * t)
    signal += rhythm
    
    # Apply envelope
    envelope = np.exp(-0.5 * t)
    signal = signal * envelope
    
    file_120_c = fixtures_dir / "test_120bpm_c_major.wav"
    sf.write(file_120_c, signal, sample_rate)
    samples["120_c_major"] = file_120_c
    
    # Sample 2: 140 BPM A minor track  
    a_minor = [220.00, 261.63, 329.63]  # A, C, E
    signal_minor = np.zeros_like(t)
    for freq in a_minor:
        signal_minor += 0.3 * np.sin(2 * np.pi * freq * t)
    
    # Add 140 BPM rhythm
    beat_freq_fast = 2.33  # 140 BPM
    rhythm_fast = 0.2 * np.sin(2 * np.pi * beat_freq_fast * t) * np.sin(2 * np.pi * 80 * t)
    signal_minor += rhythm_fast
    signal_minor = signal_minor * envelope
    
    file_140_a = fixtures_dir / "test_140bpm_a_minor.wav"
    sf.write(file_140_a, signal_minor, sample_rate)
    samples["140_a_minor"] = file_140_a
    
    # Sample 3: Noise sample for filtering tests
    noise = 0.1 * np.random.randn(len(t))
    file_noise = fixtures_dir / "test_noise.wav"
    sf.write(file_noise, noise, sample_rate)
    samples["noise"] = file_noise
    
    return samples


@pytest.fixture
def sample_audio_features():
    """Provide sample AudioFeatures object for testing"""
    return AudioFeatures(
        duration=30.0,
        sample_rate=44100,
        channels=1,
        tempo=120.0,
        key="C",
        mode="major",
        pitch_class_distribution=[0.2, 0.1, 0.15, 0.05, 0.2, 0.1, 0.05, 0.15, 0.0, 0.0, 0.0, 0.0],
        spectral_centroid=[2500.0] * 100,
        rms_energy=[0.5] * 100,
        file_hash="test_hash_123",
        file_size=1024000,
        analysis_level=AnalysisLevel.STANDARD
    )


@pytest.fixture
def sample_features_dict():
    """Provide sample audio features as dictionary for AI testing"""
    return {
        'tempo': 128.0,
        'key': 'C',
        'mode': 'major',
        'duration': 180.0,
        'sample_rate': 44100,
        'spectral_centroid': [2500.0] * 100,
        'spectral_bandwidth': [1000.0] * 100,
        'spectral_rolloff': [4000.0] * 100,
        'rms_energy': [0.5] * 100,
        'pitch_class_distribution': [0.1] * 12,
        'mfccs': [[1.0] * 13] * 100,
        'zero_crossing_rate': [0.1] * 100
    }


# ============================================================================
# Audio Engine Fixtures
# ============================================================================

@pytest.fixture
def audio_engine():
    """Provide configured AudioEngine instance"""
    engine = AudioEngine(max_workers=2, cache_size=10)
    yield engine
    engine.shutdown()


@pytest.fixture
async def async_audio_engine():
    """Provide async AudioEngine instance"""
    engine = AudioEngine(max_workers=2, cache_size=10)
    yield engine
    engine.shutdown()


# ============================================================================
# AI Integration Fixtures
# ============================================================================

@pytest.fixture
def mock_openai_producer():
    """Provide mocked OpenAI producer for testing without API calls"""
    producer = MagicMock(spec=OpenAIMusicProducer)
    
    # Mock analysis result
    mock_analysis = MagicMock()
    mock_analysis.summary = "Test analysis summary"
    mock_analysis.detailed_analysis = {"tempo_analysis": "120 BPM steady rhythm"}
    mock_analysis.production_tips = ["Add compression", "EQ the highs"]
    mock_analysis.fl_studio_recommendations = ["Use Fruity Compressor"]
    mock_analysis.creativity_score = 0.8
    mock_analysis.production_quality_score = 0.7
    mock_analysis.commercial_potential_score = 0.6
    mock_analysis.processing_time = 1.5
    mock_analysis.tokens_used = 500
    mock_analysis.confidence_score = 0.9
    
    producer.analyze_music_comprehensive = AsyncMock(return_value=mock_analysis)
    producer.analyze_music_sync = MagicMock(return_value=mock_analysis)
    producer.get_usage_stats = MagicMock(return_value={
        'total_requests': 10,
        'total_tokens': 5000,
        'avg_response_time': 2.0,
        'cache_hits': 5,
        'cache_size': 3,
        'cache_hit_rate': 0.5
    })
    
    return producer


@pytest.fixture
def real_openai_producer():
    """Provide real OpenAI producer (requires API key)"""
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        pytest.skip("OPENAI_API_KEY not available")
    
    producer = OpenAIMusicProducer(
        api_key=api_key,
        default_model=OpenAIModel.GPT_4O_MINI  # Use cheaper model for testing
    )
    yield producer
    asyncio.run(producer.close())


# ============================================================================
# Database Fixtures
# ============================================================================

@pytest.fixture
async def test_mongodb():
    """Provide test MongoDB connection"""
    # This would connect to test database
    # For now, return mock
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_db.audio_features = mock_collection
    mock_db.analysis_results = mock_collection
    
    # Mock common operations
    mock_collection.insert_one = AsyncMock(return_value=MagicMock(inserted_id="test_id"))
    mock_collection.find_one = AsyncMock(return_value=None)
    mock_collection.find = MagicMock(return_value=[])
    mock_collection.update_one = AsyncMock(return_value=MagicMock(modified_count=1))
    mock_collection.delete_one = AsyncMock(return_value=MagicMock(deleted_count=1))
    
    return mock_db


@pytest.fixture
async def test_redis():
    """Provide test Redis connection"""
    mock_redis = MagicMock()
    mock_redis.get = AsyncMock(return_value=None)
    mock_redis.set = AsyncMock(return_value=True)
    mock_redis.delete = AsyncMock(return_value=1)
    mock_redis.exists = AsyncMock(return_value=False)
    mock_redis.flushdb = AsyncMock(return_value=True)
    
    return mock_redis


@pytest.fixture
async def test_chromadb():
    """Provide test ChromaDB connection"""
    mock_chroma = MagicMock()
    mock_collection = MagicMock()
    
    mock_chroma.get_or_create_collection = MagicMock(return_value=mock_collection)
    mock_collection.add = MagicMock()
    mock_collection.query = MagicMock(return_value={
        'documents': [['test document']],
        'metadatas': [[{'id': 'test'}]],
        'distances': [[0.5]]
    })
    mock_collection.get = MagicMock(return_value={
        'documents': [],
        'metadatas': [],
        'ids': []
    })
    
    return mock_chroma


# ============================================================================
# File System Fixtures
# ============================================================================

@pytest.fixture
def temp_directory():
    """Provide temporary directory for tests"""
    temp_dir = tempfile.mkdtemp(prefix="samplemind_test_")
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def test_config_file(temp_directory):
    """Provide test configuration file"""
    config = {
        "audio_engine": {
            "max_workers": 2,
            "cache_size": 10
        },
        "ai_providers": {
            "openai": {
                "enabled": True,
                "model": "gpt-4o-mini"
            }
        },
        "database": {
            "mongodb_url": "mongodb://localhost:27017/test_samplemind",
            "redis_url": "redis://localhost:6379/1"
        }
    }
    
    config_file = temp_directory / "test_config.json"
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    
    return config_file


# ============================================================================
# Environment Fixtures
# ============================================================================

@pytest.fixture
def clean_environment():
    """Provide clean environment variables for testing"""
    original_env = os.environ.copy()
    
    # Set test environment variables
    test_env = {
        'SAMPLEMIND_ENV': 'test',
        'SAMPLEMIND_LOG_LEVEL': 'DEBUG',
        'SAMPLEMIND_CACHE_SIZE': '10',
        'SAMPLEMIND_MAX_WORKERS': '2'
    }
    
    for key, value in test_env.items():
        os.environ[key] = value
    
    yield test_env
    
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


# ============================================================================
# Performance Testing Fixtures
# ============================================================================

@pytest.fixture
def performance_timer():
    """Provide performance timing utilities"""
    import time
    
    class Timer:
        def __init__(self):
            self.times = []
        
        def time_operation(self, func, *args, **kwargs):
            start = time.time()
            result = func(*args, **kwargs)
            end = time.time()
            elapsed = end - start
            self.times.append(elapsed)
            return result, elapsed
        
        async def time_async_operation(self, coro):
            start = time.time()
            result = await coro
            end = time.time()
            elapsed = end - start
            self.times.append(elapsed)
            return result, elapsed
        
        def get_stats(self):
            if not self.times:
                return {}
            return {
                'count': len(self.times),
                'total': sum(self.times),
                'average': sum(self.times) / len(self.times),
                'min': min(self.times),
                'max': max(self.times)
            }
    
    return Timer()


# ============================================================================
# Markers and Parametrization
# ============================================================================

# Custom markers for test categorization
pytestmark = [
    pytest.mark.filterwarnings("ignore::DeprecationWarning"),
    pytest.mark.filterwarnings("ignore::UserWarning")
]
