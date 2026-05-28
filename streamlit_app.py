import os
import streamlit as st
import pandas as pd
from datetime import date

# Inject DATABASE_URL from Streamlit Cloud secrets before database module loads
try:
    if "DATABASE_URL" in st.secrets:
        os.environ.setdefault("DATABASE_URL", st.secrets["DATABASE_URL"])
except Exception:
    pass

import database as db
db.init_db()

st.set_page_config(
    page_title="Summer Ball Tracker 2026",
    layout="wide",
    page_icon="⚾",
)

st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background-color: #0d1117; color: #e6edf3; }
[data-testid="stHeader"] { background-color: #161b22; }
[data-testid="stSidebar"] { background-color: #161b22; }
[data-testid="stMainBlockContainer"] { padding-top: 1.5rem; }
[data-testid="stMetricLabel"] { font-size: 0.7rem; color: #8b949e; text-transform: uppercase; }
[data-testid="stMetricValue"] { font-size: 1.1rem; color: #e6edf3; }
[data-testid="stVerticalBlockBorderWrapper"] {
    background-color: #161b22;
    border: 1px solid #30363d !important;
    border-radius: 8px;
}
[data-testid="stButton"] > button {
    background: #21262d;
    border: 1px solid #30363d;
    color: #e6edf3;
    border-radius: 6px;
}
[data-testid="stButton"] > button:hover { background: #30363d; border-color: #8b949e; }
div[role="radiogroup"] { gap: 0.4rem; }
div[role="radiogroup"] label { color: #e6edf3 !important; }
div[role="radiogroup"] label p { color: #e6edf3 !important; }
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
/* input / widget labels */
[data-testid="stWidgetLabel"] p { color: #e6edf3 !important; }
[data-testid="stWidgetLabel"] { color: #e6edf3 !important; }
label { color: #e6edf3 !important; }
/* expander label */
[data-testid="stExpander"] summary p { color: #e6edf3 !important; }
</style>
""", unsafe_allow_html=True)


# ── Header ─────────────────────────────────────────────────────────────────────

hcol1, hcol2 = st.columns([5, 1])
with hcol1:
    st.markdown("## ⚾ Summer Ball Tracker 2026")
    st.caption("Northwoods League · Cape Cod Baseball League · NECBL · 2026 Season")
with hcol2:
    if st.button("↻ Refresh Stats", use_container_width=True):
        try:
            import scraper, threading
            threading.Thread(target=lambda: scraper.scrape_all(headless=True), daemon=True).start()
            st.toast("Scrape started", icon="↻")
        except Exception as e:
            st.toast(f"Scrape error: {e}", icon="⚠️")

# ── Filters ────────────────────────────────────────────────────────────────────

fc1, fc2 = st.columns([4, 2])
with fc1:
    team_filter = st.radio(
        "Team",
        ["All Players", "Kenosha Kingfish", "St. Cloud Rox", "Willmar Stingers",
         "Falmouth Commodores", "Bourne Braves", "Upper Valley Nighthawks"],
        horizontal=True, label_visibility="collapsed", key="team_filter",
    )
with fc2:
    pos_filter = st.radio(
        "Position", ["All Positions", "Pitchers", "Hitters"],
        horizontal=True, label_visibility="collapsed", key="pos_filter",
    )

st.divider()

# ── Data ───────────────────────────────────────────────────────────────────────

data = db.get_full_dashboard_data()

# ── Column definitions ─────────────────────────────────────────────────────────

PITCH_COLS   = ['game_date','opponent','home_away','IP','BF','K','BB','HBP',
                'R','ER','H_allowed','doubles_allowed','triples_allowed','HR_allowed',
                'strikes','balls','total_pitches']
PITCH_RENAME = {'game_date':'DATE','opponent':'OPP','home_away':'H/A',
                'H_allowed':'H','doubles_allowed':'2B','triples_allowed':'3B',
                'HR_allowed':'HR','strikes':'STR','balls':'BALL','total_pitches':'PIT'}
BAT_COLS     = ['game_date','opponent','home_away','AB','H','doubles','triples','HR','BB','HBP','PA','R','RBI','SB']
BAT_RENAME   = {'game_date':'DATE','opponent':'OPP','home_away':'H/A','doubles':'2B','triples':'3B'}


# ── Helpers ────────────────────────────────────────────────────────────────────

def _i(prefix, key):
    return int(st.session_state.get(f"{prefix}_{key}") or 0)

def _s(prefix, key):
    return str(st.session_state.get(f"{prefix}_{key}") or "")


# ── Inline pitching form ───────────────────────────────────────────────────────

def show_pitching_form(pid, edit_id=None):
    px = f"pf_{pid}"
    st.session_state.setdefault(f"{px}_ip", "0.0")
    mode_label = "✏️ Edit Pitching Line" if edit_id else "➕ Add Pitching Line"

    with st.container(border=True):
        st.markdown(f"##### {mode_label}")
        c1, c2, c3 = st.columns(3)
        c1.date_input("Date",     key=f"{px}_date")
        c2.text_input("Opponent", key=f"{px}_opp")
        c3.radio("H / A", ["H", "A"], key=f"{px}_ha", horizontal=True)

        a, b, c = st.columns(3)
        a.text_input("IP",  key=f"{px}_ip")
        b.number_input("BF",  key=f"{px}_bf",  min_value=0, step=1)
        c.number_input("K",   key=f"{px}_k",   min_value=0, step=1)

        d, e, f = st.columns(3)
        d.number_input("BB",  key=f"{px}_bb",  min_value=0, step=1)
        e.number_input("HBP", key=f"{px}_hbp", min_value=0, step=1)
        f.number_input("R",   key=f"{px}_r",   min_value=0, step=1)

        g, h, i = st.columns(3)
        g.number_input("ER",  key=f"{px}_er",  min_value=0, step=1)
        h.number_input("H",   key=f"{px}_hall", min_value=0, step=1)
        i.number_input("HR",  key=f"{px}_hr",  min_value=0, step=1)

        j, k, l = st.columns(3)
        j.number_input("2B",      key=f"{px}_2b",   min_value=0, step=1)
        k.number_input("3B",      key=f"{px}_3b",   min_value=0, step=1)
        l.number_input("Strikes", key=f"{px}_str",  min_value=0, step=1)

        m, n = st.columns(2)
        m.number_input("Balls",         key=f"{px}_balls", min_value=0, step=1)
        n.number_input("Total Pitches", key=f"{px}_pit",   min_value=0, step=1)

        sc, cc = st.columns(2)
        if sc.button("✓ Save Game", key=f"{px}_save", type="primary", use_container_width=True):
            parts = _s(px, "ip").split(".")
            outs = int(parts[0]) * 3 + (int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0)
            strikes = _i(px, "str"); balls = _i(px, "balls")
            kwargs = dict(
                game_date=str(st.session_state.get(f"{px}_date", date.today())),
                opponent=_s(px, "opp"),
                home_away=st.session_state.get(f"{px}_ha", "H"),
                outs=outs, BF=_i(px,"bf"), K=_i(px,"k"), BB=_i(px,"bb"), HBP=_i(px,"hbp"),
                strikes=strikes, balls=balls,
                total_pitches=_i(px,"pit") or strikes+balls,
                H_allowed=_i(px,"hall"), HR_allowed=_i(px,"hr"),
                doubles_allowed=_i(px,"2b"), triples_allowed=_i(px,"3b"),
                R=_i(px,"r"), ER=_i(px,"er"),
            )
            if edit_id:
                db.update_pitching_line(edit_id, **kwargs)
            else:
                db.add_pitching_line(player_id=pid, **kwargs)
            st.session_state["active_form"] = None
            for k2 in ["ip","opp","bf","k","bb","hbp","r","er","hall","hr","2b","3b","str","balls","pit"]:
                st.session_state.pop(f"{px}_{k2}", None)
            st.rerun()

        if cc.button("✗ Cancel", key=f"{px}_cancel", use_container_width=True):
            st.session_state["active_form"] = None
            st.rerun()


# ── Inline batting form ────────────────────────────────────────────────────────

def show_batting_form(pid, edit_id=None):
    px = f"bf_{pid}"
    mode_label = "✏️ Edit Batting Line" if edit_id else "➕ Add Batting Line"

    with st.container(border=True):
        st.markdown(f"##### {mode_label}")
        c1, c2, c3 = st.columns(3)
        c1.date_input("Date",     key=f"{px}_date")
        c2.text_input("Opponent", key=f"{px}_opp")
        c3.radio("H / A", ["H", "A"], key=f"{px}_ha", horizontal=True)

        a, b, c, d = st.columns(4)
        a.number_input("AB",  key=f"{px}_ab",  min_value=0, step=1)
        b.number_input("PA",  key=f"{px}_pa",  min_value=0, step=1)
        c.number_input("H",   key=f"{px}_h",   min_value=0, step=1)
        d.number_input("BB",  key=f"{px}_bb",  min_value=0, step=1)

        e, f, g, h = st.columns(4)
        e.number_input("2B",  key=f"{px}_2b",  min_value=0, step=1)
        f.number_input("3B",  key=f"{px}_3b",  min_value=0, step=1)
        g.number_input("HR",  key=f"{px}_hr",  min_value=0, step=1)
        h.number_input("HBP", key=f"{px}_hbp", min_value=0, step=1)

        i2, j2, k2 = st.columns(3)
        i2.number_input("R",   key=f"{px}_r",   min_value=0, step=1)
        j2.number_input("RBI", key=f"{px}_rbi", min_value=0, step=1)
        k2.number_input("SB",  key=f"{px}_sb",  min_value=0, step=1)

        sc, cc = st.columns(2)
        if sc.button("✓ Save Game", key=f"{px}_save", type="primary", use_container_width=True):
            ab=_i(px,"ab"); bb=_i(px,"bb"); hbp=_i(px,"hbp")
            kwargs = dict(
                game_date=str(st.session_state.get(f"{px}_date", date.today())),
                opponent=_s(px,"opp"),
                home_away=st.session_state.get(f"{px}_ha","H"),
                H=_i(px,"h"), doubles=_i(px,"2b"), triples=_i(px,"3b"),
                HR=_i(px,"hr"), BB=bb, HBP=hbp, AB=ab,
                PA=_i(px,"pa") or ab+bb+hbp,
                R=_i(px,"r"), RBI=_i(px,"rbi"), SB=_i(px,"sb"),
            )
            if edit_id:
                db.update_batting_line(edit_id, **kwargs)
            else:
                db.add_batting_line(player_id=pid, **kwargs)
            st.session_state["active_form"] = None
            for k2 in ["opp","ab","pa","h","bb","2b","3b","hr","hbp","r","rbi","sb"]:
                st.session_state.pop(f"{px}_{k2}", None)
            st.rerun()

        if cc.button("✗ Cancel", key=f"{px}_cancel", use_container_width=True):
            st.session_state["active_form"] = None
            st.rerun()


# ── Delete section ─────────────────────────────────────────────────────────────

def _load_pitch_edit(pid, g):
    """Pre-populate session state for a pitching edit."""
    px = f"pf_{pid}"
    from datetime import date as _date
    try:
        st.session_state[f"{px}_date"] = _date.fromisoformat(g['game_date'])
    except Exception:
        st.session_state[f"{px}_date"] = _date.today()
    st.session_state[f"{px}_opp"]   = g.get('opponent', '')
    st.session_state[f"{px}_ha"]    = g.get('home_away', 'H')
    st.session_state[f"{px}_ip"]    = str(g.get('IP', '0.0'))
    st.session_state[f"{px}_bf"]    = g.get('BF', 0)
    st.session_state[f"{px}_k"]     = g.get('K', 0)
    st.session_state[f"{px}_bb"]    = g.get('BB', 0)
    st.session_state[f"{px}_hbp"]   = g.get('HBP', 0)
    st.session_state[f"{px}_r"]     = g.get('R', 0)
    st.session_state[f"{px}_er"]    = g.get('ER', 0)
    st.session_state[f"{px}_hall"]  = g.get('H_allowed', 0)
    st.session_state[f"{px}_hr"]    = g.get('HR_allowed', 0)
    st.session_state[f"{px}_2b"]    = g.get('doubles_allowed', 0)
    st.session_state[f"{px}_3b"]    = g.get('triples_allowed', 0)
    st.session_state[f"{px}_str"]   = g.get('strikes', 0)
    st.session_state[f"{px}_balls"] = g.get('balls', 0)
    st.session_state[f"{px}_pit"]   = g.get('total_pitches', 0)


def _load_bat_edit(pid, g):
    """Pre-populate session state for a batting edit."""
    px = f"bf_{pid}"
    from datetime import date as _date
    try:
        st.session_state[f"{px}_date"] = _date.fromisoformat(g['game_date'])
    except Exception:
        st.session_state[f"{px}_date"] = _date.today()
    st.session_state[f"{px}_opp"] = g.get('opponent', '')
    st.session_state[f"{px}_ha"]  = g.get('home_away', 'H')
    st.session_state[f"{px}_ab"]  = g.get('AB', 0)
    st.session_state[f"{px}_pa"]  = g.get('PA', 0)
    st.session_state[f"{px}_h"]   = g.get('H', 0)
    st.session_state[f"{px}_bb"]  = g.get('BB', 0)
    st.session_state[f"{px}_2b"]  = g.get('doubles', 0)
    st.session_state[f"{px}_3b"]  = g.get('triples', 0)
    st.session_state[f"{px}_hr"]  = g.get('HR', 0)
    st.session_state[f"{px}_hbp"] = g.get('HBP', 0)
    st.session_state[f"{px}_r"]   = g.get('R', 0)
    st.session_state[f"{px}_rbi"] = g.get('RBI', 0)
    st.session_state[f"{px}_sb"]  = g.get('SB', 0)


def show_delete_section(player):
    if not player['pitching'] and not player['batting']:
        return
    pid = player['id']
    with st.expander("✏️ Edit / 🗑 Delete a game line"):
        if player['pitching']:
            if player['batting']:
                st.markdown("**Pitching**")
            for g in player['pitching']:
                ck = f"conf_del_p_{g['id']}"
                c1, c2, c3 = st.columns([5, 1, 1])
                c1.write(f"{g['game_date']}  vs {g['opponent']}  —  {g['IP']} IP, {g['K']} K, {g['ER']} ER")
                if c2.button("Edit", key=f"edit_p_{g['id']}"):
                    _load_pitch_edit(pid, g)
                    st.session_state["active_form"] = {"pid": pid, "type": "pitch", "edit_id": g['id']}
                    st.rerun()
                if c3.button("Delete", key=f"del_p_{g['id']}"):
                    st.session_state[ck] = True
                if st.session_state.get(ck):
                    st.warning(f"Delete {g['game_date']} vs {g['opponent']}?")
                    y, n = st.columns(2)
                    if y.button("Yes, delete", key=f"yes_{ck}", type="primary"):
                        db.delete_pitching_line(g['id'])
                        st.session_state.pop(ck, None)
                        st.rerun()
                    if n.button("Cancel", key=f"no_{ck}"):
                        st.session_state.pop(ck, None)
                        st.rerun()

        if player['batting']:
            if player['pitching']:
                st.markdown("**Batting**")
            for g in player['batting']:
                ck = f"conf_del_b_{g['id']}"
                c1, c2, c3 = st.columns([5, 1, 1])
                c1.write(f"{g['game_date']}  vs {g['opponent']}  —  {g['AB']} AB, {g['H']} H, {g.get('R',0)} R, {g.get('RBI',0)} RBI")
                if c2.button("Edit", key=f"edit_b_{g['id']}"):
                    _load_bat_edit(pid, g)
                    st.session_state["active_form"] = {"pid": pid, "type": "bat", "edit_id": g['id']}
                    st.rerun()
                if c3.button("Delete", key=f"del_b_{g['id']}"):
                    st.session_state[ck] = True
                if st.session_state.get(ck):
                    st.warning(f"Delete {g['game_date']} vs {g['opponent']}?")
                    y, n = st.columns(2)
                    if y.button("Yes, delete", key=f"yes_{ck}", type="primary"):
                        db.delete_batting_line(g['id'])
                        st.session_state.pop(ck, None)
                        st.rerun()
                    if n.button("Cancel", key=f"no_{ck}"):
                        st.session_state.pop(ck, None)
                        st.rerun()


# ── Stat displays ──────────────────────────────────────────────────────────────

def show_pitching(player):
    pt = player.get('pitching_totals', {})
    m = st.columns(12)
    m[0].metric("G",        pt.get('G', 0))
    m[1].metric("IP",       pt.get('IP', 0.0))
    m[2].metric("ERA",      f"{pt.get('ERA', 0.0):.2f}")
    m[3].metric("WHIP",     f"{pt.get('WHIP', 0.0):.2f}")
    m[4].metric("K",        pt.get('K', 0))
    m[5].metric("BB",       pt.get('BB', 0))
    m[6].metric("R",        pt.get('R', 0))
    m[7].metric("ER",       pt.get('ER', 0))
    m[8].metric("K/9",      f"{pt.get('K_per9', 0.0):.1f}")
    m[9].metric("BB/9",     f"{pt.get('BB_per9', 0.0):.1f}")
    m[10].metric("STR%",    f"{pt.get('strike_pct', 0.0):.1f}%")
    m[11].metric("PITCHES", pt.get('total_pitches', 0))
    if player['pitching']:
        df = pd.DataFrame(player['pitching'])
        cols = [c for c in PITCH_COLS if c in df.columns]
        st.dataframe(df[cols].rename(columns=PITCH_RENAME), hide_index=True, use_container_width=True)


def show_batting(player):
    bt = player.get('batting_totals', {})
    m = st.columns(12)
    m[0].metric("G",   bt.get('G', 0))
    m[1].metric("AVG", f"{bt.get('AVG', 0.0):.3f}")
    m[2].metric("OBP", f"{bt.get('OBP', 0.0):.3f}")
    m[3].metric("SLG", f"{bt.get('SLG', 0.0):.3f}")
    m[4].metric("OPS", f"{bt.get('OPS', 0.0):.3f}")
    m[5].metric("AB",  bt.get('AB', 0))
    m[6].metric("H",   bt.get('H', 0))
    m[7].metric("HR",  bt.get('HR', 0))
    m[8].metric("BB",  bt.get('BB', 0))
    m[9].metric("R",   bt.get('R', 0))
    m[10].metric("RBI", bt.get('RBI', 0))
    m[11].metric("SB",  bt.get('SB', 0))
    if player['batting']:
        df = pd.DataFrame(player['batting'])
        cols = [c for c in BAT_COLS if c in df.columns]
        st.dataframe(df[cols].rename(columns=BAT_RENAME), hide_index=True, use_container_width=True)


# ── Player cards ───────────────────────────────────────────────────────────────

pitchers = [p for p in data if p['position'] in ('pitcher', 'two-way')]
hitters  = [p for p in data if p['position'] == 'hitter']

def passes_filter(player):
    pos = player['position']
    team_ok = team_filter == "All Players" or player['team'] == team_filter
    if pos_filter == "Pitchers":
        pos_ok = pos in ('pitcher', 'two-way')
    elif pos_filter == "Hitters":
        pos_ok = pos in ('hitter', 'two-way')
    else:
        pos_ok = True
    return team_ok and pos_ok

active = st.session_state.get("active_form")  # {"pid": int, "type": "pitch"|"bat"}

for section_label, section_players in [("PITCHERS", pitchers), ("HITTERS", hitters)]:
    visible = [p for p in section_players if passes_filter(p)]
    if not visible:
        continue
    st.markdown(f"###### {section_label}")

    for player in visible:
        pos = player['position']
        pid = player['id']
        arm = f"{player['throws']}HP" if pos != 'hitter' else f"Bats {player['bats']}"
        pos_label = "TWO-WAY" if pos == 'two-way' else pos.upper()

        with st.container(border=True):
            # Header row
            nc1, nc2, nc3 = st.columns([6, 1, 1])
            nc1.markdown(
                f"**{player['name']}** &nbsp; `{player['team']}` &nbsp; `{arm}` &nbsp; `{pos_label}`"
            )
            if pos in ('pitcher', 'two-way'):
                with nc2:
                    if st.button("+ Pitching", key=f"pbtn_{pid}", use_container_width=True):
                        st.session_state["active_form"] = {"pid": pid, "type": "pitch"}
                        st.rerun()
            if pos in ('hitter', 'two-way'):
                with nc3:
                    if st.button("+ Batting", key=f"bbtn_{pid}", use_container_width=True):
                        st.session_state["active_form"] = {"pid": pid, "type": "bat"}
                        st.rerun()

            # Pitching stats
            if pos in ('pitcher', 'two-way'):
                if pos == 'two-way':
                    st.caption("PITCHING")
                show_pitching(player)

            if pos == 'two-way':
                st.divider()

            # Batting stats
            if pos in ('hitter', 'two-way'):
                if pos == 'two-way':
                    st.caption("BATTING")
                show_batting(player)

            # Inline form — stays open when switching filters
            if active and active.get("pid") == pid:
                if active.get("type") == "pitch" and pos in ('pitcher', 'two-way'):
                    show_pitching_form(pid, edit_id=active.get("edit_id"))
                elif active.get("type") == "bat" and pos in ('hitter', 'two-way'):
                    show_batting_form(pid, edit_id=active.get("edit_id"))

            # Delete section
            show_delete_section(player)
