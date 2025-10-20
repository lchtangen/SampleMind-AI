#!/usr/bin/env python3
"""
SampleMind AI v6 - Advanced Audio File Loader
Professional audio file loading with comprehensive format support

This module provides intelligent audio file loading, format detection,
metadata extraction, and batch processing capabilities for professional
music production workflows.
"""

import asyncio
import logging
import mimetypes
import os
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union, Callable
import time
import hashlib
import json

# Audio processing libraries
import numpy as np
import librosa
import soundfile as sf
import mutagen
from mutagen.id3 import ID3NoHeaderError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AudioFormat(Enum):
    """Supported audio formats with detailed information"""
    WAV = {"ext": ".wav", "mime": "audio/wav", "compressed": False, "quality": "lossless"}
    FLAC = {"ext": ".flac", "mime": "audio/flac", "compressed": True, "quality": "lossless"}
    AIFF = {"ext": ".aiff", "mime": "audio/aiff", "compressed": False, "quality": "lossless"}
    MP3 = {"ext": ".mp3", "mime": "audio/mpeg", "compressed": True, "quality": "lossy"}
    AAC = {"ext": ".aac", "mime": "audio/aac", "compressed": True, "quality": "lossy"}
    M4A = {"ext": ".m4a", "mime": "audio/mp4", "compressed": True, "quality": "lossy"}
    OGG = {"ext": ".ogg", "mime": "audio/ogg", "compressed": True, "quality": "lossy"}
    WMA = {"ext": ".wma", "mime": "audio/x-ms-wma", "compressed": True, "quality": "lossy"}


class LoadingStrategy(Enum):
    """Audio loading strategies for different use cases"""
    FAST = "fast"  # Quick loading, lower quality for previews
    BALANCED = "balanced"  # Good balance of speed and quality
    QUALITY = "quality"  # High quality loading for analysis
    STREAMING = "streaming"  # Chunk-based loading for large files


