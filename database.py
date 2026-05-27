import os
import sqlite3
from contextlib import contextmanager

_DB_URL = os.environ.get("DATABASE_URL", "")
if _DB_URL.startswith("postgres://"):
    _DB_URL = "postgresql://" + _DB_URL[len("postgres://"):]
_PG = bool(_DB_URL)

if _PG:
    import psycopg2
    import psycopg2.extras


# ── Connection ──────────────────────────────────────────────────────────────────

@contextmanager
def get_db():
    if _PG:
        conn = psycopg2.connect(_DB_URL, cursor_factory=psycopg2.extras.RealDictCursor)
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    else:
        conn = sqlite3.connect("summer_stats.db")
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()


def _ex(conn, sql, params=()):
    """Execute SQL, translating ? → %s for PostgreSQL."""
    if _PG:
        cur = conn.cursor()
        cur.execute(sql.replace("?", "%s"), params)
        return cur
    return conn.execute(sql, params)


def _fetch(conn, sql, params=()):
    cur = _ex(conn, sql, params)
    return [dict(r) for r in cur.fetchall()]


# PostgreSQL lowercases unquoted column names; remap to the uppercase keys
# the rest of the code expects.
_BAT_NORM = {'h': 'H', 'hr': 'HR', 'bb': 'BB', 'hbp': 'HBP', 'ab': 'AB', 'pa': 'PA'}
_PIT_NORM = {
    'bf': 'BF', 'k': 'K', 'bb': 'BB', 'hbp': 'HBP',
    'h_allowed': 'H_allowed', 'hr_allowed': 'HR_allowed',
    'r': 'R', 'er': 'ER',
}


def _norm(rows, mapping):
    if not _PG:
        return rows
    return [{mapping.get(k, k): v for k, v in row.items()} for row in rows]


# ── Schema ──────────────────────────────────────────────────────────────────────

_SQLITE_SCHEMA = """
CREATE TABLE IF NOT EXISTS players (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    team TEXT NOT NULL,
    team_slug TEXT NOT NULL,
    league TEXT NOT NULL,
    position TEXT NOT NULL,
    throws TEXT DEFAULT 'R',
    bats TEXT DEFAULT 'R'
);
CREATE TABLE IF NOT EXISTS batting_lines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id INTEGER NOT NULL REFERENCES players(id),
    game_date TEXT NOT NULL,
    opponent TEXT DEFAULT '',
    home_away TEXT DEFAULT 'H',
    H INTEGER DEFAULT 0,
    doubles INTEGER DEFAULT 0,
    triples INTEGER DEFAULT 0,
    HR INTEGER DEFAULT 0,
    BB INTEGER DEFAULT 0,
    HBP INTEGER DEFAULT 0,
    AB INTEGER DEFAULT 0,
    PA INTEGER DEFAULT 0,
    UNIQUE(player_id, game_date, opponent)
);
CREATE TABLE IF NOT EXISTS pitching_lines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id INTEGER NOT NULL REFERENCES players(id),
    game_date TEXT NOT NULL,
    opponent TEXT DEFAULT '',
    home_away TEXT DEFAULT 'H',
    outs INTEGER DEFAULT 0,
    BF INTEGER DEFAULT 0,
    K INTEGER DEFAULT 0,
    BB INTEGER DEFAULT 0,
    HBP INTEGER DEFAULT 0,
    strikes INTEGER DEFAULT 0,
    balls INTEGER DEFAULT 0,
    total_pitches INTEGER DEFAULT 0,
    H_allowed INTEGER DEFAULT 0,
    HR_allowed INTEGER DEFAULT 0,
    doubles_allowed INTEGER DEFAULT 0,
    triples_allowed INTEGER DEFAULT 0,
    R INTEGER DEFAULT 0,
    ER INTEGER DEFAULT 0,
    UNIQUE(player_id, game_date, opponent)
);
"""

