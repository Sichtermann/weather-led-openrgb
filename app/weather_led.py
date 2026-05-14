import argparse
import logging
import os
import sys
import time
from dataclasses import dataclass
from typing import Iterable

import requests
from openrgb import OpenRGBClient
from openrgb.utils import RGBColor


FORECAST_URL = "https://api.open-meteo.com/v1/forecast"


@dataclass(frozen=True)
class ForecastColor:
    name: str
    reason: str
    color: RGBColor


FORECAST_COLORS = {
    "clear": ForecastColor("clear", "clear sky", RGBColor(253, 184, 19)),
    "partly_cloudy": ForecastColor("partly_cloudy", "partly cloudy", RGBColor(111, 177, 255)),
    "cloudy": ForecastColor("cloudy", "cloudy or foggy", RGBColor(154, 165, 177)),
    "rain": ForecastColor("rain", "drizzle or rain", RGBColor(46, 134, 222)),
    "snow": ForecastColor("snow", "snow or freezing precipitation", RGBColor(190, 233, 255)),
    "storm": ForecastColor("storm", "thunderstorm", RGBColor(255, 94, 91)),
    "unknown": ForecastColor("unknown", "unknown weather", RGBColor(255, 255, 255)),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Set tower LEDs to tomorrow's weather color.")
    parser.add_argument("--once", action="store_true", help="Run one update and exit.")
    return parser.parse_args()


def configure_logging() -> None:
    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(message)s",
        stream=sys.stdout,
    )


def fetch_tomorrow_forecast() -> dict:
    latitude = os.getenv("LATITUDE", "50.9375")
    longitude = os.getenv("LONGITUDE", "6.9603")
    timezone = os.getenv("TIMEZONE", "Europe/Berlin")

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "timezone": timezone,
        "daily": "weather_code,temperature_2m_min,temperature_2m_max,precipitation_probability_max",
        "forecast_days": 2,
    }

    response = requests.get(FORECAST_URL, params=params, timeout=30)
    response.raise_for_status()
    payload = response.json()
    daily = payload["daily"]

    if len(daily["time"]) < 2:
        raise RuntimeError("Open-Meteo did not return tomorrow's forecast")

    return {
        "date": daily["time"][1],
        "weather_code": daily["weather_code"][1],
        "temperature_2m_min": daily["temperature_2m_min"][1],
        "temperature_2m_max": daily["temperature_2m_max"][1],
        "precipitation_probability_max": daily["precipitation_probability_max"][1],
    }


def classify_weather(weather_code: int) -> ForecastColor:
    if weather_code == 0:
        return FORECAST_COLORS["clear"]
    if weather_code in {1, 2}:
        return FORECAST_COLORS["partly_cloudy"]
    if weather_code in {3, 45, 48}:
        return FORECAST_COLORS["cloudy"]
    if weather_code in {51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82}:
        return FORECAST_COLORS["rain"]
    if weather_code in {71, 73, 75, 77, 85, 86}:
        return FORECAST_COLORS["snow"]
    if weather_code in {95, 96, 99}:
        return FORECAST_COLORS["storm"]
    return FORECAST_COLORS["unknown"]


def connect_openrgb() -> OpenRGBClient:
    host = os.getenv("OPENRGB_HOST", "openrgb")
    port = int(os.getenv("OPENRGB_PORT", "6742"))
    name = os.getenv("OPENRGB_CLIENT_NAME", "weather-led")

    deadline = time.time() + 60
    last_error = None

    while time.time() < deadline:
        try:
            return OpenRGBClient(address=host, port=port, name=name)
        except Exception as exc:  # pragma: no cover - hardware/service timing
            last_error = exc
            logging.info("Waiting for OpenRGB at %s:%s: %s", host, port, exc)
            time.sleep(2)

    raise RuntimeError(f"Unable to connect to OpenRGB at {host}:{port}: {last_error}")


def matching_devices(devices: Iterable, needle: str):
    needle = needle.strip().lower()
    if not needle:
        return list(devices)
    return [device for device in devices if needle in device.name.lower()]


def set_device_color(device, color: RGBColor) -> None:
    modes = [mode.name.lower() for mode in getattr(device, "modes", [])]

    for preferred in ("direct", "static", "solid color"):
        if preferred in modes:
            try:
                device.set_mode(preferred)
                break
            except Exception:
                logging.debug("Mode %s failed on %s", preferred, device.name, exc_info=True)

    device.set_color(color)


def apply_color_to_devices(color_info: ForecastColor, forecast: dict) -> None:
    client = connect_openrgb()
    device_filter = os.getenv("OPENRGB_DEVICE_FILTER", "AURA")
    selected = matching_devices(client.devices, device_filter)

    if not selected:
        available = ", ".join(device.name for device in client.devices) or "none"
        raise RuntimeError(
            f"No OpenRGB device matched filter {device_filter!r}. Detected devices: {available}"
        )

    for device in selected:
        set_device_color(device, color_info.color)
        logging.info(
            "Set %s to %s for %s on %s (temp %.1f-%.1f C, precip %s%%)",
            device.name,
            color_info.name,
            color_info.reason,
            forecast["date"],
            forecast["temperature_2m_min"],
            forecast["temperature_2m_max"],
            forecast["precipitation_probability_max"],
        )


def run_once() -> None:
    forecast = fetch_tomorrow_forecast()
    color_info = classify_weather(int(forecast["weather_code"]))
    logging.info(
        "Tomorrow in configured location: weather_code=%s, date=%s, mapped_color=%s",
        forecast["weather_code"],
        forecast["date"],
        color_info.name,
    )
    apply_color_to_devices(color_info, forecast)


def main() -> int:
    args = parse_args()
    configure_logging()
    interval = int(os.getenv("UPDATE_INTERVAL_SECONDS", "21600"))

    while True:
        try:
            run_once()
        except Exception:
            logging.exception("LED update failed")
            if args.once:
                return 1
        if args.once:
            return 0
        time.sleep(interval)


if __name__ == "__main__":
    raise SystemExit(main())
