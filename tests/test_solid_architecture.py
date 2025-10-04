#!/usr/bin/env python3
"""
Test script to validate the SOLID architecture refactoring works correctly.
Tests that SessionManager orchestrates properly and returns valid SessionAction objects.
"""

import sys
import os
import time

# Add the src directory to Python path for import resolution
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src_path = os.path.join(project_root, "src")
sys.path.insert(0, src_path)

from photobooth.managers.session_manager import SessionManager
from photobooth.utils.session_action import SessionAction


def test_session_manager_orchestration():
    """Test that SessionManager.update() returns proper SessionAction objects."""
    print("🧪 Testing SOLID Architecture: SessionManager orchestration...")

    # Load config
    config_path = os.path.join(project_root, "config.json")
    import json

    with open(config_path, "r") as f:
        config = json.load(f)

    # Initialize managers
    session_manager = SessionManager(
        config, lambda category, msg: print(f"[{category}] {msg}")
    )

    # Test idle state
    now = time.time()
    action = session_manager.update(
        now=now,
        frame_dimensions=(1280, 720),
        video_recording=False,
        video_finalized=False,
    )

    assert isinstance(action, SessionAction), (
        f"Expected SessionAction, got {type(action)}"
    )
    assert not action.start_video, "Should not start video in idle state"
    print("✅ Idle state returns proper SessionAction")

    # Test button press (simulate countdown start)
    session_manager.start_countdown()
    action = session_manager.update(
        now=now,
        frame_dimensions=(1280, 720),
        video_recording=False,
        video_finalized=False,
    )

    assert action.start_video, "Should start video after button press"
    assert action.show_countdown, "Should show countdown after button press"
    assert isinstance(action.countdown_number, int), "Should have countdown number"
    print("✅ Button press triggers proper video start and countdown")

    # Test countdown progression
    time.sleep(0.1)  # Small delay
    now = time.time()
    action = session_manager.update(
        now=now,
        frame_dimensions=(1280, 720),
        video_recording=True,
        video_finalized=False,
    )

    # Should still be in countdown or moved to smile phase
    assert action.session_id is not None, "Should have valid session ID"
    print("✅ Session progression maintains proper state")

    print("🎉 SOLID Architecture test passed - SessionManager orchestrates correctly!")


def test_session_action_structure():
    """Test that SessionAction objects have expected structure."""
    print("\n🧪 Testing SessionAction structure...")

    action = SessionAction()

    # Verify all expected attributes exist
    expected_attrs = [
        "start_video",
        "stop_video",
        "video_dimensions",
        "play_beep",
        "play_shutter",
        "trigger_scare",
        "show_countdown",
        "countdown_number",
        "show_smile",
        "show_gotcha",
        "show_qr",
        "qr_url",
        "capture_photo",
        "move_files",
        "cleanup_session",
        "session_complete",
        "session_id",
        "session_time",
    ]

    for attr in expected_attrs:
        assert hasattr(action, attr), f"SessionAction missing attribute: {attr}"

    print("✅ SessionAction has all expected attributes")
    print("🎉 SessionAction structure test passed!")


if __name__ == "__main__":
    try:
        test_session_action_structure()
        test_session_manager_orchestration()
        print(
            "\n🚀 All SOLID architecture tests passed! The refactoring is working correctly."
        )
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
