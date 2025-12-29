#!/bin/bash

# PL Request Management System - Setup Script
# Automates the installation and configuration process

echo "╔════════════════════════════════════════════════════════════════════╗"
echo "║     PL Number Material Request Management System - Setup          ║"
echo "╚════════════════════════════════════════════════════════════════════╝"
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python version
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 1: Checking Python version"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    echo -e "${GREEN}✓${NC} Python 3 found: version $PYTHON_VERSION"
    
    # Check if version is 3.8+
    MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
    MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
    
    if [ "$MAJOR" -ge 3 ] && [ "$MINOR" -ge 8 ]; then
        echo -e "${GREEN}✓${NC} Python version is compatible (3.8+)"
    else
        echo -e "${RED}✗${NC} Python 3.8 or higher is required"
        echo "  Please upgrade Python and run this script again"
        exit 1
    fi
else
    echo -e "${RED}✗${NC} Python 3 not found"
    echo "  Please install Python 3.8+ and run this script again"
    exit 1
fi

# Install dependencies
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 2: Installing dependencies"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ -f "requirements.txt" ]; then
    echo "Installing Python packages..."
    python3 -m pip install -r requirements.txt --quiet
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓${NC} All dependencies installed successfully"
    else
        echo -e "${RED}✗${NC} Failed to install dependencies"
        echo "  Try running manually: pip3 install -r requirements.txt"
        exit 1
    fi
else
    echo -e "${RED}✗${NC} requirements.txt not found"
    exit 1
fi

# Check for .env file
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 3: Configuring environment"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ ! -f ".env" ]; then
    echo -e "${YELLOW}!${NC} .env file not found"
    
    if [ -f ".env.example" ]; then
        echo "Creating .env from .env.example..."
        cp .env.example .env
        echo -e "${GREEN}✓${NC} .env file created"
        echo ""
        echo -e "${YELLOW}⚠ IMPORTANT:${NC} You must edit .env with your MongoDB Atlas credentials"
        echo ""
        echo "To configure:"
        echo "  1. Open .env in a text editor"
        echo "  2. Replace <username> and <password> with your MongoDB Atlas credentials"
        echo "  3. Save the file"
        echo ""
        echo "After editing .env, run this script again or start the app with:"
        echo "  streamlit run app.py"
        echo ""
        
        # Ask if user wants to edit now
        read -p "Would you like to edit .env now? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            ${EDITOR:-nano} .env
        fi
    else
        echo -e "${RED}✗${NC} .env.example not found"
        exit 1
    fi
else
    echo -e "${GREEN}✓${NC} .env file exists"
    
    # Check if it still has placeholders
    if grep -q "<username>" .env || grep -q "<password>" .env; then
        echo -e "${YELLOW}⚠${NC} .env file contains placeholders"
        echo "  Please edit .env with your actual MongoDB Atlas credentials"
    else
        echo -e "${GREEN}✓${NC} .env appears to be configured"
    fi
fi

# Run configuration check
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 4: Verifying configuration"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

python3 check_config.py

CONFIG_CHECK_EXIT=$?

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Setup Complete"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ $CONFIG_CHECK_EXIT -eq 0 ]; then
    echo -e "${GREEN}✓${NC} System is ready to use!"
    echo ""
    echo "To start the application:"
    echo "  streamlit run app.py"
    echo ""
    echo "To run tests:"
    echo "  python3 test_system.py"
    echo ""
    echo "For more information:"
    echo "  - README.md - Complete documentation"
    echo "  - QUICKSTART.md - Quick start guide"
    echo "  - SCHEMA.md - Database schema"
else
    echo -e "${YELLOW}!${NC} Setup completed with warnings"
    echo ""
    echo "Please review and fix the issues shown above."
    echo ""
    echo "Common fixes:"
    echo "  1. Edit .env with your MongoDB Atlas credentials"
    echo "  2. Configure network access in MongoDB Atlas"
    echo "  3. Verify your connection string"
    echo ""
    echo "For detailed help, see QUICKSTART.md"
fi

echo ""
