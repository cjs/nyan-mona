import math
from pathlib import Path
import runpy
from types import SimpleNamespace
import unittest


APP = Path(__file__).resolve().parents[1] / "nyan_mona" / "__init__.py"
GRAVITY = 16384


class Badge:
    ticks_delta = 20
    sample = (0, GRAVITY, 0, 0, 0, 0)

    def __init__(self, rotated=False, autorotate=True):
        self.rotated = rotated
        self.automatic = autorotate
        self.buttons = set()

    def mode(self, mode):
        pass

    def autorotate(self, value=None):
        if value is not None:
            self.automatic = value
        return self.automatic

    def rotate_180(self, value=None):
        if value is not None:
            self.rotated = value
        return self.rotated

    def imu(self):
        return self.sample

    def pressed(self, button):
        return button in self.buttons


class Matrix:
    def __init__(self):
        self.angle = 0
        self.translations = []

    def translate(self, x, y):
        self.translations.append((x, y))
        return self

    def rotate_radians(self, angle):
        self.angle = angle
        return self


class Screen:
    width = 320
    height = 240
    antialias = 4

    def __init__(self):
        self.rectangles = []
        self.fills = []
        self.shapes = []
        self.labels = []

    def clear(self):
        self.clear_pen = self.pen
        self.rectangles.clear()
        self.fills.clear()
        self.shapes.clear()
        self.labels.clear()

    def rectangle(self, *bounds):
        self.rectangles.append(bounds)
        self.fills.append((bounds, self.pen))

    def shape(self, tile):
        self.shapes.append(tile)
        self.shape_pen = self.pen

    def text(self, *args):
        self.labels.append(args)


class Image(Screen, bytearray):
    OFF = 0
    NEAREST = 0

    def __init__(self, width, height):
        bytearray.__init__(self, width * height * 4)
        Screen.__init__(self)
        self.width = width
        self.height = height


def load_app(badge=None):
    badge = badge or Badge()
    screen = Screen()
    app = runpy.run_path(str(APP), init_globals={
        "badge": badge,
        "screen": screen,
        "font": SimpleNamespace(nope=None),
        "color": SimpleNamespace(rgb=lambda *rgb: rgb),
        "image": Image,
        "brush": SimpleNamespace(
            image=lambda source, matrix, filtering: SimpleNamespace(source=source)),
        "rect": lambda *bounds: bounds,
        "shape": SimpleNamespace(
            rectangle=lambda *bounds: SimpleNamespace(bounds=bounds)),
        "mat3": Matrix,
        "run": lambda update: None,
        "HIRES": 1,
        "VSYNC": 2,
        "BUTTON_SELECT": "select",
        "BUTTON_LEFT": "left",
        "BUTTON_RIGHT": "right",
        "BUTTON_MENU": "menu",
        "BUTTON_UP": "up",
    })
    # runpy returns a copy; functions retain their original global namespace.
    return app["update"].__globals__, badge, screen


def gravity_at(degrees):
    angle = math.radians(degrees)
    return (-GRAVITY * math.sin(angle), GRAVITY * math.cos(angle), 0, 0, 0, 0)


