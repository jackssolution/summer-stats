import streamlit as st
import pandas as pd
from datetime import date

import database as db

st.set_page_config(
    page_title="Summer Ball Tracker 2026",
    layout="wide",
    page_icon="⚾",
)

st.markdown("""
<style>
/* dark background */
[data-testid="stAppViewContainer"] { background-color: #0d1117; color: #e6edf3; }
[data-testid="stHeader"] { background-color: #161b22; }
[data-testid="stSidebar"] { background-color: #161b22; }
[data-testid="stMainBlockContainer"] { padding-top: 1.5rem; }
/* metric labels */
[data-testid="stMetricLabel"] { font-size: 0.7rem; color: #8b949e; text-transform: uppercase; }
[data-testid="stMetricValue"] { font-size: 1.1rem; color: #e6edf3; }
/* containers */
[data-testid="stVerticalBlockBorderWrapper"] {
    background-color: #161b22;
    border: 1px solid #30363d !important;
    border-radius: 8px;
}
/* dataframe */
[data-testid="stDataFrame"] { border: none; }
/* radio horizontal */
div[role="radiogroup"] { gap: 0.4rem; }
/* buttons */
[data-testid="stButton"] > button {
    background: #21262d;
    border: 1px solid #30363d;
    color: #e6edf3;
    border-radius: 6px;
}
[data-testid="stButton"] > button:hover {
    background: #30363d;
    border-color: #8b949e;
}
/* hide streamlit branding */
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# ── Dialogs ────────────────────────────────────────────────────────────────────

@st.dialog("Add Pitching Line")
def pitching_dialog(player_id: int, player_name: str):
    st.markdown(f"**{player_name}**")
    with st.form("pitching_form", border=False):
        c1, c2, c3 = st.columns(3)
        game_date = c1.date_input("Date", value=date.today())
        opponent  = c2.text_input("Opponent")
        home_away = c3.radio("H / A", ["H", "A"], horizontal=True)

        st.divider()

        r1c1, r1c2, r1c3 = st.columns(3)
        ip_str = r1c1.text_input("IP", value="0.0")
        bf     = r1c2.number_input("BF",  min_value=0, value=0, step=1)
        k      = r1c3.number_input("K",   min_value=0, value=0, step=1)

        r2c1, r2c2, r2c3 = st.columns(3)
        bb  = r2c1.number_input("BB",  min_value=0, value=0, step=1)
        hbp = r2c2.number_input("HBP", min_value=0, value=0, step=1)
        r   = r2c3.number_input("R",   min_value=0, value=0, step=1)

        r3c1, r3c2, r3c3 = st.columns(3)
        er       = r3c1.number_input("ER",  min_value=0, value=0, step=1)
        h_allow  = r3c2.number_input("H",   min_value=0, value=0, step=1)
        hr_allow = r3c3.number_input("HR",  min_value=0, value=0, step=1)

        r4c1, r4c2, r4c3 = st.columns(3)
        d_allow = r4c1.number_input("2B", min_value=0, value=0, step=1)
        t_allow = r4c2.number_input("3B", min_value=0, value=0, step=1)
        strikes = r4c3.number_input("Strikes", min_value=0, value=0, step=1)

        r5c1, r5c2 = st.columns(2)
        balls        = r5c1.number_input("Balls",        min_value=0, value=0, step=1)
        total_pitches = r5c2.number_input("Total Pitches", min_value=0, value=0, step=1)

        submitted = st.form_submit_button("Save Game", use_container_width=True, type="primary")
        if submitted:
            parts = str(ip_str).split(".")
            outs = int(parts[0]) * 3 + (int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0)
            final_tp = total_pitches or strikes + balls
            db.add_pitching_line(
                player_id=player_id,
                game_date=str(game_date),
                opponent=opponent,
                home_away=home_away,
                outs=outs, BF=bf, K=k, BB=bb, HBP=hbp,
                strikes=strikes, balls=balls, total_pitches=final_tp,
                H_allowed=h_allow, HR_allowed=hr_allow,
                doubles_allowed=d_allow, triples_allowed=t_allow,
                R=r, ER=er,
            )
            st.rerun()


@st.dialog("Add Batting Line")
def batting_dialog(player_id: int, player_name: str):
    st.markdown(f"**{player_name}**")
    with st.form("batting_form", border=False):
        c1, c2, c3 = st.columns(3)
        game_date = c1.date_input("Date", value=date.today())
        opponent  = c2.text_input("Opponent")
        home_away = c3.radio("H / A", ["H", "A"], horizontal=True)

        st.divider()

        r1c1, r1c2, r1c3, r1c4 = st.columns(4)
        ab  = r1c1.number_input("AB",  min_value=0, value=0, step=1)
        pa  = r1c2.number_input("PA",  min_value=0, value=0, step=1)
        h   = r1c3.number_input("H",   min_value=0, value=0, step=1)
        bb  = r1c4.number_input("BB",  min_value=0, value=0, step=1)

        r2c1, r2c2, r2c3, r2c4 = st.columns(4)
        doubles = r2c1.number_input("2B",  min_value=0, value=0, step=1)
        triples = r2c2.number_input("3B",  min_value=0, value=0, step=1)
        hr      = r2c3.number_input("HR",  min_value=0, value=0, step=1)
        hbp     = r2c4.number_input("HBP", min_value=0, value=0, step=1)

        submitted = st.form_submit_button("Save Game", use_container_width=True, type="primary")
        if submitted:
            final_pa = pa or ab + bb + hbp
            db.add_batting_line(
                player_id=player_id,
                game_date=str(game_date),
                opponent=opponent,
                home_away=home_away,
                H=h, doubles=doubles, triples=triples, HR=hr,
                BB=bb, HBP=hbp, AB=ab, PA=final_pa,
            )
            st.rerun()


# ── Header ─────────────────────────────────────────────────────────────────────

hcol1, hcol2 = st.columns([5, 1])
with hcol1:
    st.markdown("## ⚾ Summer Ball Tracker 2026")
    st.caption("Northwoods League · 2026 Season")
with hcol2:
    if st.button("↻ Refresh Stats", use_container_width=True):
        try:
            import scraper
            import threading
            threading.Thread(target=lambda: scraper.scrape_all(headless=True), daemon=True).start()
            st.toast("Scrape started — reloading shortly", icon="↻")
        except Exception as e:
            st.toast(f"Scrape error: {e}", icon="⚠️")

# ── Filters ────────────────────────────────────────────────────────────────────

fc1, fc2 = st.columns([3, 2])
with fc1:
    team_filter = st.radio(
        "Team",
        ["All Players", "Kenosha Kingfish", "St. Cloud Rox", "Willmar Stingers"],
        horizontal=True,
        label_visibility="collapsed",
    )
with fc2:
    pos_filter = st.radio(
        "Position",
        ["All Positions", "Pitchers", "Hitters"],
        horizontal=True,
        label_visibility="collapsed",
    )

st.divider()

# ── Load data ──────────────────────────────────────────────────────────────────

data = db.get_full_dashboard_data()

# ── Helpers ────────────────────────────────────────────────────────────────────

PITCH_DISPLAY_COLS = [
    'game_date', 'opponent', 'home_away', 'IP', 'BF', 'K', 'BB', 'HBP',
    'R', 'ER', 'H_allowed', 'doubles_allowed', 'triples_allowed', 'HR_allowed',
    'strikes', 'balls', 'total_pitches',
]
PITCH_RENAME = {
    'game_date': 'DATE', 'opponent': 'OPP', 'home_away': 'H/A',
    'H_allowed': 'H', 'doubles_allowed': '2B', 'triples_allowed': '3B',
    'HR_allowed': 'HR', 'strikes': 'STR', 'balls': 'BALL', 'total_pitches': 'PIT',
}

BAT_DISPLAY_COLS = [
    'game_date', 'opponent', 'home_away', 'AB', 'H', 'doubles', 'triples', 'HR', 'BB', 'HBP', 'PA',
]
BAT_RENAME = {
    'game_date': 'DATE', 'opponent': 'OPP', 'home_away': 'H/A',
    'doubles': '2B', 'triples': '3B',
}


def show_pitching(player):
    pt = player.get('pitching_totals', {})
    m = st.columns(11)
    m[0].metric("G",       pt.get('G', 0))
    m[1].metric("IP",      pt.get('IP', 0.0))
    m[2].metric("ERA",     f"{pt.get('ERA', 0.0):.2f}")
    m[3].metric("K",       pt.get('K', 0))
    m[4].metric("BB",      pt.get('BB', 0))
    m[5].metric("R",       pt.get('R', 0))
    m[6].metric("ER",      pt.get('ER', 0))
    m[7].metric("K%",      f"{pt.get('K_pct', 0.0):.1f}%")
    m[8].metric("BB%",     f"{pt.get('BB_pct', 0.0):.1f}%")
    m[9].metric("STR%",    f"{pt.get('strike_pct', 0.0):.1f}%")
    m[10].metric("PITCHES", pt.get('total_pitches', 0))

    if player['pitching']:
        df = pd.DataFrame(player['pitching'])
        cols = [c for c in PITCH_DISPLAY_COLS if c in df.columns]
        st.dataframe(
            df[cols].rename(columns=PITCH_RENAME),
            hide_index=True,
            use_container_width=True,
        )


def show_batting(player):
    bt = player.get('batting_totals', {})
    m = st.columns(9)
    m[0].metric("G",   bt.get('G', 0))
    m[1].metric("AVG", f"{bt.get('AVG', 0.0):.3f}")
    m[2].metric("OBP", f"{bt.get('OBP', 0.0):.3f}")
    m[3].metric("SLG", f"{bt.get('SLG', 0.0):.3f}")
    m[4].metric("OPS", f"{bt.get('OPS', 0.0):.3f}")
    m[5].metric("AB",  bt.get('AB', 0))
    m[6].metric("H",   bt.get('H', 0))
    m[7].metric("HR",  bt.get('HR', 0))
    m[8].metric("BB",  bt.get('BB', 0))

    if player['batting']:
        df = pd.DataFrame(player['batting'])
        cols = [c for c in BAT_DISPLAY_COLS if c in df.columns]
        st.dataframe(
            df[cols].rename(columns=BAT_RENAME),
            hide_index=True,
            use_container_width=True,
        )


# ── Player cards ───────────────────────────────────────────────────────────────

# Group by position section
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

    st.markdown(f"###### {section_label}")

    for player in visible:
        pos = player['position']
        arm = f"{player['throws']}HP" if pos != 'hitter' else f"Bats {player['bats']}"
        pos_label = "TWO-WAY" if pos == 'two-way' else pos.upper()

        with st.container(border=True):
            nc1, nc2, nc3 = st.columns([6, 1, 1])
            with nc1:
                st.markdown(
                    f"**{player['name']}** &nbsp; "
                    f"`{player['team']}` &nbsp; `{arm}` &nbsp; `{pos_label}`"
                )

            # Add pitching game button
            if pos in ('pitcher', 'two-way'):
                with nc2:
                    if st.button("+ Pitching", key=f"pbtn_{player['id']}", use_container_width=True):
                        pitching_dialog(player['id'], player['name'])

            # Add batting game button
            if pos in ('hitter', 'two-way'):
                with nc3:
                    if st.button("+ Batting", key=f"bbtn_{player['id']}", use_container_width=True):
                        batting_dialog(player['id'], player['name'])

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


if __name__ == "__main__":
    db.init_db()
