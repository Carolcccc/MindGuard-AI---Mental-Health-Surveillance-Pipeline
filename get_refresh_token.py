"""
Enhanced OAuth token management with security improvements.
"""

import praw
import webbrowser
from typing import Optional
from urllib.parse import urlparse, parse_qs
import re
from config import RedditConfig
from utils import StructuredLogger, retry_with_backoff
import os
from dotenv import load_dotenv

load_dotenv()

logger = StructuredLogger(__name__)


class OAuthManager:
    """Secure OAuth token management for Reddit API."""
    
    def __init__(self, config: RedditConfig):
        """Initialize OAuth manager."""
        self.config = config
        self.reddit = self._initialize_reddit(authorized=False)
    
    def _initialize_reddit(self, authorized: bool = False) -> praw.Reddit:
        """
        Initialize Reddit PRAW instance.
        
        Args:
            authorized: Whether to use refresh token for authorization
        
        Returns:
            PRAW Reddit instance
        """
        kwargs = {
            "client_id": self.config.client_id,
            "client_secret": self.config.client_secret,
            "user_agent": self.config.user_agent,
        }
        
        if authorized and self.config.refresh_token:
            kwargs["refresh_token"] = self.config.refresh_token
        else:
            kwargs["redirect_uri"] = self.config.redirect_uri
        
        try:
            reddit = praw.Reddit(**kwargs)
            logger.log_event(
                "reddit_client_initialized",
                authorized=authorized,
                user_agent=self.config.user_agent
            )
            return reddit
        except Exception as e:
            logger.log_error("reddit_initialization_failed", e)
            raise
    
    def get_authorization_url(self, scopes: list[str] = None) -> str:
        """
        Generate Reddit OAuth authorization URL.
        
        Args:
            scopes: List of OAuth scopes (defaults to minimal)
        
        Returns:
            Authorization URL
        """
        if scopes is None:
            scopes = ["identity", "read", "mysubreddits"]
        
        try:
            url = self.reddit.auth.url(scopes, "uniqueKey", "permanent")
            logger.log_event(
                "auth_url_generated",
                scopes=scopes
            )
            return url
        except Exception as e:
            logger.log_error("auth_url_generation_failed", e)
            raise
    
    def get_refresh_token(self, auth_code: Optional[str] = None) -> str:
        """
        Get refresh token from authorization code.
        
        Args:
            auth_code: Authorization code from user, if None prompts user
        
        Returns:
            Refresh token
        
        Raises:
            ValueError: If authorization fails
        """
        if auth_code is None:
            # Generate URL
            url = self.get_authorization_url()
            print("\n👉 Authorization URL:")
            print(f"   {url}\n")
            
            try:
                webbrowser.open(url)
                print("📱 Browser opened. Authorize the application.")
            except Exception as e:
                logger.log_event("browser_open_failed", error=str(e))
                print("⚠️ Could not open browser automatically. Copy the URL above.")
            
            print("\nAfter authorization, you'll see a URL like:")
            print("   http://localhost:8080/?state=uniqueKey&code=XXXX\n")
            
            raw_input_value = input("Enter authorization code OR full callback URL: ").strip()
            auth_code = self._extract_auth_code(raw_input_value)
        
        # Validate code format
        if not auth_code or len(auth_code) < 10:
            raise ValueError("Invalid authorization code format")
        
        try:
            refresh_token = self.reddit.auth.authorize(auth_code)
            
            if not refresh_token:
                raise ValueError("Authorization returned empty token")
            
            logger.log_event(
                "refresh_token_obtained",
                token_length=len(refresh_token)
            )
            
            return refresh_token
        
        except praw.exceptions.InvalidToken as e:
            logger.log_error("invalid_token_error", e)
            raise ValueError("Invalid or expired authorization code") from e
        
        except Exception as e:
            logger.log_error("refresh_token_acquisition_failed", e)
            raise

    @staticmethod
    def _extract_auth_code(value: str) -> str:
        """
        Extract authorization code from user input.

        Supports:
        - Raw code string
        - Full callback URL (http://localhost:8080/?state=...&code=...)
        - Inputs containing "code=..."
        """
        if not value:
            return ""

        cleaned = value.strip()

        # Full URL case
        if cleaned.startswith("http://") or cleaned.startswith("https://"):
            parsed = urlparse(cleaned)
            query = parse_qs(parsed.query)
            code_values = query.get("code", [])
            if code_values:
                return code_values[0].strip()

        # Inline "code=..." case
        match = re.search(r"(?:^|[?&\s])code=([^&\s]+)", cleaned)
        if match:
            return match.group(1).strip()

        # Otherwise assume it's already a raw code
        return cleaned
    
    @staticmethod
    def save_token_to_env(token: str, env_file: str = ".env"):
        """
        Save refresh token to .env file.
        
        Args:
            token: Refresh token to save
            env_file: Path to .env file
        """
        try:
            # Read existing .env
            env_content = ""
            if os.path.exists(env_file):
                with open(env_file, "r") as f:
                    env_content = f.read()
            
            # Update existing token line while preserving all other content
            lines = env_content.splitlines()
            updated = False

            for i, line in enumerate(lines):
                if line.startswith("REDDIT_REFRESH_TOKEN="):
                    lines[i] = f"REDDIT_REFRESH_TOKEN={token}"
                    updated = True
                    break

            if not updated:
                lines.append(f"REDDIT_REFRESH_TOKEN={token}")

            env_content = "\n".join(lines).rstrip() + "\n"
            
            # Write back to .env
            with open(env_file, "w") as f:
                f.write(env_content)
            
            logger.log_event("token_saved_to_env", file=env_file)
            print(f"\n✅ Token saved to {env_file}")
        
        except Exception as e:
            logger.log_error("token_save_failed", e, file=env_file)
            raise


def main():
    """Interactive OAuth token generation."""
    try:
        reddit_config = RedditConfig(
            client_id=os.getenv("REDDIT_CLIENT_ID"),
            client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
            user_agent=os.getenv("REDDIT_USER_AGENT", "MindGuard/1.0"),
            redirect_uri=os.getenv("REDDIT_REDIRECT_URI", "http://localhost:8080")
        )
        
        oauth_manager = OAuthManager(reddit_config)
        
        print("\n" + "="*60)
        print("MindGuard AI - Reddit OAuth Token Generator")
        print("="*60)
        
        # Get refresh token
        token = oauth_manager.get_refresh_token()
        
        # Save to .env
        OAuthManager.save_token_to_env(token)
        
        print(f"\n✅ Success!")
        print(f"Your refresh token is:")
        print(f"   {token[:20]}...{token[-20:]}")
        print(f"\nNext step: Run scrape_medical_data.py")
    
    except Exception as e:
        logger.log_error("oauth_flow_failed", e)
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting:")
        print("1) In Reddit app settings, ensure redirect URI exactly matches REDDIT_REDIRECT_URI")
        print("2) Paste either the raw code or the full callback URL")
        print("3) Make sure the app credentials in .env are correct")
        exit(1)


if __name__ == "__main__":
    main()