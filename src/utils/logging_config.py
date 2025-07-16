"""
Logging Configuration Module

This module provides centralized logging configuration for the application.
"""

import logging
from pathlib import Path
import os

def setup_logging(log_level: str = None) -> None:
    """
    Setup application logging with file and console handlers.
    
    Args:
        log_level: Optional log level override (DEBUG, INFO, WARNING, ERROR)
    """
    # Get log level from environment or use default
    if log_level is None:
        log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    else:
        log_level = log_level.upper()
        
    # Validate log level
    valid_levels = {'DEBUG', 'INFO', 'WARNING', 'ERROR'}
    if log_level not in valid_levels:
        log_level = 'INFO'
        
    # Create logs directory
    log_dir = Path(__file__).parent.parent.parent / 'logs'
    log_dir.mkdir(exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(
                log_dir / f"app_{log_level.lower()}.log"
            ),
            logging.StreamHandler()
        ]
    ) 