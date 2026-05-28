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
    page_icon=None,
)

st.markdown("""
<style>
/* ── Base ─────────────────────────────────────────────────────── */
[data-testid="stAppViewContainer"] { background-color: #090D16; color: #E2E8F0; }
[data-testid="stHeader"]           { background-color: #090D16 !important; border-bottom: 1px solid #131C2E; }
[data-testid="stMainBlockContainer"]{ padding-top: 2rem; }
[data-testid="stSidebar"]          { background-color: #0F1623; }
#MainMenu, footer                  { visibility: hidden; }
hr { border-color: #131C2E !important; margin: 0.6rem 0 !important; }

/* ── Player cards ─────────────────────────────────────────────── */
[data-testid="stVerticalBlockBorderWrapper"] {
    background-color: #0D1422 !important;
    border: 1px solid #17243A !important;
    border-left: 3px solid #7A0019 !important;
    border-radius: 10px !important;
}

/* ── Buttons ──────────────────────────────────────────────────── */
[data-testid="stButton"] > button {
    background: #131C2E;
    border: 1px solid #1E2D47;
    color: #7B8FA8;
    border-radius: 6px;
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.03em;
    transition: all 0.15s;
}
[data-testid="stButton"] > button:hover {
    background: #1A2640;
    border-color: #FFD700;
    color: #FFD700;
}
[data-testid="stButton"] > button[kind="primary"] {
    background: rgba(255,215,0,0.08);
    border: 1px solid rgba(255,215,0,0.4);
    color: #FFD700;
}
[data-testid="stButton"] > button[kind="primary"]:hover {
    background: rgba(255,215,0,0.18);
}

/* ── Filters — radio → pill tabs ──────────────────────────────── */
div[role="radiogroup"] { display: flex; gap: 0.3rem; flex-wrap: wrap; }
div[role="radiogroup"] > label {
    background: #111827;
    border: 1px solid #1E2D47;
    border-radius: 99px;
    padding: 4px 13px !important;
    cursor: pointer;
    transition: all 0.15s;
    display: flex !important;
    align-items: center;
}
div[role="radiogroup"] > label > div:first-child { display: none; }
div[role="radiogroup"] > label p {
    color: #4B607A !important;
    font-size: 0.68rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    margin: 0 !important;
    line-height: 1.5 !important;
}
div[role="radiogroup"] > label:has(input:checked) {
    background: rgba(255,215,0,0.07);
    border-color: rgba(255,215,0,0.45);
}
div[role="radiogroup"] > label:has(input:checked) p { color: #FFD700 !important; }

/* ── Widget labels ────────────────────────────────────────────── */
[data-testid="stWidgetLabel"] p,
[data-testid="stWidgetLabel"] { color: #4B607A !important; font-size: 0.68rem !important; }
label { color: #4B607A !important; }

/* ── Expander ─────────────────────────────────────────────────── */
[data-testid="stExpander"] {
    border: 1px solid #131C2E !important;
    border-radius: 6px !important;
    background: transparent !important;
}
[data-testid="stExpander"] summary p {
    color: #334155 !important;
    font-size: 0.65rem !important;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}

/* ── Stat grid ────────────────────────────────────────────────── */
.stat-row {
    display: flex;
    flex-wrap: wrap;
    background: #060A12;
    border-radius: 8px;
    border: 1px solid #131C2E;
    margin: 0.55rem 0 0.8rem;
    overflow: hidden;
}
.stat-item {
    flex: 1;
    min-width: 52px;
    padding: 11px 6px 8px;
    text-align: center;
    border-right: 1px solid #111827;
}
.stat-item:last-child { border-right: none; }
.stat-val {
    font-size: 1.2rem;
    font-weight: 700;
    color: #CBD5E1;
    line-height: 1.1;
    font-variant-numeric: tabular-nums;
    letter-spacing: -0.01em;
}
.stat-lbl {
    font-size: 0.54rem;
    font-weight: 800;
    color: #263347;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-top: 4px;
}
.hi  .stat-val { color: #FFD700; }
.hi  .stat-lbl { color: #4A3800; }

/* ── Player header ────────────────────────────────────────────── */
.p-name {
    font-size: 1.0rem;
    font-weight: 700;
    color: #F1F5F9;
    letter-spacing: -0.01em;
    line-height: 1.2;
    margin-bottom: 6px;
}
.p-meta { display: flex; gap: 5px; align-items: center; flex-wrap: wrap; }
.pill {
    display: inline-block;
    padding: 2px 9px;
    border-radius: 99px;
    font-size: 0.59rem;
    font-weight: 700;
    letter-spacing: 0.07em;
    text-transform: uppercase;
    line-height: 1.7;
}
.pill-team { background: #111827; color: #4B607A; border: 1px solid #1E2D47; }
.pill-pos  { background: rgba(255,215,0,0.07); color: #FFD700; border: 1px solid rgba(255,215,0,0.25); }
.pill-hand { background: #0D1422; color: #334155; border: 1px solid #1A2438; }

/* ── Section & sub-section headers ───────────────────────────── */
.sec-hdr {
    font-size: 0.6rem;
    font-weight: 800;
    letter-spacing: 0.2em;
    color: #FFD700;
    text-transform: uppercase;
    padding-bottom: 8px;
    border-bottom: 1px solid #131C2E;
    margin: 0.25rem 0 1rem;
}
.sub-hdr {
    font-size: 0.56rem;
    font-weight: 800;
    letter-spacing: 0.14em;
    color: #263347;
    text-transform: uppercase;
    margin: 0.35rem 0 0;
}

/* ── App title ────────────────────────────────────────────────── */
.app-title {
    font-size: 1.55rem;
    font-weight: 900;
    color: #7A0019;
    letter-spacing: -0.03em;
    line-height: 1;
}
.app-title .yr { color: #FFD700; }
.app-sub {
    font-size: 0.6rem;
    color: #2D4060;
    font-weight: 600;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin-top: 6px;
}

/* ── Mobile ───────────────────────────────────────────────────── */
@media screen and (max-width: 640px) {

    /* Tighter page margins */
    [data-testid="stMainBlockContainer"] {
        padding: 0.75rem 0.5rem 2rem !important;
    }

    /* Stack every st.columns() layout into a single column */
    [data-testid="stHorizontalBlock"] {
        flex-wrap: wrap !important;
        gap: 0.35rem !important;
    }
    [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {
        min-width: 100% !important;
        flex: 1 1 100% !important;
        width: 100% !important;
    }

    /* Stat grid: single scrollable row instead of wrapping chaos */
    .stat-row {
        overflow-x: auto !important;
        flex-wrap: nowrap !important;
        -webkit-overflow-scrolling: touch;
        scrollbar-width: none;
    }
    .stat-row::-webkit-scrollbar { display: none; }
    .stat-item {
        flex-shrink: 0 !important;
        min-width: 64px !important;
        padding: 9px 5px 7px !important;
    }
    .stat-val { font-size: 1.05rem !important; }
    .stat-lbl { font-size: 0.5rem !important; }

    /* Title */
    .app-title { font-size: 1.1rem !important; }
    .app-sub   { font-size: 0.52rem !important; letter-spacing: 0.08em !important; }

    /* Player name & pills */
    .p-name { font-size: 0.88rem !important; }
    .pill   { font-size: 0.55rem !important; padding: 2px 7px !important; }

    /* Larger touch targets on buttons */
    [data-testid="stButton"] > button {
        padding: 0.45rem 0.7rem !important;
        font-size: 0.72rem !important;
        min-height: 38px !important;
    }

    /* Filter pills — tighter gap, slightly smaller */
    div[role="radiogroup"] { gap: 0.25rem !important; }
    div[role="radiogroup"] > label { padding: 4px 10px !important; }
    div[role="radiogroup"] > label p {
        font-size: 0.62rem !important;
        letter-spacing: 0.04em !important;
    }

    /* Section header */
    .sec-hdr { font-size: 0.55rem !important; letter-spacing: 0.14em !important; }
}
</style>
""", unsafe_allow_html=True)


