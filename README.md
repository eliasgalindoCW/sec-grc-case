# PR Review Control Analyzer

This tool analyzes GitHub Pull Request review controls and provides compliance evidence and insights using LLMs.

## Features

- GitHub PR review control verification
- Evidence collection and storage
- LLM-powered analysis using Claude
- Compliance reporting
- Structured data for future analysis

## Project Structure

```
security-grc-case/
├── src/                      # Source code
│   ├── analyzers/           # Analysis modules
│   │   ├── pr_analyzer.py   # GitHub PR analysis
│   │   ├── llm_analyzer.py  # LLM integration
│   │   └── mcp_analyzer.py  # MCP integration
│   ├── clients/             # External service clients
│   │   └── eramba_client.py # Eramba API client
│   ├── core/                # Core functionality
│   │   └── evidence_store.py # Evidence storage
│   ├── storage/             # Data storage
│   │   ├── evidence/        # Evidence storage
│   │   │   ├── controls/    # Control evidence
│   │   │   ├── metrics/     # Metrics data
│   │   │   └── reports/     # Generated reports
│   │   └── analysis_output/ # Analysis results
│   └── utils/               # Utility modules
│       ├── config.py        # Configuration management
│       └── logging_config.py # Logging setup
├── tests/                   # Test suite
│   └── test_analyzers/      # Analyzer tests
├── .env.example            # Example environment variables
├── requirements.txt        # Dependencies
└── main.py                # Application entry point
```

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Copy `.env.example` to `.env` and configure:
```bash
cp .env.example .env
```

3. Configure environment variables in `.env`:
```env
# GitHub Configuration
GITHUB_TOKEN=your_github_token_here
GITHUB_REPO=owner/repo

# Eramba Configuration
ERAMBA_BASE_URL=https://localhost:8443
ERAMBA_TOKEN=your_eramba_token_here
ERAMBA_CONTROL_ID=123

# SSL Configuration
VERIFY_SSL=false  # Set to true in production
```

## Usage

Run specific actions:
```bash
# Check PR controls
python main.py check

# Store evidence
python main.py submit

# Generate report
python main.py report

# Analyze with LLM
python main.py analyze

# Run all actions
python main.py
```

## Evidence Structure

Evidence is stored in JSON format with:
- Control metadata
- Compliance metrics
- Review patterns
- Risk analysis
- Non-compliant PRs

Reports are generated in Markdown format for easy reading.

## LLM Analysis

The tool uses Claude to analyze:
- Compliance trends
- Review patterns
- Risk factors
- Process improvements

Analysis results include:
- Critical issues
- Process insights
- Recommended actions
- Metrics & targets
