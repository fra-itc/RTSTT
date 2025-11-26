#!/bin/bash

###############################################################################
# Parallel Development Setup Script for RTSTT Project
#
# This script sets up a multi-worktree, multi-terminal development environment
# for parallel feature implementation:
#   1. Audio File Upload & Batch Transcription
#   2. External LLM APIs (OpenAI/OpenRouter for NLP/Summary)
#   3. External STT APIs (OpenAI/OpenRouter for STT)
#   4. STT Model Benchmarking (11 models: 6 local + 5 cloud)
#
# Requirements:
#   - Git 2.5+ (for worktree support)
#   - tmux (for multi-terminal sessions)
#   - Python 3.10+
#   - Node.js 16+
###############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
MAIN_REPO="/home/frisco/projects/RTSTT"
WORKTREE_BASE="/home/frisco/projects"
MAIN_BRANCH="Main-t-orchestrazione"

# Feature branches and worktrees
declare -A FEATURES=(
    ["audio-upload"]="feature/audio-file-upload:RTSTT-audio-upload"
    ["external-llm"]="feature/external-llm-apis:RTSTT-external-llm"
    ["external-stt"]="feature/external-stt-apis:RTSTT-external-stt"
    ["model-bench"]="feature/stt-model-benchmarks:RTSTT-model-bench"
)

# Port allocations (to avoid conflicts during parallel development)
declare -A PORTS=(
    ["audio-upload"]="8001:50054:50055:50056:5174:6380"  # Backend:STT:NLP:Summary:Frontend:Redis
    ["external-llm"]="8002:50057:50058:50059:5175:6381"
    ["external-stt"]="8003:50060:50061:50062:5176:6382"
    ["model-bench"]="8004:50063:50064:50065:5177:6383"
    ["main"]="8000:50051:50052:50053:5173:6379"  # Main development
)

###############################################################################
# Helper Functions
###############################################################################

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

check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check git version
    if ! command -v git &> /dev/null; then
        log_error "Git is not installed"
        exit 1
    fi

    local git_version=$(git --version | grep -oP '\d+\.\d+' | head -1)
    if (( $(echo "$git_version < 2.5" | bc -l) )); then
        log_error "Git version 2.5+ required (found $git_version)"
        exit 1
    fi

    # Check tmux
    if ! command -v tmux &> /dev/null; then
        log_warning "tmux not installed. Install with: sudo apt-get install tmux"
        log_warning "You can still use worktrees manually without tmux"
    fi

    # Check Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is not installed"
        exit 1
    fi

    # Check Node.js
    if ! command -v node &> /dev/null; then
        log_error "Node.js is not installed"
        exit 1
    fi

    log_success "Prerequisites check passed"
}

create_worktrees() {
    log_info "Creating git worktrees for parallel development..."

    cd "$MAIN_REPO"

    # Ensure we're on main branch and up to date
    log_info "Ensuring main branch is up to date..."
    git fetch origin
    git checkout "$MAIN_BRANCH" 2>/dev/null || git checkout -b "$MAIN_BRANCH"
    git pull origin "$MAIN_BRANCH" 2>/dev/null || true

    # Create worktrees for each feature
    for feature_key in "${!FEATURES[@]}"; do
        local branch_and_dir="${FEATURES[$feature_key]}"
        local branch="${branch_and_dir%%:*}"
        local worktree_dir="${branch_and_dir##*:}"
        local full_path="$WORKTREE_BASE/$worktree_dir"

        log_info "Setting up worktree: $worktree_dir (branch: $branch)"

        # Check if worktree already exists
        if [ -d "$full_path" ]; then
            log_warning "Worktree already exists: $full_path"
            read -p "Remove and recreate? (y/N) " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                git worktree remove "$full_path" --force 2>/dev/null || rm -rf "$full_path"
            else
                log_info "Skipping $worktree_dir"
                continue
            fi
        fi

        # Create worktree with new branch
        if git rev-parse --verify "$branch" &>/dev/null; then
            log_info "Branch $branch already exists, creating worktree from existing branch"
            git worktree add "$full_path" "$branch"
        else
            log_info "Creating new branch $branch from $MAIN_BRANCH"
            git worktree add "$full_path" -b "$branch"
        fi

        log_success "Created worktree: $worktree_dir"
    done

    # List all worktrees
    log_info "Current worktrees:"
    git worktree list
}

