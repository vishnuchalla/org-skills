#!/bin/bash
#
# Orion Claude Skill Installer
#
# Installs the Orion regression analysis skill for Claude Code
#
set -euo pipefail

# Configuration
SKILL_NAME="orion-regression-analysis"
CLAUDE_SKILLS_DIR="$HOME/.claude/skills"
SKILL_INSTALL_DIR="$CLAUDE_SKILLS_DIR/$SKILL_NAME"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo
    echo "🏹 Orion Claude Skill Installer"
    echo "================================"
    echo
}

check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if Claude directory exists (indicates Claude Code is installed)
    if [[ ! -d "$HOME/.claude" ]]; then
        log_error "Claude Code not found. Please install Claude Code first."
        echo "Visit: https://code.claude.com/"
        exit 1
    fi
    
    # Check if Orion is available (optional but recommended)
    if ! command -v orion &> /dev/null; then
        log_warning "Orion CLI not found. Install it for full functionality:"
        echo "  https://github.com/cloud-bulldozer/orion"
    else
        local orion_version
        orion_version=$(orion --version 2>/dev/null || echo "unknown")
        log_info "Found Orion: $orion_version"
    fi
    
    log_success "Prerequisites checked"
}

create_directories() {
    log_info "Creating skill directories..."
    
    # Create Claude skills directory if it doesn't exist
    mkdir -p "$CLAUDE_SKILLS_DIR"
    
    # Create skill installation directory
    if [[ -d "$SKILL_INSTALL_DIR" ]]; then
        log_warning "Skill directory already exists: $SKILL_INSTALL_DIR"
        read -p "Do you want to overwrite it? [y/N]: " -r
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "Installation cancelled"
            exit 0
        fi
        rm -rf "$SKILL_INSTALL_DIR"
    fi
    
    mkdir -p "$SKILL_INSTALL_DIR"
    log_success "Directories created"
}

copy_skill_files() {
    log_info "Installing skill files..."
    
    # Copy all files to skill directory
    cp -r . "$SKILL_INSTALL_DIR/"
    
    # Remove installer script from installed location
    rm -f "$SKILL_INSTALL_DIR/install.sh"
    
    # Make scripts executable
    chmod +x "$SKILL_INSTALL_DIR/scripts"/*.sh 2>/dev/null || true
    
    log_success "Skill files installed"
}

verify_installation() {
    log_info "Verifying installation..."
    
    # Check if main skill file exists
    if [[ ! -f "$SKILL_INSTALL_DIR/SKILL.md" ]]; then
        log_error "Installation failed: SKILL.md not found"
        exit 1
    fi
    
    # Check directory structure
    local expected_dirs=("docs" "scripts")
    for dir in "${expected_dirs[@]}"; do
        if [[ ! -d "$SKILL_INSTALL_DIR/$dir" ]]; then
            log_warning "Directory missing: $dir"
        fi
    done
    
    # Count installed files
    local file_count
    file_count=$(find "$SKILL_INSTALL_DIR" -type f | wc -l)
    log_info "Installed $file_count files"
    
    log_success "Installation verified"
}

setup_environment() {
    log_info "Setting up environment..."
    
    # Add scripts to PATH (optional)
    local bashrc_entry="export PATH=\"\$PATH:$SKILL_INSTALL_DIR/scripts\""
    local zshrc_entry="export PATH=\"\$PATH:$SKILL_INSTALL_DIR/scripts\""
    
    # Check if user wants to add scripts to PATH
    echo
    read -p "Add Orion skill scripts to your PATH? [y/N]: " -r
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # Add to .bashrc if it exists
        if [[ -f "$HOME/.bashrc" ]] && ! grep -q "$SKILL_INSTALL_DIR/scripts" "$HOME/.bashrc"; then
            echo "# Orion Claude Skill Scripts" >> "$HOME/.bashrc"
            echo "$bashrc_entry" >> "$HOME/.bashrc"
            log_success "Added to ~/.bashrc"
        fi
        
        # Add to .zshrc if it exists
        if [[ -f "$HOME/.zshrc" ]] && ! grep -q "$SKILL_INSTALL_DIR/scripts" "$HOME/.zshrc"; then
            echo "# Orion Claude Skill Scripts" >> "$HOME/.zshrc"
            echo "$zshrc_entry" >> "$HOME/.zshrc"
            log_success "Added to ~/.zshrc"
        fi
        
        log_info "Restart your shell or run: source ~/.bashrc (or ~/.zshrc)"
    fi
    
    log_success "Environment setup complete"
}

print_usage() {
    echo
    echo "🎉 Installation Complete!"
    echo "========================"
    echo
    echo "The Orion regression analysis skill has been installed and is ready to use."
    echo
    echo "📍 Installation Location:"
    echo "   $SKILL_INSTALL_DIR"
    echo
    echo "🚀 How to Use:"
    echo "   1. Open Claude Code"
    echo "   2. Invoke manually: /orion-regression-analysis"
    echo "   3. Or just ask about Orion performance analysis"
    echo
    echo "📚 Available Resources:"
    echo "   • Configuration guide: $SKILL_INSTALL_DIR/docs/config-building-guide.md"
    echo "   • kube-burner patterns: $SKILL_INSTALL_DIR/docs/kube-burner-patterns.md"
    echo "   • k8s-netperf patterns: $SKILL_INSTALL_DIR/docs/k8s-netperf-patterns.md"
    echo "   • Troubleshooting:     $SKILL_INSTALL_DIR/docs/troubleshooting.md"
    echo "   • Example configs:     $SKILL_INSTALL_DIR/docs/examples/"
    echo
    echo "🛠️ Utility Scripts:"
    echo "   • validate-es-asset.py: Validate Elasticsearch configuration"
    echo "   • discover-es-data.py:  Discover available metrics and data"
    echo
    echo "💡 Example Usage:"
    echo '   "Help me create an Orion config for API server performance analysis"'
    echo '   "Can you explain these regression results from my cluster density test?"'
    echo '   "My Orion analysis isn'"'"'t finding data - help me troubleshoot"'
    echo
    echo "📖 For more information, see: $SKILL_INSTALL_DIR/README.md"
    echo
}

cleanup() {
    if [[ $? -ne 0 ]]; then
        log_error "Installation failed. Cleaning up..."
        rm -rf "$SKILL_INSTALL_DIR" 2>/dev/null || true
    fi
}

main() {
    # Set up error handling
    trap cleanup EXIT
    
    print_header
    check_prerequisites
    create_directories
    copy_skill_files
    verify_installation
    setup_environment
    print_usage
    
    # Clear error trap on successful completion
    trap - EXIT
}

main "$@"
