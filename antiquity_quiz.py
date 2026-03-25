import streamlit as st
import random
import os
import json
from datetime import datetime

QUIZ_FILE       = os.path.join(os.path.dirname(os.path.abspath(__file__)), "antiquity_quiz_102.txt")
LEADERBOARD_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "leaderboard.json")
QUESTIONS_PER_GAME = 3

POINTS_BY_ATTEMPT = {
    "Easy":   {1: 500,  2: 400,  3: 300,  4: 200,  5: 100},
    "Medium": {1: 1000, 2: 800,  3: 600,  4: 400,  5: 200},
    "Hard":   {1: 2000, 2: 1600, 3: 1200, 4: 800,  5: 400},
}

DIFF_COLOR = {"Easy": "green", "Medium": "orange", "Hard": "red"}
DIFF_INFO  = {
    "Easy":   ("Well-known figures", "Up to 500 pts"),
    "Medium": ("Significant figures", "Up to 1,000 pts"),
    "Hard":   ("Obscure specialists", "Up to 2,000 pts"),
}

# Wikipedia Commons — public domain, load fine in any browser
_BG = {
    "menu": (
        "https://upload.wikimedia.org/wikipedia/commons/thumb/d/da/"
        "The_Parthenon_in_Athens.jpg/1280px-The_Parthenon_in_Athens.jpg"
    ),
    "playing": (
        "https://upload.wikimedia.org/wikipedia/commons/thumb/4/49/"
        "Forum_romanum_6k_%285765477480%29.jpg/"
        "1280px-Forum_romanum_6k_%285765477480%29.jpg"
    ),
    "leaderboard": (
        "https://upload.wikimedia.org/wikipedia/commons/thumb/6/61/"
        "Theatre_of_Epidaurus.jpg/1280px-Theatre_of_Epidaurus.jpg"
    ),
    "result": (
        "https://upload.wikimedia.org/wikipedia/commons/thumb/d/de/"
        "Colosseo_2020.jpg/1280px-Colosseo_2020.jpg"
    ),
}

_OVERLAY = {          # how dark to make the overlay — playing needs more contrast
    "menu":        "rgba(8,5,25,0.62)",
    "playing":     "rgba(8,5,25,0.76)",
    "leaderboard": "rgba(8,5,25,0.68)",
    "result":      "rgba(8,5,25,0.70)",
}


# ── Styling ───────────────────────────────────────────────────────────────────