# ── Header ─────────────────────────────────────────────────────────────────────

hcol1, hcol2 = st.columns([5, 1])
with hcol1:
    st.markdown("""
<div class="app-title">SUMMER BALL <span class="yr">2026</span></div>
<div class="app-sub">Northwoods League &nbsp;&middot;&nbsp; Cape Cod Baseball League &nbsp;&middot;&nbsp; NECBL</div>
""", unsafe_allow_html=True)
with hcol2:
    if st.button("Refresh Stats", use_container_width=True):
        try:
            import scraper, threading
            threading.Thread(target=lambda: scraper.scrape_all(headless=True), daemon=True).start()
            st.toast("Scrape started")
        except Exception as e:
            st.toast(f"Scrape error: {e}")

st.markdown("<div style='margin-top:1.1rem'></div>", unsafe_allow_html=True)

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

# ── Data — cached in session state so filter/log toggles don't re-query DB ─────

if st.session_state.get("_data_stale", True):
    st.session_state["_data"] = db.get_full_dashboard_data()
    st.session_state["_data_stale"] = False
data = st.session_state["_data"]

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

def _stat(label, value, cls=""):
    return (
        f'<div class="stat-item {cls}">'
        f'<div class="stat-val">{value}</div>'
        f'<div class="stat-lbl">{label}</div>'
        f'</div>'
    )


