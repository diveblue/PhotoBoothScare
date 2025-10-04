# Architecture Enforcement Guide

## The Problem
Session state was scattered across multiple managers, violating SOLID principles and causing duplicate session issues.

## The Solution
Always use `SessionManager` for session coordination.

## Required Reading
Before modifying session-related code, READ:
- `src/photobooth/managers/session_manager.py` - The authoritative session coordinator
- `.github/copilot-instructions.md` - Architecture requirements marked as **CRITICAL RULE**

## Validation Tools
- `python architecture_validator.py` - Check for violations before committing
- Install pre-commit hook: `cp pre-commit-hook.py .git/hooks/pre-commit && chmod +x .git/hooks/pre-commit`

## Quick Reference

### ❌ DON'T DO (violates SOLID):
```python
# Scattered state management in main.py
if state.countdown_active or gotcha_manager.is_active():
    return
state.start_countdown(COUNTDOWN_SECONDS)
```

### ✅ DO THIS (follows SOLID):
```python
# Centralized session management
if not session_manager.is_idle():
    return
session_manager.start_countdown()
```

## Emergency Override
If you must violate architecture temporarily, add this comment:
```python
# ARCHITECTURE DEBT: This violates SessionManager pattern - TODO: refactor
# Reason: [brief explanation]
# Tracking: [issue number or timeline]
```

The validator will skip lines with `ARCHITECTURE DEBT` comments.