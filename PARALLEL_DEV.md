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