_PG_SCHEMA = [
    """CREATE TABLE IF NOT EXISTS players (
        id SERIAL PRIMARY KEY,
        name TEXT NOT NULL UNIQUE,
        team TEXT NOT NULL,
        team_slug TEXT NOT NULL,
        league TEXT NOT NULL,
        position TEXT NOT NULL,
        throws TEXT DEFAULT 'R',
        bats TEXT DEFAULT 'R'
    )""",
    """CREATE TABLE IF NOT EXISTS batting_lines (
        id SERIAL PRIMARY KEY,
        player_id INTEGER NOT NULL REFERENCES players(id),
        game_date TEXT NOT NULL,
        opponent TEXT DEFAULT '',
        home_away TEXT DEFAULT 'H',
        H INTEGER DEFAULT 0,
        doubles INTEGER DEFAULT 0,
        triples INTEGER DEFAULT 0,
        HR INTEGER DEFAULT 0,
        BB INTEGER DEFAULT 0,
        HBP INTEGER DEFAULT 0,
        AB INTEGER DEFAULT 0,
        PA INTEGER DEFAULT 0,
        UNIQUE(player_id, game_date, opponent)
    )""",
    """CREATE TABLE IF NOT EXISTS pitching_lines (
        id SERIAL PRIMARY KEY,
        player_id INTEGER NOT NULL REFERENCES players(id),
        game_date TEXT NOT NULL,
        opponent TEXT DEFAULT '',
        home_away TEXT DEFAULT 'H',
        outs INTEGER DEFAULT 0,
        BF INTEGER DEFAULT 0,
        K INTEGER DEFAULT 0,
        BB INTEGER DEFAULT 0,
        HBP INTEGER DEFAULT 0,
        strikes INTEGER DEFAULT 0,
        balls INTEGER DEFAULT 0,
        total_pitches INTEGER DEFAULT 0,
        H_allowed INTEGER DEFAULT 0,
        HR_allowed INTEGER DEFAULT 0,
        doubles_allowed INTEGER DEFAULT 0,
        triples_allowed INTEGER DEFAULT 0,
        R INTEGER DEFAULT 0,
        ER INTEGER DEFAULT 0,
        UNIQUE(player_id, game_date, opponent)
    )""",
]


def init_db():
    with get_db() as db:
        if _PG:
            for stmt in _PG_SCHEMA:
                _ex(db, stmt)
        else:
            db.executescript(_SQLITE_SCHEMA)
    seed_players()


# ── Seed ────────────────────────────────────────────────────────────────────────

def seed_players():
    players = [
        ("Nathan O'Donnell", "Kenosha Kingfish", "kenosha-kingfish",
         "Northwoods League", "two-way", "R", "R"),
        ("Ethan Felling", "St. Cloud Rox", "st-cloud-rox",
         "Northwoods League", "pitcher", "L", "L"),
        ("Jackson Akin", "St. Cloud Rox", "st-cloud-rox",
         "Northwoods League", "hitter", "R", "R"),
        ("Greyson Zach", "Willmar Stingers", "willmar-stingers",
         "Northwoods League", "pitcher", "R", "R"),
        ("Eli Kokenge", "Willmar Stingers", "willmar-stingers",
         "Northwoods League", "pitcher", "R", "R"),
    ]
    upsert = (
        "INSERT INTO players (name, team, team_slug, league, position, throws, bats) "
        "VALUES (?,?,?,?,?,?,?) ON CONFLICT (name) DO NOTHING"
        if _PG else
        "INSERT OR IGNORE INTO players "
        "(name, team, team_slug, league, position, throws, bats) VALUES (?,?,?,?,?,?,?)"
    )
    with get_db() as db:
        for p in players:
            _ex(db, upsert, p)


# ── Helpers ─────────────────────────────────────────────────────────────────────

