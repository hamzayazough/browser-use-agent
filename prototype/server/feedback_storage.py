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
