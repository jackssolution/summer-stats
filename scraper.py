"""
NWL stats scraper.

Strategy:
  1. Navigate the NWL scoreboard/scores pages with Selenium (JavaScript-rendered)
  2. Find completed game box scores for tracked teams
  3. Extract player-level batting/pitching lines
  4. Insert into the database

The NWL scorebook (scorebook.northwoodsleague.com) requires credentials.
Set NWL_EMAIL and NWL_PASSWORD environment variables to enable authenticated scraping.
Without them only public box-score pages are attempted.
"""

import os
import time
import re
import logging
from datetime import datetime, date

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

import database as db

log = logging.getLogger(__name__)

NWL_BASE = "https://northwoodsleague.com"
SCOREBOOK_BASE = "https://scorebook.northwoodsleague.com"

# Team slug → scorebook team ID
TEAM_IDS = {
    "kenosha-kingfish": 63,
    "st-cloud-rox": 56,
    "willmar-stingers": 59,
}
LEAGUE_ID = 13  # Northwoods League


def _build_driver(headless=True):
    opts = Options()
    if headless:
        opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--window-size=1280,900")
    return webdriver.Chrome(options=opts)


def _wait_text(driver, css, timeout=10):
    try:
        el = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, css))
        )
        return el.text.strip()
    except TimeoutException:
        return ""


def _ip_to_outs(ip_str: str) -> int:
    """Convert '2.1' IP string to raw out count (7 outs)."""
    try:
        parts = str(ip_str).split(".")
        full = int(parts[0]) * 3
        extra = int(parts[1]) if len(parts) > 1 else 0
        return full + extra
    except Exception:
        return 0


# ── Scorebook login ──────────────────────────────────────────────────────────

def _login_scorebook(driver):
    email = os.environ.get("NWL_EMAIL", "")
    password = os.environ.get("NWL_PASSWORD", "")
    if not email or not password:
        return False

    driver.get(f"{SCOREBOOK_BASE}/login")
    time.sleep(2)
    try:
        driver.find_element(By.CSS_SELECTOR, "input[type='email']").send_keys(email)
        driver.find_element(By.CSS_SELECTOR, "input[type='password']").send_keys(password)
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(3)
        return SCOREBOOK_BASE in driver.current_url or "login" not in driver.current_url
    except Exception as e:
        log.warning("Scorebook login failed: %s", e)
        return False


# ── Public NWL box scores ────────────────────────────────────────────────────

def _get_recent_game_links(driver, team_slug):
    """Return list of (game_date, opponent, home_away, box_score_url) for completed games."""
    driver.get(f"{NWL_BASE}/{team_slug}/schedule/")
    time.sleep(4)
    links = []
    try:
        anchors = driver.find_elements(By.CSS_SELECTOR, "a[href*='box-score'], a[href*='game-recap']")
        for a in anchors:
            href = a.get_attribute("href") or ""
            if href:
                links.append(href)
    except Exception as e:
        log.warning("Could not find game links for %s: %s", team_slug, e)
    return links


def _parse_public_box_score(driver, url):
    """
    Attempt to parse a public NWL game recap/box-score page.
    Returns dict with keys 'batting' and 'pitching', each a list of stat dicts.
    """
    driver.get(url)
    time.sleep(3)
    result = {"batting": [], "pitching": [], "game_date": "", "opponent": "", "home_away": "H"}

    try:
        date_el = driver.find_element(By.CSS_SELECTOR, ".game-date, time, .date")
        result["game_date"] = date_el.text.strip()
    except Exception:
        pass

    # Try to find box score tables
    tables = driver.find_elements(By.CSS_SELECTOR, "table")
    for table in tables:
        headers = [th.text.strip().upper() for th in table.find_elements(By.TAG_NAME, "th")]
        rows = table.find_elements(By.TAG_NAME, "tr")[1:]

        if "AB" in headers and "H" in headers:
            # batting table
            for row in rows:
                cells = [td.text.strip() for td in row.find_elements(By.TAG_NAME, "td")]
                if len(cells) >= len(headers):
                    d = dict(zip(headers, cells))
                    result["batting"].append(d)

        elif "IP" in headers and "K" in headers:
            # pitching table
            for row in rows:
                cells = [td.text.strip() for td in row.find_elements(By.TAG_NAME, "td")]
                if len(cells) >= len(headers):
                    d = dict(zip(headers, cells))
                    result["pitching"].append(d)

    return result


# ── Scorebook authenticated scraping ────────────────────────────────────────

def _scrape_scorebook_batting(driver, team_id):
    """Scrape the scorebook batting stats page for a team. Returns list of player dicts."""
    url = f"{SCOREBOOK_BASE}/statistics/batting/{LEAGUE_ID}/team/{team_id}"
    driver.get(url)
    time.sleep(4)
    players = []
    try:
        rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
        for row in rows:
            cols = row.find_elements(By.TAG_NAME, "td")
            if len(cols) < 8:
                continue
            name_el = cols[0].find_elements(By.TAG_NAME, "a")
            name = name_el[0].text.strip() if name_el else cols[0].text.strip()
            if not name:
                continue
            profile_url = name_el[0].get_attribute("href") if name_el else ""
            players.append({"name": name, "profile_url": profile_url})
    except Exception as e:
        log.warning("Scorebook batting parse error: %s", e)
    return players


