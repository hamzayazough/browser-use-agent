"""Storage for UX feedback."""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from shared.models import UXFeedback


class FeedbackStorage:
    """Simple storage for UX feedback."""
    
    def __init__(self, storage_path: Optional[Path] = None):
        """
        Initialize feedback storage.
        
        Args:
            storage_path: Path to store feedback JSON file. If None, uses memory only.
        """
        self.storage_path = storage_path
        self.feedback_list: list[UXFeedback] = []
        
        # Load existing feedback if file exists
        if storage_path and storage_path.exists():
            self._load_from_file()
    
    def store(self, feedback: UXFeedback):
        """Store a new feedback entry."""
        self.feedback_list.append(feedback)
        
        # Persist to file if path is set
        if self.storage_path:
            self._save_to_file()
    
    def get_all(self) -> list[UXFeedback]:
        """Get all stored feedback."""
        return self.feedback_list
    
    def get_by_url(self, url: str) -> list[UXFeedback]:
        """Get feedback for a specific URL."""
        return [f for f in self.feedback_list if f.url == url]
    
    def get_recent(self, n: int = 10) -> list[UXFeedback]:
        """Get the n most recent feedback entries."""
        return self.feedback_list[-n:]
    
    def clear(self):
        """Clear all stored feedback."""
        self.feedback_list.clear()
        if self.storage_path and self.storage_path.exists():
            self.storage_path.unlink()
    
    def get_summary(self) -> dict:
        """Get summary statistics."""
        if not self.feedback_list:
            return {
                "total_feedback": 0,
                "average_confidence": 0,
                "unique_urls": 0,
            }
        
        return {
            "total_feedback": len(self.feedback_list),
            "average_confidence": sum(f.confidence for f in self.feedback_list) / len(self.feedback_list),
            "unique_urls": len(set(f.url for f in self.feedback_list)),
            "priority_distribution": {
                "high": sum(1 for f in self.feedback_list if f.priority == "high"),
                "medium": sum(1 for f in self.feedback_list if f.priority == "medium"),
                "low": sum(1 for f in self.feedback_list if f.priority == "low"),
            }
        }
    
    def _save_to_file(self):
        """Save feedback to JSON file."""
        if not self.storage_path:
            return
        
        # Ensure directory exists
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert to dict and save
        data = [f.model_dump() for f in self.feedback_list]
        with open(self.storage_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _load_from_file(self):
        """Load feedback from JSON file."""
        if not self.storage_path or not self.storage_path.exists():
            return
        
        try:
            with open(self.storage_path, 'r') as f:
                data = json.load(f)
            
            self.feedback_list = [UXFeedback(**item) for item in data]
        except Exception as e:
            print(f"Warning: Failed to load feedback from {self.storage_path}: {e}")
            self.feedback_list = []
    
    def generate_report(self, task: str, output_path: Optional[Path] = None) -> str:
        """
        Generate a comprehensive UX analysis report.
        
        Args:
            task: The task that was performed
            output_path: Optional path to save the report. If None, returns report as string only.
        
        Returns:
            The report as a string
        """
        if not self.feedback_list:
            return "No feedback data available to generate report."
        
        # Build report
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("UX SPECIALIST ANALYSIS REPORT")
        report_lines.append("=" * 80)
        report_lines.append(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append(f"Task: {task}")
        report_lines.append(f"Total Steps Analyzed: {len(self.feedback_list)}")
        report_lines.append("")
        
        # Summary statistics
        summary = self.get_summary()
        report_lines.append("-" * 80)
        report_lines.append("SUMMARY STATISTICS")
        report_lines.append("-" * 80)
        report_lines.append(f"Average Confidence Score: {summary['average_confidence']:.2f}")
        report_lines.append(f"Unique URLs Visited: {summary['unique_urls']}")
        report_lines.append(f"Priority Distribution:")
        for priority, count in summary['priority_distribution'].items():
            report_lines.append(f"  - {priority.capitalize()}: {count}")
        report_lines.append("")
        
        # Detailed feedback per step
        report_lines.append("-" * 80)
        report_lines.append("DETAILED STEP-BY-STEP ANALYSIS")
        report_lines.append("-" * 80)
        
        for idx, feedback in enumerate(self.feedback_list, 1):
            report_lines.append(f"\n{'='*80}")
            report_lines.append(f"STEP {idx}")
            report_lines.append(f"{'='*80}")
            report_lines.append(f"URL: {feedback.url}")
            report_lines.append(f"Confidence: {feedback.confidence:.2f}")
            report_lines.append(f"Priority: {feedback.priority.upper()}")
            report_lines.append("")
            report_lines.append("RECOMMENDATION:")
            report_lines.append(f"  {feedback.recommendation}")
            report_lines.append("")
            
            if feedback.issues:
                report_lines.append("ISSUES IDENTIFIED:")
                for issue in feedback.issues:
                    report_lines.append(f"  • {issue}")
                report_lines.append("")
        
        # Key insights
        report_lines.append("\n" + "=" * 80)
        report_lines.append("KEY INSIGHTS")
        report_lines.append("=" * 80)
        
        # Find high-confidence recommendations
        high_conf = [f for f in self.feedback_list if f.confidence >= 0.9]
        if high_conf:
            report_lines.append(f"\n✓ {len(high_conf)} high-confidence recommendations (≥0.9)")
        
        # Find all unique issues
        all_issues = set()
        for f in self.feedback_list:
            all_issues.update(f.issues)
        
        if all_issues:
            report_lines.append(f"\n⚠ {len(all_issues)} unique UX issues identified across all steps")
        
        # Conclusion
        report_lines.append("\n" + "=" * 80)
        report_lines.append("CONCLUSION")
        report_lines.append("=" * 80)
        final_feedback = self.feedback_list[-1]
        report_lines.append(f"Final URL: {final_feedback.url}")
        report_lines.append(f"Final Recommendation: {final_feedback.recommendation}")
        report_lines.append("")
        
        # Join all lines
        report = "\n".join(report_lines)
        
        # Save to file if path provided
        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"✓ Report saved to: {output_path}")
        
        return report