setup_virtual_envs() {
    log_info "Setting up Python virtual environments for each worktree..."

    for feature_key in "${!FEATURES[@]}"; do
        local branch_and_dir="${FEATURES[$feature_key]}"
        local worktree_dir="${branch_and_dir##*:}"
        local full_path="$WORKTREE_BASE/$worktree_dir"

        if [ ! -d "$full_path" ]; then
            log_warning "Worktree not found: $full_path, skipping venv setup"
            continue
        fi

        log_info "Creating venv in $worktree_dir..."
        cd "$full_path"

        # Create virtual environment
        if [ -d "venv" ]; then
            log_warning "venv already exists in $worktree_dir"
        else
            python3 -m venv venv
            log_success "Created venv in $worktree_dir"
        fi

        # Install requirements if they exist
        if [ -f "requirements/base.txt" ]; then
            log_info "Installing requirements in $worktree_dir..."
            source venv/bin/activate
            pip install --upgrade pip
            pip install -r requirements/base.txt
            pip install -r requirements/dev.txt 2>/dev/null || true
            deactivate
            log_success "Installed requirements in $worktree_dir"
        fi
    done

    cd "$MAIN_REPO"
}

create_env_files() {
    log_info "Creating .env files for each worktree with port allocations..."

    for feature_key in "${!FEATURES[@]}"; do
        local branch_and_dir="${FEATURES[$feature_key]}"
        local worktree_dir="${branch_and_dir##*:}"
        local full_path="$WORKTREE_BASE/$worktree_dir"
        local ports="${PORTS[$feature_key]}"

        if [ ! -d "$full_path" ]; then
            continue
        fi

        # Parse ports
        IFS=':' read -ra PORT_ARRAY <<< "$ports"
        local backend_port="${PORT_ARRAY[0]}"
        local stt_port="${PORT_ARRAY[1]}"
        local nlp_port="${PORT_ARRAY[2]}"
        local summary_port="${PORT_ARRAY[3]}"
        local frontend_port="${PORT_ARRAY[4]}"
        local redis_port="${PORT_ARRAY[5]}"

        # Create .env file
        cat > "$full_path/.env.local" << EOF
# Environment configuration for $worktree_dir
# Generated by setup_parallel_dev.sh

# Backend ports
BACKEND_PORT=$backend_port
STT_SERVICE_PORT=$stt_port
NLP_SERVICE_PORT=$nlp_port
SUMMARY_SERVICE_PORT=$summary_port

# Frontend port
VITE_PORT=$frontend_port

# Redis port
REDIS_PORT=$redis_port

# Service URLs
STT_SERVICE_URL=localhost:$stt_port
NLP_SERVICE_URL=localhost:$nlp_port
SUMMARY_SERVICE_URL=localhost:$summary_port

# Database
DATABASE_URL=postgresql://rtstt:rtstt_dev@localhost:5432/rtstt_$feature_key

# Feature flag
FEATURE_BRANCH=$feature_key
EOF

        log_success "Created .env.local for $worktree_dir"
    done
}

