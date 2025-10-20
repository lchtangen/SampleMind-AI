#!/usr/bin/env python3
"""
Viral Growth Features for SampleMind AI
Implements sharing prompts, achievement system, and referral tracking
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

class AchievementSystem:
    """Track and display user achievements"""
    
    ACHIEVEMENTS = {
        "first_analysis": {
            "name": "🎯 First Analysis",
            "description": "Analyzed your first sample",
            "points": 10
        },
        "batch_master": {
            "name": "📁 Batch Master",
            "description": "Processed 10+ files in one session",
            "points": 25
        },
        "speed_demon": {
            "name": "⚡ Speed Demon",
            "description": "Analyzed 100+ samples",
            "points": 50
        },
        "theme_explorer": {
            "name": "🎨 Theme Explorer",
            "description": "Tried 5+ different themes",
            "points": 15
        },
        "ai_wizard": {
            "name": "🤖 AI Wizard",
            "description": "Used 3+ different AI models",
            "points": 20
        },
        "community_builder": {
            "name": "👥 Community Builder",
            "description": "Referred 5+ users",
            "points": 100
        },
        "power_user": {
            "name": "💪 Power User",
            "description": "Used SampleMind for 30+ days",
            "points": 75
        },
        "contributor": {
            "name": "⭐ Contributor",
            "description": "Contributed to the project",
            "points": 200
        }
    }
    
    def __init__(self, stats_file: Optional[Path] = None):
        self.stats_file = stats_file or Path.home() / ".samplemind" / "stats.json"
        self.stats_file.parent.mkdir(parents=True, exist_ok=True)
        self.stats = self._load_stats()
    
    def _load_stats(self) -> Dict:
        """Load user statistics"""
        if self.stats_file.exists():
            with open(self.stats_file, 'r') as f:
                return json.load(f)
        return {
            "total_analyses": 0,
            "total_files": 0,
            "themes_used": [],
            "models_used": [],
            "referrals": 0,
            "days_active": [],
            "achievements_unlocked": [],
            "install_date": datetime.now().isoformat(),
            "referred_by": None
        }
    
    def _save_stats(self):
        """Save user statistics"""
        with open(self.stats_file, 'w') as f:
            json.dump(self.stats, f, indent=2)
    
    def record_analysis(self, files_count: int = 1):
        """Record an analysis session"""
        self.stats["total_analyses"] += 1
        self.stats["total_files"] += files_count
        
        # Track active days
        today = datetime.now().date().isoformat()
        if today not in self.stats["days_active"]:
            self.stats["days_active"].append(today)
        
        self._save_stats()
        self._check_achievements()
    
    def record_theme_use(self, theme: str):
        """Record theme usage"""
        if theme not in self.stats["themes_used"]:
            self.stats["themes_used"].append(theme)
            self._save_stats()
            self._check_achievements()
    
    def record_model_use(self, model: str):
        """Record AI model usage"""
        if model not in self.stats["models_used"]:
            self.stats["models_used"].append(model)
            self._save_stats()
            self._check_achievements()
    
    def record_referral(self):
        """Record a referral"""
        self.stats["referrals"] += 1
        self._save_stats()
        self._check_achievements()
    
    def set_referred_by(self, referrer: str):
        """Set who referred this user"""
        if not self.stats.get("referred_by"):
            self.stats["referred_by"] = referrer
            self._save_stats()
    
    def _check_achievements(self):
        """Check and unlock new achievements"""
        newly_unlocked = []
        
        # First Analysis
        if self.stats["total_analyses"] >= 1 and "first_analysis" not in self.stats["achievements_unlocked"]:
            self.stats["achievements_unlocked"].append("first_analysis")
            newly_unlocked.append("first_analysis")
        
        # Batch Master
        if self.stats["total_files"] >= 10 and "batch_master" not in self.stats["achievements_unlocked"]:
            self.stats["achievements_unlocked"].append("batch_master")
            newly_unlocked.append("batch_master")
        
        # Speed Demon
        if self.stats["total_files"] >= 100 and "speed_demon" not in self.stats["achievements_unlocked"]:
            self.stats["achievements_unlocked"].append("speed_demon")
            newly_unlocked.append("speed_demon")
        
        # Theme Explorer
        if len(self.stats["themes_used"]) >= 5 and "theme_explorer" not in self.stats["achievements_unlocked"]:
            self.stats["achievements_unlocked"].append("theme_explorer")
            newly_unlocked.append("theme_explorer")
        
        # AI Wizard
        if len(self.stats["models_used"]) >= 3 and "ai_wizard" not in self.stats["achievements_unlocked"]:
            self.stats["achievements_unlocked"].append("ai_wizard")
            newly_unlocked.append("ai_wizard")
        
        # Community Builder
        if self.stats["referrals"] >= 5 and "community_builder" not in self.stats["achievements_unlocked"]:
            self.stats["achievements_unlocked"].append("community_builder")
            newly_unlocked.append("community_builder")
        
        # Power User
        if len(self.stats["days_active"]) >= 30 and "power_user" not in self.stats["achievements_unlocked"]:
            self.stats["achievements_unlocked"].append("power_user")
            newly_unlocked.append("power_user")
        
        if newly_unlocked:
            self._save_stats()
            self._display_new_achievements(newly_unlocked)
    
    def _display_new_achievements(self, achievements: List[str]):
        """Display newly unlocked achievements"""
        for achievement_id in achievements:
            achievement = self.ACHIEVEMENTS[achievement_id]
            console.print(Panel(
                f"[bold yellow]{achievement['name']}[/bold yellow]\n"
                f"{achievement['description']}\n"
                f"[cyan]+{achievement['points']} points[/cyan]",
                title="🎉 Achievement Unlocked!",
                border_style="yellow"
            ))
    
    def display_achievements(self):
        """Display all achievements"""
        table = Table(title="🏆 Achievements")
        table.add_column("Achievement", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Points", style="yellow")
        
        total_points = 0
        for achievement_id, achievement in self.ACHIEVEMENTS.items():
            unlocked = achievement_id in self.stats["achievements_unlocked"]
            status = "✅ Unlocked" if unlocked else "🔒 Locked"
            table.add_row(
                f"{achievement['name']}\n{achievement['description']}",
                status,
                str(achievement['points']) if unlocked else "—"
            )
            if unlocked:
                total_points += achievement['points']
        
        console.print(table)
        console.print(f"\n[bold cyan]Total Points: {total_points}[/bold cyan]")
    
    def get_stats_summary(self) -> Dict:
        """Get statistics summary"""
        return {
            "total_analyses": self.stats["total_analyses"],
            "total_files": self.stats["total_files"],
            "achievements": len(self.stats["achievements_unlocked"]),
            "days_active": len(self.stats["days_active"]),
            "referrals": self.stats["referrals"]
        }


class SharingPrompts:
    """Encourage organic sharing after successful operations"""
    
    @staticmethod
    def show_share_prompt(context: str = "analysis"):
        """Show sharing prompt based on context"""
        prompts = {
            "analysis": """
