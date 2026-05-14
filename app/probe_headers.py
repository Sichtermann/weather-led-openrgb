import time

from openrgb import OpenRGBClient
from openrgb.utils import RGBColor


SIZES = (30, 60, 90, 120)
COLORS = (
    ("red", RGBColor(255, 0, 0)),
    ("green", RGBColor(0, 255, 0)),
    ("blue", RGBColor(0, 0, 255)),
)


def main() -> int:
    client = OpenRGBClient(address="openrgb", port=6742, name="header-probe")
    device = next(d for d in client.devices if d.name.startswith("ASUS "))
    device.set_mode("Direct", force=True)

    for zone in device.zones:
        if not zone.name.startswith("Aura Addressable"):
            continue
        for size in SIZES:
            print(f"Testing {zone.name} with {size} LEDs")
            zone.resize(size)
            device.update()
            for color_name, color in COLORS:
                print(f"  -> {color_name}")
                device.set_color(color)
                time.sleep(1.0)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