create_tmux_session() {
    log_info "Creating tmux session for parallel development..."

    if ! command -v tmux &> /dev/null; then
        log_warning "tmux not installed, skipping session creation"
        return
    fi

    local session_name="rtstt-parallel-dev"

    # Kill existing session if it exists
    tmux kill-session -t "$session_name" 2>/dev/null || true

    # Create new session
    tmux new-session -d -s "$session_name" -n "main"

    # Window 0: Main development (current branch)
    tmux send-keys -t "$session_name:0" "cd $MAIN_REPO" C-m
    tmux send-keys -t "$session_name:0" "source venv/bin/activate" C-m
    tmux send-keys -t "$session_name:0" "clear && echo 'Main Development - $MAIN_BRANCH' && git status" C-m

    # Window 1: Audio Upload Feature
    tmux new-window -t "$session_name:1" -n "audio-upload"
    local audio_upload_path="$WORKTREE_BASE/${FEATURES[audio-upload]##*:}"
    tmux send-keys -t "$session_name:1" "cd $audio_upload_path" C-m
    tmux send-keys -t "$session_name:1" "source venv/bin/activate" C-m
    tmux send-keys -t "$session_name:1" "clear && echo 'Audio File Upload Feature' && git status" C-m

    # Window 2: External LLM APIs
    tmux new-window -t "$session_name:2" -n "external-llm"
    local external_llm_path="$WORKTREE_BASE/${FEATURES[external-llm]##*:}"
    tmux send-keys -t "$session_name:2" "cd $external_llm_path" C-m
    tmux send-keys -t "$session_name:2" "source venv/bin/activate" C-m
    tmux send-keys -t "$session_name:2" "clear && echo 'External LLM APIs Feature' && git status" C-m

    # Window 3: External STT APIs
    tmux new-window -t "$session_name:3" -n "external-stt"
    local external_stt_path="$WORKTREE_BASE/${FEATURES[external-stt]##*:}"
    tmux send-keys -t "$session_name:3" "cd $external_stt_path" C-m
    tmux send-keys -t "$session_name:3" "source venv/bin/activate" C-m
    tmux send-keys -t "$session_name:3" "clear && echo 'External STT APIs Feature' && git status" C-m

    # Window 4: Model Benchmarking
    tmux new-window -t "$session_name:4" -n "model-bench"
    local model_bench_path="$WORKTREE_BASE/${FEATURES[model-bench]##*:}"
    tmux send-keys -t "$session_name:4" "cd $model_bench_path" C-m
    tmux send-keys -t "$session_name:4" "source venv/bin/activate" C-m
    tmux send-keys -t "$session_name:4" "clear && echo 'STT Model Benchmarking' && git status" C-m

    # Select main window
    tmux select-window -t "$session_name:0"

    log_success "Created tmux session: $session_name"
    log_info "Attach to session with: tmux attach -t $session_name"
    log_info ""
    log_info "Tmux navigation:"
    log_info "  - Switch windows: Ctrl+b, then 0-4"
    log_info "  - Detach: Ctrl+b, then d"
    log_info "  - Kill session: tmux kill-session -t $session_name"
}

create_makefile() {
    log_info "Creating Makefile for workflow automation..."

    cat > "$MAIN_REPO/Makefile.parallel" << 'EOF'
# Parallel Development Makefile for RTSTT Project
# Usage: make -f Makefile.parallel <target>

.PHONY: help setup-worktrees setup-tmux clean-worktrees sync-all test-all

help:
	@echo "RTSTT Parallel Development Automation"
	@echo ""
	@echo "Available targets:"
	@echo "  setup-worktrees  - Create all git worktrees and venvs"
	@echo "  setup-tmux       - Create tmux session for parallel work"
	@echo "  sync-all         - Sync all worktrees with main branch"
	@echo "  test-all         - Run tests in all worktrees"
	@echo "  clean-worktrees  - Remove all worktrees (DESTRUCTIVE)"
	@echo "  list-ports       - Show port allocation for each feature"
	@echo ""

setup-worktrees:
	@bash scripts/setup_parallel_dev.sh --worktrees-only

setup-tmux:
	@bash scripts/setup_parallel_dev.sh --tmux-only

sync-all:
	@echo "Syncing all worktrees with main branch..."
	@git fetch origin
	@git checkout Main-t-orchestrazione
	@git pull origin Main-t-orchestrazione
	@for dir in ../RTSTT-*/; do \
		if [ -d "$$dir" ]; then \
			echo "Syncing $$dir..."; \
			cd "$$dir" && git fetch origin && git merge Main-t-orchestrazione && cd -; \
		fi \
	done

test-all:
	@echo "Running tests in all worktrees..."
	@for dir in ../RTSTT-*/; do \
		if [ -d "$$dir" ]; then \
			echo "Testing $$dir..."; \
			cd "$$dir" && source venv/bin/activate && pytest tests/ && cd -; \
		fi \
	done

clean-worktrees:
	@echo "WARNING: This will remove all worktrees!"
	@read -p "Are you sure? (y/N) " confirm && [ $$confirm = y ]
	@git worktree remove ../RTSTT-audio-upload --force || true
	@git worktree remove ../RTSTT-external-llm --force || true
	@git worktree remove ../RTSTT-external-stt --force || true
	@git worktree remove ../RTSTT-model-bench --force || true
	@rm -rf ../RTSTT-audio-upload ../RTSTT-external-llm ../RTSTT-external-stt ../RTSTT-model-bench

list-ports:
	@echo "Port Allocation:"
	@echo "  Main:          Backend=8000  STT=50051  NLP=50052  Summary=50053  Frontend=5173  Redis=6379"
	@echo "  Audio Upload:  Backend=8001  STT=50054  NLP=50055  Summary=50056  Frontend=5174  Redis=6380"
	@echo "  External LLM:  Backend=8002  STT=50057  NLP=50058  Summary=50059  Frontend=5175  Redis=6381"
	@echo "  External STT:  Backend=8003  STT=50060  NLP=50061  Summary=50062  Frontend=5176  Redis=6382"
	@echo "  Model Bench:   Backend=8004  STT=50063  NLP=50064  Summary=50065  Frontend=5177  Redis=6383"
EOF

    log_success "Created Makefile.parallel"
}