# ── Inline pitching form ───────────────────────────────────────────────────────

def show_pitching_form(pid, edit_id=None):
    px = f"pf_{pid}"
    st.session_state.setdefault(f"{px}_ip", "0.0")
    mode_label = "Edit Pitching Line" if edit_id else "Add Pitching Line"

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
        if sc.button("Save Game", key=f"{px}_save", type="primary", use_container_width=True):
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
            st.session_state["_data_stale"] = True
            for k2 in ["ip","opp","bf","k","bb","hbp","r","er","hall","hr","2b","3b","str","balls","pit"]:
                st.session_state.pop(f"{px}_{k2}", None)
            st.rerun()

        if cc.button("Cancel", key=f"{px}_cancel", use_container_width=True):
            st.session_state["active_form"] = None
            st.rerun()


# ── Inline batting form ────────────────────────────────────────────────────────

def show_batting_form(pid, edit_id=None):
    px = f"bf_{pid}"
    mode_label = "Edit Batting Line" if edit_id else "Add Batting Line"

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
        if sc.button("Save Game", key=f"{px}_save", type="primary", use_container_width=True):
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
            st.session_state["_data_stale"] = True
            for k2 in ["opp","ab","pa","h","bb","2b","3b","hr","hbp","r","rbi","sb"]:
                st.session_state.pop(f"{px}_{k2}", None)
            st.rerun()

        if cc.button("Cancel", key=f"{px}_cancel", use_container_width=True):
            st.session_state["active_form"] = None
            st.rerun()


# ── Delete section ─────────────────────────────────────────────────────────────

def _load_pitch_edit(pid, g):
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
    with st.expander("Edit / Delete a game line"):
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
                        st.session_state["_data_stale"] = True
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
                        st.session_state["_data_stale"] = True
                        st.rerun()
                    if n.button("Cancel", key=f"no_{ck}"):
                        st.session_state.pop(ck, None)
                        st.rerun()


# ── Stat displays ──────────────────────────────────────────────────────────────

def show_pitching(player, show_log=False):
    pt = player.get('pitching_totals', {})
    html = (
        _stat("G",       pt.get('G', 0))                          +
        _stat("IP",      pt.get('IP', 0.0))                       +
        _stat("ERA",     f"{pt.get('ERA',  0.0):.2f}")            +
        _stat("WHIP",    f"{pt.get('WHIP', 0.0):.2f}", "hi")     +
        _stat("K",       pt.get('K', 0))                          +
        _stat("BB",      pt.get('BB', 0))                         +
        _stat("R",       pt.get('R', 0))                          +
        _stat("ER",      pt.get('ER', 0))                         +
        _stat("K/9",     f"{pt.get('K_per9',  0.0):.1f}")        +
        _stat("BB/9",    f"{pt.get('BB_per9', 0.0):.1f}")        +
        _stat("STR%",    f"{pt.get('strike_pct', 0.0):.1f}%")    +
        _stat("PITCHES", pt.get('total_pitches', 0))
    )
    st.markdown(f'<div class="stat-row">{html}</div>', unsafe_allow_html=True)
    if show_log and player['pitching']:
        df = pd.DataFrame(player['pitching'])
        cols = [c for c in PITCH_COLS if c in df.columns]
        st.dataframe(df[cols].rename(columns=PITCH_RENAME), hide_index=True, use_container_width=True)


