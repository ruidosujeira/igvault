"""Central configuration for igvault - safe defaults and constants."""

from pathlib import Path
import random
import time

# Base download directory (relative to cwd)
DOWNLOAD_BASE: Path = Path("downloads")

# Default number of reels to download
DEFAULT_LIMIT: int = 10

# Humanized delay between individual reel requests (seconds)
MIN_DELAY: float = 3.0
MAX_DELAY: float = 9.5

# Cooldown between different profiles in bulk operations
BULK_COOLDOWN_MIN: float = 10.0
BULK_COOLDOWN_MAX: float = 18.0

# Minimum file size in bytes to consider a valid reel download
MIN_VALID_SIZE: int = 80_000

# Stealth headers (mobile-first + browser realistic)
def get_headers() -> dict:
    """Return realistic stealth headers for Instagram requests."""
    return {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1",
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9,pt-BR;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "X-IG-App-ID": "936619743392459",
        "X-ASBD-ID": "198387",
        "X-IG-WWW-Claim": "0",
        "Origin": "https://www.instagram.com",
        "Referer": "https://www.instagram.com/",
        "Connection": "keep-alive",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "Pragma": "no-cache",
        "Cache-Control": "no-cache",
    }


def human_delay(min_s: float | None = None, max_s: float | None = None) -> float:
    """Sleep a random human-like delay and return the duration."""
    mn = min_s or MIN_DELAY
    mx = max_s or MAX_DELAY
    delay = random.uniform(mn, mx)
    time.sleep(delay)
    return delay

