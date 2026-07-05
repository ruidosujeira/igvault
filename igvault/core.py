"""Core engine for igvault: profile discovery, reel URL extraction and download."""

import httpx
import json
import re
import time
import random
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from urllib.parse import quote

from .config import (
    DOWNLOAD_BASE,
    get_headers,
    MIN_DELAY,
    MAX_DELAY,
    MIN_VALID_SIZE,
    BULK_COOLDOWN_MIN,
    BULK_COOLDOWN_MAX,
)


def _clean_username(username: str) -> str:
    """Remove @ and whitespace."""
    return username.strip().lstrip("@").strip()


def fetch_profile_reels(username: str, limit: int = 20) -> List[str]:
    """
    Fetch public reel shortcodes from a profile using Instagram's web_profile_info endpoint.
    Returns list of shortcodes (most recent first).
    """
    clean = _clean_username(username)
    if not clean:
        return []

    url = f"https://i.instagram.com/api/v1/users/web_profile_info/?username={clean}"
    headers = get_headers()

    try:
        with httpx.Client(timeout=25.0, follow_redirects=True) as client:
            resp = client.get(url, headers=headers)
            if resp.status_code != 200:
                return []

            data = resp.json()
            user = data.get("data", {}).get("user") or {}
            timeline = user.get("edge_owner_to_timeline_media", {}) or {}
            edges = timeline.get("edges", []) or []

            shortcodes: List[str] = []
            for edge in edges:
                node = edge.get("node", {}) or {}
                # Reels are videos. Many have product_type == "clips"
                is_video = node.get("is_video") is True
                product = node.get("product_type", "")
                is_reel_like = product in ("clips", "reel", "clips") or is_video

                if is_video or is_reel_like:
                    shortcode = node.get("shortcode") or node.get("code")
                    if shortcode and shortcode not in shortcodes:
                        shortcodes.append(shortcode)
                        if len(shortcodes) >= limit:
                            break
            return shortcodes
    except Exception:
        return []


def get_reel_video_url(shortcode: str) -> Optional[str]:
    """
    Get direct MP4 video URL for a reel shortcode.
    Uses session (visit page first to acquire cookies) + GraphQL for reliability.
    Falls back to limited HTML parsing.
    """
    headers = get_headers()
    shortcode = shortcode.strip()
    reel_page = f"https://www.instagram.com/reel/{shortcode}/"

    try:
        with httpx.Client(timeout=25.0, follow_redirects=True) as client:
            # Warm up: visit reel page to get cookies / csrftoken (critical for graphql)
            page_resp = client.get(reel_page, headers=headers)
            if page_resp.status_code == 200:
                # Merge any cookies automatically handled by client
                csrf = page_resp.cookies.get("csrftoken")
                if csrf:
                    headers["X-CSRFToken"] = csrf

            # GraphQL with session cookies
            variables = json.dumps({"shortcode": shortcode})
            payload = f"variables={quote(variables)}&doc_id=24368985919464652"

            g_headers = {
                **headers,
                "Content-Type": "application/x-www-form-urlencoded",
                "Referer": reel_page,
            }
            g_resp = client.post(
                "https://www.instagram.com/graphql/query",
                headers=g_headers,
                data=payload,
            )

            if g_resp.status_code == 200:
                try:
                    j = g_resp.json()
                    items = (
                        j.get("data", {})
                        .get("xdt_api__v1__media__shortcode__web_info", {})
                        .get("items", [])
                    )
                    if items:
                        item = items[0]
                        versions = item.get("video_versions", []) or []
                        if versions:
                            # Highest quality first
                            best = max(
                                versions,
                                key=lambda v: (v.get("width") or 0, v.get("height") or 0),
                            )
                            url = best.get("url")
                            if url and ".mp4" in url:
                                return url
                        direct = item.get("video_url")
                        if direct and ".mp4" in direct:
                            return direct
                except (KeyError, IndexError, TypeError, json.JSONDecodeError):
                    pass

            # Fallback: try to parse any video url that appeared after page load (rare)
            html = page_resp.text
            patterns = [
                r'"video_url":"(https?://[^"]+?\.mp4[^"]*)"',
                r'"url":"(https://[^"]+?\.mp4[^"]*)"',
                r'video_versions":\s*\[\s*\{[^}]*"url":"(https[^"]+)"',
            ]
            for pat in patterns:
                m = re.search(pat, html)
                if m:
                    url = m.group(1).replace("\\/", "/").replace("\\u0026", "&")
                    if ".mp4" in url and url.startswith(("http://", "https://")):
                        return url
    except Exception:
        pass

    return None


