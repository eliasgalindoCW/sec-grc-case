"""
Configuration Management Module

This module handles all configuration settings for the application,
including environment variables, secrets, and runtime settings.
"""

import os
from typing import Optional
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv

@dataclass
class Config:
    """Application configuration settings."""
    # GitHub settings
    github_token: str
    github_repo: str
    
    # Eramba settings
    eramba_base_url: str
    eramba_api_url: str
    eramba_token: str
    eramba_control_id: int
    
    # SSL settings
    verify_ssl: bool
    
    # Paths
    evidence_dir: Path
    output_dir: Path
    
    @classmethod
    def load(cls) -> 'Config':
        """Load configuration from environment variables."""
        # Load environment variables
        load_dotenv()
        
        # Set default paths
        base_dir = Path(__file__).parent.parent
        evidence_dir = base_dir / "storage/evidence"
        output_dir = base_dir / "storage/analysis_output"
        
        # Create required directories
        evidence_dir.mkdir(parents=True, exist_ok=True)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Load and validate settings
        github_token = os.getenv('GITHUB_TOKEN')
        if not github_token:
            raise ValueError("GITHUB_TOKEN is required. Please set it in your .env file")
            
        eramba_token = os.getenv('ERAMBA_TOKEN')
        if not eramba_token:
            raise ValueError("ERAMBA_TOKEN is required. Please set it in your .env file")
            
        return cls(
            github_token=github_token,
            github_repo=os.getenv('GITHUB_REPO', 'eliasgalindoCW/sec-grc-case'),
            eramba_base_url=os.getenv('ERAMBA_BASE_URL', 'https://localhost:8443'),
            eramba_api_url=f"{os.getenv('ERAMBA_BASE_URL', 'https://localhost:8443')}/api/v1",
            eramba_token=eramba_token,
            eramba_control_id=int(os.getenv('ERAMBA_CONTROL_ID', '123')),
            verify_ssl=os.getenv('VERIFY_SSL', 'false').lower() == 'true',
            evidence_dir=evidence_dir,
            output_dir=output_dir
        )

# Create a singleton instance
_config_instance = None

def load_config() -> Config:
    """Load and return application configuration."""
    global _config_instance
    if _config_instance is None:
        _config_instance = Config.load()
    return _config_instance

__all__ = ['Config', 'load_config'] 