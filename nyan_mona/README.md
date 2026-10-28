# Nyan Mona

Nyan Mona is a pixel animation of Mona the Octocat flying through stars with a rainbow trail of GitHub contribution squares.

Requires a Badger 2350 running the Universe 2026 MonaOS runtime. No Wi-Fi,
downloads, audio, or credentials are needed.

## Controls

- SELECT: pause or resume.
- LEFT / RIGHT: choose 0.5x, 1x, 1.5x, 2x, or 3x speed.
- UP: turn the motion response on or off.
- MENU: hide or show control hints.
- HOME: return to MonaOS.

## Motion response

Moving the badge makes Mona and her trail briefly lean by up to 10 degrees.
The rainbow ripples a little more during the lean, keeping its distinct
contribution squares. Hold the badge still at any angle and both effects settle
back to normal, with Mona upright on screen. This is not gravity leveling.
Stars, text, and controls stay fixed to the screen.

Motion response starts disabled whenever the app opens. Press the front UP
button to toggle it; the status line shows MOTION ON or MOTION OFF. Turning it
on takes the badge's current orientation as the resting angle, without an
initial lean. Turning it off or laying the badge flat gradually returns Mona
upright. The effect remains active while the animation is paused.

The app temporarily disables the firmware's automatic screen flip and restores
the previous orientation settings on exit. The onboard IMU is required.

## Install

Copy this entire `nyan_mona` folder, including `__init__.py` and `icon.png`,
into the writable `apps` folder on the BADGER disk in USB Disk Mode. Safely
eject the disk, restart the badge, and open Nyan Mona from the menu.

This is an unofficial fan-made animation, not an official GitHub asset.
