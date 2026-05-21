import asyncio
import logging
import os
import re
import sys
import time
import json
from typing import Optional
from pathlib import Path

import aiohttp
import winrt.windows.media.control as wmc

CONFIG_FILE = Path(__file__).parent / "config.json"
MAX_STATUS_LEN = 128
DEFAULT_TIME_OFFSET = 2.0
MAX_NONE_COUNT = 5
MAX_RETRY_ATTEMPTS = 3
RETRY_DELAY = 2.0

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
    stream=sys.stdout
)
log = logging.getLogger("ym-discord")

lyrics_cache: dict[str, dict] = {}

def load_config() -> dict:
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {}

def save_config(config: dict):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    except:
        pass

def get_token() -> str:
    config = load_config()
    token = os.getenv("DISCORD_TOKEN") or config.get("discord_token") or ""
    if not token:
        log.error("Токен не найден! Укажите его в config.json или переменной окружения DISCORD_TOKEN")
        sys.exit(1)
    return token

async def get_smtc_state() -> Optional[dict]:
    try:
        manager = await wmc.GlobalSystemMediaTransportControlsSessionManager.request_async()
        ym_session = None
        for session in manager.get_sessions():
            app_id = (session.source_app_user_model_id or "").lower()
            if "yandex" in app_id or "music.yandex" in app_id:
                ym_session = session
                break
        if ym_session is None:
            return None
        info = await ym_session.try_get_media_properties_async()
        timeline = ym_session.get_timeline_properties()
        status = int(ym_session.get_playback_info().playback_status)
        playing = status == 4
        title = info.title or ""
        if not title:
            return None
        return {
            "artist": info.artist or "",
            "title": title,
            "position": timeline.position.total_seconds(),
            "playing": playing,
        }
    except Exception as e:
        log.warning(f"SMTC: {e}")
        return None

def parse_lrc(synced: str) -> list[tuple[float, str]]:
    lines = []
    for line in synced.splitlines():
        m = re.match(r'\[(\d+):(\d+\.\d+)\]\s*(.*)', line)
        if not m:
            continue
        t = int(m.group(1)) * 60 + float(m.group(2))
        text = m.group(3).strip()
        if text:
            lines.append((t, text))
    return lines

async def search_lrclib(session: aiohttp.ClientSession, q: str) -> list[tuple[float, str]]:
    try:
        async with session.get(
            "https://lrclib.net/api/search",
            params={"q": q},
            timeout=aiohttp.ClientTimeout(total=10)
        ) as r:
            if r.status != 200:
                return []
            results = await r.json()
        for item in results:
            synced = item.get("syncedLyrics", "")
            if synced:
                lines = parse_lrc(synced)
                if lines:
                    return lines
    except Exception as e:
        log.warning(f"lrclib '{q}': {e}")
    return []

async def get_lyrics(http_session: aiohttp.ClientSession, artist: str, title: str) -> list[tuple[float, str]]:
    cache_key = f"{artist}|{title}"
    cached = lyrics_cache.get(cache_key)
    if cached:
        if cached.get("expires", 0) > time.time():
            return cached["lines"]
    log.info(f"Ищу текст: {artist} — {title}")
    queries = [
        f"{artist} {title}",
        title,
        f"{artist.split(',')[0].strip()} {title}",
    ]
    lines = []
    for q in queries:
        lines = await search_lrclib(http_session, q)
        if lines:
            log.info(f"lrclib: {len(lines)} строк")
            break
    if not lines:
        log.warning("Текст не найден")
    lyrics_cache[cache_key] = {"lines": lines, "expires": time.time() + 3600}
    return lines

