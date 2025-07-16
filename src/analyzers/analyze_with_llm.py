"""
LLM Evidence Analysis

This module uses Anthropic's Claude to analyze PR review control evidence and provide
intelligent recommendations for process improvement.
"""

import os
from typing import Dict, Optional
import logging
from datetime import datetime
import json
from pathlib import Path
import requests
from src.analyzers.mcp_evidence_analyzer import MCPEvidenceAnalyzer
from dotenv import load_dotenv
from src.utils.config import load_config

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"

class LLMAnalyzer:
    """
    Uses Claude to analyze control evidence and provide recommendations.
    """
    
    def __init__(
        self,
        evidence_dir: str = None,
        model: str = "claude-3-opus-20240229",
        temperature: float = 0.7,
        max_tokens: int = 4096
    ):
        """
        Initialize LLM analyzer.
        
        Args:
            evidence_dir: Directory containing evidence (defaults to config path)
            model: Anthropic model to use
            temperature: Model temperature (0.0 to 1.0)
            max_tokens: Maximum tokens in response
        """
        config = load_config()
        self.evidence_analyzer = MCPEvidenceAnalyzer(
            evidence_dir or str(config.evidence_dir)
        )
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.output_dir = config.output_dir
        
        # Get API key from environment
        self.api_key = os.getenv('ANTHROPIC_API_KEY')
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is not set")
            
        # Setup headers
        self.headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        
        # Create output directory
        self.output_dir.mkdir(exist_ok=True)
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for the analysis."""
        return """You are an expert security and compliance analyst specializing in code review processes.
Your task is to analyze evidence from GitHub PR reviews and provide specific, actionable recommendations.

Focus on:
1. Identifying critical issues that need immediate attention
2. Recognizing patterns that indicate process improvements
3. Suggesting concrete, implementable solutions
4. Providing specific metrics and targets

Format your response in clear sections:
- Critical Issues
- Process Insights
- Recommended Actions
- Metrics & Targets

Be specific and practical in your recommendations. Use markdown formatting for better readability."""
    
    def analyze_evidence(
        self,
        control_id: Optional[int] = None,
        days: int = 30,
        save_output: bool = True
    ) -> Dict:
        """
        Analyze evidence using Claude and provide recommendations.
        
        Args:
            control_id: Optional control ID to filter
            days: Number of days of history to include
            save_output: Whether to save analysis to file
            
        Returns:
            Dictionary with analysis results
        """
        # Get MCP prompt
        evidence_prompt = self.evidence_analyzer.generate_mcp_prompt(control_id, days)
        
        try:
            # Prepare request payload
            payload = {
                "model": self.model,
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
                "system": self._get_system_prompt(),
                "messages": [
                    {
                        "role": "user",
                        "content": evidence_prompt
                    }
                ]
            }
            
            # Make API request
            logger.info("Sending request to Claude API...")
            response = requests.post(
                ANTHROPIC_API_URL,
                headers=self.headers,
                json=payload
            )
            
            # Log response for debugging
            logger.debug(f"API Response Status: {response.status_code}")
            logger.debug(f"API Response Headers: {response.headers}")
            logger.debug(f"API Response Body: {response.text}")
            
            # Check for errors
            response.raise_for_status()
            response_data = response.json()
            
            # Extract analysis
            analysis = response_data['content'][0]['text']
            
            # Prepare result
            result = {
                'timestamp': datetime.utcnow().isoformat(),
                'analysis_parameters': {
                    'control_id': control_id,
                    'days_analyzed': days,
                    'model': self.model
                },
                'evidence_context': self.evidence_analyzer.get_evidence_context(control_id, days),
                'analysis': analysis
            }
            
            # Save output if requested
            if save_output:
                self._save_analysis(result)
            
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error during API request: {str(e)}")
            if hasattr(e, 'response'):
                logger.error(f"API Response: {e.response.text}")
                logger.error(f"Request Payload: {json.dumps(payload, indent=2)}")
            raise
        except Exception as e:
            logger.error(f"Error during analysis: {str(e)}")
            raise
    
    def _save_analysis(self, result: Dict) -> str:
        """Save analysis results to file."""
        timestamp = datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S")
        control_id = result['analysis_parameters']['control_id'] or 'all'
        
        # Save JSON
        json_path = self.output_dir / f"analysis_{control_id}_{timestamp}.json"
        with open(json_path, 'w') as f:
            json.dump(result, f, indent=2)
        
        # Save markdown report
        md_path = self.output_dir / f"analysis_{control_id}_{timestamp}.md"
        with open(md_path, 'w') as f:
            f.write(f"# PR Review Control Analysis\n\n")
            f.write(f"Generated: {result['timestamp']}\n\n")
            
            f.write("## Analysis Parameters\n")
            f.write(f"- Control ID: {result['analysis_parameters']['control_id']}\n")
            f.write(f"- Days Analyzed: {result['analysis_parameters']['days_analyzed']}\n")
            f.write(f"- Model: {result['analysis_parameters']['model']}\n\n")
            
            f.write("## Evidence Summary\n")
            summary = result['evidence_context']['evidence_summary']
            f.write(f"- Period: {summary['date_range']['start']} to {summary['date_range']['end']}\n")
            f.write(f"- Total Records: {summary['total_records']}\n")
            f.write(f"- Current Status: {summary['latest_status']}\n")
            f.write(f"- Compliance Trend: {summary['compliance_trend']['direction']}\n\n")
            
            f.write("## Analysis\n")
            f.write(result['analysis'])
        
        logger.info(f"Analysis saved to {json_path} and {md_path}")
        return str(md_path)

def main():
    """Main function to run analysis."""
    try:
        # Initialize analyzer
        analyzer = LLMAnalyzer()
        
        # Run analysis
        logger.info("Starting evidence analysis...")
        result = analyzer.analyze_evidence(days=30)
        
        # Print analysis
        print("\nAnalysis Results:")
        print("----------------")
        print(result['analysis'])
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise

if __name__ == "__main__":
    main() 