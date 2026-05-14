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

- Clear: `RGB(253, 184, 19)` warm sun yellow
- Partly cloudy: `RGB(111, 177, 255)` soft sky blue
- Cloudy or fog: `RGB(154, 165, 177)` cool gray
- Rain or drizzle: `RGB(46, 134, 222)` rain blue
- Snow: `RGB(190, 233, 255)` icy white-blue
- Thunderstorm: `RGB(255, 94, 91)` warning red
- Unknown: `RGB(255, 255, 255)` white

## Requirements

- Docker and Docker Compose
- Linux host
- USB access to the ASUS Aura controller
- For some ASUS boards/controllers, OpenRGB may also need access to I2C/SMBus devices

This machine already exposes an ASUS Aura USB controller as `0b05:19af`, which is a good sign.

## Setup

1. Copy `.env.example` to `.env`.
2. Adjust `OPENRGB_DEVICE_FILTER` if you want to target a different device name or comma-separated list of device names.
3. If your tower LEDs are connected to an ASUS addressable header, set `AURA_ADDRESSABLE_1_LEDS` or `AURA_ADDRESSABLE_2_LEDS` to the actual LED count on that header.
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

6. If the tower strip stays on rainbow, probe the ASUS addressable headers:

```bash
docker compose exec weatherled python /app/probe_headers.py
```

Watch for which `Aura Addressable` header responds, then set `AURA_ADDRESSABLE_1_LEDS` or `AURA_ADDRESSABLE_2_LEDS` in `.env` to the closest LED count that worked.

## Addressing the LEDs

There are two separate things to configure:

1. Which OpenRGB device to target.

Use `OPENRGB_DEVICE_FILTER` in `.env`.

Examples:

```env
OPENRGB_DEVICE_FILTER=ASUS
OPENRGB_DEVICE_FILTER=NZXT
OPENRGB_DEVICE_FILTER=ASUS,NZXT
```

On this host, the motherboard appears in OpenRGB as `ASUS PRIME Z590-P`.

2. Which ASUS addressable header the strip is connected to.

OpenRGB exposes two motherboard ARGB headers:

- `Aura Addressable 1`
- `Aura Addressable 2`

The app can only control a header after it knows how many LEDs are attached to it.

Configure that in `.env`:

```env
AURA_ADDRESSABLE_1_LEDS=0
AURA_ADDRESSABLE_2_LEDS=120
```

`0` means "do not use this header". A positive number means "resize this header to this LED count before writing color".

Current working local setup:

```env
OPENRGB_DEVICE_FILTER=ASUS
AURA_ADDRESSABLE_1_LEDS=0
AURA_ADDRESSABLE_2_LEDS=120
```

That means the strip is currently being addressed as:

- OpenRGB device: `ASUS PRIME Z590-P`
- Header: `Aura Addressable 2`
- LED count: `120`

## Notes

- `OPENRGB_DEVICE_FILTER=ASUS,NZXT` is the default so the stack will try both the motherboard controller and the separate NZXT controller on this host.
- If your strip/fans are on `Aura Addressable 1` or `Aura Addressable 2`, OpenRGB needs the LED count before it can override rainbow on that header.
- If no device matches, the app logs all detected device names so you can tighten the filter.
- The OpenRGB container runs privileged and mounts `/dev` because hardware RGB access is not cleanly namespaced.

## Forecast API

Open-Meteo daily forecast endpoint:

`https://api.open-meteo.com/v1/forecast`