class TiltTests(unittest.TestCase):
    def sample_for(self, app, badge, degrees, duration=1000, dt=20):
        badge.sample = gravity_at(degrees)
        for _ in range(duration // dt):
            app["update_tilt"](dt)
        return app["tilt_angle"]

    def test_enabling_at_an_existing_angle_does_not_lean(self):
        for degrees in (-180, -90, 0, 45, 90, 180):
            with self.subTest(degrees=degrees):
                app, badge, _ = load_app()
                app["tilt_enabled"] = True
                self.sample_for(app, badge, degrees)
                self.assertAlmostEqual(app["tilt_angle"], 0)

    def test_movement_leans_slightly_then_recentres_at_held_angle(self):
        for degrees in (-150, -45, 45, 150):
            with self.subTest(degrees=degrees):
                app, badge, _ = load_app()
                app["tilt_enabled"] = True
                self.sample_for(app, badge, 0)
                badge.sample = gravity_at(degrees)
                angles = []
                for _ in range(25):
                    app["update_tilt"](20)
                    angles.append(app["tilt_angle"])
                self.assertGreater(max(abs(angle) for angle in angles), math.radians(1))
                self.assertLessEqual(max(abs(angle) for angle in angles), math.radians(10))
                self.assertGreater(angles[0] * degrees, 0)
                self.sample_for(app, badge, degrees, duration=4000)
                self.assertLess(abs(app["tilt_angle"]), math.radians(0.1))

    def test_full_rotation_never_exceeds_ten_degrees(self):
        app, badge, _ = load_app()
        app["tilt_enabled"] = True
        for degrees in range(-360, 361, 15):
            with self.subTest(degrees=degrees):
                angle = self.sample_for(app, badge, degrees, duration=100)
                self.assertLessEqual(abs(angle), math.radians(10))

    def test_crossing_upside_down_takes_short_path(self):
        app, badge, _ = load_app()
        app["tilt_enabled"] = True
        self.sample_for(app, badge, 179)
        badge.sample = gravity_at(-179)
        for _ in range(10):
            app["update_tilt"](20)
        self.assertGreater(app["tilt_angle"], 0)
        self.assertLess(app["tilt_angle"], math.radians(1))

    def test_flat_returns_gradually_even_with_sensor_noise(self):
        for z in (-GRAVITY, GRAVITY):
            with self.subTest(z=z):
                app, badge, _ = load_app()
                app["tilt_enabled"] = True
                self.sample_for(app, badge, 0)
                self.sample_for(app, badge, 90, duration=200)
                before = app["tilt_angle"]
                badge.sample = (100, -100, z, 0, 0, 0)
                app["update_tilt"](20)
                self.assertFalse(app["tilt_active"])
                self.assertGreater(app["tilt_angle"], 0)
                self.assertLess(app["tilt_angle"], before)
                for _ in range(150):
                    app["update_tilt"](20)
                self.assertLess(abs(app["tilt_angle"]), math.radians(1))
                self.sample_for(app, badge, -90, duration=200)
                self.assertLess(abs(app["tilt_angle"]), math.radians(0.1))

    def test_flat_threshold_has_hysteresis(self):
        app, badge, _ = load_app()
        app["tilt_enabled"] = True
        badge.sample = (0, 0.24 * GRAVITY, GRAVITY, 0, 0, 0)
        app["update_tilt"](20)
        self.assertFalse(app["tilt_active"])
        self.sample_for(app, badge, 45)
        badge.sample = (0, 0.24 * GRAVITY, GRAVITY, 0, 0, 0)
        app["update_tilt"](20)
        self.assertTrue(app["tilt_active"])
        badge.sample = (0, 0.1 * GRAVITY, GRAVITY, 0, 0, 0)
        app["update_tilt"](20)
        self.assertFalse(app["tilt_active"])

    def test_smoothing_is_frame_rate_independent(self):
        results = []
        for dt in (10, 20, 50):
            app, badge, _ = load_app()
            app["tilt_enabled"] = True
            self.sample_for(app, badge, 0, dt=dt)
            results.append(self.sample_for(app, badge, 20, duration=200, dt=dt))
        for angle in results:
            self.assertLess(abs(angle - results[0]), math.radians(0.4))

    def test_zero_time_and_no_initial_sample(self):
        app, badge, _ = load_app()
        app["tilt_enabled"] = True
        badge.sample = (0, 0, 0, 0, 0, 0)
        app["update_tilt"](20)
        self.assertEqual(app["tilt_angle"], 0)
        badge.sample = gravity_at(90)
        app["update_tilt"](0)
        self.assertEqual(app["tilt_angle"], 0)

    def test_only_mona_and_trail_rotate_around_screen_centre(self):
        app, badge, screen = load_app()
        app["tilt_enabled"] = True
        app["update"]()
        badge.sample = gravity_at(45)
        app["update"]()
        self.assertEqual(len(screen.rectangles), 52)
        self.assertEqual(len(screen.shapes), 1)
        layer = app["flight_layer"]
        self.assertGreater(len(layer.rectangles), len(app["RUNS"]) + 16)
        self.assertIs(screen.shape_pen.source, layer)
        transform = screen.shapes[0].transform
        self.assertGreater(transform.angle, 0)
        self.assertEqual(transform.translations,
                         [(160, 120), (app["TRAIL_LEFT"] - 160, -42)])
        self.assertEqual(screen.labels[0], ("NYAN MONA", 8, 8))
        self.assertLess(app["TRAIL_LEFT"], -40)

    def test_layer_bounds_include_all_animation_frames(self):
        app, _, _ = load_app()
        layer = app["flight_layer"]
        layer.pen = (0, 0, 0, 0)
        for frame in range(6):
            layer.clear()
            app["mona"](layer, 160 - 36 - app["TRAIL_LEFT"],
                        9 + (0, 0, 1, 2, 2, 1)[frame] * 3, 3, frame)
            for x, y, width, height in layer.rectangles:
                self.assertGreaterEqual(x, 0)
                self.assertGreaterEqual(y, 0)
                self.assertLessEqual(x + width, layer.width)
                self.assertLessEqual(y + height, layer.height)

    def test_layer_keeps_a_transparent_sampling_border(self):
        app, _, _ = load_app()
        layer = app["flight_layer"]
        self.assertEqual(layer.clip, (1, 1, layer.width - 2, layer.height - 2))
        self.assertFalse(any(layer))

    def test_layer_erases_previous_pixels_instead_of_blending_transparency(self):
        app, _, _ = load_app()
        layer = app["flight_layer"]
        layer[:] = b"\xff" * len(layer)
        app["update"]()
        self.assertFalse(any(layer))

    def test_layer_preserves_upright_trail_positions_and_activity(self):
        app, _, _ = load_app()
        left = app["TRAIL_LEFT"]
        original = Image(320, 240)
        layer = app["flight_layer"]
        for time in (0, 0.137, 1, 100):
            with self.subTest(time=time):
                original.fills.clear()
                layer.fills.clear()
                app["rainbow_trail"](original, 124, 87, 3, time)
                app["rainbow_trail"](layer, 124 - left, 6, 3, time, left // 9)
                expected = {bounds: pen for bounds, pen in original.fills
                            if bounds[0] >= 0}
                actual = {(x + left, y + 81, width, height): pen
                          for (x, y, width, height), pen in layer.fills
                          if x + left >= 0}
                self.assertEqual(actual, expected)

    def test_tilt_continues_when_paused_and_ignores_speed(self):
        angles = []
        for speed_index in (0, 4):
            app, badge, _ = load_app()
            app["tilt_enabled"] = True
            app["paused"] = True
            app["speed_index"] = speed_index
            app["update"]()
            badge.sample = gravity_at(90)
            app["update"]()
            self.assertEqual(app["elapsed"], 0)
            angles.append(app["tilt_angle"])
        self.assertGreater(angles[0], 0)
        self.assertEqual(angles[0], angles[1])

    def test_controls_preserve_pause_speed_and_hints(self):
        app, badge, screen = load_app()
        badge.buttons = {"select", "right", "menu"}
        app["update"]()
        self.assertTrue(app["paused"])
        self.assertEqual(app["speed_index"], 2)
        self.assertFalse(app["show_controls"])
        self.assertEqual(len(screen.labels), 2)
        badge.buttons = {"select", "left"}
        app["update"]()
        self.assertFalse(app["paused"])
        self.assertEqual(app["speed_index"], 1)
        self.assertGreater(app["elapsed"], 0)

    def test_up_toggles_motion_without_a_kick_at_current_orientation(self):
        app, badge, screen = load_app()
        self.assertFalse(app["tilt_enabled"])
        badge.sample = gravity_at(90)
        app["update"]()
        self.assertEqual(app["tilt_angle"], 0)
        self.assertIn("MOTION OFF", screen.labels[1][0])
        badge.buttons = {"up"}
        app["update"]()
        self.assertTrue(app["tilt_enabled"])
        self.assertEqual(app["tilt_angle"], 0)
        badge.buttons.clear()
        self.sample_for(app, badge, 135, duration=200)
        before = app["tilt_angle"]
        badge.buttons = {"up"}
        app["update"]()
        self.assertFalse(app["tilt_enabled"])
        self.assertGreater(app["tilt_angle"], 0)
        self.assertLess(app["tilt_angle"], before)
        self.assertIn("MOTION OFF", screen.labels[1][0])
        badge.buttons.clear()
        for _ in range(150):
            app["update_tilt"](20)
        self.assertLess(abs(app["tilt_angle"]), math.radians(1))
        badge.buttons = {"up"}
        app["update"]()
        self.assertTrue(app["tilt_enabled"])
        self.assertIn("MOTION ON", screen.labels[1][0])
        self.assertLess(abs(app["tilt_angle"]), math.radians(1))
        reopened, _, _ = load_app()
        self.assertFalse(reopened["tilt_enabled"])

    def test_ripple_moves_squares_without_changing_their_sizes_or_activity(self):
        app, _, _ = load_app()
        normal = Image(320, 240)
        ripple = Image(320, 240)
        app["rainbow_trail"](normal, 124, 87, 3, 0.137)
        app["rainbow_trail"](ripple, 124, 87, 3, 0.137, ripple=1)
        self.assertEqual(len(normal.fills), len(ripple.fills))
        changed = False
        for ((x, y, width, height), pen), ((rx, ry, rw, rh), rpen) in zip(
                normal.fills, ripple.fills):
            self.assertEqual((x, width, height, pen), (rx, rw, rh, rpen))
            self.assertLessEqual(abs(ry - y), 2)
            changed = changed or ry != y
        self.assertTrue(changed)

    def test_motion_ripple_grows_and_settles_with_lean(self):
        app, badge, _ = load_app()
        app["tilt_enabled"] = True
        ripples = []
        draw_trail = app["rainbow_trail"]

        def capture_trail(*args, **kwargs):
            ripples.append(kwargs["ripple"])
            draw_trail(*args, **kwargs)

        app["rainbow_trail"] = capture_trail
        app["update"]()
        self.assertEqual(ripples[-1], 0)
        badge.sample = gravity_at(90)
        app["update"]()
        peak = ripples[-1]
        self.assertGreater(peak, 0)
        self.assertLessEqual(peak, 1)
        self.sample_for(app, badge, 90, duration=4000)
        app["update"]()
        self.assertLess(ripples[-1], peak / 10)

    def test_exit_restores_original_orientation_and_antialias(self):
        for automatic in (False, True):
            for rotated in (False, True):
                with self.subTest(automatic=automatic, rotated=rotated):
                    app, badge, screen = load_app(Badge(rotated, automatic))
                    self.assertFalse(badge.automatic)
                    self.assertFalse(badge.rotated)
                    self.assertEqual(screen.antialias, 0)
                    app["on_exit"]()
                    self.assertEqual(badge.automatic, automatic)
                    self.assertEqual(badge.rotated, rotated)
                    self.assertEqual(screen.antialias, 4)


if __name__ == "__main__":
    unittest.main()
