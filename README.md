# weatherLed

Map Cologne's next-day weather forecast to your tower LEDs with Docker Compose.

## What it does

- Fetches tomorrow's forecast from Open-Meteo.
- Maps the forecast condition to a single RGB color.
- Connects to an OpenRGB server and applies that color to matching devices.
- Repeats on a configurable interval so the LED tracks forecast changes.

Default location is Cologne, Germany:

- Latitude: `50.9375`
- Longitude: `6.9603`
- Timezone: `Europe/Berlin`

## Color map

- Clear: warm sun yellow
- Partly cloudy: soft sky blue
- Cloudy or fog: cool gray
- Rain or drizzle: deep rain blue
- Snow: icy white-blue
- Thunderstorm: warning red

## Requirements

- Docker and Docker Compose
- Linux host
- USB access to the ASUS Aura controller
- For some ASUS boards/controllers, OpenRGB may also need access to I2C/SMBus devices

This machine already exposes an ASUS Aura USB controller as `0b05:19af`, which is a good sign.

## Setup

1. Copy `.env.example` to `.env`.
2. Adjust `OPENRGB_DEVICE_FILTER` if you want to target a different device name.
3. Start the stack:

```bash
docker compose up --build -d
```

4. Inspect detected devices:

```bash
docker compose exec weatherled python /app/list_devices.py
```

5. Trigger an immediate update:

```bash
docker compose exec weatherled python /app/weather_led.py --once
```

## Notes

- `OPENRGB_DEVICE_FILTER=ASUS` is the default because this host exposes the motherboard as `ASUS PRIME Z590-P` through OpenRGB.
- If no device matches, the app logs all detected device names so you can tighten the filter.
- The OpenRGB container runs privileged and mounts `/dev` because hardware RGB access is not cleanly namespaced.

## Forecast API

Open-Meteo daily forecast endpoint:

`https://api.open-meteo.com/v1/forecast`
