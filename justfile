# Justfile to automate Security GRC Case project tasks
# Usage: just <command>

# Configuration
ERAMBA_REPO := "https://github.com/eramba/docker.git"
ERAMBA_DIR := "eramba-docker"
ERAMBA_BRANCH := "1.x"

# Default commands
default:
    @just --list

# === ERAMBA COMMANDS ===

# Clone the Eramba Docker repository
clone-eramba:
    #!/usr/bin/env bash
    echo "🔄 Cloning Eramba Docker repository..."
    if [ -d "{{ERAMBA_DIR}}" ]; then
        echo "⚠️  Directory {{ERAMBA_DIR}} already exists. Removing..."
        rm -rf {{ERAMBA_DIR}}
    fi
    git clone -b {{ERAMBA_BRANCH}} {{ERAMBA_REPO}} {{ERAMBA_DIR}}
    echo "✅ Repository cloned successfully!"

# Configure Eramba environment
setup-eramba: clone-eramba
    #!/usr/bin/env bash
    echo "🔧 Configuring Eramba environment..."
    cd {{ERAMBA_DIR}}
    
    # Check if .env file exists, if not, create one based on example
    if [ ! -f .env ]; then
        echo "📝 Creating .env file..."
        cp .env .env.backup 2>/dev/null || true
        
        # Basic configurations for local development
        {
            echo "# Eramba Docker Configuration"
            echo "MYSQL_ROOT_PASSWORD=rootpassword"
            echo "MYSQL_DATABASE=eramba"
            echo "MYSQL_USER=eramba"
            echo "MYSQL_PASSWORD=eramba123"
            echo "MYSQL_HOST=mysql"
            echo "MYSQL_PORT=3306"
            echo ""
            echo "# PHP Configuration"
            echo "PHP_VERSION=8.1"
            echo "APACHE_PORT=8080"
            echo ""
            echo "# Eramba Configuration"
            echo "ERAMBA_VERSION=latest"
            echo "ERAMBA_TIMEZONE=America/Sao_Paulo"
            echo "ERAMBA_ADMIN_EMAIL=admin@localhost"
            echo "ERAMBA_ADMIN_PASSWORD=admin123"
            echo ""
            echo "# Development Configuration"
            echo "DEBUG=1"
            echo "ENVIRONMENT=development"
        } > .env
        echo "✅ .env file created with default configurations"
    fi
    
    echo "🔧 Configuration completed!"

# Start Eramba server
start-eramba: setup-eramba
    #!/usr/bin/env bash
    echo "🚀 Starting Eramba server..."
    cd {{ERAMBA_DIR}}

    docker rm -f $(docker ps -aq) || true
    docker ps -a
    
    # Check which docker-compose to use
    if [ -f "docker-compose.simple-install.yml" ]; then
        echo "📦 Using docker-compose.simple-install.yml..."
        docker-compose -f docker-compose.simple-install.yml up -d
    else
        echo "📦 Using default docker-compose.yml..."
        docker-compose up -d
    fi
    
    echo "⏳ Waiting for services to start..."
    sleep 10
    
    echo "✅ Eramba started successfully!"
    echo "🌐 Access: https://localhost:8443"
    echo "👤 User: admin"
    echo "🔑 Password: admin123"

# Stop Eramba server
stop-eramba:
    #!/usr/bin/env bash
    echo "🛑 Stopping Eramba server..."
    cd {{ERAMBA_DIR}}
    
    if [ -f "docker-compose.simple-install.yml" ]; then
        docker-compose -f docker-compose.simple-install.yml down
    else
        docker-compose down
    fi
    
    echo "✅ Eramba server stopped!"

# Restart Eramba server
restart-eramba: stop-eramba start-eramba

# Check Eramba containers status
status-eramba:
    #!/usr/bin/env bash
    echo "📊 Eramba containers status:"
    cd {{ERAMBA_DIR}}
    
    if [ -f "docker-compose.simple-install.yml" ]; then
        docker-compose -f docker-compose.simple-install.yml ps
    else
        docker-compose ps
    fi

# Show Eramba logs
logs-eramba:
    #!/usr/bin/env bash
    echo "📋 Eramba logs:"
    cd {{ERAMBA_DIR}}
    
    if [ -f "docker-compose.simple-install.yml" ]; then
        docker-compose -f docker-compose.simple-install.yml logs -f
    else
        docker-compose logs -f
    fi

# Access Eramba container shell
shell-eramba:
    #!/usr/bin/env bash
    echo "🐚 Accessing Eramba container shell..."
    cd {{ERAMBA_DIR}}
    
    CONTAINER_NAME=$(docker-compose ps -q web 2>/dev/null || docker-compose ps -q app 2>/dev/null || docker-compose ps -q eramba 2>/dev/null)
    
    if [ -n "$CONTAINER_NAME" ]; then
        docker exec -it $CONTAINER_NAME /bin/bash
    else
        echo "❌ Eramba container not found!"
        echo "📊 Available containers:"
        docker-compose ps
    fi

