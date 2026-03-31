"""
Data cleaning and preprocessing for healthcare NLP.
Preserves emotional nuances while removing PII and noise.
"""

import re
from typing import Optional
import hashlib


class MedicalTextCleaner:
    """
    Medical-grade text cleaner for healthcare NLP.
    
    Preserves:
    - First-person pronouns (I, me, my) for emotional context
    - Emotional punctuation (!, ?)
    - Contractions (don't, won't) for natural language
    
    Removes:
    - URLs
    - Reddit mentions (u/, r/)
    - Email addresses
    - Excessive whitespace
    """
    
    # Regex patterns
    URL_PATTERN = r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+"
    REDDIT_MENTION_PATTERN = r"(?:^|\s)(?:u/|/u/|r/|/r/)[\w-]+"
    EMAIL_PATTERN = r"[\w\.-]+@[\w\.-]+\.\w+"
    DELETED_REMOVED = ["[deleted]", "[removed]"]
    
    @staticmethod
        if not isinstance(text, str) or not text.strip():
            return ""
        
        if text in MedicalTextCleaner.DELETED_REMOVED:
            return ""

        text = re.sub(MedicalTextCleaner.URL_PATTERN, "", text)
        text = re.sub(MedicalTextCleaner.REDDIT_MENTION_PATTERN, " ", text)
        text = re.sub(MedicalTextCleaner.EMAIL_PATTERN, "", text)

        if preserve_structure:
            text = text.replace("\n", " . ").replace("\r", "")
        else:
            text = text.replace("\n", " ").replace("\r", "")
        text = re.sub(r"\s+", " ", text).strip()
        text = re.sub(r"([!?.])\1{2,}", r"\1\1", text)
        
        return text if text else ""
    
    @staticmethod
    def get_word_count(text: str) -> int:
        """Get word count of cleaned text."""
        return len(text.split()) if text else 0


class DataAnonymizer:
    """Anonymize sensitive data for privacy compliance."""
    
    @staticmethod
    def hash_id(value: str, salt: str = "") -> str:
        combined = f"{value}{salt}"
        return hashlib.sha256(combined.encode()).hexdigest()[:16]
    
    @staticmethod
    def anonymize_post(post_data: dict, hash_ids: bool = True) -> dict:
        anonymized = {}
        
        if hash_ids:
            anonymized["post_id_hash"] = DataAnonymizer.hash_id(post_data.get("post_id", ""))
        else:
            anonymized["post_id"] = post_data.get("post_id", "")
        
        anonymized["subreddit"] = post_data.get("subreddit", "")
        anonymized["created_utc"] = post_data.get("created_utc", "")
        anonymized["title"] = post_data.get("title", "")
        anonymized["text"] = post_data.get("text", "")
        
        return anonymized


class QualityValidator:
    """Validate data quality and consistency."""
    
    @staticmethod
    def is_valid_post(text: str, min_words: int = 10, max_words: int = 5000) -> bool:
        word_count = MedicalTextCleaner.get_word_count(text)
        
        # Check word count range
        if not (min_words <= word_count <= max_words):
            return False
        
        # Check for minimum variation (not just repetition)
        if text and len(set(text.split())) < len(text.split()) * 0.3:
            return False
        
        return True