create_readme() {
    log_info "Creating README for parallel development workflow..."

    cat > "$MAIN_REPO/PARALLEL_DEV.md" << 'EOF'
# Parallel Development Workflow

This document describes the parallel development setup for implementing 3 major features simultaneously.

## Overview

We use **git worktrees** to enable parallel development on 4 feature branches:

1. **Audio File Upload** (`feature/audio-file-upload`) - Batch transcription from uploaded files
2. **External LLM APIs** (`feature/external-llm-apis`) - OpenAI/OpenRouter for NLP/Summary
3. **External STT APIs** (`feature/external-stt-apis`) - Cloud STT providers
4. **Model Benchmarking** (`feature/stt-model-benchmarks`) - Compare 11 STT models

## Quick Start

```bash
# 1. Setup all worktrees and environments
bash scripts/setup_parallel_dev.sh

# 2. Attach to tmux session
tmux attach -t rtstt-parallel-dev

# 3. Navigate between windows (Ctrl+b, then 0-4)
#    Window 0: Main development
#    Window 1: Audio upload
#    Window 2: External LLM
#    Window 3: External STT
#    Window 4: Model benchmarking
```

## Directory Structure

```
/home/frisco/projects/
├── RTSTT/                    # Main repo (Main-t-orchestrazione)
├── RTSTT-audio-upload/       # feature/audio-file-upload
├── RTSTT-external-llm/       # feature/external-llm-apis
├── RTSTT-external-stt/       # feature/external-stt-apis
└── RTSTT-model-bench/        # feature/stt-model-benchmarks
```

## Port Allocation

To avoid conflicts when running multiple instances:

| Feature       | Backend | STT   | NLP   | Summary | Frontend | Redis |
|---------------|---------|-------|-------|---------|----------|-------|
| Main          | 8000    | 50051 | 50052 | 50053   | 5173     | 6379  |
| Audio Upload  | 8001    | 50054 | 50055 | 50056   | 5174     | 6380  |
| External LLM  | 8002    | 50057 | 50058 | 50059   | 5175     | 6381  |
| External STT  | 8003    | 50060 | 50061 | 50062   | 5176     | 6382  |
| Model Bench   | 8004    | 50063 | 50064 | 50065   | 5177     | 6383  |

## Workflow Commands

```bash
# Create/update worktrees
make -f Makefile.parallel setup-worktrees

# Create tmux session
make -f Makefile.parallel setup-tmux

# Sync all worktrees with main
make -f Makefile.parallel sync-all

# Run tests in all worktrees
make -f Makefile.parallel test-all

# List port allocations
make -f Makefile.parallel list-ports

# Clean up all worktrees (DESTRUCTIVE)
make -f Makefile.parallel clean-worktrees
```

## Development Tips

### Working in Multiple Worktrees

Each worktree is an independent working directory with its own:
- Branch checkout
- Virtual environment
- .env configuration
- Running services

You can:
- Edit files in multiple worktrees simultaneously
- Run different service versions on different ports
- Test integration between features
- Make commits independently

### Syncing with Main Branch

Regularly sync your feature branch with main:

```bash
cd /home/frisco/projects/RTSTT-audio-upload
git fetch origin
git merge Main-t-orchestrazione
# Resolve conflicts if any
git push origin feature/audio-file-upload
```

### Running Services in Parallel

```bash
# Terminal 1: Main development backend
cd /home/frisco/projects/RTSTT
docker-compose up  # Uses ports 8000, 50051-50053, 6379

# Terminal 2: Audio upload feature
cd /home/frisco/projects/RTSTT-audio-upload
docker-compose -f docker-compose.override.yml up  # Uses ports 8001, 50054-50056, 6380

# Terminal 3: External LLM feature
cd /home/frisco/projects/RTSTT-external-llm
docker-compose -f docker-compose.override.yml up  # Uses ports 8002, 50057-50059, 6381
```

### Merging Features

When a feature is complete:

```bash
# 1. Ensure feature branch is up to date
cd /home/frisco/projects/RTSTT-audio-upload
git fetch origin
git merge Main-t-orchestrazione
git push origin feature/audio-file-upload

# 2. Create pull request on GitHub
gh pr create --title "feat: Audio file upload and batch transcription" \
             --body "Implements batch processing for uploaded audio files"

# 3. After review and merge, sync main
cd /home/frisco/projects/RTSTT
git checkout Main-t-orchestrazione
git pull origin Main-t-orchestrazione

# 4. Sync other worktrees
make -f Makefile.parallel sync-all
```

## Troubleshooting

### Worktree Already Exists

If you see "worktree already exists", you can:
- Let the script skip it (N)
- Remove and recreate (y)
- Manually remove: `git worktree remove ../RTSTT-audio-upload --force`

### Port Conflicts

If ports are already in use:
```bash
# Find process using port
lsof -i :8001

# Kill process
kill -9 <PID>
```

### Tmux Not Attached

```bash
# List sessions
tmux ls

# Attach to session
tmux attach -t rtstt-parallel-dev

# Kill and recreate
tmux kill-session -t rtstt-parallel-dev
bash scripts/setup_parallel_dev.sh --tmux-only
```

## References

- [Git Worktree Documentation](https://git-scm.com/docs/git-worktree)
- [Tmux Cheat Sheet](https://tmuxcheatsheet.com/)
- [Project Main README](./README.md)
EOF

    log_success "Created PARALLEL_DEV.md"
}

print_summary() {
    log_success "Parallel development environment setup complete!"
    echo ""
    echo "=============================================="
    echo "  Worktrees Created:"
    echo "=============================================="
    git worktree list
    echo ""
    echo "=============================================="
    echo "  Next Steps:"
    echo "=============================================="
    echo "  1. Attach to tmux session:"
    echo "     tmux attach -t rtstt-parallel-dev"
    echo ""
    echo "  2. Navigate between features:"
    echo "     Ctrl+b, then 0-4"
    echo ""
    echo "  3. Start development in parallel!"
    echo ""
    echo "  4. Read PARALLEL_DEV.md for detailed workflow"
    echo "=============================================="
}

###############################################################################
# Main Execution
###############################################################################

main() {
    log_info "Starting parallel development setup for RTSTT project"
    echo ""

    # Parse arguments
    WORKTREES_ONLY=false
    TMUX_ONLY=false

    for arg in "$@"; do
        case $arg in
            --worktrees-only)
                WORKTREES_ONLY=true
                ;;
            --tmux-only)
                TMUX_ONLY=true
                ;;
        esac
    done

    # Check prerequisites
    check_prerequisites
    echo ""

    if [ "$TMUX_ONLY" = true ]; then
        create_tmux_session
        exit 0
    fi

    # Setup worktrees
    create_worktrees
    echo ""

    # Setup virtual environments
    setup_virtual_envs
    echo ""

    # Create environment files
    create_env_files
    echo ""

    # Create automation files
    create_makefile
    create_readme
    echo ""

    if [ "$WORKTREES_ONLY" = false ]; then
        # Create tmux session
        create_tmux_session
        echo ""
    fi

    # Print summary
    print_summary
}

# Run main function
main "$@"
