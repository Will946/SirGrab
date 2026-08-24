"""
Local serial bridge for the 3D arm viewer.

The 3D view runs in your browser and can't talk to the Arduino directly
(browsers can't open serial ports on their own). This script is the piece
that actually holds the serial connection - it runs locally, opens a
WebSocket server, and forwards whatever angles the browser sends over to
the Arduino.

Install deps first (inside your venv):
    pip install pyserial websockets

Run this FIRST, then open arm_3d_viewer.html in your browser:
    python arm_3d_bridge.py
"""

import asyncio
import websockets
import serial
import json
import time

SERIAL_PORT = "/dev/tty.usbmodemE8F60AA9A0342"  # <-- update if your port differs
BAUD_RATE = 115200
WS_PORT = 8765

CALIBRATION = {
    0: 90, 3: 75, 8: 105, 4: 90, 7: 105, 11: 90, 12: 90, 15: 60,
}

try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    time.sleep(2)
    print("Connected to Arduino.")
except Exception as e:
    ser = None
    print(f"No serial connection ({e}) - bridge will run but won't move anything.")

last_sent = {}


def send_command(channel, angle):
    angle = int(max(0, min(180, angle)))
    if last_sent.get(channel) == angle:
        return
    last_sent[channel] = angle
    if ser:
        ser.write(f"{channel}:{angle}\n".encode())
    print(f"Ch{channel} -> {angle}")


async def handle_client(websocket):
    print("Browser connected.")

    # Send the whole arm to calibration once a browser tab connects
    for ch, angle in CALIBRATION.items():
        send_command(ch, angle)

    try:
        async for message in websocket:
            data = json.loads(message)
            channel = data.get("channel")
            angle = data.get("angle")
            if channel is not None and angle is not None:
                send_command(channel, angle)
    except websockets.exceptions.ConnectionClosed:
        print("Browser disconnected.")


async def main():
    async with websockets.serve(handle_client, "localhost", WS_PORT):
        print(f"Bridge running on ws://localhost:{WS_PORT}")
        print("Now open arm_3d_viewer.html in your browser.")
        await asyncio.Future()  # run forever


if __name__ == "__main__":
    asyncio.run(main())
