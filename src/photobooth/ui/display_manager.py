"""
display_manager.py
Handles display setup and rendering for both pygame and OpenCV
"""

import os
import pygame
import cv2


class DisplayManager:
    def __init__(self, config, args, debug_log_func):
        self.config = config
        self.args = args
        self.debug_log = debug_log_func

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

        self.debug_log(
            "camera",
            f"[ENV] IS_LINUX={self.is_linux} HAS_DISPLAY_SERVER={self.has_display_server} "
            f"SSH_SESSION={self.ssh_session} ON_CONSOLE_VT={self.on_console_vt} USE_PYGAME_DISPLAY={self.use_pygame}",
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
                self.debug_log("camera", f"[INFO] Trying SDL driver: {drv}")

                pygame.display.init()
                info = pygame.display.Info()

                if self.args.windowed:
                    # Windowed mode for development
                    screen_size = (1024, 768)
                    self.screen = pygame.display.set_mode(screen_size, 0)
                    pygame.mouse.set_visible(True)
                    pygame.display.set_caption("PhotoBooth Scare - Development Mode")
                    print(
                        f"[INFO] Pygame windowed mode with driver '{drv}' -> {screen_size}"
                    )
                else:
                    # Fullscreen mode for production
                    screen_size = (info.current_w, info.current_h)
                    self.screen = pygame.display.set_mode(
                        screen_size, pygame.FULLSCREEN
                    )
                    pygame.mouse.set_visible(False)
                    print(
                        f"[INFO] Pygame fullscreen with driver '{drv}' -> {screen_size}"
                    )
                break
            except Exception as e:
                print(f"[WARN] Driver '{drv}' failed: {e}")
                self.screen = None

        if self.screen is None:
            print(
                "[ERROR] No suitable SDL framebuffer driver worked; falling back to OpenCV"
            )
            self.use_pygame = False
            self._setup_opencv()

    def _setup_opencv(self):
        """Setup OpenCV display."""
        try:
            cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
            if not self.args.windowed:
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
        """Display a frame using the appropriate display system."""
        if frame is None:
            return None

        if self.use_pygame and self.screen:
            return self._show_pygame_frame(frame)
        else:
            return self._show_opencv_frame(frame)

    def _show_pygame_frame(self, frame):
        """Display frame using pygame."""
        try:
            # Convert BGR to RGB and rotate/flip for pygame
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame_surface = pygame.surfarray.make_surface(frame_rgb.swapaxes(0, 1))

            # Scale to screen size
            screen_size = self.screen.get_size()
            frame_scaled = pygame.transform.scale(frame_surface, screen_size)

            self.screen.blit(frame_scaled, (0, 0))
            pygame.display.flip()

            # Handle pygame events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return ord("q")
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q or event.key == pygame.K_ESCAPE:
                        return ord("q")
                    elif event.key == pygame.K_SPACE:
                        return ord(" ")
                    elif event.key == pygame.K_F11:
                        return ord("q")
                    else:
                        # Convert pygame key to ASCII if possible
                        if event.unicode and len(event.unicode) == 1:
                            return ord(event.unicode)
        except Exception as e:
            print(f"[WARN] Pygame display error: {e}")

        return None

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
