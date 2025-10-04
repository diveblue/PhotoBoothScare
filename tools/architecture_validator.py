"""
architecture_validator.py
Validates that code follows established architectural patterns
"""

import ast
import os
from typing import List, Dict


class ArchitectureValidator:
    """Validates PhotoBooth code follows SOLID principles and session manager patterns."""

    def __init__(self):
        self.violations = []

    def validate_file(self, filepath: str) -> List[str]:
        """Validate a Python file for architecture violations."""
        self.violations = []

        if not filepath.endswith(".py"):
            return []

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()

            tree = ast.parse(content)

            # Check for session management violations in main.py
            if "main.py" in filepath:
                self._check_main_session_violations(tree, content)

            # Check for scattered state management
            self._check_scattered_state(tree, content)

        except Exception as e:
            self.violations.append(f"Failed to parse {filepath}: {e}")

        return self.violations

    def _check_main_session_violations(self, tree: ast.AST, content: str):
        """Check main.py for session management violations."""

        # Skip if there's architecture debt acknowledged
        if "ARCHITECTURE DEBT" in content:
            return

        # Rule: main.py should use SessionManager, not manual state coordination
        if "state.start_countdown(" in content and "session_manager" not in content:
            self.violations.append(
                "VIOLATION: main.py uses manual state.start_countdown() instead of session_manager.start_countdown()"
            )

        if "state.countdown_active" in content and "session_manager" not in content:
            self.violations.append(
                "VIOLATION: main.py checks state.countdown_active directly instead of session_manager.is_idle()"
            )

        # Rule: Should import SessionManager if doing session coordination
        if any(
            keyword in content
            for keyword in ["countdown_active", "gotcha_active", "start_countdown"]
        ):
            if (
                "from photobooth.managers.session_manager import SessionManager"
                not in content
            ):
                self.violations.append(
                    "VIOLATION: main.py handles session logic but doesn't import SessionManager"
                )

    def _check_scattered_state(self, tree: ast.AST, content: str):
        """Check for scattered state management across managers."""

        # Rule: Managers shouldn't directly manipulate PhotoBoothState
        if "managers/" in content and "PhotoBoothState" in content:
            if "session_manager.py" not in content:  # SessionManager is allowed
                self.violations.append(
                    "VIOLATION: Manager directly manipulates PhotoBoothState instead of using SessionManager"
                )


def validate_architecture(root_dir: str = "src/photobooth") -> Dict[str, List[str]]:
    """Validate entire codebase architecture."""
    validator = ArchitectureValidator()
    results = {}

    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.endswith(".py"):
                filepath = os.path.join(root, file)
                violations = validator.validate_file(filepath)
                if violations:
                    results[filepath] = violations

    return results


if __name__ == "__main__":
    # Run validation
    violations = validate_architecture()

    if violations:
        print("🚨 ARCHITECTURE VIOLATIONS FOUND:")
        for filepath, issues in violations.items():
            print(f"\n📄 {filepath}:")
            for issue in issues:
                print(f"  ❌ {issue}")
        print("\n💡 SOLUTION: Use SessionManager for all session state management")
        print("   See: src/photobooth/managers/session_manager.py")
        exit(1)
    else:
        print("✅ No architecture violations found")
        exit(0)
