#!/usr/bin/env python3
"""
SampleMind AI v6 - Interactive CLI Menu System
Professional music production AI with beautiful terminal interface

This module provides an interactive menu-driven interface for all
SampleMind AI functionality with rich terminal UI and progress indicators.
"""

import asyncio
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.prompt import Prompt, Confirm
from rich.progress import (
    Progress, SpinnerColumn, TextColumn, BarColumn,
    TaskProgressColumn, TimeElapsedColumn, TimeRemainingColumn
)
from rich.tree import Tree
from rich.layout import Layout
from rich.live import Live
from rich.align import Align
import typer

# Import our core components
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from samplemind.core.engine.audio_engine import AudioEngine, AnalysisLevel
from samplemind.core.loader import AdvancedAudioLoader, LoadingStrategy
from samplemind.integrations.ai_manager import SampleMindAIManager, AnalysisType, AIProvider
from samplemind.utils.finder_dialog import select_audio_file, select_directory, select_multiple_audio_files

# Rich console setup
console = Console()

class SampleMindCLI:
    """
    Interactive CLI for SampleMind AI v6
    
    Professional music production interface with rich terminal UI,
    real-time progress indicators, and comprehensive functionality.
    """
    
    def __init__(self):
        self.audio_engine: Optional[AudioEngine] = None
        self.audio_loader: Optional[AdvancedAudioLoader] = None
        self.ai_manager: Optional[SampleMindAIManager] = None
        self.initialized = False
        self.current_directory = Path.cwd()
        
        # Stats tracking
        self.session_stats = {
            'files_analyzed': 0,
            'total_processing_time': 0.0,
            'ai_requests': 0,
            'session_start': time.time()
        }
    
    def display_banner(self):
        """Display the SampleMind AI banner"""
        banner = """
        ╔══════════════════════════════════════════════════════════════╗
        ║                    🎵 SAMPLEMIND AI v6 🎵                    ║
        ║              Professional Music Production Suite              ║
        ║                  Powered by GPT-5 & AI Magic                 ║
        ╚══════════════════════════════════════════════════════════════╝
        """
        
        panel = Panel(
            Align.center(Text(banner, style="bold blue")),
            border_style="blue",
            padding=(1, 2)
        )
        console.print(panel)
    
    async def initialize_system(self):
        """Initialize all SampleMind components"""
        if self.initialized:
            return True
        
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                
                # Initialize Audio Engine
                task1 = progress.add_task("🎛️ Initializing Audio Engine...", total=None)
                self.audio_engine = AudioEngine(max_workers=4)
                progress.remove_task(task1)
                
                # Initialize Audio Loader
                task2 = progress.add_task("📁 Initializing Audio Loader...", total=None)
                self.audio_loader = AdvancedAudioLoader(max_workers=4)
                progress.remove_task(task2)
                
                # Initialize AI Manager
                task3 = progress.add_task("🤖 Initializing AI Manager...", total=None)
                self.ai_manager = SampleMindAIManager()
                progress.remove_task(task3)
                
                # Verify AI providers
                task4 = progress.add_task("🔍 Checking AI Providers...", total=None)
                provider_status = self.ai_manager.get_provider_status()
                enabled_providers = sum(1 for status in provider_status.values() if status['enabled'])
                progress.remove_task(task4)
                
                if enabled_providers == 0:
                    console.print("[bold red]⚠️ No AI providers configured![/bold red]")
                    console.print("Please run the API setup scripts first:")
                    console.print("  • [cyan]./setup_openai_api.sh[/cyan] - For OpenAI GPT-5")
                    console.print("  • [cyan]./setup_google_ai_api.sh[/cyan] - For Google AI")
                    return False
            
            self.initialized = True
            
            # Show initialization success
            success_table = Table(show_header=False, box=None)
            success_table.add_column("Component", style="cyan")
            success_table.add_column("Status", style="green")
            
            success_table.add_row("🎛️ Audio Engine", "✅ Ready")
            success_table.add_row("📁 Audio Loader", "✅ Ready")
            success_table.add_row("🤖 AI Manager", f"✅ Ready ({enabled_providers} providers)")
            
            panel = Panel(
                success_table,
                title="[bold green]🚀 System Initialized[/bold green]",
                border_style="green"
            )
            console.print(panel)
            
            return True
            
        except Exception as e:
            console.print(f"[bold red]❌ Initialization failed: {e}[/bold red]")
            return False
    
    def display_main_menu(self):
        """Display the main menu options"""
        menu_table = Table(show_header=False, box=None, padding=(0, 2))
        menu_table.add_column("Option", style="bold cyan", width=3)
        menu_table.add_column("Description", style="white")
        menu_table.add_column("Details", style="dim")
        
        menu_table.add_row("1", "🎯 Analyze Single File", "AI-powered analysis of audio file")
        menu_table.add_row("2", "📁 Batch Process Directory", "Process multiple files with AI")
        menu_table.add_row("3", "📁 Analyze Folder Samples", "Select folder and analyze all audio files")
        menu_table.add_row("4", "🔍 Scan & Preview", "Scan directory and preview files")
        menu_table.add_row("5", "⚙️ Configuration", "Manage settings and preferences")
        menu_table.add_row("6", "📊 System Status", "View performance and statistics")
        menu_table.add_row("7", "🤖 AI Provider Settings", "Manage AI providers and models")
        menu_table.add_row("8", "💡 Production Tips", "Get production coaching")
        menu_table.add_row("9", "🎛️ FL Studio Integration", "FL Studio specific tools")
        menu_table.add_row("A", "📈 Session Analytics", "View current session stats")
        menu_table.add_row("0", "🚪 Exit", "Quit SampleMind AI")
        
        panel = Panel(
            menu_table,
            title="[bold blue]🎵 SampleMind AI v6 - Main Menu[/bold blue]",
            border_style="blue"
        )
        console.print(panel)
    
    async def run_single_analysis(self):
        """Run single file analysis with AI"""
        console.print("\n[bold blue]🎯 Single File Analysis[/bold blue]")
        
        # Use Finder dialog to select file
        console.print("[cyan]📁 Choose audio file using Finder...[/cyan]")
        file_path = select_audio_file(
            title="Choose Audio File for Analysis",
            initial_directory=self.current_directory
        )
        
        if not file_path:
            # Fallback to manual input
            if Confirm.ask("Would you like to enter the file path manually?"):
                file_path_str = Prompt.ask("📁 Enter audio file path", default=str(self.current_directory))
                file_path = Path(file_path_str)
            else:
                console.print("[yellow]⚠️ No file selected[/yellow]")
                return
        
        if not file_path.exists():
            console.print(f"[red]❌ File not found: {file_path}[/red]")
            return
        
        if file_path.is_dir():
            # If directory provided, let user select file
            audio_files = self.audio_loader.scan_directory(file_path, supported_only=True)
            if not audio_files:
                console.print("[yellow]⚠️ No audio files found[/yellow]")
                return
            
            # Show file selection
            file_table = Table()
            file_table.add_column("Index", style="cyan")
            file_table.add_column("File", style="white")
            file_table.add_column("Size", style="dim")
            
            for i, audio_file in enumerate(audio_files[:20]):  # Show max 20 files
                size = audio_file.stat().st_size / (1024 * 1024)
                file_table.add_row(str(i + 1), audio_file.name, f"{size:.1f} MB")
            
            console.print(file_table)
            
            file_index = Prompt.ask("Select file number", default="1")
            try:
                file_path = audio_files[int(file_index) - 1]
            except (ValueError, IndexError):
                console.print("[red]❌ Invalid file selection[/red]")
                return
        
        # Get analysis preferences
        analysis_types = ["comprehensive", "production", "creative", "fl_studio", "quick"]
        analysis_type = Prompt.ask(
            "🔍 Analysis type",
            choices=analysis_types,
            default="comprehensive"
        )
        
        providers = ["auto", "openai", "google_ai"]
        provider = Prompt.ask(
            "🤖 AI Provider",
            choices=providers,
            default="auto"
        )
        
        # Convert to enums
        analysis_type_enum = AnalysisType(analysis_type.upper() + "_ANALYSIS" if not analysis_type.endswith("_analysis") else analysis_type.upper())
        provider_enum = None if provider == "auto" else AIProvider(provider.upper())
        
        try:
            start_time = time.time()
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                TimeElapsedColumn(),
                console=console
            ) as progress:
                
                # Step 1: Load audio
                load_task = progress.add_task("📁 Loading audio...", total=100)
                loaded_audio = self.audio_loader.load_audio(file_path, strategy=LoadingStrategy.QUALITY)
                progress.update(load_task, completed=100)
                
                # Step 2: Extract features
                feature_task = progress.add_task("🎵 Extracting features...", total=100)
                features = self.audio_engine.analyze_audio(file_path, level=AnalysisLevel.DETAILED)
                progress.update(feature_task, completed=100)
                
                # Step 3: AI Analysis
                ai_task = progress.add_task("🤖 AI analysis...", total=100)
                features_dict = features.to_dict()
                ai_result = await self.ai_manager.analyze_music(
                    features_dict,
                    analysis_type_enum,
                    preferred_provider=provider_enum
                )
                progress.update(ai_task, completed=100)
            
            # Display results
            self._display_analysis_results(ai_result, loaded_audio, features)
            
            # Update session stats
            self.session_stats['files_analyzed'] += 1
            self.session_stats['total_processing_time'] += time.time() - start_time
            self.session_stats['ai_requests'] += 1
            
            # Ask to save results
            if Confirm.ask("💾 Save analysis results?"):
                output_file = file_path.with_suffix('.samplemind.json')
                self._save_analysis(ai_result, loaded_audio, features, output_file)
                console.print(f"[green]✅ Results saved: {output_file}[/green]")
            
        except Exception as e:
            console.print(f"[bold red]❌ Analysis failed: {e}[/bold red]")
    
    async def run_multiple_files_analysis(self):
        """Run analysis on all audio files in selected folder"""
        console.print("\n[bold blue]📁 Folder Samples Analysis[/bold blue]")
        
        # Use Finder dialog to select folder
        console.print("[cyan]📁 Choose folder containing audio samples using Finder...[/cyan]")
        folder_path = select_directory(
            title="Choose Folder with Audio Samples for Analysis",
            initial_directory=self.current_directory
        )
        
        if not folder_path:
            console.print("[yellow]⚠️ No folder selected[/yellow]")
            return
        
        # Scan folder for audio files
        console.print("[cyan]🔍 Scanning folder for audio files...[/cyan]")
        file_paths = self.audio_loader.scan_directory(folder_path, recursive=True, supported_only=True)
        
        if not file_paths:
            console.print("[yellow]⚠️ No audio files found in selected folder[/yellow]")
            return
        
        console.print(f"[green]Found {len(file_paths)} audio files in folder for analysis[/green]")
        
        # Show found files preview
        preview_table = Table(title="🎵 Audio Files Found")
        preview_table.add_column("File", style="cyan")
        preview_table.add_column("Size", style="dim")
        
        for i, file_path in enumerate(file_paths[:10]):  # Show first 10 files
            size = file_path.stat().st_size / (1024 * 1024)
            preview_table.add_row(file_path.name, f"{size:.1f} MB")
        
        if len(file_paths) > 10:
            preview_table.add_row(f"... and {len(file_paths) - 10} more files", "")
        
        console.print(preview_table)
        
        # Ask for confirmation
        if not Confirm.ask(f"Proceed with analyzing all {len(file_paths)} files?"):
            console.print("[yellow]⚠️ Analysis cancelled[/yellow]")
            return
        
        # Get analysis preferences
        analysis_types = ["comprehensive", "production", "creative", "fl_studio", "quick"]
        analysis_type = Prompt.ask(
            "🔍 Analysis type",
            choices=analysis_types,
            default="comprehensive"
        )
        
        providers = ["auto", "openai", "google_ai"]
        provider = Prompt.ask(
            "🤖 AI Provider",
            choices=providers,
            default="auto"
        )
        
        # Convert to enums
        analysis_type_enum = AnalysisType(analysis_type.upper() + "_ANALYSIS" if not analysis_type.endswith("_analysis") else analysis_type.upper())
        provider_enum = None if provider == "auto" else AIProvider(provider.upper())
        
        results = []
        start_time = time.time()
        
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                TimeElapsedColumn(),
                TimeRemainingColumn(),
                console=console
            ) as progress:
                
                main_task = progress.add_task(f"🔄 Processing {len(file_paths)} files...", total=len(file_paths))
                
                for i, file_path in enumerate(file_paths):
                    try:
                        progress.update(main_task, description=f"Processing: {file_path.name}")
                        
                        # Load and analyze
                        loaded_audio = self.audio_loader.load_audio(file_path, strategy=LoadingStrategy.QUALITY)
                        features = self.audio_engine.analyze_audio(file_path, level=AnalysisLevel.DETAILED)
                        features_dict = features.to_dict()
                        
                        # AI analysis
                        ai_result = await self.ai_manager.analyze_music(
                            features_dict,
                            analysis_type_enum,
                            preferred_provider=provider_enum
                        )
                        
                        results.append({
                            'file': str(file_path),
                            'ai_result': ai_result,
                            'features': features,
                            'loaded_audio': loaded_audio
                        })
                        
                        progress.advance(main_task)
                        
                    except Exception as e:
                        console.print(f"[red]❌ Failed: {file_path.name} - {e}[/red]")
                        continue
            
            # Display individual results for each file
            for result in results:
                console.print(f"\n[bold cyan]═══ Analysis for {Path(result['file']).name} ═══[/bold cyan]")
                self._display_analysis_results(result['ai_result'], result['loaded_audio'], result['features'])
            
            # Generate summary
            self._display_batch_summary(results, time.time() - start_time)
            
            # Update session stats
            self.session_stats['files_analyzed'] += len(results)
            self.session_stats['total_processing_time'] += time.time() - start_time
            self.session_stats['ai_requests'] += len(results)
            
            # Ask to save results
            if results and Confirm.ask("💾 Save all analysis results?"):
                folder_name = folder_path.name
                output_dir = Path(f"./{folder_name}_analysis_results")
                output_dir.mkdir(exist_ok=True)
                
                for result in results:
                    file_name = Path(result['file']).stem
                    output_file = output_dir / f"{file_name}.samplemind.json"
                    self._save_analysis(result['ai_result'], result['loaded_audio'], result['features'], output_file)
                
                console.print(f"[green]✅ All results saved to: {output_dir}[/green]")
            
        except Exception as e:
            console.print(f"[bold red]❌ Multiple files analysis failed: {e}[/bold red]")
    
    async def run_batch_processing(self):
        """Run batch processing on directory"""
        console.print("\n[bold blue]📁 Batch Processing[/bold blue]")
        
        # Use Finder dialog to select directory
        console.print("[cyan]📁 Choose directory using Finder...[/cyan]")
        directory = select_directory(
            title="Choose Directory for Batch Processing",
            initial_directory=self.current_directory
        )
        
        if not directory:
            # Fallback to manual input
            if Confirm.ask("Would you like to enter the directory path manually?"):
                directory_str = Prompt.ask("📁 Enter directory path", default=str(self.current_directory))
                directory = Path(directory_str)
            else:
                console.print("[yellow]⚠️ No directory selected[/yellow]")
                return
        
        if not directory.exists() or not directory.is_dir():
            console.print(f"[red]❌ Directory not found: {directory}[/red]")
            return
        
        # Scan directory
        console.print("[cyan]🔍 Scanning directory...[/cyan]")
        audio_files = self.audio_loader.scan_directory(directory, recursive=True)
        
        if not audio_files:
            console.print("[yellow]⚠️ No audio files found[/yellow]")
            return
        
        console.print(f"[green]Found {len(audio_files)} audio files[/green]")
        
        # Get batch settings
        max_files = Prompt.ask("📊 Max files to process (0 for all)", default="0")
        max_files = int(max_files) if max_files != "0" else len(audio_files)
        
        analysis_type = Prompt.ask(
            "🔍 Analysis type",
            choices=["comprehensive", "production", "creative", "quick"],
            default="comprehensive"
        )
        
        output_dir = Prompt.ask("📂 Output directory", default="./results")
        
        # Process files
        files_to_process = audio_files[:max_files]
        analysis_type_enum = AnalysisType(analysis_type.upper() + "_ANALYSIS")
        
        results = []
        start_time = time.time()
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
            console=console
        ) as progress:
            
            main_task = progress.add_task(f"🔄 Processing {len(files_to_process)} files...", total=len(files_to_process))
            
            for i, file_path in enumerate(files_to_process):
                try:
                    progress.update(main_task, description=f"Processing: {file_path.name}")
                    
                    # Load and analyze
                    loaded_audio = self.audio_loader.load_audio(file_path)
                    features = self.audio_engine.analyze_audio(file_path)
                    features_dict = features.to_dict()
                    
                    # AI analysis
                    ai_result = await self.ai_manager.analyze_music(
                        features_dict,
                        analysis_type_enum
                    )
                    
                    results.append({
                        'file': str(file_path),
                        'ai_result': ai_result,
                        'features': features,
                        'loaded_audio': loaded_audio
                    })
                    
                    # Save individual result
                    output_dir_path = Path(output_dir)
                    output_dir_path.mkdir(parents=True, exist_ok=True)
                    output_file = output_dir_path / f"{file_path.stem}.samplemind.json"
                    self._save_analysis(ai_result, loaded_audio, features, output_file)
                    
                    progress.advance(main_task)
                    
                except Exception as e:
                    console.print(f"[red]❌ Failed: {file_path.name} - {e}[/red]")
                    continue
        
        # Generate summary
        self._display_batch_summary(results, time.time() - start_time)
        
        # Update session stats
        self.session_stats['files_analyzed'] += len(results)
        self.session_stats['total_processing_time'] += time.time() - start_time
        self.session_stats['ai_requests'] += len(results)
    
    def scan_and_preview(self):
        """Scan directory and show preview"""
        console.print("\n[bold blue]🔍 Scan & Preview[/bold blue]")
        
        # Use Finder dialog to select directory
        console.print("[cyan]📁 Choose directory using Finder...[/cyan]")
        directory = select_directory(
            title="Choose Directory to Scan & Preview",
            initial_directory=self.current_directory
        )
        
        if not directory:
            # Fallback to manual input
            if Confirm.ask("Would you like to enter the directory path manually?"):
                directory_str = Prompt.ask("📁 Enter directory path", default=str(self.current_directory))
                directory = Path(directory_str)
            else:
                console.print("[yellow]⚠️ No directory selected[/yellow]")
                return
        
        if not directory.exists():
            console.print(f"[red]❌ Directory not found: {directory}[/red]")
            return
        
        # Get directory info
        console.print("[cyan]📊 Analyzing directory...[/cyan]")
        dir_info = self.audio_loader.get_directory_info(directory)
        
        # Display summary
        self._display_directory_info(dir_info)
    
    def show_system_status(self):
        """Display comprehensive system status"""
        console.print("\n[bold blue]📊 System Status[/bold blue]")
        
        # Get stats from all components
        engine_stats = self.audio_engine.get_performance_stats()
        loader_stats = self.audio_loader.get_loading_stats()
        ai_stats = self.ai_manager.get_global_stats()
        provider_status = self.ai_manager.get_provider_status()
        
        # Create comprehensive status display
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="body")
        )
        
        layout["body"].split_row(
            Layout(name="left"),
            Layout(name="right")
        )
        
        # Header
        layout["header"].update(
            Panel("📊 SampleMind AI v6 - System Status", style="bold blue")
        )
        
        # Left panel - Performance
        perf_table = Table(title="🚀 Performance Metrics")
        perf_table.add_column("Metric", style="cyan")
        perf_table.add_column("Value", style="green")
        
        perf_table.add_row("Audio Engine", "✅ Active")
        perf_table.add_row("Avg Analysis Time", f"{engine_stats['avg_analysis_time']:.2f}s")
        perf_table.add_row("Cache Hit Rate", f"{engine_stats['cache_hit_rate']:.1%}")
        perf_table.add_row("Total Analyses", str(engine_stats['total_analyses']))
        perf_table.add_row("AI Requests", str(ai_stats['total_requests']))
        perf_table.add_row("Total Tokens", str(ai_stats['total_tokens']))
        
        layout["left"].update(perf_table)
        
        # Right panel - Providers
        provider_table = Table(title="🤖 AI Providers")
        provider_table.add_column("Provider", style="cyan")
        provider_table.add_column("Status", style="green")
        provider_table.add_column("Requests", style="yellow")
        
        for provider, status in provider_status.items():
            status_icon = "✅" if status['enabled'] else "❌"
            provider_table.add_row(
                provider,
                status_icon,
                str(status['total_requests'])
            )
        
        layout["right"].update(provider_table)
        
        console.print(layout)
    
    def show_session_analytics(self):
        """Display current session analytics"""
        console.print("\n[bold blue]📈 Session Analytics[/bold blue]")
        
        session_time = time.time() - self.session_stats['session_start']
        
        analytics_table = Table(title="📊 Current Session")
        analytics_table.add_column("Metric", style="cyan")
        analytics_table.add_column("Value", style="green")
        
        analytics_table.add_row("Session Duration", f"{session_time / 60:.1f} minutes")
        analytics_table.add_row("Files Analyzed", str(self.session_stats['files_analyzed']))
        analytics_table.add_row("AI Requests", str(self.session_stats['ai_requests']))
        analytics_table.add_row("Total Processing Time", f"{self.session_stats['total_processing_time']:.1f}s")
        
        if self.session_stats['files_analyzed'] > 0:
            avg_time = self.session_stats['total_processing_time'] / self.session_stats['files_analyzed']
            analytics_table.add_row("Avg Time Per File", f"{avg_time:.2f}s")
        
        console.print(analytics_table)
    
    async def show_configuration_menu(self):
        """Display and manage configuration settings"""
        console.print("\n[bold blue]⚙️ Configuration Menu[/bold blue]")
        
        while True:
            config_table = Table(show_header=False, box=None, padding=(0, 2))
            config_table.add_column("Option", style="bold cyan", width=3)
            config_table.add_column("Description", style="white")
            
            config_table.add_row("1", "🎛️ Audio Engine Settings")
            config_table.add_row("2", "📁 Default Directories")
            config_table.add_row("3", "🔧 Processing Preferences")
            config_table.add_row("4", "💾 Cache Management")
            config_table.add_row("5", "📊 Logging Level")
            config_table.add_row("6", "🌐 API Settings")
            config_table.add_row("7", "💾 Export/Import Config")
            config_table.add_row("0", "🔙 Back to Main Menu")
            
            panel = Panel(
                config_table,
                title="[bold blue]⚙️ Configuration Options[/bold blue]",
                border_style="blue"
            )
            console.print(panel)
            
            config_choice = Prompt.ask("⚙️ Select configuration option", 
                                     choices=["0", "1", "2", "3", "4", "5", "6", "7"])
            
            if config_choice == "0":
                break
            elif config_choice == "1":
                await self._configure_audio_engine()
            elif config_choice == "2":
                await self._configure_directories()
            elif config_choice == "3":
                await self._configure_processing()
            elif config_choice == "4":
                await self._manage_cache()
            elif config_choice == "5":
                await self._configure_logging()
            elif config_choice == "6":
                await self._configure_api_settings()
            elif config_choice == "7":
                await self._export_import_config()
    
    async def _configure_audio_engine(self):
        """Configure audio engine settings"""
        console.print("\n[bold cyan]🎛️ Audio Engine Settings[/bold cyan]")
        
        current_stats = self.audio_engine.get_performance_stats()
        
        settings_table = Table(title="Current Audio Engine Settings")
        settings_table.add_column("Setting", style="cyan")
        settings_table.add_column("Current Value", style="green")
        settings_table.add_column("Description", style="dim")
        
        settings_table.add_row("Max Workers", str(self.audio_engine.max_workers), "Parallel processing threads")
        settings_table.add_row("Cache Size", str(self.audio_engine.cache_size), "Feature cache capacity")
        settings_table.add_row("Cache Hit Rate", f"{current_stats['cache_hit_rate']:.1%}", "Cache effectiveness")
        
        console.print(settings_table)
        
        if Confirm.ask("🔧 Modify audio engine settings?"):
            new_workers = Prompt.ask("Max Workers", default=str(self.audio_engine.max_workers))
            new_cache_size = Prompt.ask("Cache Size", default=str(self.audio_engine.cache_size))
            
            try:
                self.audio_engine.max_workers = int(new_workers)
                self.audio_engine.cache_size = int(new_cache_size)
                console.print("[green]✅ Audio engine settings updated![/green]")
            except ValueError:
                console.print("[red]❌ Invalid settings values[/red]")
    
    async def _configure_directories(self):
        """Configure default directories"""
        console.print("\n[bold cyan]📁 Default Directories[/bold cyan]")
        
        dirs_table = Table(title="Default Directories")
        dirs_table.add_column("Type", style="cyan")
        dirs_table.add_column("Path", style="green")
        
        dirs_table.add_row("Current Working", str(self.current_directory))
        dirs_table.add_row("Audio Samples", str(Path.home() / "Music"))
        dirs_table.add_row("Analysis Results", str(Path.cwd() / "results"))
        
        console.print(dirs_table)
        
        if Confirm.ask("📂 Change default directories?"):
            new_current = Prompt.ask("Working Directory", default=str(self.current_directory))
            self.current_directory = Path(new_current)
            console.print(f"[green]✅ Working directory set to: {self.current_directory}[/green]")
    
    async def _configure_processing(self):
        """Configure processing preferences"""
        console.print("\n[bold cyan]🔧 Processing Preferences[/bold cyan]")
        
        prefs_table = Table(title="Processing Preferences")
        prefs_table.add_column("Setting", style="cyan")
        prefs_table.add_column("Options", style="green")
        
        prefs_table.add_row("Default Analysis Level", "BASIC, STANDARD, DETAILED, PROFESSIONAL")
        prefs_table.add_row("Default AI Provider", "auto, openai, google_ai")
        prefs_table.add_row("Auto-save Results", "yes, no")
        prefs_table.add_row("Parallel Processing", "yes, no")
        
        console.print(prefs_table)
        console.print("[yellow]💡 Processing preferences configuration coming in next update![/yellow]")
    
    async def _manage_cache(self):
        """Manage system cache"""
        console.print("\n[bold cyan]💾 Cache Management[/bold cyan]")
        
        engine_stats = self.audio_engine.get_performance_stats()
        ai_stats = self.ai_manager.get_global_stats()
        
        cache_table = Table(title="Cache Status")
        cache_table.add_column("Cache Type", style="cyan")
        cache_table.add_column("Size", style="green")
        cache_table.add_column("Hit Rate", style="yellow")
        
        cache_table.add_row("Audio Features", str(engine_stats['cache_size']), f"{engine_stats['cache_hit_rate']:.1%}")
        cache_table.add_row("AI Responses", str(ai_stats.get('cache_size', 0)), f"{ai_stats.get('cache_hit_rate', 0):.1%}")
        
        console.print(cache_table)
        
        cache_choice = Prompt.ask("Cache action", 
                                choices=["view", "clear_audio", "clear_ai", "clear_all", "cancel"],
                                default="view")
        
        if cache_choice == "clear_audio":
            self.audio_engine.clear_cache()
            console.print("[green]✅ Audio cache cleared![/green]")
        elif cache_choice == "clear_ai":
            await self.ai_manager.clear_cache()
            console.print("[green]✅ AI cache cleared![/green]")
        elif cache_choice == "clear_all":
            self.audio_engine.clear_cache()
            await self.ai_manager.clear_cache()
            console.print("[green]✅ All caches cleared![/green]")
    
    async def _configure_logging(self):
        """Configure logging settings"""
        console.print("\n[bold cyan]📊 Logging Configuration[/bold cyan]")
        
        import logging
        current_level = logging.getLogger().level
        level_names = {10: "DEBUG", 20: "INFO", 30: "WARNING", 40: "ERROR"}
        
        log_table = Table(title="Logging Settings")
        log_table.add_column("Level", style="cyan")
        log_table.add_column("Description", style="green")
        log_table.add_column("Current", style="yellow")
        
        log_table.add_row("DEBUG", "Detailed debugging info", "✅" if current_level <= 10 else "")
        log_table.add_row("INFO", "General information", "✅" if current_level <= 20 else "")
        log_table.add_row("WARNING", "Warning messages", "✅" if current_level <= 30 else "")
        log_table.add_row("ERROR", "Error messages only", "✅" if current_level <= 40 else "")
        
        console.print(log_table)
        console.print(f"[cyan]Current Level: {level_names.get(current_level, current_level)}[/cyan]")
        
        if Confirm.ask("🔧 Change logging level?"):
            new_level = Prompt.ask("Logging level", 
                                 choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                                 default="INFO")
            level_value = {"DEBUG": 10, "INFO": 20, "WARNING": 30, "ERROR": 40}[new_level]
            logging.getLogger().setLevel(level_value)
            console.print(f"[green]✅ Logging level set to {new_level}![/green]")
    
    async def _configure_api_settings(self):
        """Configure API settings"""
        console.print("\n[bold cyan]🌐 API Settings[/bold cyan]")
        
        import os
        
        api_table = Table(title="API Configuration")
        api_table.add_column("Service", style="cyan")
        api_table.add_column("Status", style="green")
        api_table.add_column("Key Present", style="yellow")
        
        openai_key = "✅" if os.getenv('OPENAI_API_KEY') else "❌"
        google_key = "✅" if os.getenv('GOOGLE_AI_API_KEY') else "❌"
        
        api_table.add_row("OpenAI", "Available", openai_key)
        api_table.add_row("Google AI", "Available", google_key)
        
        console.print(api_table)
        
        console.print("\n[yellow]💡 To configure API keys, run:[/yellow]")
        console.print("  • [cyan]./setup_openai_api.sh[/cyan] - For OpenAI")
        console.print("  • [cyan]./setup_google_ai_api.sh[/cyan] - For Google AI")
    
    async def _export_import_config(self):
        """Export or import configuration"""
        console.print("\n[bold cyan]💾 Export/Import Configuration[/bold cyan]")
        
        action = Prompt.ask("Action", choices=["export", "import", "cancel"], default="export")
        
        if action == "export":
            config_data = {
                "audio_engine": {
                    "max_workers": self.audio_engine.max_workers,
                    "cache_size": self.audio_engine.cache_size
                },
                "directories": {
                    "current": str(self.current_directory)
                },
                "session": self.session_stats
            }
            
            import json
            config_file = Path("samplemind_config.json")
            with open(config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
            
            console.print(f"[green]✅ Configuration exported to: {config_file}[/green]")
        
        elif action == "import":
            config_file = Prompt.ask("Configuration file path", default="samplemind_config.json")
            try:
                import json
                with open(config_file, 'r') as f:
                    config_data = json.load(f)
                
                # Apply configuration
                if "audio_engine" in config_data:
                    self.audio_engine.max_workers = config_data["audio_engine"]["max_workers"]
                    self.audio_engine.cache_size = config_data["audio_engine"]["cache_size"]
                
                if "directories" in config_data:
                    self.current_directory = Path(config_data["directories"]["current"])
                
                console.print(f"[green]✅ Configuration imported from: {config_file}[/green]")
            except Exception as e:
                console.print(f"[red]❌ Failed to import configuration: {e}[/red]")
    
    async def show_ai_provider_settings(self):
        """Display and manage AI provider settings"""
        console.print("\n[bold blue]🤖 AI Provider Settings[/bold blue]")
        
        provider_status = self.ai_manager.get_provider_status()
        
        # Display current providers
        provider_table = Table(title="AI Provider Status")
        provider_table.add_column("Provider", style="cyan")
        provider_table.add_column("Status", style="green")
        provider_table.add_column("Model", style="yellow")
        provider_table.add_column("Requests", style="dim")
        provider_table.add_column("Avg Response Time", style="dim")
        
        for provider, status in provider_status.items():
            status_icon = "✅ Enabled" if status['enabled'] else "❌ Disabled"
            model = status.get('default_model', 'N/A')
            requests = status.get('total_requests', 0)
            avg_time = status.get('avg_response_time', 0)
            
            provider_table.add_row(
                provider,
                status_icon,
                model,
                str(requests),
                f"{avg_time:.2f}s"
            )
        
        console.print(provider_table)
        
        # Provider management options
        provider_actions = Table(show_header=False, box=None, padding=(0, 2))
        provider_actions.add_column("Option", style="bold cyan", width=3)
        provider_actions.add_column("Description", style="white")
        
        provider_actions.add_row("1", "🔧 Configure Provider Priority")
        provider_actions.add_row("2", "🎯 Test Provider Connection")
        provider_actions.add_row("3", "📊 View Provider Statistics")
        provider_actions.add_row("4", "⚙️ Model Settings")
        provider_actions.add_row("5", "🔄 Refresh Provider Status")
        provider_actions.add_row("0", "🔙 Back to Main Menu")
        
        panel = Panel(
            provider_actions,
            title="[bold blue]🤖 Provider Management[/bold blue]",
            border_style="blue"
        )
        console.print(panel)
        
        choice = Prompt.ask("🤖 Select action", choices=["0", "1", "2", "3", "4", "5"])
        
        if choice == "1":
            await self._configure_provider_priority()
        elif choice == "2":
            await self._test_provider_connections()
        elif choice == "3":
            await self._show_provider_statistics()
        elif choice == "4":
            await self._configure_model_settings()
        elif choice == "5":
            console.print("[cyan]🔄 Refreshing provider status...[/cyan]")
            # The status is already refreshed when we call get_provider_status()
            console.print("[green]✅ Provider status refreshed![/green]")
    
    async def _configure_provider_priority(self):
        """Configure AI provider priority"""
        console.print("\n[cyan]🔧 Configure Provider Priority[/cyan]")
        
        provider_status = self.ai_manager.get_provider_status()
        enabled_providers = [p for p, s in provider_status.items() if s['enabled']]
        
        if not enabled_providers:
            console.print("[red]❌ No providers enabled![/red]")
            return
        
        priority_table = Table(title="Current Priority Order")
        priority_table.add_column("Priority", style="cyan")
        priority_table.add_column("Provider", style="green")
        
        for i, provider in enumerate(enabled_providers, 1):
            priority_table.add_row(str(i), provider)
        
        console.print(priority_table)
        console.print("[yellow]💡 Priority configuration coming in next update![/yellow]")
    
    async def _test_provider_connections(self):
        """Test AI provider connections"""
        console.print("\n[cyan]🎯 Testing Provider Connections[/cyan]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            
            # Test with sample data
            sample_features = {
                'tempo': 120.0,
                'key': 'C',
                'mode': 'major',
                'duration': 30.0,
                'sample_rate': 44100
            }
            
            provider_status = self.ai_manager.get_provider_status()
            
            for provider, status in provider_status.items():
                if not status['enabled']:
                    continue
                
                task = progress.add_task(f"Testing {provider}...", total=None)
                
                try:
                    # Test quick analysis
                    result = await self.ai_manager.analyze_music(
                        sample_features,
                        AnalysisType.QUICK_ANALYSIS,
                        preferred_provider=AIProvider(provider.upper())
                    )
                    progress.remove_task(task)
                    console.print(f"[green]✅ {provider}: Connection successful[/green]")
                    
                except Exception as e:
                    progress.remove_task(task)
                    console.print(f"[red]❌ {provider}: {str(e)[:50]}...[/red]")
    
    async def _show_provider_statistics(self):
        """Show detailed provider statistics"""
        console.print("\n[cyan]📊 Provider Statistics[/cyan]")
        
        ai_stats = self.ai_manager.get_global_stats()
        
        stats_table = Table(title="Global AI Statistics")
        stats_table.add_column("Metric", style="cyan")
        stats_table.add_column("Value", style="green")
        
        stats_table.add_row("Total Requests", str(ai_stats.get('total_requests', 0)))
        stats_table.add_row("Total Tokens", str(ai_stats.get('total_tokens', 0)))
        stats_table.add_row("Average Response Time", f"{ai_stats.get('avg_response_time', 0):.2f}s")
        stats_table.add_row("Cache Hit Rate", f"{ai_stats.get('cache_hit_rate', 0):.1%}")
        
        console.print(stats_table)
    
    async def _configure_model_settings(self):
        """Configure model-specific settings"""
        console.print("\n[cyan]⚙️ Model Settings[/cyan]")
        
        models_table = Table(title="Available Models")
        models_table.add_column("Provider", style="cyan")
        models_table.add_column("Model", style="green")
        models_table.add_column("Description", style="dim")
        
        models_table.add_row("OpenAI", "gpt-5", "Latest and most advanced")
        models_table.add_row("OpenAI", "gpt-4o", "High quality, fast")
        models_table.add_row("OpenAI", "gpt-4o-mini", "Fast and cost-effective")
        models_table.add_row("Google AI", "gemini-1.5-pro", "Advanced reasoning")
        
        console.print(models_table)
        console.print("[yellow]💡 Model configuration coming in next update![/yellow]")
    
    async def show_production_tips(self):
        """Show production tips and coaching"""
        console.print("\n[bold blue]💡 Production Tips & Coaching[/bold blue]")
        
        tips_menu = Table(show_header=False, box=None, padding=(0, 2))
        tips_menu.add_column("Option", style="bold cyan", width=3)
        tips_menu.add_column("Description", style="white")
        
        tips_menu.add_row("1", "🎛️ Mixing Fundamentals")
        tips_menu.add_row("2", "🎵 Arrangement Techniques")
        tips_menu.add_row("3", "🔊 Mastering Basics")
        tips_menu.add_row("4", "🎹 Sound Design Tips")
        tips_menu.add_row("5", "📈 Workflow Optimization")
        tips_menu.add_row("6", "🎯 Genre-Specific Advice")
        tips_menu.add_row("7", "🤖 AI-Powered Coaching")
        tips_menu.add_row("0", "🔙 Back to Main Menu")
        
        panel = Panel(
            tips_menu,
            title="[bold blue]💡 Production Tips Menu[/bold blue]",
            border_style="blue"
        )
        console.print(panel)
        
        choice = Prompt.ask("💡 Select tip category", choices=["0", "1", "2", "3", "4", "5", "6", "7"])
        
        if choice == "0":
            return
        elif choice == "1":
            self._show_mixing_tips()
        elif choice == "2":
            self._show_arrangement_tips()
        elif choice == "3":
            self._show_mastering_tips()
        elif choice == "4":
            self._show_sound_design_tips()
        elif choice == "5":
            self._show_workflow_tips()
        elif choice == "6":
            await self._show_genre_specific_tips()
        elif choice == "7":
            await self._show_ai_coaching()
    
    def _show_mixing_tips(self):
        """Display mixing fundamentals"""
        console.print("\n[bold cyan]🎛️ Mixing Fundamentals[/bold cyan]")
        
        mixing_tips = [
            "🔊 **EQ First**: Always EQ before compression to shape the sound",
            "📊 **Reference Monitoring**: Use multiple speaker systems and headphones",
            "🎚️ **Gain Staging**: Keep levels consistent throughout your signal chain",
            "🔈 **Low-End Management**: Use high-pass filters to clean up unnecessary bass",
            "🎵 **Frequency Separation**: Give each element its own frequency space",
            "🎛️ **Compression Technique**: Use slow attack for punch, fast attack for control",
            "🌊 **Reverb & Delay**: Create depth with spatial effects, but don't overdo it",
            "📈 **Mix in Mono**: Check mono compatibility for translation across systems"
        ]
        
        for tip in mixing_tips:
            console.print(f"   {tip}")
        
        console.print("\n[yellow]💡 Pro Tip: Trust your ears over your eyes when mixing![/yellow]")
    
    def _show_arrangement_tips(self):
        """Display arrangement techniques"""
        console.print("\n[bold cyan]🎵 Arrangement Techniques[/bold cyan]")
        
        arrangement_tips = [
            "🎼 **Song Structure**: Intro → Verse → Chorus → Verse → Chorus → Bridge → Chorus → Outro",
            "🎹 **Layering**: Build complexity gradually, add/remove elements for dynamics",
            "🎚️ **Contrast**: Create tension and release with dynamic changes",
            "🎵 **Melodic Movement**: Keep melodies interesting with variation and development",
            "🥁 **Rhythm Variation**: Change drum patterns between sections for movement",
            "🎸 **Instrumental Roles**: Lead, rhythm, bass, percussion - define each element's purpose",
            "🎯 **Focus Elements**: Don't let everything compete - create a hierarchy",
            "⏰ **Timing**: Know when to introduce and remove elements for maximum impact"
        ]
        
        for tip in arrangement_tips:
            console.print(f"   {tip}")
        
        console.print("\n[yellow]💡 Pro Tip: Less is often more - every element should serve a purpose![/yellow]")
    
    def _show_mastering_tips(self):
        """Display mastering basics"""
        console.print("\n[bold cyan]🔊 Mastering Basics[/bold cyan]")
        
        mastering_tips = [
            "🎧 **Reference Tracks**: Compare your master to professional releases in your genre",
            "📊 **EQ Corrections**: Make subtle broad EQ moves to enhance the overall tone",
            "🔒 **Gentle Compression**: Use light compression to glue the mix together",
            "📈 **Limiting**: Use a limiter for final loudness control, but preserve dynamics",
            "🔊 **LUFS Targets**: Aim for -14 LUFS for streaming, -8 to -10 for club music",
            "🎵 **Stereo Imaging**: Enhance width carefully, keep bass centered",
            "⚡ **Transient Control**: Shape attack and sustain of the overall mix",
            "🎚️ **Multiple Versions**: Create different masters for different platforms"
        ]
        
        for tip in mastering_tips:
            console.print(f"   {tip}")
        
        console.print("\n[yellow]💡 Pro Tip: Mastering should enhance, not fix - get your mix right first![/yellow]")
    
    def _show_sound_design_tips(self):
        """Display sound design tips"""
        console.print("\n[bold cyan]🎹 Sound Design Tips[/bold cyan]")
        
        sound_design_tips = [
            "🎛️ **Start Simple**: Begin with basic waveforms and build complexity",
            "🔊 **Layering**: Combine multiple sounds for richness and depth",
            "⚡ **Modulation**: Use LFOs and envelopes to add movement and interest",
            "🎚️ **Filter Sweeps**: Automate filters for dynamic tonal changes",
            "🔄 **Effects Processing**: Reverb, delay, distortion for character",
            "🎵 **Harmonic Content**: Add overtones and harmonics for richness",
            "📊 **Frequency Analysis**: Use spectrum analyzer to understand your sounds",
            "🎯 **Context Mixing**: Design sounds to fit in the mix, not in isolation"
        ]
        
        for tip in sound_design_tips:
            console.print(f"   {tip}")
        
        console.print("\n[yellow]💡 Pro Tip: Record real-world sounds and process them for unique textures![/yellow]")
    
    def _show_workflow_tips(self):
        """Display workflow optimization tips"""
        console.print("\n[bold cyan]📈 Workflow Optimization[/bold cyan]")
        
        workflow_tips = [
            "⚡ **Templates**: Create project templates with your go-to instruments and effects",
            "🗂️ **Organization**: Use consistent naming conventions and folder structures",
            "💾 **Save Often**: Regular saves and version control prevent data loss",
            "🎹 **MIDI Mapping**: Map controllers to frequently used parameters",
            "⌨️ **Keyboard Shortcuts**: Learn and use DAW shortcuts for speed",
            "🎯 **Focus Sessions**: Dedicate specific sessions to writing, recording, mixing",
            "📋 **Track Bouncing**: Bounce MIDI to audio to free up CPU resources",
            "🔄 **Backup Strategy**: Automated backups to cloud and external drives"
        ]
        
        for tip in workflow_tips:
            console.print(f"   {tip}")
        
        console.print("\n[yellow]💡 Pro Tip: Spend time setting up your environment - it pays off in productivity![/yellow]")
    
    async def _show_genre_specific_tips(self):
        """Show genre-specific production advice"""
        console.print("\n[bold cyan]🎯 Genre-Specific Advice[/bold cyan]")
        
        genre = Prompt.ask("Select genre", 
                          choices=["house", "techno", "trap", "pop", "rock", "jazz", "ambient"],
                          default="house")
        
        genre_tips = {
            "house": [
                "🥁 **Four-on-the-floor**: Strong kick on every beat",
                "🎵 **Groove**: Swing and shuffle for that house feel",
                "🔊 **Bass**: Deep, warm basslines that complement the kick",
                "🎹 **Chords**: Warm pads and stabby chord progressions"
            ],
            "techno": [
                "⚡ **Driving Rhythm**: Relentless, hypnotic beats",
                "🔊 **Industrial Sounds**: Metallic, mechanical textures",
                "🎛️ **Automation**: Constant parameter changes for evolution",
                "📊 **Minimal Approach**: Less elements, more impact"
            ],
            "trap": [
                "🥁 **808s**: Deep, punchy 808 drums with long decay",
                "⚡ **Hi-hats**: Fast, syncopated hi-hat patterns",
                "🎵 **Melody**: Dark, minor scale melodies",
                "🔊 **Dynamics**: Heavy use of drops and buildups"
            ],
            "pop": [
                "🎵 **Catchy Hooks**: Memorable melodies and phrases",
                "🎚️ **Vocal Focus**: Vocals are the star, everything supports them",
                "📊 **Radio Ready**: Consistent levels, commercial sound",
                "🎹 **Instrument Balance**: Clear separation, nothing muddy"
            ],
            "rock": [
                "🎸 **Guitar Power**: Distorted power chords and riffs",
                "🥁 **Live Drums**: Natural, dynamic drum sounds",
                "🔊 **Energy**: High energy throughout, driving rhythms",
                "🎵 **Song Structure**: Traditional verse/chorus structures"
            ],
            "jazz": [
                "🎹 **Complex Harmony**: Extended chords and progressions",
                "🎵 **Improvisation**: Space for solos and musical expression",
                "🥁 **Swing Feel**: Rhythmic complexity and groove",
                "🎚️ **Natural Sound**: Minimal processing, acoustic instruments"
            ],
            "ambient": [
                "🌊 **Atmosphere**: Focus on mood and texture over rhythm",
                "⏰ **Long Forms**: Slow evolution over extended periods",
                "🔊 **Reverb**: Spacious, ethereal soundscapes",
                "🎵 **Minimalism**: Subtle changes, less is more"
            ]
        }
        
        console.print(f"\n[bold yellow]🎯 {genre.title()} Production Tips:[/bold yellow]")
        for tip in genre_tips[genre]:
            console.print(f"   {tip}")
        
        console.print(f"\n[yellow]💡 Pro Tip: Listen to reference tracks in {genre} and analyze their production techniques![/yellow]")
    
    async def _show_ai_coaching(self):
        """Provide AI-powered production coaching"""
        console.print("\n[bold cyan]🤖 AI-Powered Production Coaching[/bold cyan]")
        
        coaching_options = [
            "🎯 Get personalized tips based on your recent tracks",
            "🎵 Analyze a specific track for improvement suggestions",
            "📈 Production skill assessment and learning path",
            "🎛️ Technical problem solving assistance"
        ]
        
        for i, option in enumerate(coaching_options, 1):
            console.print(f"   {i}. {option}")
        
        choice = Prompt.ask("Select coaching option", choices=["1", "2", "3", "4"])
        
        if choice == "1":
            console.print("[cyan]🔍 Analyzing your session data for personalized tips...[/cyan]")
            await self._generate_personalized_tips()
        elif choice == "2":
            console.print("[cyan]📁 Select a track to analyze for improvement...[/cyan]")
            await self._analyze_track_for_coaching()
        else:
            console.print("[yellow]💡 Advanced AI coaching features coming in next update![/yellow]")
    
    async def _generate_personalized_tips(self):
        """Generate personalized tips based on session data"""
        session_duration = time.time() - self.session_stats['session_start']
        files_analyzed = self.session_stats['files_analyzed']
        
        if files_analyzed == 0:
            console.print("[yellow]💡 No tracks analyzed yet. Try analyzing some files first![/yellow]")
            return
        
        # Mock personalized coaching based on session stats
        tips = []
        
        if session_duration > 3600:  # More than 1 hour
            tips.append("⏰ **Take breaks**: You've been working for over an hour. Take regular breaks to keep your ears fresh!")
        
        if files_analyzed > 5:
            tips.append("📊 **Batch processing**: You've analyzed many files. Consider using batch processing for efficiency!")
        
        avg_time = self.session_stats['total_processing_time'] / files_analyzed
        if avg_time > 10:
            tips.append("⚡ **Optimize workflow**: Your average processing time is high. Consider using faster analysis modes for iteration!")
        
        tips.extend([
            "🎯 **Focus on fundamentals**: Master EQ, compression, and reverb before moving to advanced techniques",
            "🎵 **Reference often**: A/B compare your tracks with professional releases",
            "📈 **Track your progress**: Keep notes on what you learn in each session"
        ])
        
        console.print("\n[bold green]🤖 Your Personalized Tips:[/bold green]")
        for tip in tips[:5]:  # Show top 5 tips
            console.print(f"   {tip}")
    
    async def _analyze_track_for_coaching(self):
        """Analyze a specific track for coaching suggestions"""
        # Use existing file selection logic
        file_path = select_audio_file(
            title="Choose Track for AI Coaching Analysis",
            initial_directory=self.current_directory
        )
        
        if not file_path:
            console.print("[yellow]⚠️ No file selected[/yellow]")
            return
        
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                
                task = progress.add_task("🤖 Analyzing track for coaching insights...", total=None)
                
                # Analyze the track
                features = self.audio_engine.analyze_audio(file_path, level=AnalysisLevel.DETAILED)
                features_dict = features.to_dict()
                
                # Get AI coaching analysis
                ai_result = await self.ai_manager.analyze_music(
                    features_dict,
                    AnalysisType.PRODUCTION_ANALYSIS,
                    user_context={'goal': 'coaching', 'skill_level': 'intermediate'}
                )
                
                progress.remove_task(task)
            
            # Display coaching results
            console.print(f"\n[bold green]🎯 Coaching Analysis for: {file_path.name}[/bold green]")
            console.print(f"\n[cyan]Summary:[/cyan] {ai_result.summary}")
            
            if ai_result.production_tips:
                console.print("\n[bold yellow]💡 Specific Improvements:[/bold yellow]")
                for tip in ai_result.production_tips:
                    console.print(f"   • {tip}")
            
            if ai_result.fl_studio_recommendations:
                console.print("\n[bold magenta]🎛️ Technical Recommendations:[/bold magenta]")
                for rec in ai_result.fl_studio_recommendations:
                    console.print(f"   • {rec}")
        
        except Exception as e:
            console.print(f"[red]❌ Coaching analysis failed: {e}[/red]")
    
    async def show_fl_studio_integration(self):
        """Display FL Studio integration features"""
        console.print("\n[bold blue]🎛️ FL Studio Integration[/bold blue]")
        
        fl_menu = Table(show_header=False, box=None, padding=(0, 2))
        fl_menu.add_column("Option", style="bold cyan", width=3)
        fl_menu.add_column("Description", style="white")
        
        fl_menu.add_row("1", "🎹 Generate FL Studio Presets")
        fl_menu.add_row("2", "🎛️ Mixer Setup Recommendations")
        fl_menu.add_row("3", "🔗 Plugin Chain Suggestions")
        fl_menu.add_row("4", "📁 Project Template Generator")
        fl_menu.add_row("5", "🎯 FL-Specific Production Tips")
        fl_menu.add_row("6", "⚙️ Workflow Optimization")
        fl_menu.add_row("7", "🔄 Export Settings Guide")
        fl_menu.add_row("0", "🔙 Back to Main Menu")
        
        panel = Panel(
            fl_menu,
            title="[bold blue]🎛️ FL Studio Integration[/bold blue]",
            border_style="blue"
        )
        console.print(panel)
        
        choice = Prompt.ask("🎛️ Select FL Studio feature", choices=["0", "1", "2", "3", "4", "5", "6", "7"])
        
        if choice == "0":
            return
        elif choice == "1":
            await self._generate_fl_presets()
        elif choice == "2":
            await self._show_mixer_recommendations()
        elif choice == "3":
            await self._show_plugin_chains()
        elif choice == "4":
            await self._generate_project_template()
        elif choice == "5":
            self._show_fl_tips()
        elif choice == "6":
            self._show_fl_workflow()
        elif choice == "7":
            self._show_export_settings()
    
    async def _generate_fl_presets(self):
        """Generate FL Studio presets based on audio analysis"""
        console.print("\n[bold cyan]🎹 Generate FL Studio Presets[/bold cyan]")
        
        # Select audio file for preset generation
        file_path = select_audio_file(
            title="Choose Audio File for Preset Generation",
            initial_directory=self.current_directory
        )
        
        if not file_path:
            console.print("[yellow]⚠️ No file selected[/yellow]")
            return
        
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                
                task = progress.add_task("🔍 Analyzing audio for FL preset generation...", total=None)
                
                # Analyze the audio
                features = self.audio_engine.analyze_audio(file_path, level=AnalysisLevel.DETAILED)
                
                # Generate FL Studio preset based on features
                from samplemind.core.engine.audio_engine import FLStudioIntegration
                preset = FLStudioIntegration.generate_fl_preset(features)
                
                progress.remove_task(task)
            
            # Display preset information
            console.print(f"\n[bold green]🎹 Generated FL Studio Preset:[/bold green]")
            
            preset_table = Table(title=f"Preset: {preset['name']}")
            preset_table.add_column("Parameter", style="cyan")
            preset_table.add_column("Value", style="green")
            preset_table.add_column("Description", style="dim")
            
            preset_table.add_row("Tempo", f"{preset['tempo']:.1f} BPM", "Project tempo setting")
            preset_table.add_row("Key", f"{preset['key']} {preset['mode']}", "Musical key signature")
            
            console.print(preset_table)
            
            # Show suggested effects
            if preset['suggested_effects']:
                console.print("\n[bold yellow]🎛️ Recommended Effects:[/bold yellow]")
                for effect in preset['suggested_effects']:
                    console.print(f"   • {effect}")
            
            # Show mixer settings
            if preset['mixer_settings']:
                mixer_settings = preset['mixer_settings']
                console.print("\n[bold magenta]🎚️ Mixer Recommendations:[/bold magenta]")
                
                if 'eq' in mixer_settings:
                    eq = mixer_settings['eq']
                    console.print(f"   EQ: Low Cut @ {eq['low_cut']}Hz, Mid Boost: {eq['mid_boost']}dB")
                
                if 'compression' in mixer_settings:
                    comp = mixer_settings['compression']
                    console.print(f"   Compression: Ratio {comp['ratio']}:1, {comp['attack']} attack")
            
            # Ask to save preset
            if Confirm.ask("💾 Save FL Studio preset file?"):
                preset_file = file_path.with_suffix('.flp_preset.json')
                import json
                with open(preset_file, 'w') as f:
                    json.dump(preset, f, indent=2)
                console.print(f"[green]✅ Preset saved: {preset_file}[/green]")
        
        except Exception as e:
            console.print(f"[red]❌ Preset generation failed: {e}[/red]")
    
    async def _show_mixer_recommendations(self):
        """Show FL Studio mixer setup recommendations"""
        console.print("\n[bold cyan]🎛️ FL Studio Mixer Recommendations[/bold cyan]")
        
        mixer_tips = [
            "🎛️ **Channel Rack Organization**: Group similar instruments on adjacent mixer tracks",
            "🎚️ **Send Effects**: Use Send tracks for reverb and delay instead of individual inserts",
            "📊 **EQ Strategy**: High-pass unnecessary low frequencies, boost presence frequencies",
            "🔊 **Compression**: Use Fruity Compressor for general dynamics, Maximus for multiband",
            "🎵 **Sidechain**: Use Fruity Peak Controller for sidechain compression effects",
            "🔗 **Routing**: Route drums to a bus for group processing",
            "📈 **Automation**: Automate send levels for dynamic effects",
            "🎯 **Master Chain**: EQ → Compression → Limiting on master channel"
        ]
        
        for tip in mixer_tips:
            console.print(f"   {tip}")
        
        console.print("\n[yellow]💡 Pro Tip: Use FL's built-in analyzer plugins to visualize your frequency spectrum![/yellow]")
    
    async def _show_plugin_chains(self):
        """Show recommended FL Studio plugin chains"""
        console.print("\n[bold cyan]🔗 FL Studio Plugin Chain Suggestions[/bold cyan]")
        
        chain_types = {
            "Vocal": [
                "1. Fruity Parametric EQ 2 (High-pass @ 80Hz)",
                "2. Fruity Compressor (3:1 ratio, medium attack)",
                "3. Fruity DeEsser (if needed)",
                "4. Fruity Parametric EQ 2 (Presence boost @ 3-5kHz)",
                "5. Fruity Reverb 2 (Send track)"
            ],
            "Drums": [
                "1. Fruity Parametric EQ 2 (Shape for punch)",
                "2. Fruity Compressor (Fast attack, auto release)",
                "3. Fruity Multiband Compressor (Maximus)",
                "4. Fruity Limiter (Gentle limiting)"
            ],
            "Bass": [
                "1. Fruity Parametric EQ 2 (Low-end sculpting)",
                "2. Fruity Compressor (Slow attack, fast release)",
                "3. Fruity Waveshaper (Harmonic saturation)",
                "4. Fruity Parametric EQ 2 (High-frequency control)"
            ],
            "Lead/Synth": [
                "1. Fruity Parametric EQ 2 (Frequency carving)",
                "2. Fruity Chorus (Width and movement)",
                "3. Fruity Delay 3 (Rhythmic delays)",
                "4. Fruity Reverb 2 (Spatial depth)"
            ]
        }
        
        chain_type = Prompt.ask("Select instrument type", 
                               choices=list(chain_types.keys()),
                               default="Vocal")
        
        console.print(f"\n[bold green]🔗 {chain_type} Plugin Chain:[/bold green]")
        for step in chain_types[chain_type]:
            console.print(f"   {step}")
        
        console.print(f"\n[yellow]💡 Tip: Adjust parameters based on the specific {chain_type.lower()} source material![/yellow]")
    
    async def _generate_project_template(self):
        """Generate FL Studio project template"""
        console.print("\n[bold cyan]📁 Project Template Generator[/bold cyan]")
        
        template_types = {
            "House": {
                "bpm": 128,
                "tracks": ["Kick", "Bass", "Lead", "Pads", "Percussion", "FX"],
                "effects": ["Reverb Send", "Delay Send", "Master Bus"]
            },
            "Trap": {
                "bpm": 140,
                "tracks": ["808", "Kick", "Snare", "Hi-hats", "Melody", "Lead"],
                "effects": ["Reverb Send", "Distortion", "Master Bus"]
            },
            "Pop": {
                "bpm": 120,
                "tracks": ["Drums", "Bass", "Guitar", "Vocals", "Synths", "Strings"],
                "effects": ["Vocal Reverb", "Instrument Reverb", "Master Bus"]
            }
        }
        
        template_type = Prompt.ask("Select template type", 
                                  choices=list(template_types.keys()),
                                  default="House")
        
        template = template_types[template_type]
        
        console.print(f"\n[bold green]📁 {template_type} Project Template:[/bold green]")
        console.print(f"   🎵 **BPM**: {template['bpm']}")
        console.print(f"   🎛️ **Mixer Tracks**: {len(template['tracks'])} channels")
        
        for i, track in enumerate(template['tracks'], 1):
            console.print(f"      Track {i}: {track}")
        
        console.print(f"   🔊 **Effect Sends**: {len(template['effects'])} sends")
        for effect in template['effects']:
            console.print(f"      • {effect}")
        
        console.print("\n[yellow]💡 Pro Tip: Save this as an FL Studio template file for quick project starts![/yellow]")
    
    def _show_fl_tips(self):
        """Show FL Studio specific production tips"""
        console.print("\n[bold cyan]🎯 FL Studio Production Tips[/bold cyan]")
        
        fl_tips = [
            "⌨️ **Shortcuts**: Learn F9 (Mixer), F5 (Playlist), F6 (Step Sequencer)",
            "🎹 **Piano Roll**: Use Alt+L to legato notes, Ctrl+L to select linked",
            "🎛️ **Mixer Tricks**: Right-click to link controls, use Peak Controller for sidechaining",
            "📊 **Playlist**: Use Ctrl+G to group clips, Alt+G to ungroup",
            "🔄 **Automation**: Right-click any knob and select 'Edit Events' for precision",
            "🎵 **Step Sequencer**: Use swing settings for groove, layer patterns for variation",
            "💾 **Project Management**: Save different versions, use 'Save New Version'",
            "🎯 **CPU Optimization**: Freeze tracks with complex processing"
        ]
        
        for tip in fl_tips:
            console.print(f"   {tip}")
        
        console.print("\n[yellow]💡 Master Tip: Use FL's lifetime free updates - always stay current![/yellow]")
    
    def _show_fl_workflow(self):
        """Show FL Studio workflow optimization"""
        console.print("\n[bold cyan]⚙️ FL Studio Workflow Optimization[/bold cyan]")
        
        workflow_sections = {
            "Composing": [
                "Start with Step Sequencer for drum patterns",
                "Use Piano Roll for melodies and chords",
                "Layer instruments in the Channel Rack",
                "Arrange in Playlist view"
            ],
            "Mixing": [
                "Group related tracks in Mixer",
                "Use Color coding for organization",
                "Set up Send tracks early",
                "Mix with reference tracks"
            ],
            "Efficiency": [
                "Create custom templates",
                "Use keyboard shortcuts extensively",
                "Save channel presets",
                "Organize samples in Browser"
            ]
        }
        
        for section, tips in workflow_sections.items():
            console.print(f"\n[bold yellow]{section}:[/bold yellow]")
            for tip in tips:
                console.print(f"   • {tip}")
        
        console.print("\n[yellow]💡 Workflow Tip: Spend time customizing FL Studio to match your creative process![/yellow]")
    
    def _show_export_settings(self):
        """Show FL Studio export settings guide"""
        console.print("\n[bold cyan]🔄 FL Studio Export Settings Guide[/bold cyan]")
        
        export_formats = {
            "Streaming (Spotify, Apple Music)": {
                "format": "WAV 24-bit",
                "sample_rate": "44.1 kHz",
                "lufs": "-14 LUFS",
                "notes": "Use Fruity Limiter with LUFS metering"
            },
            "Club/DJ Play": {
                "format": "WAV 24-bit",
                "sample_rate": "44.1 kHz",
                "lufs": "-8 to -10 LUFS",
                "notes": "Higher loudness for club systems"
            },
            "Mastering": {
                "format": "WAV 32-bit float",
                "sample_rate": "48 kHz or higher",
                "lufs": "No limiting",
                "notes": "Full dynamic range for mastering engineer"
            },
            "Demo/Rough Mix": {
                "format": "MP3 320 kbps",
                "sample_rate": "44.1 kHz",
                "lufs": "-12 LUFS",
                "notes": "Good quality, smaller file size"
            }
        }
        
        format_type = Prompt.ask("Select export purpose", 
                                choices=list(export_formats.keys()),
                                default="Streaming (Spotify, Apple Music)")
        
        settings = export_formats[format_type]
        
        console.print(f"\n[bold green]🔄 Export Settings for {format_type}:[/bold green]")
        for key, value in settings.items():
            if key != "notes":
                console.print(f"   📊 **{key.title().replace('_', ' ')}**: {value}")
        
        console.print(f"\n[yellow]💡 Note: {settings['notes']}[/yellow]")
        
        console.print("\n[cyan]📋 FL Studio Export Steps:[/cyan]")
        console.print("   1. File → Export → Wave file")
        console.print("   2. Set quality settings based on purpose")
        console.print("   3. Choose 'Full song' or selection")
        console.print("   4. Enable 'Split mixer tracks' if needed")
        console.print("   5. Click 'Start' to export")
    
    def _display_analysis_results(self, ai_result, loaded_audio, features):
        """Display comprehensive analysis results"""
        
        # File info panel
        info_table = Table(show_header=False, box=None)
        info_table.add_column("Property", style="cyan")
        info_table.add_column("Value", style="white")
        
        info_table.add_row("📁 File", loaded_audio.metadata.file_path.name)
        info_table.add_row("⏱️ Duration", f"{loaded_audio.get_duration_seconds():.2f}s")
        info_table.add_row("🎵 Tempo", f"{features.tempo:.1f} BPM")
        info_table.add_row("🎼 Key", f"{features.key} {features.mode}")
        info_table.add_row("📊 Sample Rate", f"{loaded_audio.metadata.sample_rate} Hz")
        info_table.add_row("🤖 AI Provider", ai_result.provider.value)
        info_table.add_row("⚡ Processing Time", f"{ai_result.processing_time:.2f}s")
        
        file_panel = Panel(
            info_table,
            title="📋 File Information",
            border_style="blue"
        )
        console.print(file_panel)
        
        # AI Analysis summary
        summary_panel = Panel(
            ai_result.summary,
            title="🤖 AI Analysis Summary",
            border_style="green"
        )
        console.print(summary_panel)
        
        # Production tips
        if ai_result.production_tips:
            tips_text = "\n".join([f"• {tip}" for tip in ai_result.production_tips])
            tips_panel = Panel(
                tips_text,
                title="💡 Production Tips",
                border_style="yellow"
            )
            console.print(tips_panel)
        
        # FL Studio recommendations
        if ai_result.fl_studio_recommendations:
            fl_text = "\n".join([f"• {rec}" for rec in ai_result.fl_studio_recommendations])
            fl_panel = Panel(
                fl_text,
                title="🎛️ FL Studio Recommendations",
                border_style="magenta"
            )
            console.print(fl_panel)
        
        # Scores
        scores_table = Table(title="🏆 Quality Scores")
        scores_table.add_column("Aspect", style="cyan")
        scores_table.add_column("Score", style="green")
        scores_table.add_column("Rating", style="yellow")
        
        def get_rating(score):
            if score >= 0.8: return "🌟 Excellent"
            elif score >= 0.6: return "⭐ Good"
            elif score >= 0.4: return "✨ Average"
            else: return "💫 Needs Work"
        
        scores_table.add_row("Creativity", f"{ai_result.creativity_score:.2f}", get_rating(ai_result.creativity_score))
        scores_table.add_row("Production Quality", f"{ai_result.production_quality_score:.2f}", get_rating(ai_result.production_quality_score))
        scores_table.add_row("Commercial Potential", f"{ai_result.commercial_potential_score:.2f}", get_rating(ai_result.commercial_potential_score))
        
        console.print(scores_table)
    
    def _display_batch_summary(self, results, processing_time):
        """Display batch processing summary"""
        if not results:
            return
        
        # Calculate statistics
        creativity_scores = [r['ai_result'].creativity_score for r in results]
        production_scores = [r['ai_result'].production_quality_score for r in results]
        
        avg_creativity = sum(creativity_scores) / len(creativity_scores)
        avg_production = sum(production_scores) / len(production_scores)
        
        summary_table = Table(title="📊 Batch Processing Summary")
        summary_table.add_column("Metric", style="cyan")
        summary_table.add_column("Value", style="green")
        
        summary_table.add_row("Files Processed", str(len(results)))
        summary_table.add_row("Total Time", f"{processing_time:.1f}s")
        summary_table.add_row("Avg Time Per File", f"{processing_time / len(results):.2f}s")
        summary_table.add_row("Avg Creativity Score", f"{avg_creativity:.2f}")
        summary_table.add_row("Avg Production Score", f"{avg_production:.2f}")
        
        console.print(summary_table)
        
        # Top files by creativity
        top_creative = sorted(results, key=lambda x: x['ai_result'].creativity_score, reverse=True)[:5]
        
        top_table = Table(title="🌟 Top Creative Files")
        top_table.add_column("File", style="cyan")
        top_table.add_column("Creativity", style="green")
        top_table.add_column("Production", style="yellow")
        
        for result in top_creative:
            file_name = Path(result['file']).name
            creativity = result['ai_result'].creativity_score
            production = result['ai_result'].production_quality_score
            top_table.add_row(file_name, f"{creativity:.2f}", f"{production:.2f}")
        
        console.print(top_table)
    
    def _display_directory_info(self, dir_info):
        """Display directory scanning info"""
        
        summary_table = Table(title="📁 Directory Summary")
        summary_table.add_column("Property", style="cyan")
        summary_table.add_column("Value", style="green")
        
        summary_table.add_row("Total Files", str(dir_info['total_files']))
        summary_table.add_row("Total Size", f"{dir_info['total_size'] / (1024*1024):.1f} MB")
        
        console.print(summary_table)
        
        # Format distribution
        if dir_info['format_distribution']:
            format_table = Table(title="🎵 Format Distribution")
            format_table.add_column("Format", style="cyan")
            format_table.add_column("Count", style="green")
            format_table.add_column("Percentage", style="yellow")
            
            total = dir_info['total_files']
            for fmt, count in dir_info['format_distribution'].items():
                percentage = (count / total) * 100 if total > 0 else 0
                format_table.add_row(fmt, str(count), f"{percentage:.1f}%")
            
            console.print(format_table)
    
    def _save_analysis(self, ai_result, loaded_audio, features, output_file):
        """Save analysis results to file"""
        import json
        
        result = {
            'timestamp': time.time(),
            'file_info': {
                'path': str(loaded_audio.metadata.file_path),
                'duration': loaded_audio.get_duration_seconds(),
                'sample_rate': loaded_audio.metadata.sample_rate,
                'format': loaded_audio.metadata.format.name,
            },
            'audio_features': features.to_dict(),
            'ai_analysis': {
                'provider': ai_result.provider.value,
                'model': ai_result.model_used,
                'summary': ai_result.summary,
                'production_tips': ai_result.production_tips,
                'fl_studio_recommendations': ai_result.fl_studio_recommendations,
                'scores': {
                    'creativity': ai_result.creativity_score,
                    'production_quality': ai_result.production_quality_score,
                    'commercial_potential': ai_result.commercial_potential_score
                }
            }
        }
        
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
    
    async def run(self):
        """Main CLI loop"""
        self.display_banner()
        
        # Initialize system
        if not await self.initialize_system():
            console.print("[bold red]❌ Failed to initialize SampleMind AI[/bold red]")
            return
        
        while True:
            try:
                console.print("\n")
                self.display_main_menu()
                
                choice = Prompt.ask("\n🎵 Select option", choices=["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "A", "a"])
                
                if choice == "0":
                    console.print("\n[bold blue]👋 Thank you for using SampleMind AI v6![/bold blue]")
                    break
                elif choice == "1":
                    await self.run_single_analysis()
                elif choice == "2":
                    await self.run_batch_processing()
                elif choice == "3":
                    await self.run_multiple_files_analysis()
                elif choice == "4":
                    self.scan_and_preview()
                elif choice == "5":
                    await self.show_configuration_menu()
                elif choice == "6":
                    self.show_system_status()
                elif choice == "7":
                    await self.show_ai_provider_settings()
                elif choice == "8":
                    await self.show_production_tips()
                elif choice == "9":
                    await self.show_fl_studio_integration()
                elif choice.upper() == "A":
                    self.show_session_analytics()
                
                # Pause before showing menu again
                if choice != "0":
                    Prompt.ask("\n[dim]Press Enter to continue...[/dim]", default="")
                
            except KeyboardInterrupt:
                console.print("\n[yellow]👋 Goodbye![/yellow]")
                break
            except Exception as e:
                console.print(f"[bold red]❌ Error: {e}[/bold red]")


async def main():
    """Entry point for the CLI"""
    cli = SampleMindCLI()
    await cli.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[yellow]👋 Goodbye![/yellow]")
    except Exception as e:
        console.print(f"[bold red]❌ Unexpected error: {e}[/bold red]")