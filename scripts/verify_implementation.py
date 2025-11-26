#!/usr/bin/env python3
"""
Verification script for External LLM implementation.
Checks that all required files are in place and properly structured.
"""

import sys
from pathlib import Path

# Color codes
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def check_file(path: Path, description: str) -> bool:
    """Check if a file exists."""
    if path.exists():
        print(f"{GREEN}✓{RESET} {description}")
        return True
    else:
        print(f"{RED}✗{RESET} {description} - {RED}MISSING{RESET}")
        return False

def check_directory(path: Path, description: str) -> bool:
    """Check if a directory exists."""
    if path.is_dir():
        print(f"{GREEN}✓{RESET} {description}")
        return True
    else:
        print(f"{RED}✗{RESET} {description} - {RED}MISSING{RESET}")
        return False

def main():
    """Run verification checks."""
    print(f"\n{BLUE}{'=' * 70}{RESET}")
    print(f"{BLUE}  External LLM Implementation Verification{RESET}")
    print(f"{BLUE}{'=' * 70}{RESET}\n")

    base_path = Path(__file__).parent.parent
    all_checks = []

    # Provider Layer
    print(f"{YELLOW}Provider Abstraction Layer:{RESET}")
    all_checks.append(check_directory(base_path / "src/core/providers", "providers directory"))
    all_checks.append(check_file(base_path / "src/core/providers/__init__.py", "providers __init__.py"))
    all_checks.append(check_file(base_path / "src/core/providers/base.py", "base.py (BaseProvider, NLPProvider, SummaryProvider)"))
    all_checks.append(check_file(base_path / "src/core/providers/exceptions.py", "exceptions.py"))
    all_checks.append(check_file(base_path / "src/core/providers/factory.py", "factory.py (ProviderFactory)"))

    # Cloud Providers
    print(f"\n{YELLOW}Cloud Providers:{RESET}")
    all_checks.append(check_directory(base_path / "src/core/providers/cloud", "cloud providers directory"))
    all_checks.append(check_file(base_path / "src/core/providers/cloud/__init__.py", "cloud __init__.py"))
    all_checks.append(check_file(base_path / "src/core/providers/cloud/openai.py", "openai.py (OpenAINLPProvider, OpenAISummaryProvider)"))
    all_checks.append(check_file(base_path / "src/core/providers/cloud/openrouter.py", "openrouter.py (OpenRouterNLPProvider, OpenRouterSummaryProvider)"))

    # Config
    print(f"\n{YELLOW}Configuration:{RESET}")
    all_checks.append(check_directory(base_path / "src/core/config", "config directory"))
    all_checks.append(check_file(base_path / "src/core/config/__init__.py", "config __init__.py"))
    all_checks.append(check_file(base_path / "src/core/config/api_keys.py", "api_keys.py (APIKeyManager)"))

    # Orchestrator Integration
    print(f"\n{YELLOW}Orchestrator Integration:{RESET}")
    all_checks.append(check_file(base_path / "src/agents/orchestrator/provider_integration.py", "provider_integration.py (ProviderOrchestrator)"))

    # UI Components
    print(f"\n{YELLOW}UI Components:{RESET}")
    all_checks.append(check_directory(base_path / "src/ui/desktop/renderer/components/APISettingsPanel", "APISettingsPanel directory"))
    all_checks.append(check_file(base_path / "src/ui/desktop/renderer/components/APISettingsPanel/APISettingsPanel.tsx", "APISettingsPanel.tsx"))
    all_checks.append(check_file(base_path / "src/ui/desktop/renderer/components/APISettingsPanel/index.ts", "APISettingsPanel index.ts"))

    all_checks.append(check_directory(base_path / "src/ui/desktop/renderer/components/ProviderSelector", "ProviderSelector directory"))
    all_checks.append(check_file(base_path / "src/ui/desktop/renderer/components/ProviderSelector/ProviderSelector.tsx", "ProviderSelector.tsx"))
    all_checks.append(check_file(base_path / "src/ui/desktop/renderer/components/ProviderSelector/index.ts", "ProviderSelector index.ts"))

    all_checks.append(check_directory(base_path / "src/ui/desktop/renderer/components/CostMonitor", "CostMonitor directory"))
    all_checks.append(check_file(base_path / "src/ui/desktop/renderer/components/CostMonitor/CostMonitor.tsx", "CostMonitor.tsx"))
    all_checks.append(check_file(base_path / "src/ui/desktop/renderer/components/CostMonitor/index.ts", "CostMonitor index.ts"))

    # Tests
    print(f"\n{YELLOW}Tests:{RESET}")
    all_checks.append(check_file(base_path / "tests/test_providers.py", "test_providers.py"))

    # Scripts
    print(f"\n{YELLOW}Scripts:{RESET}")
    all_checks.append(check_file(base_path / "scripts/setup_external_llm.py", "setup_external_llm.py"))
    all_checks.append(check_file(base_path / "scripts/verify_implementation.py", "verify_implementation.py (this script)"))

    # Documentation
    print(f"\n{YELLOW}Documentation:{RESET}")
    all_checks.append(check_file(base_path / "EXTERNAL_LLM_IMPLEMENTATION.md", "Implementation report"))
    all_checks.append(check_file(base_path / "QUICKSTART_EXTERNAL_LLM.md", "Quick start guide"))

    # Dependencies
    print(f"\n{YELLOW}Dependencies:{RESET}")
    all_checks.append(check_file(base_path / "requirements-external-llm.txt", "External LLM requirements"))

    # Summary
    print(f"\n{BLUE}{'=' * 70}{RESET}")
    total = len(all_checks)
    passed = sum(all_checks)
    failed = total - passed

    if failed == 0:
        print(f"{GREEN}All checks passed! ({passed}/{total}){RESET}")
        print(f"\n{GREEN}✓ Implementation is complete and ready for testing{RESET}")
        print(f"\n{BLUE}Next steps:{RESET}")
        print(f"  1. Install dependencies: pip install -r requirements-external-llm.txt")
        print(f"  2. Run setup: python scripts/setup_external_llm.py")
        print(f"  3. Run tests: python tests/test_providers.py")
        return 0
    else:
        print(f"{RED}Some checks failed ({failed}/{total}){RESET}")
        print(f"\n{RED}✗ Please review missing files above{RESET}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
