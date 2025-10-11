"""
display_manager.py
Handles display setup and rendering for both pygame and OpenCV
"""

import os
import pygame
import cv2

import logging
import time


class DisplayManager:
    def __init__(
        self,
        config,
        camera_manager,
        overlay_renderer,
        session_manager,
        keyboard_input_manager=None,
        logger=None,
    ):
        self.config = config
        self.logger = logger or logging.getLogger("DisplayManager")

        # Core managers
        self.camera_manager = camera_manager
        self.overlay_renderer = overlay_renderer
        self.session_manager = session_manager
        self.keyboard_input_manager = keyboard_input_manager

        # Display state
        self.screen = None
        self.use_pygame = False
        self.window_name = config["WINDOW_NAME"]

        # Environment detection
        self.is_linux = os.name == "posix"
        self.has_display_server = bool(
            os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")
        )
        self.ssh_session = bool(
            os.environ.get("SSH_CLIENT") or os.environ.get("SSH_TTY")
        )
        self.on_console_vt = self._detect_console_vt()

        self._setup_display()

    def _detect_console_vt(self):
        """Detect if running on console VT."""
        try:
            with open("/sys/class/tty/tty0/active", "r") as f:
                active_vt = f.read().strip()
                return active_vt.startswith("tty")
        except Exception:
            return False

    def _setup_display(self):
        """Setup display system (pygame or OpenCV)."""
        self.use_pygame = self._should_use_pygame()

        self.logger.debug(
            f"[ENV] IS_LINUX={self.is_linux} HAS_DISPLAY_SERVER={self.has_display_server} "
            f"SSH_SESSION={self.ssh_session} ON_CONSOLE_VT={self.on_console_vt} USE_PYGAME_DISPLAY={self.use_pygame}"
        )

        if self.use_pygame:
            self._setup_pygame()
        else:
            self._setup_opencv()

    def _should_use_pygame(self):
        """Determine if pygame should be used for display."""
        if not self.is_linux:
            return False
        if self.ssh_session:
            return False
        if not self.has_display_server and not self.on_console_vt:
            return False
        return True

    def _setup_pygame(self):
        """Setup pygame display."""
        pygame.display.init()

        # Try different SDL drivers
        drivers = self.config.get(
            "PYGAME_DRIVERS", ["kmsdrm", "fbcon", "directfb", "svgalib"]
        )

        for drv in drivers:
            try:
                os.environ["SDL_VIDEODRIVER"] = drv
                self.logger.debug(f"[INFO] Trying SDL driver: {drv}")

                pygame.display.init()
                info = pygame.display.Info()

                if self.config.get("WINDOWED", False):
                    # Windowed mode for development
                    screen_size = (1024, 768)
                    self.screen = pygame.display.set_mode(screen_size, 0)
                    pygame.mouse.set_visible(True)
                    pygame.display.set_caption("PhotoBooth Scare - Development Mode")
                    self.logger.info(
                        f"Pygame windowed mode with driver '{drv}' -> {screen_size}"
                    )
                else:
                    # Fullscreen mode for production
                    screen_size = (info.current_w, info.current_h)
                    self.screen = pygame.display.set_mode(
                        screen_size, pygame.FULLSCREEN
                    )
                    pygame.mouse.set_visible(False)
                    self.logger.info(
                        f"Pygame fullscreen with driver '{drv}' -> {screen_size}"
                    )
                break
            except Exception as e:
                self.logger.warning(f"Driver '{drv}' failed: {e}")
                self.screen = None

        if self.screen is None:
            self.logger.error(
                "No suitable SDL framebuffer driver worked; falling back to OpenCV"
            )
            self.use_pygame = False
            self._setup_opencv()

    def _setup_opencv(self):
        """Setup OpenCV display."""
        try:
            cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
            if not self.config.get("WINDOWED", False):
                # Try to make OpenCV window fullscreen
                try:
                    cv2.setWindowProperty(
                        self.window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN
                    )
                    cv2.moveWindow(self.window_name, 0, 0)
                except Exception:
                    pass
            else:
                # Windowed mode - resize to development size
                try:
                    cv2.resizeWindow(self.window_name, 1024, 768)
                except Exception:
                    pass
        except Exception:
            pass

    def show_frame(self, frame):
        """Display a single frame using the appropriate display system."""
        if frame is None or not hasattr(frame, "shape"):
            print("[DEBUG] show_frame: frame is None or invalid")
            self.logger.warning(
                "DisplayManager: show_frame called with None or invalid frame"
            )
            return
        h, w = frame.shape[:2]
        if h == 0 or w == 0:
            print(f"[DEBUG] show_frame: frame shape is {frame.shape} (empty)")
            self.logger.warning(
                f"DisplayManager: show_frame called with empty frame (shape={frame.shape})"
            )
            return
        if self.use_pygame:
            if self.screen is not None:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                surf = pygame.surfarray.make_surface(frame_rgb.swapaxes(0, 1))
                self.screen.blit(surf, (0, 0))
                pygame.display.flip()
        else:
            cv2.imshow(self.window_name, frame)
            cv2.waitKey(1)  # Always call waitKey to keep window responsive
        # No recursion, no loop, just display the frame

    def _show_opencv_frame(self, frame):
        """Display frame using OpenCV."""
        try:
            cv2.imshow(self.window_name, frame)
            key = cv2.waitKey(1) & 0xFF
            if key != 255:  # 255 means no key pressed
                return key
        except Exception:
            pass

        return None

    def cleanup(self):
        """Cleanup display resources."""
        if self.use_pygame:
            try:
                pygame.quit()
            except Exception:
                pass
        else:
            try:
                cv2.destroyAllWindows()
            except Exception:
                pass

    def run(self):
        """
        Main display loop: fetch frames, apply overlay, display. Exits on quit flag.

        NOTE: This method must be called from the main thread when using OpenCV or pygame display backends,
        especially on Windows. GUI operations in background threads may result in no window or display issues.
        """

        while True:
            frame = self.camera_manager.get_frame()
            print(
                f"[DEBUG] camera_manager.get_frame() -> {type(frame)}, shape={getattr(frame, 'shape', None)}"
            )
            if frame is None:
                self.logger.warning(
                    "DisplayManager: camera_manager.get_frame() returned None"
                )
                time.sleep(0.05)
                continue

            # Update session state machine every frame
            self.session_manager.update(time.time(), frame.shape[:2])

            # Get current state (idle, etc.)
            state = self.session_manager.state
            frame_with_overlay = self.overlay_renderer.draw_overlay(frame, state)
            print(
                f"[DEBUG] overlay_renderer.draw_overlay() -> {type(frame_with_overlay)}, shape={getattr(frame_with_overlay, 'shape', None)}"
            )
            if frame_with_overlay is None:
                self.logger.warning(
                    "DisplayManager: overlay_renderer.draw_overlay() returned None"
                )
            key = None
            if self.use_pygame:
                self.show_frame(frame_with_overlay)
                if self.keyboard_input_manager is not None:
                    if self.keyboard_input_manager.handle_pygame_events(state):
                        self.logger.info(
                            "Quit requested by keyboard input (pygame backend)."
                        )
                        return
                else:
                    time.sleep(0.01)
            else:
                import cv2

                # Only call waitKey once per loop, use result for both display and input
                cv2.imshow(self.window_name, frame_with_overlay)
                key = cv2.waitKey(1)
                if self.keyboard_input_manager is not None:
                    if self.keyboard_input_manager.handle_opencv_key(key, state):
                        self.logger.info(
                            "Quit requested by keyboard input (opencv backend)."
                        )
                        return
                else:
                    time.sleep(0.01)
