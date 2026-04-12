import json
from pathlib import Path
from typing import Optional

class SyncConfig:
    """
    Handles loading and processing of custom synchronization configuration (metadata.json).
    """
    def __init__(self, template: Optional[str] = None, fallback_template: Optional[str] = None):
        self.template = template
        self.fallback_template = fallback_template

    @classmethod
    def load(cls, base_dir: Path) -> "SyncConfig":
        """Loads configuration from metadata.json in the base directory."""
        json_path = base_dir / "metadata.json"
        if not json_path.exists():
            return cls()
            
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                config = json.load(f)
                return cls(
                    template=config.get("input", {}).get("file_name"),
                    fallback_template=config.get("output", {}).get("fallback_title")
                )
        except Exception:
            return cls()

    def apply_fallback(self, track: Optional[str], parsed_title: Optional[str]) -> Optional[str]:
        """Applies fallback title logic if the parsed title is missing."""
        if parsed_title:
            return parsed_title
        
        if track and self.fallback_template:
            return self.fallback_template.replace("%track%", track)
        
        return parsed_title
