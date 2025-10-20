#!/usr/bin/env python3
"""
SampleMind AI v6 - Main Entry Point
Professional AI-powered music production suite

Usage:
    python main.py                    # Interactive CLI menu
    python main.py --help            # Show help
    python main.py analyze <file>    # Quick analysis
    python main.py batch <directory> # Batch processing
"""

import argparse
import asyncio
import sys
from pathlib import Path

# Add src to Python path
sys.path.append(str(Path(__file__).parent / "src"))

from src.samplemind.interfaces.cli.menu import SampleMindCLI, main as cli_main


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="🎵 SampleMind AI v6 - Professional Music Production Suite",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                           # Start interactive menu
  python main.py analyze song.wav         # Analyze single file
  python main.py batch ./music_folder     # Process directory
  python main.py --setup-openai          # Setup OpenAI API
  python main.py --setup-google          # Setup Google AI API
        """
    )
    
    parser.add_argument(
        "command",
        nargs="?",
        choices=["analyze", "batch", "scan", "status"],
        help="Command to execute"
    )
    
    parser.add_argument(
        "path",
        nargs="?",
        help="File or directory path"
    )
    
    parser.add_argument(
        "--setup-openai",
        action="store_true",
        help="Run OpenAI API setup"
    )
    
    parser.add_argument(
        "--setup-google",
        action="store_true",
        help="Run Google AI API setup"
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version="SampleMind AI v6.0.0"
    )
    
    return parser.parse_args()


async def quick_analyze(file_path: str):
    """Quick file analysis without menu"""
    from src.samplemind.core.engine.audio_engine import AudioEngine, AnalysisLevel
    from src.samplemind.core.loader import AdvancedAudioLoader, LoadingStrategy
    from src.samplemind.integrations.ai_manager import SampleMindAIManager, AnalysisType
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, TextColumn
    
    console = Console()
    file_path = Path(file_path)
    
    if not file_path.exists():
        console.print(f"[bold red]❌ File not found: {file_path}[/bold red]")
        return
    
    try:
        console.print(f"[bold blue]🎵 Analyzing: {file_path.name}[/bold blue]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            
            # Initialize components
            progress.add_task("Initializing...", total=None)
            audio_engine = AudioEngine()
            audio_loader = AdvancedAudioLoader()
            ai_manager = SampleMindAIManager()
            
            # Process file
            progress.add_task("Loading audio...", total=None)
            loaded_audio = audio_loader.load_audio(file_path)
            
            progress.add_task("Extracting features...", total=None)
            features = audio_engine.analyze_audio(file_path)
            
            progress.add_task("AI analysis...", total=None)
            ai_result = await ai_manager.analyze_music(
                features.to_dict(),
                AnalysisType.COMPREHENSIVE_ANALYSIS
            )
        
        # Display quick results
        console.print(f"\n[bold green]✅ Analysis Complete[/bold green]")
        console.print(f"[cyan]Duration:[/cyan] {loaded_audio.get_duration_seconds():.2f}s")
        console.print(f"[cyan]Tempo:[/cyan] {features.tempo:.1f} BPM")
        console.print(f"[cyan]Key:[/cyan] {features.key} {features.mode}")
        console.print(f"[cyan]Provider:[/cyan] {ai_result.provider.value}")
        console.print(f"\n[bold blue]🤖 AI Summary:[/bold blue]")
        console.print(ai_result.summary)
        
    except Exception as e:
        console.print(f"[bold red]❌ Analysis failed: {e}[/bold red]")


def run_setup_script(script_name: str):
    """Run setup script"""
    import subprocess
    from rich.console import Console
    
    console = Console()
    script_path = Path(__file__).parent / script_name
    
    if not script_path.exists():
        console.print(f"[bold red]❌ Setup script not found: {script_path}[/bold red]")
        return
    
    try:
        console.print(f"[bold blue]🚀 Running {script_name}...[/bold blue]")
        subprocess.run(["bash", str(script_path)], check=True)
    except subprocess.CalledProcessError as e:
        console.print(f"[bold red]❌ Setup failed: {e}[/bold red]")


async def main():
    """Main entry point"""
    args = parse_args()
    
    # Handle setup commands
    if args.setup_openai:
        run_setup_script("setup_openai_api.sh")
        return
    
    if args.setup_google:
        run_setup_script("setup_google_ai_api.sh")
        return
    
    # Handle quick commands
    if args.command == "analyze" and args.path:
        await quick_analyze(args.path)
        return
    
    # For other commands or no command, start interactive CLI
    await cli_main()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)