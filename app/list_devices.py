import os
import sys
import time

from openrgb import OpenRGBClient


def main() -> int:
    host = os.getenv("OPENRGB_HOST", "openrgb")
    port = int(os.getenv("OPENRGB_PORT", "6742"))

    deadline = time.time() + 30
    last_error = None

    while time.time() < deadline:
        try:
            client = OpenRGBClient(address=host, port=port, name="weather-led-inspector")
            break
        except Exception as exc:  # pragma: no cover - operational probe
            last_error = exc
            time.sleep(1)
    else:
        print(f"Failed to connect to OpenRGB at {host}:{port}: {last_error}", file=sys.stderr)
        return 1

    for index, device in enumerate(client.devices):
        print(f"{index}: {device.name} ({device.type})")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
