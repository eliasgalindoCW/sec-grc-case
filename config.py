"""Configuration settings for the application."""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# GitHub configuration
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
GITHUB_REPO = os.getenv('GITHUB_REPO', 'eliasgalindoCW/sec-grc-case')

# Eramba configuration
ERAMBA_BASE_URL = os.getenv('ERAMBA_BASE_URL', 'https://localhost:8443')
ERAMBA_API_URL = f"{ERAMBA_BASE_URL}/api/v1"  # Eramba 3.26.4 API endpoint
ERAMBA_TOKEN = os.getenv('ERAMBA_TOKEN')
ERAMBA_CONTROL_ID = int(os.getenv('ERAMBA_CONTROL_ID', '123'))

# SSL Configuration
VERIFY_SSL = os.getenv('VERIFY_SSL', 'false').lower() == 'true'

# Validate required configuration
if not GITHUB_TOKEN:
    raise ValueError("GITHUB_TOKEN is required. Please set it in your .env file")

if not ERAMBA_TOKEN:
    raise ValueError("ERAMBA_TOKEN is required. Please set it in your .env file") 