def _scrape_scorebook_game_log(driver, profile_url):
    """Scrape a player's game-by-game log from scorebook. Returns list of game lines."""
    if not profile_url:
        return []
    log_url = profile_url.rstrip("/") + "/game-log"
    driver.get(log_url)
    time.sleep(3)
    lines = []
    try:
        rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
        for row in rows:
            cols = [td.text.strip() for td in row.find_elements(By.TAG_NAME, "td")]
            if cols:
                lines.append(cols)
    except Exception as e:
        log.warning("Game log parse error for %s: %s", log_url, e)
    return lines


# ── Main entry point ─────────────────────────────────────────────────────────

def scrape_all(headless=True):
    """
    Run the full scrape cycle. Returns a summary dict.
    """
    summary = {"scraped": 0, "errors": [], "players_updated": []}
    players = db.get_all_players()
    if not players:
        summary["errors"].append("No players in database")
        return summary

    driver = None
    try:
        driver = _build_driver(headless=headless)
        logged_in = _login_scorebook(driver)

        # Group players by team
        teams = {}
        for p in players:
            slug = p["team_slug"]
            teams.setdefault(slug, []).append(p)

        for team_slug, team_players in teams.items():
            team_id = TEAM_IDS.get(team_slug)
            if not team_id:
                summary["errors"].append(f"Unknown team slug: {team_slug}")
                continue

            if logged_in:
                # Use authenticated scorebook
                _scrape_authenticated(driver, team_players, team_id, summary)
            else:
                # Try public box score pages
                game_links = _get_recent_game_links(driver, team_slug)
                for url in game_links:
                    box = _parse_public_box_score(driver, url)
                    _store_box_score(box, team_players, summary)

    except Exception as e:
        summary["errors"].append(f"Fatal scraper error: {e}")
        log.exception("Scraper failed")
    finally:
        if driver:
            driver.quit()

    return summary


def _scrape_authenticated(driver, team_players, team_id, summary):
    scorebook_players = _scrape_scorebook_batting(driver, team_id)
    for sp in scorebook_players:
        matched = _match_player(sp["name"], team_players)
        if not matched:
            continue
        lines = _scrape_scorebook_game_log(driver, sp.get("profile_url", ""))
        for line in lines:
            try:
                _store_batting_line_from_scorebook(matched["id"], line)
                summary["scraped"] += 1
                if matched["name"] not in summary["players_updated"]:
                    summary["players_updated"].append(matched["name"])
            except Exception as e:
                summary["errors"].append(f"{matched['name']}: {e}")


def _match_player(scraped_name: str, db_players: list) -> dict | None:
    scraped_lower = scraped_name.lower().replace(",", "").replace(".", "").strip()
    for p in db_players:
        db_name = p["name"].lower().replace(",", "").replace(".", "").strip()
        last = db_name.split()[-1] if db_name.split() else ""
        if scraped_lower == db_name or last in scraped_lower:
            return p
    return None


def _store_batting_line_from_scorebook(player_id, cols):
    """Store a batting line parsed from scorebook game log."""
    if len(cols) < 8:
        return
    # Expected order: Date, Opponent, AB, R, H, 2B, 3B, HR, RBI, BB, HBP, SO, PA
    def safe_int(v):
        try:
            return int(v)
        except Exception:
            return 0
    game_date = cols[0] if cols[0] else date.today().isoformat()
    opponent = cols[1] if len(cols) > 1 else ""
    ab = safe_int(cols[2]) if len(cols) > 2 else 0
    h = safe_int(cols[4]) if len(cols) > 4 else 0
    doubles = safe_int(cols[5]) if len(cols) > 5 else 0
    triples = safe_int(cols[6]) if len(cols) > 6 else 0
    hr = safe_int(cols[7]) if len(cols) > 7 else 0
    bb = safe_int(cols[9]) if len(cols) > 9 else 0
    hbp = safe_int(cols[10]) if len(cols) > 10 else 0
    pa = safe_int(cols[12]) if len(cols) > 12 else ab + bb + hbp
    db.add_batting_line(player_id, game_date, opponent, "?",
                        h, doubles, triples, hr, bb, hbp, ab, pa)


def _store_box_score(box, team_players, summary):
    """Attempt to match box score batting/pitching rows to tracked players."""
    game_date = box.get("game_date", date.today().isoformat())
    opponent = box.get("opponent", "")
    home_away = box.get("home_away", "H")

    for row in box.get("batting", []):
        player_name = row.get("PLAYER", row.get("NAME", ""))
        matched = _match_player(player_name, team_players)
        if not matched:
            continue
        def si(k, default=0):
            try:
                return int(row.get(k, default))
            except Exception:
                return default
        db.add_batting_line(
            matched["id"], game_date, opponent, home_away,
            si("H"), si("2B"), si("3B"), si("HR"), si("BB"), si("HBP"),
            si("AB"), si("PA")
        )
        summary["scraped"] += 1
        if matched["name"] not in summary["players_updated"]:
            summary["players_updated"].append(matched["name"])