def inject_base_styles():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;600;700&family=Cinzel+Decorative:wght@400;700&family=IM+Fell+English:ital@0;1&display=swap');

    /* ── Global ── */
    html, body, [class*="css"] {
        font-family: 'IM Fell English', Georgia, serif !important;
    }

    /* ── Scrollbar ── */
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: rgba(0,0,0,0.3); }
    ::-webkit-scrollbar-thumb { background: rgba(212,175,55,0.4); border-radius: 3px; }

    /* ── Main content block ── */
    .main .block-container {
        background: rgba(6, 4, 20, 0.70) !important;
        border: 1px solid rgba(212,175,55,0.22) !important;
        border-radius: 3px !important;
        max-width: 780px !important;
        padding: 2.5rem 3rem !important;
        box-shadow: 0 0 80px rgba(0,0,0,0.9),
                    inset 0 0 40px rgba(0,0,0,0.4),
                    0 0 0 1px rgba(212,175,55,0.06) !important;
    }

    /* ── Typography ── */
    h1 {
        font-family: 'Cinzel Decorative', serif !important;
        color: #d4af37 !important;
        text-align: center !important;
        font-size: 2.1rem !important;
        font-weight: 700 !important;
        letter-spacing: 0.06em !important;
        text-shadow: 0 0 40px rgba(212,175,55,0.55),
                     0 2px 6px rgba(0,0,0,0.9) !important;
        margin-bottom: 0.2rem !important;
    }
    h2 {
        font-family: 'Cinzel', serif !important;
        color: #d4af37 !important;
        font-weight: 600 !important;
        letter-spacing: 0.04em !important;
        text-shadow: 0 0 20px rgba(212,175,55,0.35) !important;
    }
    h3, h4 {
        font-family: 'Cinzel', serif !important;
        color: #c9a227 !important;
        letter-spacing: 0.03em !important;
    }
    h5, h6 { font-family: 'Cinzel', serif !important; color: #b89020 !important; }

    p, li { color: #e8d5a3 !important; line-height: 1.75 !important; }
    strong { color: #f0e0b0 !important; }

    /* ── Captions ── */
    .stCaption, [data-testid="stCaptionContainer"] p {
        color: #9e8a5e !important;
        font-style: italic !important;
        font-family: 'IM Fell English', serif !important;
    }

    /* ── Labels ── */
    label, [data-testid="stWidgetLabel"] p {
        color: #b8a47a !important;
        font-family: 'Cinzel', serif !important;
        font-size: 0.82rem !important;
        letter-spacing: 0.06em !important;
        text-transform: uppercase !important;
    }

    /* ── Buttons ── */
    .stButton > button,
    .stFormSubmitButton > button {
        background: rgba(212,175,55,0.07) !important;
        border: 1px solid rgba(212,175,55,0.50) !important;
        color: #d4af37 !important;
        font-family: 'Cinzel', serif !important;
        font-size: 0.76rem !important;
        font-weight: 600 !important;
        letter-spacing: 0.12em !important;
        text-transform: uppercase !important;
        border-radius: 2px !important;
        padding: 0.55rem 1.1rem !important;
        transition: all 0.25s ease !important;
    }
    .stButton > button:hover,
    .stFormSubmitButton > button:hover {
        background: rgba(212,175,55,0.18) !important;
        border-color: #d4af37 !important;
        box-shadow: 0 0 22px rgba(212,175,55,0.28) !important;
        transform: translateY(-1px) !important;
        color: #f0d060 !important;
    }
    .stButton > button[kind="primary"],
    .stFormSubmitButton > button[kind="primary"] {
        background: rgba(212,175,55,0.18) !important;
        border-color: #d4af37 !important;
        box-shadow: 0 0 16px rgba(212,175,55,0.18) !important;
    }
    .stButton > button[kind="primary"]:hover,
    .stFormSubmitButton > button[kind="primary"]:hover {
        background: rgba(212,175,55,0.30) !important;
        box-shadow: 0 0 28px rgba(212,175,55,0.38) !important;
    }

    /* ── Text input ── */
    .stTextInput > div > div > input {
        background: rgba(12,8,30,0.88) !important;
        border: 1px solid rgba(212,175,55,0.35) !important;
        border-radius: 2px !important;
        color: #e8d5a3 !important;
        font-family: 'IM Fell English', serif !important;
        font-size: 1rem !important;
        caret-color: #d4af37 !important;
    }
    .stTextInput > div > div > input:focus {
        border-color: #d4af37 !important;
        box-shadow: 0 0 12px rgba(212,175,55,0.22) !important;
        outline: none !important;
    }
    .stTextInput > div > div > input::placeholder { color: #6e5f3a !important; font-style: italic; }

    /* ── Selectbox ── */
    [data-testid="stSelectbox"] > div > div {
        background: rgba(12,8,30,0.88) !important;
        border: 1px solid rgba(212,175,55,0.35) !important;
        border-radius: 2px !important;
        color: #e8d5a3 !important;
    }
    [data-testid="stSelectbox"] svg { fill: #d4af37 !important; }
    /* dropdown list portal */
    [data-testid="stSelectboxVirtualDropdown"],
    ul[data-testid="stSelectboxVirtualDropdown"] {
        background: rgba(12,8,30,0.97) !important;
        border: 1px solid rgba(212,175,55,0.35) !important;
    }
    li[role="option"] { color: #e8d5a3 !important; }
    li[role="option"]:hover, li[aria-selected="true"] {
        background: rgba(212,175,55,0.15) !important;
        color: #f0d060 !important;
    }

    /* ── Form container ── */
    [data-testid="stForm"] {
        border: 1px solid rgba(212,175,55,0.18) !important;
        border-radius: 3px !important;
        background: rgba(4,2,14,0.45) !important;
        padding: 1.3rem 1.5rem !important;
    }

    /* ── Metric ── */
    [data-testid="metric-container"] {
        background: rgba(212,175,55,0.06) !important;
        border: 1px solid rgba(212,175,55,0.25) !important;
        border-radius: 2px !important;
        padding: 0.8rem !important;
    }
    [data-testid="stMetricLabel"] p {
        color: #9e8a5e !important;
        font-family: 'Cinzel', serif !important;
        font-size: 0.7rem !important;
        letter-spacing: 0.10em !important;
        text-transform: uppercase !important;
    }
    [data-testid="stMetricValue"] {
        color: #d4af37 !important;
        font-family: 'Cinzel', serif !important;
        font-size: 1.9rem !important;
    }

    /* ── Alerts ── */
    [data-testid="stAlert"] {
        border-radius: 2px !important;
        font-family: 'IM Fell English', serif !important;
        border-left-width: 3px !important;
    }
    [data-testid="stAlert"][kind="success"],
    div.stSuccess {
        background: rgba(0,55,28,0.55) !important;
        border-color: rgba(100,210,120,0.55) !important;
        color: #b8f0c8 !important;
    }
    [data-testid="stAlert"][kind="error"],
    div.stError {
        background: rgba(65,0,0,0.55) !important;
        border-color: rgba(210,60,60,0.55) !important;
        color: #f0b8b8 !important;
    }
    [data-testid="stAlert"][kind="warning"],
    div.stWarning {
        background: rgba(65,45,0,0.55) !important;
        border-color: rgba(210,160,0,0.55) !important;
        color: #f0dcb0 !important;
    }

    /* ── Divider ── */
    hr {
        border: none !important;
        border-top: 1px solid rgba(212,175,55,0.22) !important;
        margin: 1.4rem 0 !important;
    }

    /* ── Tables (leaderboard) ── */
    table { border-collapse: collapse !important; width: 100% !important; }
    thead tr { border-bottom: 1px solid rgba(212,175,55,0.35) !important; }
    th {
        color: #d4af37 !important;
        font-family: 'Cinzel', serif !important;
        font-size: 0.72rem !important;
        letter-spacing: 0.10em !important;
        text-transform: uppercase !important;
        padding: 0.5rem 0.6rem !important;
        background: rgba(212,175,55,0.06) !important;
    }
    td {
        color: #e8d5a3 !important;
        font-family: 'IM Fell English', serif !important;
        border-bottom: 1px solid rgba(255,255,255,0.04) !important;
        padding: 0.45rem 0.6rem !important;
    }
    tr:hover td { background: rgba(212,175,55,0.06) !important; }

    /* ── Ornament classes ── */
    .ornament-divider {
        text-align: center;
        color: #d4af37;
        letter-spacing: 0.5em;
        font-size: 0.9rem;
        margin: 0.5rem 0 1rem 0;
        opacity: 0.65;
        font-family: 'Cinzel', serif;
    }
    .screen-subtitle {
        text-align: center;
        color: #9e8a5e;
        font-style: italic;
        font-family: 'IM Fell English', serif;
        font-size: 1rem;
        margin: -0.4rem 0 1.2rem 0;
        letter-spacing: 0.03em;
    }

    /* ── Hide Streamlit chrome ── */
    #MainMenu            { visibility: hidden !important; }
    footer               { visibility: hidden !important; }
    [data-testid="stHeader"]  { background: transparent !important; }
    [data-testid="stToolbar"] { display: none !important; }
    </style>
    """, unsafe_allow_html=True)


def set_bg(category: str):
    """Inject the per-screen background image with a dark overlay."""
    url     = _BG.get(category, _BG["menu"])
    overlay = _OVERLAY.get(category, "rgba(8,5,25,0.70)")
    st.markdown(f"""
    <style>
    .stApp {{
        background-image:
            linear-gradient({overlay}, {overlay}),
            url('{url}');
        background-size: cover;
        background-attachment: fixed;
        background-position: center center;
        background-color: #0a0618;
    }}
    </style>
    """, unsafe_allow_html=True)


def ornament_divider():
    st.markdown('<div class="ornament-divider">— ✦ —</div>', unsafe_allow_html=True)


def screen_subtitle(text: str):
    st.markdown(f'<p class="screen-subtitle">{text}</p>', unsafe_allow_html=True)


# ── Data helpers ──────────────────────────────────────────────────────────────

def parse_quiz_file(filepath):
    questions = {"Easy": [], "Medium": [], "Hard": []}
    current_difficulty = None
    current_question   = None
    with open(filepath, "r") as f:
        lines = [line.strip() for line in f.readlines()]
    for line in lines:
        if line in ("Easy", "Medium", "Hard"):
            current_difficulty = line
            continue
        if current_difficulty and line.startswith(f"{current_difficulty} #"):
            if current_question:
                questions[current_question["difficulty"]].append(current_question)
            current_question = {"difficulty": current_difficulty, "clues": [], "answer": None}
            continue
        if current_question is None:
            continue
        if line.startswith("Clue "):
            clue_text = line.split(": ", 1)[1] if ": " in line else line
            current_question["clues"].append(clue_text)
        elif line.startswith("Answer: "):
            current_question["answer"] = line[len("Answer: "):]
    if current_question:
        questions[current_question["difficulty"]].append(current_question)
    return questions


def load_leaderboard():
    if os.path.exists(LEADERBOARD_FILE):
        with open(LEADERBOARD_FILE, "r") as f:
            return json.load(f)
    return []


def save_leaderboard(entries):
    with open(LEADERBOARD_FILE, "w") as f:
        json.dump(entries, f, indent=2)


def add_to_leaderboard(name, score, difficulties_used):
    unique      = set(difficulties_used)
    diff_label  = difficulties_used[0] if len(unique) == 1 else "Mixed"
    entries     = load_leaderboard()
    entries.append({
        "name":       name,
        "difficulty": diff_label,
        "score":      score,
        "date":       datetime.now().strftime("%Y-%m-%d"),
    })
    entries.sort(key=lambda e: e["score"], reverse=True)
    save_leaderboard(entries)
    return entries


def normalize(text):
    return text.strip().lower()


def check_answer(guess, answer):
    g = normalize(guess)
    a = normalize(answer)
    if g == a:
        return True
    answer_words = a.split()
    if len(answer_words) > 1 and g in answer_words:
        return True
    return False


# ── State ─────────────────────────────────────────────────────────────────────

def init_state():
    defaults = {
        "screen":               "name_entry",
        "player_name":          "",
        "all_questions":        None,
        "all_answers":          None,
        "difficulty":           None,
        "current":              None,
        "clues_shown":          1,
        "total_score":          0,
        "questions_played":     0,
        "last_points":          0,
        "wrong_guesses":        [],
        "feedback":             None,
        "leaderboard_saved":    False,
        "used_answers":         [],
        "difficulties_used":    [],
        "question_result_correct": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v
    if st.session_state.all_questions is None:
        st.session_state.all_questions = parse_quiz_file(QUIZ_FILE)
    if st.session_state.all_answers is None:
        st.session_state.all_answers = sorted(set(
            q["answer"]
            for diff_qs in st.session_state.all_questions.values()
            for q in diff_qs
        ))


def pick_question(difficulty):
    pool      = st.session_state.all_questions[difficulty]
    used      = set(st.session_state.used_answers)
    available = [q for q in pool if q["answer"] not in used] or pool
    st.session_state.difficulty    = difficulty
    st.session_state.current       = random.choice(available)
    st.session_state.clues_shown   = 1
    st.session_state.wrong_guesses = []
    st.session_state.feedback      = None


def start_game(difficulty):
    st.session_state.total_score       = 0
    st.session_state.questions_played  = 0
    st.session_state.leaderboard_saved = False
    st.session_state.used_answers      = []
    st.session_state.difficulties_used = []
    pick_question(difficulty)
    st.session_state.screen = "playing"


def after_question():
    if st.session_state.questions_played >= QUESTIONS_PER_GAME:
        if not st.session_state.leaderboard_saved:
            add_to_leaderboard(
                st.session_state.player_name,
                st.session_state.total_score,
                st.session_state.difficulties_used,
            )
            st.session_state.leaderboard_saved = True
        st.session_state.screen = "final_score"
    else:
        st.session_state.screen = "difficulty_pick"


# ── Shared UI helpers ─────────────────────────────────────────────────────────

def diff_buttons(key_prefix):
    """Three difficulty buttons; returns chosen difficulty string or None."""
    col1, col2, col3 = st.columns(3)
    chosen = None
    for col, diff in zip([col1, col2, col3], ["Easy", "Medium", "Hard"]):
        desc, pts = DIFF_INFO[diff]
        with col:
            st.markdown(
                f'<p style="text-align:center;font-family:\'Cinzel\',serif;'
                f'color:#d4af37;font-size:1rem;letter-spacing:0.08em;'
                f'margin-bottom:0.1rem;">{diff}</p>'
                f'<p style="text-align:center;color:#9e8a5e;font-style:italic;'
                f'font-size:0.82rem;margin-top:0;">{desc}<br>{pts}/question</p>',
                unsafe_allow_html=True,
            )
            is_current = diff == st.session_state.difficulty
            if st.button(
                f"Choose {diff}",
                key=f"{key_prefix}_{diff}",
                use_container_width=True,
                type="primary" if is_current else "secondary",
            ):
                chosen = diff
    return chosen


def leaderboard_table(entries, highlight_name=None, highlight_score=None,
                      highlight_diff=None, max_rows=20):
    if not entries:
        screen_subtitle("No scores yet — be the first to etch your name in stone.")
        return
    player_idx = next(
        (i for i, e in enumerate(entries)
         if e["name"] == highlight_name
         and e["score"] == highlight_score
         and e["difficulty"] == highlight_diff),
        None,
    ) if highlight_name else None

    rows = []
    for i, e in enumerate(entries[:max_rows]):
        marker = " ◀ you" if i == player_idx else ""
        rows.append(
            f"| {i+1} | {e['name']} | {e['difficulty']} | {e['score']} | {e['date']} |{marker}"
        )
    st.markdown(
        "| # | Name | Difficulty | Score | Date |\n"
        "|---|------|------------|-------|------|\n"
        + "\n".join(rows)
    )


# ── Screens ───────────────────────────────────────────────────────────────────

def render_name_entry():
    set_bg("menu")
    st.title("🏛️ What a Classic")
    ornament_divider()
    screen_subtitle("Test your knowledge of the ancient world")
    st.markdown("---")
    st.markdown("### Who approaches the gates of knowledge?")
    with st.form("name_form"):
        name = st.text_input("Your name:", placeholder="e.g. Commodus")
        submitted = st.form_submit_button(
            "Enter the Forum →", type="primary", use_container_width=True
        )
    if submitted:
        if name.strip():
            st.session_state.player_name = name.strip()
            st.session_state.screen      = "main_menu"
            st.rerun()
        else:
            st.warning("A name is required before you may proceed, scholar.")


def render_main_menu():
    set_bg("menu")
    st.title("🏛️ What a Classic")
    ornament_divider()
    screen_subtitle(f"Ave, {st.session_state.player_name}!")
    st.markdown("---")

    col_start, col_board = st.columns(2)
    with col_start:
        if st.button("⚔  Start Game", type="primary", use_container_width=True):
            st.session_state.screen = "select"
            st.rerun()
    with col_board:
        if st.button("🏆  Leaderboard", use_container_width=True):
            st.session_state.screen = "leaderboard"
            st.rerun()

    st.markdown("---")
    st.caption(
        f"Each game is {QUESTIONS_PER_GAME} questions. "
        "Choose a difficulty before every question — mix and match as you see fit."
    )

    entries = load_leaderboard()
    if entries:
        ornament_divider()
        st.markdown("#### 🏆 Hall of Fame — Top 5")
        leaderboard_table(entries, max_rows=5)


def render_leaderboard():
    set_bg("leaderboard")
    st.title("🏆 Hall of Fame")
    ornament_divider()
    screen_subtitle("Those whose deeds shall be remembered through the ages")
    st.markdown("---")
    leaderboard_table(load_leaderboard(), max_rows=50)
    st.markdown("---")
    if st.button("← Return to the Forum", use_container_width=False):
        st.session_state.screen = "main_menu"
        st.rerun()


def render_select():
    """Difficulty picker for the first question of a new game."""
    set_bg("menu")
    st.title("🏛️ What a Classic")
    ornament_divider()
    screen_subtitle(f"Welcome, {st.session_state.player_name} — choose your first trial")
    st.markdown("---")
    st.markdown("### Question I of III — Choose a Difficulty")
    st.markdown(" ")

    chosen = diff_buttons("start")
    if chosen:
        start_game(chosen)
        st.rerun()

    st.markdown("---")
    if st.button("← Back to Menu", use_container_width=False):
        st.session_state.screen = "main_menu"
        st.rerun()


def render_difficulty_pick():
    """Difficulty picker shown between questions."""
    set_bg("menu")
    qnum    = st.session_state.questions_played + 1
    numeral = ["I", "II", "III"][qnum - 1] if qnum <= 3 else str(qnum)

    st.title("🏛️ Choose Your Trial")
    ornament_divider()
    screen_subtitle(f"Running score: {st.session_state.total_score} pts")
    st.markdown("---")
    st.markdown(f"### Question {numeral} of III — Choose a Difficulty")
    st.caption("Dare you test yourself on harder ground for greater glory?")
    st.markdown(" ")

    chosen = diff_buttons("pick")
    if chosen:
        pick_question(chosen)
        st.session_state.screen = "playing"
        st.rerun()


def render_playing():
    set_bg("playing")
    q = st.session_state.current
    if q is None:
        after_question()
        st.rerun()
        return

    diff    = st.session_state.difficulty
    color   = DIFF_COLOR.get(diff, "blue")
    qnum    = st.session_state.questions_played + 1
    numeral = ["I", "II", "III"][qnum - 1] if qnum <= 3 else str(qnum)

    col_left, col_right = st.columns([3, 1])
    with col_left:
        st.markdown(
            f"<h3 style='margin-bottom:0.1rem;'>:{color}[{diff}] &nbsp;·&nbsp; "
            f"Question {numeral} of III</h3>",
            unsafe_allow_html=True,
        )
        st.caption(f"Player: {st.session_state.player_name}")
    with col_right:
        st.metric("Score", st.session_state.total_score)

    ornament_divider()

    clues        = q["clues"]
    shown        = st.session_state.clues_shown
    points_table = POINTS_BY_ATTEMPT[diff]

    for i in range(shown):
        if i < len(clues):
            st.markdown(
                f'<p style="font-size:1.05rem;color:#e8d5a3;">'
                f'<span style="color:#d4af37;font-family:\'Cinzel\',serif;'
                f'font-size:0.78rem;letter-spacing:0.08em;">CLUE {i+1}</span>'
                f'&nbsp;&nbsp;{clues[i]}</p>',
                unsafe_allow_html=True,
            )

    if st.session_state.wrong_guesses:
        wrong_list = ", ".join(st.session_state.wrong_guesses)
        st.markdown(f":red[*Incorrect guesses:* {wrong_list}]")

    st.markdown("---")

    points_available = points_table.get(shown, points_table[max(points_table)])
    st.caption(f"Answer now for: **{points_available} pts**")

    if st.session_state.feedback:
        st.warning(st.session_state.feedback)

    with st.form("guess_form", clear_on_submit=True):
        guess = st.selectbox(
            "Name the figure:",
            options=[None] + st.session_state.all_answers,
            index=0,
            format_func=lambda x: "— begin typing to search —" if x is None else x,
        )
        col_submit, col_reveal = st.columns([2, 1])
        with col_submit:
            submitted = st.form_submit_button(
                "Submit Answer", use_container_width=True, type="primary"
            )
        with col_reveal:
            at_last_clue = shown >= len(clues)
            reveal = st.form_submit_button(
                "Concede Defeat" if at_last_clue else "Reveal Next Clue",
                use_container_width=True,
            )

    if submitted and guess is not None:
        if check_answer(guess, q["answer"]):
            points = points_table.get(shown, points_table[max(points_table)])
            st.session_state.total_score          += points
            st.session_state.questions_played     += 1
            st.session_state.last_points           = points
            st.session_state.feedback              = None
            st.session_state.used_answers          = st.session_state.used_answers + [q["answer"]]
            st.session_state.difficulties_used     = st.session_state.difficulties_used + [diff]
            st.session_state.screen                = "question_result"
            st.session_state.question_result_correct = True
            st.rerun()
        else:
            st.session_state.wrong_guesses = st.session_state.wrong_guesses + [guess]
            if shown >= len(clues):
                st.session_state.questions_played     += 1
                st.session_state.last_points           = 0
                st.session_state.feedback              = None
                st.session_state.used_answers          = st.session_state.used_answers + [q["answer"]]
                st.session_state.difficulties_used     = st.session_state.difficulties_used + [diff]
                st.session_state.screen                = "question_result"
                st.session_state.question_result_correct = False
            else:
                st.session_state.clues_shown += 1
                st.session_state.feedback    = f"'{guess}' is not the answer — try again."
            st.rerun()

    if reveal:
        if not at_last_clue:
            st.session_state.clues_shown += 1
            st.rerun()
        else:
            st.session_state.questions_played     += 1
            st.session_state.last_points           = 0
            st.session_state.used_answers          = st.session_state.used_answers + [q["answer"]]
            st.session_state.difficulties_used     = st.session_state.difficulties_used + [diff]
            st.session_state.screen                = "question_result"
            st.session_state.question_result_correct = False
            st.rerun()


def render_question_result():
    set_bg("result")
    q       = st.session_state.current
    correct = st.session_state.get("question_result_correct", False)
    is_last = st.session_state.questions_played >= QUESTIONS_PER_GAME

    if correct:
        st.balloons()
        st.success(f"✅  Correct! The answer was **{q['answer']}**")
        st.markdown(
            f'<h3 style="color:#d4af37;text-align:center;">+ {st.session_state.last_points} pts</h3>',
            unsafe_allow_html=True,
        )
    else:
        st.error(f"❌  The answer was **{q['answer']}**")
        st.markdown(
            '<h3 style="color:#9e6060;text-align:center;">+ 0 pts</h3>',
            unsafe_allow_html=True,
        )

    ornament_divider()
    st.markdown(
        f'<p style="text-align:center;font-family:\'Cinzel\',serif;'
        f'color:#b8a47a;letter-spacing:0.06em;">Running Total: '
        f'<span style="color:#d4af37;">{st.session_state.total_score}</span></p>',
        unsafe_allow_html=True,
    )
    st.markdown("---")

    if is_last:
        if st.button("See Final Reckoning →", type="primary", use_container_width=True):
            after_question()
            st.rerun()
    else:
        qnum  = st.session_state.questions_played + 1
        numer = ["I", "II", "III"][qnum - 1] if qnum <= 3 else str(qnum)
        if st.button(
            f"Choose Difficulty for Question {numer} →",
            type="primary", use_container_width=True,
        ):
            after_question()
            st.rerun()


def render_final_score():
    set_bg("result")
    score      = st.session_state.total_score
    diffs      = st.session_state.difficulties_used
    diff_label = diffs[0] if len(set(diffs)) == 1 else "Mixed"

    st.title("🏛️ The Reckoning")
    ornament_divider()
    screen_subtitle(f"{st.session_state.player_name} · {diff_label}")
    st.markdown(
        f'<h2 style="text-align:center;">Final Score: '
        f'<span style="color:#d4af37;">{score}</span></h2>',
        unsafe_allow_html=True,
    )
    st.markdown("---")

    st.markdown("### 🏆 Hall of Fame")
    leaderboard_table(
        load_leaderboard(),
        highlight_name=st.session_state.player_name,
        highlight_score=score,
        highlight_diff=diff_label,
    )

    st.markdown("---")
    col_menu, col_play = st.columns(2)
    with col_menu:
        if st.button("← Main Menu", use_container_width=True):
            st.session_state.screen = "main_menu"
            st.rerun()
    with col_play:
        if st.button("⚔  Play Again", type="primary", use_container_width=True):
            st.session_state.screen = "select"
            st.rerun()


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    st.set_page_config(
        page_title="What a Classic",
        page_icon="🏛️",
        layout="centered",
        initial_sidebar_state="collapsed",
    )
    inject_base_styles()
    init_state()

    dispatch = {
        "name_entry":      render_name_entry,
        "main_menu":       render_main_menu,
        "leaderboard":     render_leaderboard,
        "select":          render_select,
        "difficulty_pick": render_difficulty_pick,
        "playing":         render_playing,
        "question_result": render_question_result,
        "final_score":     render_final_score,
    }
    dispatch.get(st.session_state.screen, render_main_menu)()


if __name__ == "__main__":
    main()
