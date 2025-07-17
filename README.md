# Security GRC - PR Review Control Analyzer

This tool analyzes GitHub Pull Request review controls and provides compliance evidence and insights using LLMs. It's designed to help security and compliance teams automate the verification of PR review controls and maintain evidence for audits.

## Features

### PR Review Control Verification
- Automated analysis of PR review compliance
- Risk assessment based on multiple factors:
  - Code complexity analysis
  - Sensitive pattern detection
  - File type risk evaluation
  - Review pattern analysis
- Configurable compliance thresholds
- Statistical metrics and trend analysis

### Evidence Management
- Structured evidence storage
- Automatic evidence collection
- Historical tracking
- Evidence report generation
- Metrics aggregation

### LLM-Powered Analysis
- Intelligent analysis using Claude
- Context-aware recommendations
- Pattern recognition
- Actionable insights
- MCP (Model Context Protocol) integration

## Project Structure

```
security-grc-case/
├── src/                      # Source code
│   ├── analyzers/           # Analysis modules
│   │   ├── pr_analyzer.py   # GitHub PR analysis
│   │   ├── llm_analyzer.py  # LLM integration
│   │   ├── code_analyzer.py # Code complexity analysis
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
│       ├── cache.py         # Caching functionality
│       └── logging_config.py # Logging setup
├── tests/                   # Test suite
│   └── test_analyzers/      # Analyzer tests
├── eramba_pr_control.csv   # Sample control definition for Eramba
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

# Logging
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR

# LLM Configuration
ANTHROPIC_API_KEY=your_anthropic_key_here
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

## Compliance Criteria

The tool evaluates PR compliance based on several criteria:

### Review Requirements
- PRs must be approved by someone other than the author
- Reviews must be thorough and documented
- High-risk changes require additional scrutiny

### Risk Assessment
PRs are classified into risk levels based on:
- Code complexity (lines changed, nesting depth, etc.)
- Sensitive patterns (auth, security, etc.)
- File types (config, infrastructure, etc.)
- Review patterns (timing, thoroughness)

### Compliance Thresholds
- Overall compliance rate must be ≥ 95%
- High-risk PRs must be < 10% of total
- Critical changes require specific approvals

## Evidence Structure

Evidence is stored in a structured format with:

### Control Evidence
- Control metadata
- Compliance status
- Timestamps
- Description

### Metrics
- Compliance rates
- Risk distribution
- Review patterns
- Statistical metrics

### Reports
- Generated in Markdown format
- Include summary statistics
- List non-compliant PRs
- Show risk analysis

## Internal Control Framework

### Sample Control Definition (`eramba_pr_control.csv`)

This repository includes a sample control definition file that demonstrates how PR review controls can be structured for GRC systems like Eramba. The file contains an example of a comprehensive internal control framework for GitHub Pull Request reviews.

**File:** `eramba_pr_control.csv`

**Control Definition:**
- **Control Name:** PR Review Control - GitHub
- **Control Description:** All Pull Requests must be reviewed and approved by someone other than the author before being merged. This control ensures code quality, security, and compliance with development standards.
- **Risk Level:** Critical
- **Compliance Criteria:** 95% compliance rate with no unapproved merged PRs
- **Review Schedule:** Quarterly (15-01|15-04|15-07|15-10)
- **Responsible Parties:** Group-Admin, User-admin

### Control Framework Structure

The CSV file follows a structured format that can be imported into Eramba or similar GRC platforms:

```csv
Control Name, Description, [Additional Fields], Risk Level, Owner, Reviewer, 
Compliance Criteria, Review Schedule, Responsible Parties, Review Dates
```

**Key Fields:**
- **Control Name**: Unique identifier for the control
- **Description**: Detailed explanation of the control's purpose and scope
- **Risk Level**: Classification (Critical, High, Medium, Low)
- **Compliance Criteria**: Measurable success criteria (e.g., "95% compliance rate")
- **Review Schedule**: Periodic review dates in MM-DD format
- **Responsible Parties**: Groups or individuals responsible for control execution
- **Evidence Requirements**: Types of evidence needed for compliance verification

### Usage in GRC Systems

This sample control definition can be used to:

1. **Set up Controls in Eramba:**
   - Import the CSV file directly into Eramba
   - Configure automated evidence collection
   - Set up review workflows

2. **Establish Compliance Framework:**
   - Define measurable compliance criteria
   - Set review schedules and responsibilities
   - Configure risk assessment parameters

3. **Automate Evidence Collection:**
   - Link to this tool's evidence generation
   - Configure automated reporting
   - Set up compliance monitoring

### Future Enhancements

The control framework is designed to be extensible for additional controls:

- **Code Quality Controls**: Static analysis, test coverage requirements
- **Security Controls**: Vulnerability scanning, dependency checks
- **Deployment Controls**: Change management, rollback procedures
- **Documentation Controls**: README updates, change logs

This sample provides a foundation for implementing comprehensive software development lifecycle controls within your GRC framework.

## Cache Management

The tool implements caching to optimize performance:

- API response caching
- Analysis result caching
- Configurable TTL
- Automatic invalidation

## Testing

Run the test suite:
```bash
pytest tests/
```

Tests cover:
- PR analysis logic
- Evidence storage
- LLM integration
- Cache functionality

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request