class DiscordClient:
    API = "https://discord.com/api/v9"

    def __init__(self, token: str):
        self.headers = {"Authorization": token, "Content-Type": "application/json"}
        self._status_text = ""
        self._last_request = 0
        self._request_count = 0

    async def _rate_limit(self):
        now = time.time()
        if now - self._last_request < 1:
            self._request_count += 1
            if self._request_count > 5:
                await asyncio.sleep(2)
                self._request_count = 0
        else:
            self._request_count = 0
        self._last_request = time.time()

    async def set_status(self, text: str, retry: int = 0):
        if text == self._status_text:
            return
        self._status_text = text
        await self._rate_limit()
        try:
            async with aiohttp.ClientSession() as session:
                payload = {"custom_status": {"text": text, "emoji_name": "🎵"} if text else None}
                async with session.patch(f"{self.API}/users/@me/settings", json=payload, headers=self.headers) as r:
                    if r.status == 200:
                        log.info(f"Статус → {text!r}")
                    elif r.status == 401:
                        log.error("Неверный токен! Проверьте config.json")
                    elif r.status == 429 and retry < MAX_RETRY_ATTEMPTS:
                        reset = int(r.headers.get("Retry-After", RETRY_DELAY))
                        await asyncio.sleep(reset)
                        await self.set_status(text, retry + 1)
                    else:
                        log.warning(f"Discord {r.status}")
        except Exception as e:
            if retry < MAX_RETRY_ATTEMPTS:
                await asyncio.sleep(RETRY_DELAY * (retry + 1))
                await self.set_status(text, retry + 1)
            else:
                log.warning(f"Discord: {e}")

    async def clear_status(self):
        await self.set_status("")

def get_current_line(lines: list[tuple[float, str]], position: float) -> str:
    if not lines:
        return ""
    current = lines[0][1]
    for t, text in lines:
        if position >= t:
            current = text
        else:
            break
    return current

async def main():
    token = get_token()
    config = load_config()
    time_offset = config.get("time_offset", DEFAULT_TIME_OFFSET)
    
    dc = DiscordClient(token)
    current_key: Optional[str] = None
    lines: list[tuple[float, str]] = []
    none_count = 0
    paused_count = 0
    prev_position = -999.0
    base_position = 0.0
    base_time = 0.0

    log.info("Запуск — жду музыку...")
    
    async with aiohttp.ClientSession() as http_session:
        while True:
            try:
                state = await get_smtc_state()

                if state is None:
                    none_count += 1
                    if none_count >= MAX_NONE_COUNT and current_key is not None:
                        log.info("Плеер закрыт — очищаю статус")
                        current_key = None
                        lines = []
                        none_count = 0
                        paused_count = 0
                        prev_position = -999.0
                        await dc.clear_status()
                    if lines and current_key is not None:
                        elapsed = time.monotonic() - base_time
                        cur_pos = base_position + elapsed + time_offset
                        line = get_current_line(lines, cur_pos)
                        if len(line) > MAX_STATUS_LEN:
                            line = line[:MAX_STATUS_LEN - 1] + "…"
                        await dc.set_status(f"🎵 {line}")
                else:
                    none_count = 0
                    artist = state["artist"]
                    title = state["title"]
                    position = state["position"]
                    playing = state["playing"]
                    key = f"{artist}|{title}"

                    if key != current_key:
                        log.info(f"Новый трек: {artist} — {title}")
                        current_key = key
                        paused_count = 0
                        prev_position = -999.0
                        base_position = position
                        base_time = time.monotonic()
                        lines = await get_lyrics(http_session, artist, title)

                    if abs(position - prev_position) > 0.3:
                        base_position = position
                        base_time = time.monotonic()
                    prev_position = position

                    if not playing:
                        if current_key is not None:
                            log.info("Пауза — очищаю статус")
                            current_key = None
                            lines = []
                            prev_position = -999.0
                            await dc.clear_status()
                    else:
                        elapsed = time.monotonic() - base_time
                        cur_pos = base_position + elapsed + time_offset
                        if lines:
                            line = get_current_line(lines, cur_pos)
                            if len(line) > MAX_STATUS_LEN:
                                line = line[:MAX_STATUS_LEN - 1] + "…"
                            await dc.set_status(f"🎵 {line}")
                        else:
                            await dc.set_status(f"🎵 {artist} — {title}")
            except KeyboardInterrupt:
                break
            except Exception as e:
                log.error(f"Ошибка в цикле: {e}")
            await asyncio.sleep(2)
    
    log.info("Остановлено.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log.info("Остановлено.")