@dataclass
class AudioMetadata:
    """Comprehensive audio file metadata"""
    # File information
    file_path: Path
    file_size: int
    file_hash: str
    format: AudioFormat
    creation_time: float
    modification_time: float
    
    # Audio properties
    duration: float
    sample_rate: int
    channels: int
    bit_depth: Optional[int] = None
    bitrate: Optional[int] = None
    
    # Musical metadata
    title: Optional[str] = None
    artist: Optional[str] = None
    album: Optional[str] = None
    genre: Optional[str] = None
    year: Optional[int] = None
    track_number: Optional[int] = None
    bpm: Optional[float] = None
    key: Optional[str] = None
    
    # Technical metadata
    codec: Optional[str] = None
    encoder: Optional[str] = None
    encoding_settings: Dict[str, Any] = field(default_factory=dict)
    
    # Processing metadata
    load_time: float = 0.0
    strategy_used: LoadingStrategy = LoadingStrategy.BALANCED
    normalization_applied: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary"""
        result = {}
        for key, value in self.__dict__.items():
            if isinstance(value, Path):
                result[key] = str(value)
            elif isinstance(value, Enum):
                result[key] = value.value
            else:
                result[key] = value
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AudioMetadata':
        """Create metadata from dictionary"""
        if 'file_path' in data:
            data['file_path'] = Path(data['file_path'])
        if 'format' in data:
            data['format'] = AudioFormat(data['format'])
        if 'strategy_used' in data:
            data['strategy_used'] = LoadingStrategy(data['strategy_used'])
        return cls(**data)


@dataclass
class LoadedAudio:
    """Container for loaded audio data and metadata"""
    audio_data: np.ndarray
    metadata: AudioMetadata
    chunks: Optional[List[np.ndarray]] = None  # For streaming
    is_stereo: bool = False
    peak_amplitude: float = 0.0
    rms_level: float = 0.0
    
    def get_duration_samples(self) -> int:
        """Get duration in samples"""
        return len(self.audio_data)
    
    def get_duration_seconds(self) -> float:
        """Get duration in seconds"""
        return len(self.audio_data) / self.metadata.sample_rate
    
    def to_mono(self) -> np.ndarray:
        """Convert to mono if stereo"""
        if self.is_stereo and len(self.audio_data.shape) > 1:
            return np.mean(self.audio_data, axis=1)
        return self.audio_data
    
    def normalize(self, target_level: float = 0.95) -> np.ndarray:
        """Normalize audio to target level"""
        peak = np.max(np.abs(self.audio_data))
        if peak > 0:
            normalized = self.audio_data * (target_level / peak)
            self.metadata.normalization_applied = True
            return normalized
        return self.audio_data


class AudioFormatDetector:
    """Intelligent audio format detection"""
    
    @staticmethod
    def detect_format(file_path: Path) -> Optional[AudioFormat]:
        """Detect audio format from file"""
        if not file_path.exists():
            return None
        
        # Check by extension first
        ext = file_path.suffix.lower()
        for fmt in AudioFormat:
            if fmt.value["ext"] == ext:
                return fmt
        
        # Check by MIME type
        mime_type, _ = mimetypes.guess_type(str(file_path))
        if mime_type:
            for fmt in AudioFormat:
                if fmt.value["mime"] == mime_type:
                    return fmt
        
        # Check by file signature (magic bytes)
        try:
            with open(file_path, 'rb') as f:
                header = f.read(12)
                
            # WAV signature
            if header[:4] == b'RIFF' and header[8:12] == b'WAVE':
                return AudioFormat.WAV
            
            # FLAC signature
            if header[:4] == b'fLaC':
                return AudioFormat.FLAC
            
            # MP3 signature
            if header[:3] == b'ID3' or header[:2] == b'\xff\xfb':
                return AudioFormat.MP3
            
            # OGG signature
            if header[:4] == b'OggS':
                return AudioFormat.OGG
                
        except Exception:
            pass
        
        return None
    
    @staticmethod
    def is_supported_format(file_path: Path) -> bool:
        """Check if file format is supported"""
        return AudioFormatDetector.detect_format(file_path) is not None
    
    @staticmethod
    def get_format_info(fmt: AudioFormat) -> Dict[str, Any]:
        """Get detailed format information"""
        return fmt.value


class MetadataExtractor:
    """Extract comprehensive metadata from audio files"""
    
    @staticmethod
    def extract_metadata(file_path: Path, audio_format: AudioFormat) -> Dict[str, Any]:
        """Extract all available metadata"""
        metadata = {}
        
        try:
            # Use mutagen for tag extraction
            audio_file = mutagen.File(str(file_path))
            
            if audio_file is not None:
                # Common tags
                metadata['title'] = MetadataExtractor._get_tag(audio_file, ['TIT2', 'TITLE', '\xa9nam'])
                metadata['artist'] = MetadataExtractor._get_tag(audio_file, ['TPE1', 'ARTIST', '\xa9ART'])
                metadata['album'] = MetadataExtractor._get_tag(audio_file, ['TALB', 'ALBUM', '\xa9alb'])
                metadata['genre'] = MetadataExtractor._get_tag(audio_file, ['TCON', 'GENRE', '\xa9gen'])
                metadata['year'] = MetadataExtractor._get_year(audio_file)
                metadata['track_number'] = MetadataExtractor._get_track_number(audio_file)
                
                # Audio properties
                if hasattr(audio_file, 'info'):
                    info = audio_file.info
                    metadata['duration'] = getattr(info, 'length', 0.0)
                    metadata['bitrate'] = getattr(info, 'bitrate', None)
                    metadata['sample_rate'] = getattr(info, 'sample_rate', None)
                    metadata['channels'] = getattr(info, 'channels', None)
                    
                    # Format-specific properties
                    if hasattr(info, 'bits_per_sample'):
                        metadata['bit_depth'] = info.bits_per_sample
                    elif hasattr(info, 'bits'):
                        metadata['bit_depth'] = info.bits
        
        except Exception as e:
            logger.warning(f"⚠️ Metadata extraction failed for {file_path}: {e}")
        
        return metadata
    
    @staticmethod
    def _get_tag(audio_file, tag_names: List[str]) -> Optional[str]:
        """Get tag value from multiple possible tag names"""
        for tag_name in tag_names:
            if tag_name in audio_file:
                value = audio_file[tag_name]
                if isinstance(value, list) and value:
                    return str(value[0])
                elif value:
                    return str(value)
        return None
    
    @staticmethod
    def _get_year(audio_file) -> Optional[int]:
        """Extract year from various date formats"""
        year_tags = ['TDRC', 'TYER', 'DATE', '\xa9day']
        for tag in year_tags:
            if tag in audio_file:
                value = audio_file[tag]
                if isinstance(value, list) and value:
                    value = value[0]
                
                try:
                    # Extract year from various formats
                    year_str = str(value)[:4]
                    return int(year_str)
                except (ValueError, TypeError):
                    continue
        return None
    
    @staticmethod
    def _get_track_number(audio_file) -> Optional[int]:
        """Extract track number"""
        track_tags = ['TRCK', 'TRACKNUMBER', 'trkn']
        for tag in track_tags:
            if tag in audio_file:
                value = audio_file[tag]
                if isinstance(value, list) and value:
                    value = value[0]
                
                try:
                    # Handle "track/total" format
                    track_str = str(value).split('/')[0]
                    return int(track_str)
                except (ValueError, TypeError):
                    continue
        return None


class AdvancedAudioLoader:
    """
    Advanced audio file loader with professional features
    
    Provides intelligent loading strategies, format detection, metadata extraction,
    and batch processing for professional music production workflows.
    """
    
    def __init__(
        self,
        default_strategy: LoadingStrategy = LoadingStrategy.BALANCED,
        max_workers: int = 4,
        cache_enabled: bool = True,
        cache_size: int = 100
    ):
        self.default_strategy = default_strategy
        self.max_workers = max_workers
        self.cache_enabled = cache_enabled
        self.cache_size = cache_size
        
        # Initialize components
        self.format_detector = AudioFormatDetector()
        self.metadata_extractor = MetadataExtractor()
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        
        # Cache and performance tracking
        self.audio_cache: Dict[str, LoadedAudio] = {}
        self.metadata_cache: Dict[str, AudioMetadata] = {}
        self.loading_stats = {
            'total_loads': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'avg_load_time': 0.0,
            'total_files_processed': 0,
            'format_distribution': {}
        }
        
        logger.info(f"🎵 Advanced Audio Loader initialized (strategy: {default_strategy.value})")
    
    def load_audio(
        self,
        file_path: Union[str, Path],
        strategy: Optional[LoadingStrategy] = None,
        target_sr: Optional[int] = None,
        mono: bool = True,
        normalize: bool = True,
        use_cache: bool = True
    ) -> LoadedAudio:
        """
        Load audio file with specified strategy
        
        Args:
            file_path: Path to audio file
            strategy: Loading strategy to use
            target_sr: Target sample rate (None for original)
            mono: Convert to mono
            normalize: Normalize audio
            use_cache: Use cached results if available
            
        Returns:
            LoadedAudio object with audio data and metadata
        """
        start_time = time.time()
        file_path = Path(file_path)
        strategy = strategy or self.default_strategy
        
        # Generate cache key
        cache_key = self._generate_cache_key(file_path, strategy, target_sr, mono, normalize)
        
        # Check cache
        if use_cache and self.cache_enabled and cache_key in self.audio_cache:
            self.loading_stats['cache_hits'] += 1
            logger.info(f"📦 Cache hit for {file_path.name}")
            return self.audio_cache[cache_key]
        
        self.loading_stats['cache_misses'] += 1
        
        try:
            # Detect format
            audio_format = self.format_detector.detect_format(file_path)
            if not audio_format:
                raise ValueError(f"Unsupported audio format: {file_path}")
            
            # Extract metadata
            metadata = self._create_metadata(file_path, audio_format)
            
            # Load audio data based on strategy
            audio_data, actual_sr = self._load_with_strategy(file_path, strategy, target_sr)
            
            # Process audio
            is_stereo = len(audio_data.shape) > 1
            
            if mono and is_stereo:
                audio_data = np.mean(audio_data, axis=1)
                is_stereo = False
            
            if normalize:
                peak = np.max(np.abs(audio_data))
                if peak > 0:
                    audio_data = audio_data * (0.95 / peak)
                    metadata.normalization_applied = True
            
            # Calculate audio statistics
            peak_amplitude = np.max(np.abs(audio_data))
            rms_level = np.sqrt(np.mean(audio_data ** 2))
            
            # Update metadata with actual values
            metadata.sample_rate = actual_sr
            metadata.channels = 1 if mono else (2 if is_stereo else 1)
            metadata.duration = len(audio_data) / actual_sr
            metadata.load_time = time.time() - start_time
            metadata.strategy_used = strategy
            
            # Create loaded audio object
            loaded_audio = LoadedAudio(
                audio_data=audio_data,
                metadata=metadata,
                is_stereo=is_stereo,
                peak_amplitude=peak_amplitude,
                rms_level=rms_level
            )
            
            # Cache result
            if use_cache and self.cache_enabled:
                self._cache_audio(cache_key, loaded_audio)
            
            # Update statistics
            self._update_loading_stats(audio_format, time.time() - start_time)
            
            logger.info(f"✅ Loaded: {file_path.name} ({loaded_audio.get_duration_seconds():.2f}s, {strategy.value})")
            return loaded_audio
            
        except Exception as e:
            logger.error(f"❌ Failed to load {file_path}: {e}")
            raise
    
    async def load_audio_async(
        self,
        file_path: Union[str, Path],
        strategy: Optional[LoadingStrategy] = None,
        **kwargs
    ) -> LoadedAudio:
        """Asynchronous audio loading"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            self.load_audio,
            file_path,
            strategy,
            kwargs.get('target_sr'),
            kwargs.get('mono', True),
            kwargs.get('normalize', True),
            kwargs.get('use_cache', True)
        )
    
    def batch_load(
        self,
        file_paths: List[Union[str, Path]],
        strategy: Optional[LoadingStrategy] = None,
        parallel: bool = True,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> List[LoadedAudio]:
        """
        Load multiple audio files in batch
        
        Args:
            file_paths: List of file paths to load
            strategy: Loading strategy for all files
            parallel: Whether to load in parallel
            progress_callback: Callback for progress updates (current, total)
            
        Returns:
            List of LoadedAudio objects
        """
        logger.info(f"🔄 Starting batch load of {len(file_paths)} files")
        strategy = strategy or self.default_strategy
        
        if parallel:
            return self._batch_load_parallel(file_paths, strategy, progress_callback)
        else:
            return self._batch_load_sequential(file_paths, strategy, progress_callback)
    
    def _batch_load_parallel(
        self,
        file_paths: List[Union[str, Path]],
        strategy: LoadingStrategy,
        progress_callback: Optional[Callable[[int, int], None]]
    ) -> List[LoadedAudio]:
        """Load files in parallel"""
        futures = []
        results = [None] * len(file_paths)  # Preserve order
        
        # Submit all tasks
        for i, file_path in enumerate(file_paths):
            future = self.executor.submit(self.load_audio, file_path, strategy)
            futures.append((i, future))
        
        # Collect results
        completed = 0
        for i, future in futures:
            try:
                results[i] = future.result()
                completed += 1
                
                if progress_callback:
                    progress_callback(completed, len(file_paths))
                    
            except Exception as e:
                logger.error(f"❌ Failed to load {file_paths[i]}: {e}")
                # Create empty audio for failed loads
                results[i] = None
        
        # Filter out None results
        return [r for r in results if r is not None]
    
    def _batch_load_sequential(
        self,
        file_paths: List[Union[str, Path]],
        strategy: LoadingStrategy,
        progress_callback: Optional[Callable[[int, int], None]]
    ) -> List[LoadedAudio]:
        """Load files sequentially"""
        results = []
        
        for i, file_path in enumerate(file_paths):
            try:
                audio = self.load_audio(file_path, strategy)
                results.append(audio)
                
                if progress_callback:
                    progress_callback(i + 1, len(file_paths))
                    
            except Exception as e:
                logger.error(f"❌ Failed to load {file_path}: {e}")
                continue
        
        return results
    
    def scan_directory(
        self,
        directory: Union[str, Path],
        recursive: bool = True,
        supported_only: bool = True
    ) -> List[Path]:
        """
        Scan directory for audio files
        
        Args:
            directory: Directory to scan
            recursive: Scan subdirectories
            supported_only: Only return supported formats
            
        Returns:
            List of audio file paths
        """
        directory = Path(directory)
        if not directory.exists():
            raise ValueError(f"Directory does not exist: {directory}")
        
        pattern = "**/*" if recursive else "*"
        all_files = list(directory.glob(pattern))
        
        # Filter for files only
        files = [f for f in all_files if f.is_file()]
        
        if supported_only:
            audio_files = []
            for file_path in files:
                if self.format_detector.is_supported_format(file_path):
                    audio_files.append(file_path)
            return audio_files
        
        return files
    
    def get_directory_info(self, directory: Union[str, Path]) -> Dict[str, Any]:
        """Get comprehensive information about audio files in directory"""
        audio_files = self.scan_directory(directory, recursive=True, supported_only=True)
        
        info = {
            'total_files': len(audio_files),
            'total_size': 0,
            'format_distribution': {},
            'estimated_duration': 0.0,
            'files_by_format': {}
        }
        
        for file_path in audio_files:
            # File size
            info['total_size'] += file_path.stat().st_size
            
            # Format distribution
            fmt = self.format_detector.detect_format(file_path)
            if fmt:
                fmt_name = fmt.name
                if fmt_name not in info['format_distribution']:
                    info['format_distribution'][fmt_name] = 0
                    info['files_by_format'][fmt_name] = []
                
                info['format_distribution'][fmt_name] += 1
                info['files_by_format'][fmt_name].append(str(file_path))
        
        return info
    
    def _load_with_strategy(
        self,
        file_path: Path,
        strategy: LoadingStrategy,
        target_sr: Optional[int]
    ) -> Tuple[np.ndarray, int]:
        """Load audio with specific strategy"""
        
        if strategy == LoadingStrategy.FAST:
            # Fast loading with potential quality trade-offs
            y, sr = librosa.load(str(file_path), sr=target_sr or 22050, mono=False)
            
        elif strategy == LoadingStrategy.BALANCED:
            # Balanced loading
            y, sr = librosa.load(str(file_path), sr=target_sr, mono=False)
            
        elif strategy == LoadingStrategy.QUALITY:
            # High quality loading
            y, sr = sf.read(str(file_path), always_2d=False)
            if target_sr and sr != target_sr:
                y = librosa.resample(y, orig_sr=sr, target_sr=target_sr)
                sr = target_sr
                
        elif strategy == LoadingStrategy.STREAMING:
            # For large files, implement chunked loading
            y, sr = sf.read(str(file_path), always_2d=False)
            if target_sr and sr != target_sr:
                y = librosa.resample(y, orig_sr=sr, target_sr=target_sr)
                sr = target_sr
        
        else:
            raise ValueError(f"Unknown loading strategy: {strategy}")
        
        return y, sr
    
    def _create_metadata(self, file_path: Path, audio_format: AudioFormat) -> AudioMetadata:
        """Create comprehensive metadata for audio file"""
        # Get file stats
        file_stat = file_path.stat()
        file_hash = self._compute_file_hash(file_path)
        
        # Extract metadata
        extracted_metadata = self.metadata_extractor.extract_metadata(file_path, audio_format)
        
        # Create metadata object
        metadata = AudioMetadata(
            file_path=file_path,
            file_size=file_stat.st_size,
            file_hash=file_hash,
            format=audio_format,
            creation_time=file_stat.st_ctime,
            modification_time=file_stat.st_mtime,
            duration=extracted_metadata.get('duration', 0.0),
            sample_rate=extracted_metadata.get('sample_rate', 44100),
            channels=extracted_metadata.get('channels', 2),
            bit_depth=extracted_metadata.get('bit_depth'),
            bitrate=extracted_metadata.get('bitrate'),
            title=extracted_metadata.get('title'),
            artist=extracted_metadata.get('artist'),
            album=extracted_metadata.get('album'),
            genre=extracted_metadata.get('genre'),
            year=extracted_metadata.get('year'),
            track_number=extracted_metadata.get('track_number')
        )
        
        return metadata
    
    def _generate_cache_key(
        self,
        file_path: Path,
        strategy: LoadingStrategy,
        target_sr: Optional[int],
        mono: bool,
        normalize: bool
    ) -> str:
        """Generate cache key for audio loading request"""
        file_stat = file_path.stat()
        key_data = f"{file_path}_{file_stat.st_mtime}_{file_stat.st_size}_{strategy.value}_{target_sr}_{mono}_{normalize}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _compute_file_hash(self, file_path: Path) -> str:
        """Compute SHA-256 hash of file"""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    
    def _cache_audio(self, cache_key: str, loaded_audio: LoadedAudio):
        """Cache loaded audio with size management"""
        if len(self.audio_cache) >= self.cache_size:
            # Remove oldest entry
            oldest_key = next(iter(self.audio_cache))
            del self.audio_cache[oldest_key]
        
        self.audio_cache[cache_key] = loaded_audio
    
    def _update_loading_stats(self, audio_format: AudioFormat, load_time: float):
        """Update loading statistics"""
        self.loading_stats['total_loads'] += 1
        
        # Update average load time
        prev_avg = self.loading_stats['avg_load_time']
        prev_count = self.loading_stats['total_loads'] - 1
        self.loading_stats['avg_load_time'] = (prev_avg * prev_count + load_time) / self.loading_stats['total_loads']
        
        # Update format distribution
        fmt_name = audio_format.name
        if fmt_name not in self.loading_stats['format_distribution']:
            self.loading_stats['format_distribution'][fmt_name] = 0
        self.loading_stats['format_distribution'][fmt_name] += 1
    
    def get_loading_stats(self) -> Dict[str, Any]:
        """Get loading performance statistics"""
        cache_hit_rate = 0.0
        total_requests = self.loading_stats['cache_hits'] + self.loading_stats['cache_misses']
        if total_requests > 0:
            cache_hit_rate = self.loading_stats['cache_hits'] / total_requests
        
        return {
            **self.loading_stats,
            'cache_hit_rate': cache_hit_rate,
            'cache_size': len(self.audio_cache),
            'supported_formats': [fmt.name for fmt in AudioFormat]
        }
    
    def clear_cache(self):
        """Clear all caches"""
        self.audio_cache.clear()
        self.metadata_cache.clear()
        self.loading_stats['cache_hits'] = 0
        self.loading_stats['cache_misses'] = 0
        logger.info("🧹 Audio loader cache cleared")
    
    def shutdown(self):
        """Shutdown the audio loader"""
        self.executor.shutdown(wait=True)
        logger.info("🔴 Audio Loader shutdown complete")


# Utility functions
def create_loader_from_config(config: Dict[str, Any]) -> AdvancedAudioLoader:
    """Create audio loader from configuration"""
    return AdvancedAudioLoader(
        default_strategy=LoadingStrategy(config.get('default_strategy', 'balanced')),
        max_workers=config.get('max_workers', 4),
        cache_enabled=config.get('cache_enabled', True),
        cache_size=config.get('cache_size', 100)
    )


# Example usage
if __name__ == "__main__":
    # Initialize loader
    loader = AdvancedAudioLoader()
    
    try:
        logger.info("🎵 Advanced Audio Loader - Ready for Professional Loading!")
        logger.info("📋 Supported formats: WAV, FLAC, AIFF, MP3, AAC, M4A, OGG, WMA")
        logger.info("🔧 Loading strategies: FAST, BALANCED, QUALITY, STREAMING")
        logger.info("🎯 Professional features: Metadata extraction, batch processing, caching")
        
        # Performance stats
        stats = loader.get_loading_stats()
        logger.info(f"📊 Loader Stats: {stats}")
        
    except Exception as e:
        logger.error(f"❌ Loader initialization failed: {e}")
    finally:
        loader.shutdown()