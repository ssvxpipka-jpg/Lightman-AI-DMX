# Lightman Deployment Guide

## Overview

This guide covers deploying the Lightman system for a school theater environment.

## Prerequisites

- Python 3.10+
- One computer to run the Director (Windows/macOS/Linux)
- Sound computer (Windows/macOS/Linux) with audio input
- Light computer (Windows/macOS/Linux) with DMX/BLE hardware

## Quick Start

1. Run the installer:
   ```bash
   # macOS/Linux
   bash install.sh

   # Windows
   install.bat

   # Cross-platform Python
   python install.py
   ```

2. Activate the virtual environment:
   ```bash
   source venv/bin/activate    # macOS/Linux
   venv\Scripts\activate.bat   # Windows
   ```

3. Start the Director:
   ```bash
   python -m src.director.main
   ```

4. Start the Sound app:
   ```bash
   python -m src.sound.app
   ```

5. Start the Light app:
   ```python -m src.light.app
   ```

## Pairing

1. Start the Sound and Light apps — each displays a random code (SL-SOUND-XXXX / SL-LIGHT-XXXX).
2. In the Director, enter the codes to establish a BLE GATT connection via HMAC-SHA256 signed packets.
3. Once paired, the Director can control Sound (OSC) and Light (console protocol) apps.

## Server OS (Future)

A dedicated Server OS image will be available in Lightman 2.0. See `docs/server_os.md` for details.

## Production Deployment

For production theater setups:

1. Install Lightman on all machines in the same network.
2. Configure console connection in `config/servers.yaml`.
3. Set up the IP camera RTSP URL in Director settings.
4. Use the Knowledge Base tab to upload scripts and documentation.
5. Run a rehearsal to calibrate tracking and lighting behavior.

## Troubleshooting

- Ensure all three apps are on the same network.
- If BLE pairing fails, check that Bluetooth is enabled and not in use by another app.
- For console connection issues, verify IP and port in `config/servers.yaml`.