💡 Love SampleMind AI? Share your results!
   • Screenshot: Cmd+Shift+4 (Mac) or Win+Shift+S (Windows)
   • Tag: @samplemindai #SampleMindAI
   • Get featured on our showcase!
   
   🌟 Star us on GitHub: https://github.com/lchtangen/samplemind-ai
   💬 Join Discord: https://discord.gg/samplemind
""",
            "achievement": """
🎉 Achievement unlocked! Share it with the community!
   • Post on Twitter/X with #SampleMindAI
   • Share in our Discord #achievements channel
   • Inspire other producers!
""",
            "milestone": """
🚀 You've reached a milestone! 
   • Share your journey with #SampleMindAI
   • Help others discover the tool
   • Join our growing community of 500+ producers
"""
        }
        
        console.print(Panel(
            prompts.get(context, prompts["analysis"]),
            title="[bold cyan]Share the Love[/bold cyan]",
            border_style="cyan"
        ))
    
    @staticmethod
    def show_referral_info():
        """Show referral program information"""
        console.print(Panel(
            """
👥 Refer friends and unlock exclusive themes!

How it works:
1. Share your referral link: samplemind.ai?ref=YOUR_USERNAME
2. When 5 friends install, unlock special themes
3. Both you and your friend get bonus features!

Current referrals: Check with 'samplemind stats --referrals'
""",
            title="[bold yellow]Referral Program[/bold yellow]",
            border_style="yellow"
        ))


class ViralGrowthManager:
    """Manage all viral growth features"""
    
    def __init__(self):
        self.achievements = AchievementSystem()
        self.sharing = SharingPrompts()
    
    def on_analysis_complete(self, files_count: int = 1):
        """Called after successful analysis"""
        self.achievements.record_analysis(files_count)
        
        # Show sharing prompt occasionally (every 5th analysis)
        if self.achievements.stats["total_analyses"] % 5 == 0:
            self.sharing.show_share_prompt("analysis")
    
    def on_milestone_reached(self, milestone: str):
        """Called when user reaches a milestone"""
        self.sharing.show_share_prompt("milestone")
    
    def display_stats(self):
        """Display user statistics"""
        stats = self.achievements.get_stats_summary()
        
        table = Table(title="📊 Your SampleMind AI Stats")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Total Analyses", str(stats["total_analyses"]))
        table.add_row("Files Processed", str(stats["total_files"]))
        table.add_row("Achievements Unlocked", f"{stats['achievements']}/{len(self.achievements.ACHIEVEMENTS)}")
        table.add_row("Days Active", str(stats["days_active"]))
        table.add_row("Referrals", str(stats["referrals"]))
        
        console.print(table)
        
        # Show achievements
        self.achievements.display_achievements()