def show_batting(player, show_log=False):
    bt = player.get('batting_totals', {})
    html = (
        _stat("G",   bt.get('G', 0))                           +
        _stat("AVG", f"{bt.get('AVG', 0.0):.3f}")             +
        _stat("OBP", f"{bt.get('OBP', 0.0):.3f}")             +
        _stat("SLG", f"{bt.get('SLG', 0.0):.3f}")             +
        _stat("OPS", f"{bt.get('OPS', 0.0):.3f}", "hi")       +
        _stat("AB",  bt.get('AB', 0))                          +
        _stat("H",   bt.get('H', 0))                           +
        _stat("HR",  bt.get('HR', 0))                          +
        _stat("BB",  bt.get('BB', 0))                          +
        _stat("R",   bt.get('R', 0))                           +
        _stat("RBI", bt.get('RBI', 0))                         +
        _stat("SB",  bt.get('SB', 0))
    )
    st.markdown(f'<div class="stat-row">{html}</div>', unsafe_allow_html=True)
    if show_log and player['batting']:
        df = pd.DataFrame(player['batting'])
        cols = [c for c in BAT_COLS if c in df.columns]
        st.dataframe(df[cols].rename(columns=BAT_RENAME), hide_index=True, use_container_width=True)


# ── Player card — fragment so log toggle only rerenders this card ───────────────

@st.fragment
def render_player_card(pid):
    # Pull fresh player data from session-state cache (works on fragment reruns too)
    player = next((p for p in st.session_state.get("_data", []) if p['id'] == pid), None)
    if not player:
        return

    pos = player['position']
    arm = f"{player['throws']}HP" if pos != 'hitter' else f"Bats {player['bats']}"
    pos_label = "Two-Way" if pos == 'two-way' else pos.capitalize()

    log_key = f"show_log_{pid}"
    st.session_state.setdefault(log_key, False)
    show_log = st.session_state[log_key]

    active = st.session_state.get("active_form")

    with st.container(border=True):
        # Header row
        nc1, nc2, nc3 = st.columns([6, 1, 1])
        nc1.markdown(
            f'<div class="p-name">{player["name"]}</div>'
            f'<div class="p-meta">'
            f'<span class="pill pill-team">{player["team"]}</span>'
            f'<span class="pill pill-pos">{pos_label}</span>'
            f'<span class="pill pill-hand">{arm}</span>'
            f'</div>',
            unsafe_allow_html=True,
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
                st.markdown('<div class="sub-hdr">Pitching</div>', unsafe_allow_html=True)
            show_pitching(player, show_log)

        if pos == 'two-way':
            st.divider()

        # Batting stats
        if pos in ('hitter', 'two-way'):
            if pos == 'two-way':
                st.markdown('<div class="sub-hdr">Batting</div>', unsafe_allow_html=True)
            show_batting(player, show_log)

        # Game log toggle — fragment-scoped rerun so single click reflects immediately
        has_games = bool(player['pitching'] or player['batting'])
        if has_games:
            log_label = "Hide Game Log" if show_log else "Show Game Log"
            if st.button(log_label, key=f"log_toggle_{pid}", use_container_width=True):
                st.session_state[log_key] = not show_log
                st.rerun(scope="fragment")

        # Inline form — stays open when switching filters
        if active and active.get("pid") == pid:
            if active.get("type") == "pitch" and pos in ('pitcher', 'two-way'):
                show_pitching_form(pid, edit_id=active.get("edit_id"))
            elif active.get("type") == "bat" and pos in ('hitter', 'two-way'):
                show_batting_form(pid, edit_id=active.get("edit_id"))

        # Delete section
        show_delete_section(player)


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

for section_label, section_players in [("PITCHERS", pitchers), ("HITTERS", hitters)]:
    visible = [p for p in section_players if passes_filter(p)]
    if not visible:
        continue
    st.markdown(f'<div class="sec-hdr">{section_label}</div>', unsafe_allow_html=True)
    for player in visible:
        render_player_card(player['id'])
