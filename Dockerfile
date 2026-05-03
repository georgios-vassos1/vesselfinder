FROM python:3.12-slim-bookworm

ENV TZ=Europe/Madrid \
    PYTHONUNBUFFERED=1 \
    DISPLAY=:99

# System deps: chromium + Xvfb (virtual display for non-headless Playwright)
RUN apt-get update && apt-get install -y --no-install-recommends \
        chromium \
        xvfb \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir uv

WORKDIR /app
RUN mkdir -p /app/data

COPY pyproject.toml README.md License.txt ./
COPY vessel_tracker ./vessel_tracker/

RUN uv pip install --system .

# Start Xvfb then run the scraper loop via the installed console script
CMD ["sh", "-c", "Xvfb :99 -screen 0 1280x720x24 -nolisten tcp & sleep 1 && vessel-tracker"]