def outs_to_ip(outs: int) -> float:
    return int(outs // 3) + (outs % 3) / 10


def batting_totals(rows):
    t = dict(H=0, doubles=0, triples=0, HR=0, BB=0, HBP=0, AB=0, PA=0, G=0)
    for r in rows:
        t['G'] += 1
        for k in ('H', 'doubles', 'triples', 'HR', 'BB', 'HBP', 'AB', 'PA'):
            t[k] += r[k]
    ab, pa = t['AB'], t['PA']
    h, bb, hbp = t['H'], t['BB'], t['HBP']
    singles = h - t['doubles'] - t['triples'] - t['HR']
    t['AVG'] = round(h / ab, 3) if ab else 0.000
    t['OBP'] = round((h + bb + hbp) / pa, 3) if pa else 0.000
    t['SLG'] = round((singles + 2*t['doubles'] + 3*t['triples'] + 4*t['HR']) / ab, 3) if ab else 0.000
    t['OPS'] = round(t['OBP'] + t['SLG'], 3)
    return t


def pitching_totals(rows):
    t = dict(outs=0, BF=0, K=0, BB=0, HBP=0,
             strikes=0, balls=0, total_pitches=0,
             H_allowed=0, HR_allowed=0, doubles_allowed=0, triples_allowed=0,
             R=0, ER=0, G=0)
    for r in rows:
        t['G'] += 1
        for k in ('outs', 'BF', 'K', 'BB', 'HBP', 'strikes', 'balls',
                  'total_pitches', 'H_allowed', 'HR_allowed',
                  'doubles_allowed', 'triples_allowed', 'R', 'ER'):
            t[k] += r[k]
    outs = t['outs']
    ip = outs / 3 if outs else 0
    bf = t['BF']
    t['IP'] = outs_to_ip(outs)
    t['K_pct'] = round(t['K'] / bf * 100, 1) if bf else 0.0
    t['BB_pct'] = round(t['BB'] / bf * 100, 1) if bf else 0.0
    t['K_per9'] = round(t['K'] / ip * 9, 2) if ip else 0.0
    t['BB_per9'] = round(t['BB'] / ip * 9, 2) if ip else 0.0
    t['H_per9'] = round(t['H_allowed'] / ip * 9, 2) if ip else 0.0
    tp = t['total_pitches']
    t['strike_pct'] = round(t['strikes'] / tp * 100, 1) if tp else 0.0
    t['ERA'] = round(t['ER'] / ip * 9, 2) if ip else 0.0
    return t


# ── Queries ─────────────────────────────────────────────────────────────────────

def get_all_players():
    with get_db() as db:
        return _fetch(db, "SELECT * FROM players ORDER BY team, name")


def get_batting_lines(player_id):
    with get_db() as db:
        rows = _fetch(db,
            "SELECT * FROM batting_lines WHERE player_id=? ORDER BY game_date",
            (player_id,))
    return _norm(rows, _BAT_NORM)


def get_pitching_lines(player_id):
    with get_db() as db:
        rows = _fetch(db,
            "SELECT * FROM pitching_lines WHERE player_id=? ORDER BY game_date",
            (player_id,))
    rows = _norm(rows, _PIT_NORM)
    for line in rows:
        line['IP'] = outs_to_ip(line['outs'])
    return rows


def add_batting_line(player_id, game_date, opponent, home_away,
                     H, doubles, triples, HR, BB, HBP, AB, PA):
    params = (player_id, game_date, opponent, home_away,
              H, doubles, triples, HR, BB, HBP, AB, PA)
    if _PG:
        sql = """
            INSERT INTO batting_lines
                (player_id, game_date, opponent, home_away,
                 H, doubles, triples, HR, BB, HBP, AB, PA)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT (player_id, game_date, opponent) DO UPDATE SET
                home_away=EXCLUDED.home_away, H=EXCLUDED.H,
                doubles=EXCLUDED.doubles, triples=EXCLUDED.triples,
                HR=EXCLUDED.HR, BB=EXCLUDED.BB, HBP=EXCLUDED.HBP,
                AB=EXCLUDED.AB, PA=EXCLUDED.PA
        """
    else:
        sql = """
            INSERT OR REPLACE INTO batting_lines
                (player_id, game_date, opponent, home_away,
                 H, doubles, triples, HR, BB, HBP, AB, PA)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
        """
    with get_db() as db:
        _ex(db, sql, params)


def add_pitching_line(player_id, game_date, opponent, home_away,
                      outs, BF, K, BB, HBP, strikes, balls, total_pitches,
                      H_allowed, HR_allowed, doubles_allowed, triples_allowed,
                      R=0, ER=0):
    params = (player_id, game_date, opponent, home_away,
              outs, BF, K, BB, HBP, strikes, balls, total_pitches,
              H_allowed, HR_allowed, doubles_allowed, triples_allowed, R, ER)
    if _PG:
        sql = """
            INSERT INTO pitching_lines
                (player_id, game_date, opponent, home_away,
                 outs, BF, K, BB, HBP, strikes, balls, total_pitches,
                 H_allowed, HR_allowed, doubles_allowed, triples_allowed, R, ER)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT (player_id, game_date, opponent) DO UPDATE SET
                home_away=EXCLUDED.home_away, outs=EXCLUDED.outs,
                BF=EXCLUDED.BF, K=EXCLUDED.K, BB=EXCLUDED.BB,
                HBP=EXCLUDED.HBP, strikes=EXCLUDED.strikes,
                balls=EXCLUDED.balls, total_pitches=EXCLUDED.total_pitches,
                H_allowed=EXCLUDED.H_allowed, HR_allowed=EXCLUDED.HR_allowed,
                doubles_allowed=EXCLUDED.doubles_allowed,
                triples_allowed=EXCLUDED.triples_allowed,
                R=EXCLUDED.R, ER=EXCLUDED.ER
        """
    else:
        sql = """
            INSERT OR REPLACE INTO pitching_lines
                (player_id, game_date, opponent, home_away,
                 outs, BF, K, BB, HBP, strikes, balls, total_pitches,
                 H_allowed, HR_allowed, doubles_allowed, triples_allowed, R, ER)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """
    with get_db() as db:
        _ex(db, sql, params)


def delete_batting_line(line_id):
    with get_db() as db:
        _ex(db, "DELETE FROM batting_lines WHERE id=?", (line_id,))


def delete_pitching_line(line_id):
    with get_db() as db:
        _ex(db, "DELETE FROM pitching_lines WHERE id=?", (line_id,))


def get_full_dashboard_data():
    players = get_all_players()
    result = []
    for p in players:
        pid = p['id']
        pos = p['position']
        entry = dict(p)
        entry['batting'] = []
        entry['batting_totals'] = {}
        entry['pitching'] = []
        entry['pitching_totals'] = {}

        if pos in ('hitter', 'two-way'):
            lines = get_batting_lines(pid)
            entry['batting'] = lines
            entry['batting_totals'] = batting_totals(lines)

        if pos in ('pitcher', 'two-way'):
            lines = get_pitching_lines(pid)
            entry['pitching'] = lines
            entry['pitching_totals'] = pitching_totals(lines)

        result.append(entry)
    return result
