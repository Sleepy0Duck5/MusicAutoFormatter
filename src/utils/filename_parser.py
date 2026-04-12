import os
import re
from typing import List, Tuple, Optional

class FilenameParser:
    """
    Utility for simplifying filenames by removing common prefixes 
    and extracting track numbers and titles using regex.
    """

    @staticmethod
    def get_common_prefix(filenames: List[str]) -> str:
        """
        Finds the common prefix among a list of strings.
        Ensures we don't accidentally cut off the start of a track number.
        """
        if not filenames or len(filenames) < 2:
            return ""
        
        prefix = os.path.commonprefix(filenames)
        
        # If the prefix ends in a digit, it's likely part of a track number 
        # (e.g., '0' from '01', '02'). We should backtrack to the last separator.
        if prefix and prefix[-1].isdigit():
            # Find the last non-digit character
            match = re.search(r'[^0-9]', prefix[::-1])
            if match:
                # index is from the end
                split_idx = len(prefix) - match.start()
                prefix = prefix[:split_idx]
            else:
                # Prefix is all digits, likely the track numbers themselves start with common digits
                return ""
                
        return prefix

    @staticmethod
    def parse_track_and_title(filename: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Parses a filename (without extension) into (track, title).
        Handles formats like:
        - "01. Title"
        - "01 - Title"
        - "01_Title"
        - "01 Title"
        - "Title" (track is None)
        """
        # Regex explanation:
        # ^(\d+)?           : Optional leading digits (track number)
        # [\s\.\-\_\(\)\[\]]* : Optional separators (space, dot, dash, underscore, brackets)
        # (.*)$             : The rest is the title
        
        # Try to find a track number at the beginning
        match = re.match(r"^(\d+)?[\s\.\-\_\(\)\[\]]*(.*)$", filename.strip())
        
        if not match:
            return None, filename.strip()
            
        track = match.group(1)
        title = match.group(2).strip()
        
        if not title:
            # If everything was matched as track or title is empty, 
            # might be just a track number or something went wrong.
            if track:
                return track, None
            return None, filename.strip()
            
        return track, title

    @classmethod
    def process_filenames(cls, filenames: List[str]) -> List[Tuple[Optional[str], Optional[str]]]:
        """
        Takes a list of raw filenames (with or without extensions),
        simplifies them by removing common prefix, and parses each into (track, title).
        """
        # Remove extensions first
        stems = [os.path.splitext(f)[0] for f in filenames]
        
        # Get common prefix
        prefix = cls.get_common_prefix(stems)
        
        results = []
        for stem in stems:
            # Remove prefix
            clean_name = stem[len(prefix):] if prefix else stem
            
            # Parse track and title
            track, title = cls.parse_track_and_title(clean_name)
            results.append((track, title))
            
        return results

    @staticmethod
    def _template_to_regex(template: str) -> str:
        """Converts a template string like '%track% %title%' into a regex pattern."""
        mapping = {
            "%track%": r"(?P<track>\d+)",
            "%track-optional%": r"(?P<track>\d*)",
            "%title%": r"(?P<title>.+)",
            "%title-optional%": r"(?P<title>.*)",
            "%sep%": r"[_\.\s-]+",
            "%sep-optional%": r"[_\.\s-]*",
        }
        
        parts = re.split(r"(%.*?%)", template)
        re_parts = []
        for part in parts:
            if part in mapping:
                re_parts.append(mapping[part])
            else:
                re_parts.append(re.escape(part))
        
        return "^" + "".join(re_parts) + "$"

    @classmethod
    def parse_with_template(cls, filename: str, template: str) -> Tuple[Optional[str], Optional[str]]:
        """Parses a filename using a custom template string."""
        stem = os.path.splitext(filename)[0]
        pattern = cls._template_to_regex(template)
        
        try:
            match = re.match(pattern, stem)
            if match:
                groups = match.groupdict()
                track = groups.get("track")
                title = groups.get("title")
                return track if track else None, title if title else None
        except Exception:
            pass
            
        return None, None