def download_reel(video_url: str, dest: Path, referer: str | None = None) -> Tuple[bool, Optional[str]]:
    """
    Download a reel MP4 to dest path.
    Returns (success, error_message_or_None).
    """
    headers = get_headers()
    if referer:
        headers["Referer"] = referer
    else:
        headers["Referer"] = "https://www.instagram.com/"
    tmp = dest.with_suffix(".mp4.tmp")

    try:
        with httpx.stream(
            "GET",
            video_url,
            headers=headers,
            follow_redirects=True,
            timeout=90.0,
        ) as resp:
            resp.raise_for_status()

            dest.parent.mkdir(parents=True, exist_ok=True)

            with open(tmp, "wb") as f:
                for chunk in resp.iter_bytes(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

        # Atomic move
        if tmp.exists():
            tmp.replace(dest)

        # Validate
        if not dest.exists():
            return False, "file not created"
        size = dest.stat().st_size
        if size < MIN_VALID_SIZE:
            dest.unlink(missing_ok=True)
            return False, f"file too small ({size} bytes)"

        # Very basic MP4 magic check (ftyp box)
        try:
            with open(dest, "rb") as f:
                header = f.read(12)
            if b"ftyp" not in header and not header.startswith(b"\x00\x00\x00"):
                # Still allow it - some CDNs vary, but size passed
                pass
        except Exception:
            pass

        return True, None

    except httpx.HTTPStatusError as e:
        if tmp.exists():
            tmp.unlink(missing_ok=True)
        return False, f"http error {e.response.status_code}"
    except Exception as e:
        if tmp.exists():
            tmp.unlink(missing_ok=True)
        return False, str(e)


def human_sleep(min_s: float = MIN_DELAY, max_s: float = MAX_DELAY) -> float:
    """Sleep random human delay. Returns actual seconds slept."""
    delay = random.uniform(min_s, max_s)
    time.sleep(delay)
    return delay


def bulk_cooldown() -> float:
    """Longer pause between different usernames."""
    delay = random.uniform(BULK_COOLDOWN_MIN, BULK_COOLDOWN_MAX)
    time.sleep(delay)
    return delay


def download_reels(
    username: str,
    limit: int = 10,
    dry_run: bool = False,
    base_dir: Optional[Path] = None,
) -> Dict:
    """
    Main high-level function.
    Returns summary dict with keys: username, shortcodes_found, attempted, downloaded, skipped, errors, files
    """
    clean = _clean_username(username)
    base = base_dir or DOWNLOAD_BASE
    target_dir = base / f"@{clean}" / "reels"

    result = {
        "username": clean,
        "target_dir": str(target_dir),
        "shortcodes_found": [],
        "attempted": 0,
        "downloaded": 0,
        "skipped": 0,
        "errors": 0,
        "files": [],
        "dry_run": dry_run,
    }

    shortcodes = fetch_profile_reels(clean, limit=limit + 5)[:limit]
    result["shortcodes_found"] = shortcodes

    if not shortcodes:
        return result

    for idx, sc in enumerate(shortcodes):
        result["attempted"] += 1

        # Delay between reels (except first)
        if idx > 0:
            human_sleep()

        video_url = get_reel_video_url(sc)
        if not video_url:
            result["errors"] += 1
            continue

        filename = f"{sc}.mp4"
        dest = target_dir / filename

        if dest.exists() and not dry_run:
            result["skipped"] += 1
            result["files"].append(str(dest))
            continue

        if dry_run:
            result["downloaded"] += 1  # pretend
            result["files"].append(str(dest))
            continue

        success, err = download_reel(video_url, dest, referer="https://www.instagram.com/")
        if success:
            result["downloaded"] += 1
            result["files"].append(str(dest))
        else:
            result["errors"] += 1

    return result