# Completely remove Eramba (containers, volumes, network)
clean-eramba:
    #!/usr/bin/env bash
    echo "🧹 Completely removing Eramba..."
    cd {{ERAMBA_DIR}}
    
    if [ -f "docker-compose.simple-install.yml" ]; then
        docker-compose -f docker-compose.simple-install.yml down -v --remove-orphans
    else
        docker-compose down -v --remove-orphans
    fi
    
    # Remove Eramba-related images
    echo "🗑️  Removing Eramba Docker images..."
    docker images | grep eramba | awk '{print $3}' | xargs docker rmi -f 2>/dev/null || true
    
    echo "✅ Eramba completely removed!"

# Update Eramba repository
update-eramba:
    #!/usr/bin/env bash
    echo "🔄 Updating Eramba repository..."
    cd {{ERAMBA_DIR}}
    
    git fetch origin
    git reset --hard origin/{{ERAMBA_BRANCH}}
    
    echo "✅ Repository updated!"

# === PROJECT COMMANDS ===

# Install project dependencies
install:
    #!/usr/bin/env bash
    echo "📦 Installing dependencies..."
    pip install -r requirements.txt
    echo "✅ Dependencies installed!"

# Run PR analysis
analyze:
    #!/usr/bin/env bash
    echo "🔍 Running PR analysis..."
    python main.py analyze
    echo "✅ Analysis completed!"

# Run all checks
check:
    #!/usr/bin/env bash
    echo "🔍 Running control checks..."
    python main.py check
    echo "✅ Checks completed!"

# Submit evidence
submit:
    #!/usr/bin/env bash
    echo "📤 Submitting evidence..."
    python main.py submit
    echo "✅ Evidence submitted!"

# Generate report
report:
    #!/usr/bin/env bash
    echo "📊 Generating report..."
    python main.py report
    echo "✅ Report generated!"

# Run tests
test:
    #!/usr/bin/env bash
    echo "🧪 Running tests..."
    python -m pytest tests/ -v
    echo "✅ Tests completed!"

# === DEVELOPMENT COMMANDS ===

# Configure development environment
dev-setup: install setup-eramba
    #!/usr/bin/env bash
    echo "🚀 Configuring development environment..."
    
    # Check if virtual environment exists
    if [ ! -d "venv" ]; then
        echo "🐍 Creating virtual environment..."
        python -m venv venv
    fi
    
    echo "✅ Development environment configured!"
    echo "🔧 To activate virtual environment: source venv/bin/activate"
    echo "🌐 To access Eramba: just start-eramba"

# Clean cache and temporary files
clean:
    #!/usr/bin/env bash
    echo "🧹 Cleaning cache and temporary files..."
    find . -type f -name "*.pyc" -delete
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
    rm -rf .pytest_cache/ 2>/dev/null || true
    echo "✅ Cleanup completed!"

# Show environment information
info:
    #!/usr/bin/env bash
    echo "ℹ️  Environment information:"
    echo "🐍 Python: $(python --version)"
    echo "🐋 Docker: $(docker --version)"
    echo "📦 Docker Compose: $(docker-compose --version)"
    echo "📁 Current directory: $(pwd)"
    echo "📊 Eramba status:"
    if [ -d "{{ERAMBA_DIR}}" ]; then
        echo "   ✅ Repository cloned"
        cd {{ERAMBA_DIR}}
        if docker-compose ps | grep -q "Up"; then
            echo "   🟢 Server running"
        else
            echo "   🔴 Server stopped"
        fi
    else
        echo "   ❌ Repository not cloned"
    fi

# === INTEGRATION COMMANDS ===

# Run complete pipeline
pipeline: install check submit report
    #!/usr/bin/env bash
    echo "🎯 Pipeline executed successfully!"

# Run pipeline with Eramba
full-pipeline: dev-setup start-eramba pipeline
    #!/usr/bin/env bash
    echo "🎯 Full pipeline executed successfully!"
    echo "🌐 Eramba available at: https://localhost:8443"

# Backup Eramba data
backup-eramba:
    #!/usr/bin/env bash
    echo "💾 Backing up Eramba data..."
    cd {{ERAMBA_DIR}}
    
    BACKUP_DIR="../eramba-backup-$(date +%Y%m%d_%H%M%S)"
    mkdir -p $BACKUP_DIR
    
    # Database backup
    MYSQL_CONTAINER=$(docker-compose ps -q mysql 2>/dev/null || docker-compose ps -q db 2>/dev/null)
    if [ -n "$MYSQL_CONTAINER" ]; then
        echo "📊 Backing up database..."
        docker exec $MYSQL_CONTAINER mysqldump -u root -prootpassword eramba > $BACKUP_DIR/eramba_db.sql
    fi
    
    # Configuration files backup
    cp -r . $BACKUP_DIR/docker-files/
    
    echo "✅ Backup created at: $BACKUP_DIR" 