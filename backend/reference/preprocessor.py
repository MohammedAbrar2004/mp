"""
Preprocessing module for EchoMind.
Transforms NormalizedInput into DB-ready format.
"""

import re
from models.normalized_input import NormalizedInput


class Preprocessor:
    """Preprocesses normalized inputs for database storage."""
    
    # Keywords that increase salience score
    SALIENCE_KEYWORDS = {
        "meeting", "deadline", "task", "decide", "important",
        "urgent", "action", "decision", "schedule", "confirm"
    }
    
    def clean_text(self, text: str) -> str:
        """
        Clean and normalize text.
        
        Args:
            text: Raw text to clean
            
        Returns:
            Cleaned text string
        """
        # Strip leading/trailing whitespace
        text = text.strip()
        
        # Replace multiple spaces with single space
        text = re.sub(r'\s+', ' ', text)
        
        # Remove newline clutter
        text = text.replace('\n', ' ').replace('\r', ' ')
        
        return text.strip()
    
    def normalize_participants(self, participants: list[str]) -> list[str]:
        """
        Normalize participant names.
        
        Args:
            participants: List of participant names
            
        Returns:
            Normalized list of participant names
        """
        normalized = []
        
        for participant in participants:
            # Strip whitespace
            p = participant.strip()
            
            # Convert to lowercase
            p = p.lower()
            
            # Skip empty values
            if p:
                normalized.append(p)
        
        return normalized
    
    def compute_initial_salience(self, text: str) -> float:
        """
        Compute initial salience score using heuristics.
        
        Args:
            text: Cleaned text content
            
        Returns:
            Salience score between 0 and 1
        """
        # Base score
        score = 0.1
        
        # Check for keywords (case-insensitive)
        text_lower = text.lower()
        keyword_count = sum(1 for keyword in self.SALIENCE_KEYWORDS if keyword in text_lower)
        
        # Increase score based on keywords found
        score += keyword_count * 0.15
        
        # Increase score slightly based on text length
        # Longer content generally more relevant
        if len(text) > 100:
            score += 0.1
        if len(text) > 500:
            score += 0.1
        
        # Cap at 1.0
        return min(score, 1.0)
    
    def process(self, input: NormalizedInput) -> dict:
        """
        Process NormalizedInput into DB-ready dictionary.
        
        Args:
            input: NormalizedInput object
            
        Returns:
            Dictionary ready for database insertion
        """
        cleaned_text = self.clean_text(input.raw_content)
        normalized_participants = self.normalize_participants(input.participants)
        salience_score = self.compute_initial_salience(cleaned_text)
        
        return {
            "source_type": input.source_type,
            "external_message_id": input.external_message_id,
            "timestamp": input.timestamp,
            "participants": normalized_participants,
            "content_type": input.content_type,
            "raw_content": cleaned_text,
            "initial_salience": salience_score,
            "metadata": input.metadata
        }
