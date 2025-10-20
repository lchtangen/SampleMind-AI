#!/usr/bin/env python3
"""
macOS Finder Dialog Integration for SampleMind AI

This module provides native macOS Finder dialog functionality using AppleScript
for selecting files and directories through the native macOS interface.
"""

import subprocess
import sys
from pathlib import Path
from typing import Optional, List, Union


class FinderDialog:
    """
    Native macOS Finder dialog integration using AppleScript.
    
    Provides methods to open native file and folder selection dialogs
    that integrate seamlessly with macOS Finder.
    """
    
    @staticmethod
    def is_macos() -> bool:
        """Check if running on macOS"""
        return sys.platform == "darwin"
    
    @staticmethod
    def choose_file(
        title: str = "Choose Audio File",
        file_types: Optional[List[str]] = None,
        initial_directory: Optional[Union[str, Path]] = None
    ) -> Optional[Path]:
        """
        Open native macOS file chooser dialog.
        
        Args:
            title: Dialog window title
            file_types: List of file extensions (e.g., ['wav', 'mp3', 'flac'])
            initial_directory: Initial directory to open
            
        Returns:
            Selected file path or None if cancelled
        """
        if not FinderDialog.is_macos():
            return None
        
        # Default audio file types if none specified
        if file_types is None:
            file_types = ['wav', 'mp3', 'flac', 'aiff', 'aif', 'm4a', 'ogg', 'wma']
        
        # Build AppleScript for file selection
        applescript_parts = [
            'tell application "System Events"',
            'activate',
            f'set chosenFile to choose file with prompt "{title}"'
        ]
        
        # Add file type filtering if specified
        if file_types:
            type_list = ', '.join([f'"{ext}"' for ext in file_types])
            applescript_parts[2] += f' of type {{{type_list}}}'
        
        # Add initial directory if specified
        if initial_directory:
            initial_path = Path(initial_directory).expanduser().absolute()
            if initial_path.exists():
                applescript_parts[2] += f' default location alias POSIX file "{initial_path}"'
        
        applescript_parts.extend([
            'set chosenPath to POSIX path of chosenFile',
            'return chosenPath',
            'end tell'
        ])
        
        applescript = '\n'.join(applescript_parts)
        
        try:
            result = subprocess.run(
                ['osascript', '-e', applescript],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0 and result.stdout.strip():
                return Path(result.stdout.strip())
            
        except subprocess.TimeoutExpired:
            pass
        except Exception:
            pass
        
        return None
    
    @staticmethod
    def choose_folder(
        title: str = "Choose Directory",
        initial_directory: Optional[Union[str, Path]] = None
    ) -> Optional[Path]:
        """
        Open native macOS folder chooser dialog.
        
        Args:
            title: Dialog window title
            initial_directory: Initial directory to open
            
        Returns:
            Selected directory path or None if cancelled
        """
        if not FinderDialog.is_macos():
            return None
        
        # Build AppleScript for folder selection
        applescript_parts = [
            'tell application "System Events"',
            'activate',
            f'set chosenFolder to choose folder with prompt "{title}"'
        ]
        
        # Add initial directory if specified
        if initial_directory:
            initial_path = Path(initial_directory).expanduser().absolute()
            if initial_path.exists():
                applescript_parts[2] += f' default location alias POSIX file "{initial_path}"'
        
        applescript_parts.extend([
            'set chosenPath to POSIX path of chosenFolder',
            'return chosenPath',
            'end tell'
        ])
        
        applescript = '\n'.join(applescript_parts)
        
        try:
            result = subprocess.run(
                ['osascript', '-e', applescript],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0 and result.stdout.strip():
                return Path(result.stdout.strip())
            
        except subprocess.TimeoutExpired:
            pass
        except Exception:
            pass
        
        return None
    
    @staticmethod
    def choose_multiple_files(
        title: str = "Choose Audio Files",
        file_types: Optional[List[str]] = None,
        initial_directory: Optional[Union[str, Path]] = None
    ) -> List[Path]:
        """
        Open native macOS file chooser dialog for multiple files.
        
        Args:
            title: Dialog window title
            file_types: List of file extensions (e.g., ['wav', 'mp3', 'flac'])
            initial_directory: Initial directory to open
            
        Returns:
            List of selected file paths (empty if cancelled)
        """
        if not FinderDialog.is_macos():
            return []
        
        # Default audio file types if none specified
        if file_types is None:
            file_types = ['wav', 'mp3', 'flac', 'aiff', 'aif', 'm4a', 'ogg', 'wma']
        
        # Build AppleScript for multiple file selection
        applescript_parts = [
            'tell application "System Events"',
            'activate',
            f'set chosenFiles to choose file with prompt "{title}" with multiple selections allowed'
        ]
        
        # Add file type filtering if specified
        if file_types:
            type_list = ', '.join([f'"{ext}"' for ext in file_types])
            applescript_parts[2] += f' of type {{{type_list}}}'
        
        # Add initial directory if specified
        if initial_directory:
            initial_path = Path(initial_directory).expanduser().absolute()
            if initial_path.exists():
                applescript_parts[2] += f' default location alias POSIX file "{initial_path}"'
        
        applescript_parts.extend([
            'set chosenPaths to {}',
            'repeat with aFile in chosenFiles',
            '    set end of chosenPaths to POSIX path of aFile',
            'end repeat',
            'set AppleScript\'s text item delimiters to "\\n"',
            'set pathsText to chosenPaths as text',
            'set AppleScript\'s text item delimiters to ""',
            'return pathsText',
            'end tell'
        ])
        
        applescript = '\n'.join(applescript_parts)
        
        try:
            result = subprocess.run(
                ['osascript', '-e', applescript],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0 and result.stdout.strip():
                paths = result.stdout.strip().split('\n')
                return [Path(path.strip()) for path in paths if path.strip()]
            
        except subprocess.TimeoutExpired:
            pass
        except Exception:
            pass
        
        return []


# Fallback functions for non-macOS systems
def fallback_input_file(prompt: str = "Enter file path") -> Optional[Path]:
    """Fallback file input for non-macOS systems"""
    try:
        path_str = input(f"{prompt}: ").strip()
        if path_str:
            path = Path(path_str).expanduser()
            if path.exists() and path.is_file():
                return path
    except (KeyboardInterrupt, EOFError):
        pass
    return None


def fallback_input_directory(prompt: str = "Enter directory path") -> Optional[Path]:
    """Fallback directory input for non-macOS systems"""
    try:
        path_str = input(f"{prompt}: ").strip()
        if path_str:
            path = Path(path_str).expanduser()
            if path.exists() and path.is_dir():
                return path
    except (KeyboardInterrupt, EOFError):
        pass
    return None


# Convenience functions that work cross-platform
def select_audio_file(
    title: str = "Choose Audio File",
    initial_directory: Optional[Union[str, Path]] = None
) -> Optional[Path]:
    """
    Cross-platform audio file selection.
    Uses native Finder on macOS, falls back to input prompt on other systems.
    """
    if FinderDialog.is_macos():
        return FinderDialog.choose_file(
            title=title,
            file_types=['wav', 'mp3', 'flac', 'aiff', 'aif', 'm4a', 'ogg', 'wma'],
            initial_directory=initial_directory
        )
    else:
        return fallback_input_file("Enter audio file path")


def select_directory(
    title: str = "Choose Directory",
    initial_directory: Optional[Union[str, Path]] = None
) -> Optional[Path]:
    """
    Cross-platform directory selection.
    Uses native Finder on macOS, falls back to input prompt on other systems.
    """
    if FinderDialog.is_macos():
        return FinderDialog.choose_folder(
            title=title,
            initial_directory=initial_directory
        )
    else:
        return fallback_input_directory("Enter directory path")


def select_multiple_audio_files(
    title: str = "Choose Audio Files",
    initial_directory: Optional[Union[str, Path]] = None
) -> List[Path]:
    """
    Cross-platform multiple audio file selection.
    Uses native Finder on macOS, falls back to single file on other systems.
    """
    if FinderDialog.is_macos():
        return FinderDialog.choose_multiple_files(
            title=title,
            file_types=['wav', 'mp3', 'flac', 'aiff', 'aif', 'm4a', 'ogg', 'wma'],
            initial_directory=initial_directory
        )
    else:
        file_path = fallback_input_file("Enter audio file path")
        return [file_path] if file_path else []