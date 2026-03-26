"""
Production-ready medical data scraper for MindGuard AI.

Features:
- Rate limit compliance
- Error handling with exponential backoff
- Privacy-preserving anonymization
- Structured logging for compliance
- Medical-grade text cleaning
- Data quality validation
"""

import pandas as pd
import praw
from typing import List, Optional
from datetime import datetime
import logging

from config import load_config, RedditConfig
from cleaner import MedicalTextCleaner, DataAnonymizer, QualityValidator
from utils import StructuredLogger, retry_with_backoff, RateLimiter
from get_refresh_token import OAuthManager

# Initialize logger
logger = StructuredLogger(__name__)


class MedicalRedditScraper:
    """Production-ready Reddit scraper with privacy and compliance features."""
    
    def __init__(self, reddit: praw.Reddit, data_config, security_config):
        """
        Initialize scraper.
        
        Args:
            reddit: Authorized PRAW Reddit instance
            data_config: Data configuration
            security_config: Security/privacy configuration
        """
        self.reddit = reddit
        self.data_config = data_config
        self.security_config = security_config
        self.rate_limiter = RateLimiter(max_requests=60, window_seconds=60)
        self.scrape_stats = {
            "total_posts": 0,
            "valid_posts": 0,
            "filtered_posts": 0,
            "errors": 0,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    @retry_with_backoff(max_retries=3, initial_delay=2.0)
    def scrape_subreddit(self, subreddit_name: str) -> pd.DataFrame:
        """
        Scrape posts from a subreddit with error handling.
        
        Args:
            subreddit_name: Name of subreddit to scrape
        
        Returns:
            DataFrame with cleaned posts
        
        Raises:
            praw.exceptions.PrawException: If API call fails
        """
        posts = []
        logger.log_event(
            "scrape_start",
            subreddit=subreddit_name,
            limit=self.data_config.posts_per_subreddit
        )
        
        try:
            subreddit = self.reddit.subreddit(subreddit_name)
            
            # Verify subreddit exists
            _ = subreddit.display_name
            
            # Scrape with rate limiting
            for submission in subreddit.new(
                limit=self.data_config.posts_per_subreddit
            ):
                # Rate limiting
                self.rate_limiter.wait_if_needed()
                self.scrape_stats["total_posts"] += 1
                
                try:
                    # Clean text
                    cleaned_text = MedicalTextCleaner.clean(
                        submission.selftext,
                        preserve_structure=True
                    )
                    
                    # Validate quality
                    if not QualityValidator.is_valid_post(
                        cleaned_text,
                        min_words=self.data_config.min_word_count
                    ):
                        self.scrape_stats["filtered_posts"] += 1
                        continue
                    
                    # Build post record
                    post_record = {
                        "post_id": submission.id,
                        "subreddit": subreddit_name,
                        "created_utc": submission.created_utc,
                        "title": submission.title,
                        "text": cleaned_text,
                        "score": submission.score,
                        "num_comments": submission.num_comments
                    }
                    
                    # Anonymize if configured
                    if self.security_config.hash_sensitive_ids:
                        post_record = DataAnonymizer.anonymize_post(
                            post_record,
                            hash_ids=True
                        )
                    
                    posts.append(post_record)
                    self.scrape_stats["valid_posts"] += 1
                
                except Exception as e:
                    self.scrape_stats["errors"] += 1
                    logger.log_error(
                        "post_processing_error",
                        e,
                        post_id=submission.id,
                        subreddit=subreddit_name
                    )
                    continue
            
            logger.log_event(
                "scrape_complete",
                subreddit=subreddit_name,
                posts_collected=len(posts),
                valid=self.scrape_stats["valid_posts"],
                filtered=self.scrape_stats["filtered_posts"]
            )
            
            return pd.DataFrame(posts)
        
        except praw.exceptions.Redirect as e:
            logger.log_error("subreddit_not_found", e, subreddit=subreddit_name)
            raise ValueError(f"Subreddit r/{subreddit_name} not found") from e
        
        except praw.exceptions.ResponseException as e:
            logger.log_error("reddit_api_error", e, subreddit=subreddit_name)
            raise
        
        except Exception as e:
            logger.log_error("scrape_error", e, subreddit=subreddit_name)
            raise
    
    def scrape_multiple_subreddits(self) -> pd.DataFrame:
        """
        Scrape multiple subreddits and combine results.
        
        Returns:
            Combined DataFrame
        """
        all_data = []
        
        for subreddit_name in self.data_config.target_subreddits:
            try:
                df_sub = self.scrape_subreddit(subreddit_name.strip())
                if not df_sub.empty:
                    all_data.append(df_sub)
            
            except Exception as e:
                logger.log_error(
                    "subreddit_scrape_failed",
                    e,
                    subreddit=subreddit_name
                )
                continue
        
        if not all_data:
            logger.log_event("no_data_collected", subreddits=self.data_config.target_subreddits)
            return pd.DataFrame()
        
        # Combine and deduplicate
        combined_df = pd.concat(all_data, ignore_index=True)
        
        # Deduplicate by text content (prevent model bias)
        initial_count = len(combined_df)
        combined_df = combined_df.drop_duplicates(
            subset=["text"] if "text" in combined_df.columns else None,
            keep="first"
        )
        duplicates_removed = initial_count - len(combined_df)
        
        logger.log_event(
            "deduplication_complete",
            initial_count=initial_count,
            duplicates_removed=duplicates_removed,
            final_count=len(combined_df)
        )
        
        return combined_df


def save_data_with_metadata(
    df: pd.DataFrame,
    output_file: str,
    scraper: MedicalRedditScraper
):
    """
    Save data to CSV with metadata for compliance.
    
    Args:
        df: DataFrame to save
        output_file: Output file path
        scraper: Scraper instance for stats
    """
    try:
        df.to_csv(output_file, index=False)
        
        # Save metadata
        metadata = {
            "total_posts": scraper.scrape_stats["total_posts"],
            "valid_posts": scraper.scrape_stats["valid_posts"],
            "filtered_posts": scraper.scrape_stats["filtered_posts"],
            "errors": scraper.scrape_stats["errors"],
            "data_file": output_file,
            "scrape_timestamp": scraper.scrape_stats["timestamp"],
            "subreddits": scraper.data_config.target_subreddits
        }
        
        logger.log_event("data_saved", **metadata)
        
        print(f"\n{'='*60}")
        print("✅ Data Collection Complete")
        print(f"{'='*60}")
        print(f"📊 Statistics:")
        print(f"   Total posts processed: {metadata['total_posts']}")
        print(f"   Valid posts saved:     {metadata['valid_posts']}")
        print(f"   Posts filtered out:    {metadata['filtered_posts']}")
        print(f"   Errors encountered:    {metadata['errors']}")
        print(f"\n📁 Data saved to: {output_file}")
        print(f"{'='*60}\n")
    
    except Exception as e:
        logger.log_error("data_save_failed", e, output_file=output_file)
        raise


def main():
    """Main entry point."""
    try:
        print("\n" + "="*60)
        print("MindGuard AI - Medical Data Scraper")
        print("="*60 + "\n")
        
        # Load configuration
        reddit_config, data_config, security_config = load_config()
        
        # Initialize Reddit client
        oauth_manager = OAuthManager(reddit_config)
        reddit = oauth_manager._initialize_reddit(authorized=True)
        
        # Initialize scraper
        scraper = MedicalRedditScraper(reddit, data_config, security_config)
        
        # Scrape data
        print(f"🚀 Scraping subreddits: {', '.join(data_config.target_subreddits)}")
        final_df = scraper.scrape_multiple_subreddits()
        
        if final_df.empty:
            print("❌ No data collected. Check credentials and subreddits.")
            exit(1)
        
        # Save data
        output_file = f"medical_raw_data_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
        save_data_with_metadata(final_df, output_file, scraper)
    
    except Exception as e:
        logger.log_error("main_execution_failed", e)
        print(f"\n❌ Error: {e}")
        exit(1)


if __name__ == "__main__":
    main()