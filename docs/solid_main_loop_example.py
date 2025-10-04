"""
SOLID-compliant main loop example for PhotoBooth

This shows how main.py should work with the new SessionManager.update() architecture.
The main loop only executes actions returned by SessionManager - no decision making.
"""


def main_loop_solid_example():
    """Example of SOLID-compliant main loop."""

    # Initialize managers (same as before)
    session_manager = SessionManager(CONFIG, debug_log)
    # ... other manager initialization

    while True:
        frame = camera.get_frame()
        if frame is None:
            continue
        frame = cv2.flip(frame, 1)

        now = time.time()
        height, width = frame.shape[:2]

        # SINGLE CALL TO SESSION MANAGER - this is the key change
        action = session_manager.update(
            now=now,
            frame_dimensions=(width, height),
            video_recording=video_manager.recording,
            video_finalized=video_manager.is_finalized(),
        )

        # EXECUTE ACTIONS - main.py just follows orders
        if action.start_video:
            video_manager.start_recording(
                action.session_id, action.session_time, action.video_dimensions
            )

        if action.stop_video:
            video_manager.stop_recording()

        if action.play_beep:
            audio.play_beep()

        if action.play_shutter:
            audio.play_shutter()

        if action.trigger_scare:
            gpio.trigger_scare()

        if action.capture_photo:
            photo_manager.capture_photo(
                frame, action.session_time, action.session_id, now
            )

        if action.move_files:
            file_manager.move_files_to_network(action.session_id)

        # DISPLAY OVERLAYS based on actions
        if action.show_countdown and action.countdown_number:
            overlay_renderer.draw_countdown(frame, action.countdown_number)
        elif action.show_smile:
            overlay_renderer.draw_smile(frame)
        elif action.show_gotcha:
            overlay_renderer.draw_gotcha(frame)
            if action.show_qr and qr_img is not None:
                overlay_renderer.draw_qr_code(frame, qr_img)

        if action.session_complete:
            # Clean up session
            qr_img = None
            photo_manager.reset()
            gotcha_manager.reset()

        # Handle QR generation
        if action.show_qr and action.qr_url and qr_img is None:
            qr_path = f"qr_{action.session_id}.png"
            generate_qr(action.qr_url, qr_path, size=8)
            qr_img = cv2.imread(qr_path)

        # Display frame
        display_manager.display_frame(frame)

        # Handle input
        if keyboard_input.handle_events():
            break
