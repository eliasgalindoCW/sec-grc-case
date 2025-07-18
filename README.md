# Security GRC - PR Review Control Analyzer

This tool analyzes GitHub Pull Request review controls and provides compliance evidence and insights using LLMs. It's designed to help security and compliance teams automate the verification of PR review controls and maintain evidence for audits.

**✨ Features automated setup and local Eramba deployment via comprehensive Justfile with 25+ commands.**

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

### Automation & Integration
- **Comprehensive Justfile** with 25+ commands
- **Local Eramba deployment** using official Docker repository
- **One-command setup** for complete development environment
- **Automated evidence collection** and GRC integration
- **Container lifecycle management** (start/stop/backup/restore)
- **Development workflow automation** with pipeline commands

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
├── eramba-docker/           # Eramba Docker repository (auto-created)
│   ├── .env                 # Auto-generated Eramba configuration
│   ├── docker-compose.simple-install.yml
│   └── ...                  # Additional Eramba files
├── justfile                 # Automation commands (25+ commands)
├── eramba_pr_control.csv   # Sample control definition for Eramba
├── .env.example            # Example environment variables
├── requirements.txt        # Dependencies
└── main.py                # Application entry point
```

## Setup

### Option 1: Automated Setup (Recommended)

1. Install Just command runner:
```bash
# macOS
brew install just

# Ubuntu/Debian
curl --proto '=https' --tlsv1.2 -sSf https://just.systems/install.sh | bash -s -- --to /usr/local/bin

# Windows (using Scoop)
scoop install just
```

2. Install Docker and Docker Compose:
   - [Docker Installation Guide](https://docs.docker.com/get-docker/)
   - [Docker Compose Installation Guide](https://docs.docker.com/compose/install/)

3. Run automated setup:
```bash
just dev-setup
```

This command will:
- Install Python dependencies
- Clone and configure Eramba Docker repository
- Create necessary configuration files
- Set up the development environment

### Option 2: Manual Setup

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

## Automation with Justfile

For streamlined development and deployment, this project includes a comprehensive Justfile that automates all tasks including local Eramba setup. The Justfile provides 25+ commands to manage both the project and a local Eramba instance.

### Prerequisites

- [Just](https://github.com/casey/just) - Command runner
- [Docker](https://docs.docker.com/get-docker/) - Container platform
- [Docker Compose](https://docs.docker.com/compose/install/) - Container orchestration

### Quick Start

```bash
# Setup complete development environment (Python + Eramba)
just dev-setup

# Start local Eramba server
just start-eramba

# Access Eramba at https://localhost:8443
# Default credentials: admin / admin123
```

### Available Commands

View all available commands:
```bash
just
# or
just --list
```

### Eramba Management (10 commands)

```bash
# Eramba setup and management
just clone-eramba      # Clone official Eramba Docker repository
just setup-eramba      # Configure Eramba environment (.env creation)
just start-eramba      # Start Eramba server (port 8443)
just stop-eramba       # Stop Eramba server
just restart-eramba    # Restart Eramba server
just status-eramba     # Check container status
just logs-eramba       # View Eramba logs (follow mode)
just shell-eramba      # Access Eramba container shell
just clean-eramba      # Remove Eramba completely (containers, volumes)
just backup-eramba     # Backup Eramba data and configuration
```

### Project Commands (6 commands)

```bash
# Project analysis and management
just install           # Install Python dependencies
just analyze           # Run PR analysis with LLM
just check             # Execute control checks
just submit            # Submit evidence
just report            # Generate reports
just test              # Run test suite
```

### Development Commands (5 commands)

```bash
# Development utilities
just dev-setup         # Complete environment setup
just clean             # Clean cache and temporary files
just info              # Show environment information
just pipeline          # Run complete project pipeline
just full-pipeline     # Run pipeline with Eramba integration
```

### Eramba Integration

The Justfile automatically:
- Clones the official [Eramba Docker repository](https://github.com/eramba/docker)
- Creates secure default configurations for development
- Manages container lifecycle (start/stop/restart)
- Provides backup and restore functionality
- Integrates with the project's GRC analysis pipeline

### Configuration

The system automatically creates a `.env` file in the `eramba-docker/` directory with secure defaults:

```env
# Database
MYSQL_ROOT_PASSWORD=rootpassword
MYSQL_DATABASE=eramba
MYSQL_USER=eramba
MYSQL_PASSWORD=eramba123

# Server
APACHE_PORT=8443

# Eramba
ERAMBA_ADMIN_EMAIL=admin
ERAMBA_ADMIN_PASSWORD=admin123
ERAMBA_TIMEZONE=America/Sao_Paulo
```

⚠️ **Note**: These are development defaults. Change credentials for production use.

### Typical Workflow

```bash
# Daily development workflow
just start-eramba      # Start Eramba server
just analyze           # Run your analysis
just logs-eramba       # Check logs if needed
just stop-eramba       # Stop when done

# Complete pipeline
just full-pipeline     # Runs dev-setup + start-eramba + analysis pipeline
```

### File Structure After Setup

```
security-grc-case/
├── justfile           # Automation commands
├── eramba-docker/     # Eramba Docker repository (auto-created)
│   ├── .env          # Auto-generated configuration
│   ├── docker-compose.simple-install.yml
│   └── ...
├── src/
├── logs/
└── ...
```

## Manual Usage

If you prefer manual execution without Justfile:

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

## Troubleshooting

### Justfile Issues

**Error: "just command not found"**
```bash
# Install Just command runner
brew install just  # macOS
# or follow installation instructions in Setup section
```

**Error: "docker-compose not found"**
```bash
# Install Docker Compose
pip install docker-compose
```

**Error: "Port 8443 already in use"**
```bash
# Check what's using port 8443
lsof -i :8443

# Or change port in eramba-docker/.env
echo "APACHE_PORT=8081" >> eramba-docker/.env
```

**Error: "Container won't start"**
```bash
# Check logs
just logs-eramba

# Clean and restart
just clean-eramba
just start-eramba
```

### Environment Information

Check your environment setup:
```bash
just info
```

This will show:
- Python version
- Docker version
- Docker Compose version
- Current directory
- Eramba status

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `just test` or `pytest tests/`
5. Submit a pull request
