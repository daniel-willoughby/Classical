import streamlit as st
import random
import os
import json
from datetime import datetime

QUIZ_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "antiquity_quiz_102.txt")
LEADERBOARD_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "leaderboard.json")
QUESTIONS_PER_GAME = 3

POINTS_BY_ATTEMPT = {
    "Easy":   {1: 500,  2: 400,  3: 300,  4: 200,  5: 100},
    "Medium": {1: 1000, 2: 800,  3: 600,  4: 400,  5: 200},
    "Hard":   {1: 2000, 2: 1600, 3: 1200, 4: 800,  5: 400},
}
MAX_SCORE = {"Easy": 1500, "Medium": 3000, "Hard": 6000}

DIFF_COLOR = {"Easy": "green", "Medium": "orange", "Hard": "red"}


# ── Data helpers ─────────────────────────────────────────────────────────────

def parse_quiz_file(filepath):
    questions = {"Easy": [], "Medium": [], "Hard": []}
    current_difficulty = None
    current_question = None
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


def add_to_leaderboard(name, difficulty, score):
    entries = load_leaderboard()
    entries.append({
        "name": name,
        "difficulty": difficulty,
        "score": score,
        "date": datetime.now().strftime("%Y-%m-%d"),
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
        "screen": "name_entry",
        "player_name": "",
        "all_questions": None,
        "difficulty": None,
        "queue": [],
        "current": None,
        "clues_shown": 1,
        "total_score": 0,
        "questions_played": 0,
        "last_points": 0,
        "wrong_guesses": [],
        "feedback": None,
        "leaderboard_saved": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v
    if st.session_state.all_questions is None:
        st.session_state.all_questions = parse_quiz_file(QUIZ_FILE)


def start_game(difficulty):
    questions = st.session_state.all_questions[difficulty].copy()
    random.shuffle(questions)
    st.session_state.difficulty = difficulty
    st.session_state.queue = questions[:QUESTIONS_PER_GAME]
    st.session_state.total_score = 0
    st.session_state.questions_played = 0
    st.session_state.leaderboard_saved = False
    load_next_question()
    st.session_state.screen = "playing"


def load_next_question():
    queue = st.session_state.queue
    if queue:
        st.session_state.current = queue[0]
        st.session_state.queue = queue[1:]  # reassign rather than mutate in-place
    else:
        st.session_state.current = None
    st.session_state.clues_shown = 1
    st.session_state.wrong_guesses = []
    st.session_state.feedback = None


def after_question():
    """Decide whether to go to next question or final score."""
    if st.session_state.questions_played >= QUESTIONS_PER_GAME or not st.session_state.queue:
        # Save to leaderboard once
        if not st.session_state.leaderboard_saved:
            add_to_leaderboard(
                st.session_state.player_name,
                st.session_state.difficulty,
                st.session_state.total_score,
            )
            st.session_state.leaderboard_saved = True
        st.session_state.screen = "final_score"
    else:
        load_next_question()
        st.session_state.screen = "playing"


# ── Screens ───────────────────────────────────────────────────────────────────

def render_name_entry():
    st.title("🏛️ Antiquity Quiz")
    st.markdown("Guess the historical figure from antiquity using progressively easier clues.")
    st.markdown("---")
    st.subheader("What's your name?")
    with st.form("name_form"):
        name = st.text_input("Enter your name:", placeholder="e.g. Marcus Aurelius")
        submitted = st.form_submit_button("Continue →", type="primary", use_container_width=True)
    if submitted:
        if name.strip():
            st.session_state.player_name = name.strip()
            st.session_state.screen = "select"
            st.rerun()
        else:
            st.warning("Please enter your name to continue.")


def render_select():
    st.title("🏛️ Antiquity Quiz")
    st.markdown(f"Welcome, **{st.session_state.player_name}**! Choose a difficulty to play **{QUESTIONS_PER_GAME} questions**.")
    st.markdown("---")

    diff_info = {
        "Easy":   ("Well-known figures", "Up to 1,500 pts"),
        "Medium": ("Significant figures", "Up to 3,000 pts"),
        "Hard":   ("Obscure specialists", "Up to 6,000 pts"),
    }

    col1, col2, col3 = st.columns(3)
    for col, diff in zip([col1, col2, col3], ["Easy", "Medium", "Hard"]):
        desc, pts = diff_info[diff]
        with col:
            st.markdown(f"**{diff}**")
            st.caption(f"{desc}\n{pts}")
            if st.button(f"Play {diff}", key=f"btn_{diff}", use_container_width=True,
                         type="primary" if diff == "Easy" else "secondary"):
                start_game(diff)
                st.rerun()

    st.markdown("---")
    _render_leaderboard_preview()


def render_playing():
    q = st.session_state.current
    if q is None:
        after_question()
        st.rerun()
        return

    diff = st.session_state.difficulty
    color = DIFF_COLOR.get(diff, "blue")
    qnum = st.session_state.questions_played + 1

    col_left, col_right = st.columns([3, 1])
    with col_left:
        st.markdown(f"### :{color}[{diff}] — Question {qnum} of {QUESTIONS_PER_GAME}")
        st.caption(f"Player: {st.session_state.player_name}")
    with col_right:
        st.metric("Score", st.session_state.total_score)

    st.markdown("---")

    clues = q["clues"]
    shown = st.session_state.clues_shown
    points_table = POINTS_BY_ATTEMPT[diff]

    for i in range(shown):
        if i < len(clues):
            st.markdown(f"**Clue {i + 1}:** {clues[i]}")

    if st.session_state.wrong_guesses:
        wrong_list = ", ".join(st.session_state.wrong_guesses)
        st.markdown(f":red[Incorrect guesses: {wrong_list}]")

    st.markdown("---")

    points_available = points_table.get(shown, points_table[max(points_table)])
    st.caption(f"Points for correct answer now: **{points_available}**")

    if st.session_state.feedback:
        st.warning(st.session_state.feedback)

    with st.form("guess_form", clear_on_submit=True):
        guess = st.text_input("Your guess:", placeholder="Type a name and press Enter or Submit")
        col_submit, col_reveal = st.columns([2, 1])
        with col_submit:
            submitted = st.form_submit_button("Submit Guess", use_container_width=True, type="primary")
        with col_reveal:
            at_last_clue = shown >= len(clues)
            reveal = st.form_submit_button(
                "Give Up" if at_last_clue else "Reveal Next Clue",
                use_container_width=True,
            )

    if submitted and guess.strip():
        if check_answer(guess, q["answer"]):
            points = points_table.get(shown, points_table[max(points_table)])
            st.session_state.total_score += points
            st.session_state.questions_played += 1
            st.session_state.last_points = points
            st.session_state.feedback = None
            st.session_state.screen = "question_result"
            st.session_state.question_result_correct = True
            st.rerun()
        else:
            st.session_state.wrong_guesses = st.session_state.wrong_guesses + [guess.strip()]
            if shown >= len(clues):
                st.session_state.questions_played += 1
                st.session_state.last_points = 0
                st.session_state.feedback = None
                st.session_state.screen = "question_result"
                st.session_state.question_result_correct = False
            else:
                st.session_state.clues_shown += 1
                st.session_state.feedback = f"'{guess.strip()}' is incorrect."
            st.rerun()

    if reveal:
        if not at_last_clue:
            st.session_state.clues_shown += 1
            st.rerun()
        else:
            st.session_state.questions_played += 1
            st.session_state.last_points = 0
            st.session_state.screen = "question_result"
            st.session_state.question_result_correct = False
            st.rerun()


def render_question_result():
    q = st.session_state.current
    correct = st.session_state.get("question_result_correct", False)
    is_last = st.session_state.questions_played >= QUESTIONS_PER_GAME

    if correct:
        st.balloons()
        st.success(f"Correct! The answer was **{q['answer']}**")
        st.markdown(f"### +{st.session_state.last_points} points")
    else:
        st.error(f"The answer was **{q['answer']}**")
        st.markdown("### +0 points")

    st.markdown(f"**Running total: {st.session_state.total_score}**")
    st.markdown("---")

    label = "See Final Score →" if is_last else f"Question {st.session_state.questions_played + 1} of {QUESTIONS_PER_GAME} →"
    if st.button(label, type="primary", use_container_width=True):
        after_question()
        st.rerun()


def render_final_score():
    diff = st.session_state.difficulty
    score = st.session_state.total_score
    max_s = MAX_SCORE[diff]
    pct = int(score / max_s * 100)

    st.title("🏛️ Game Over")
    st.markdown(f"### {st.session_state.player_name} — {diff} difficulty")
    st.markdown(f"## Final Score: **{score}** / {max_s} ({pct}%)")
    st.markdown("---")

    # Leaderboard
    st.subheader("🏆 Leaderboard")
    entries = load_leaderboard()
    if entries:
        # Highlight the player's own latest entry
        player_score_idx = next(
            (i for i, e in enumerate(entries)
             if e["name"] == st.session_state.player_name and e["score"] == score and e["difficulty"] == diff),
            None,
        )
        rows = []
        for i, e in enumerate(entries[:20]):  # top 20
            marker = " ◀ you" if i == player_score_idx else ""
            rows.append(f"| {i+1} | {e['name']} | {e['difficulty']} | {e['score']} | {e['date']} |{marker}")
        table = (
            "| # | Name | Difficulty | Score | Date |\n"
            "|---|------|------------|-------|------|\n"
            + "\n".join(rows)
        )
        st.markdown(table)
    else:
        st.caption("No entries yet.")

    st.markdown("---")
    st.subheader("Play again — choose a difficulty")
    col1, col2, col3 = st.columns(3)
    for col, diff in zip([col1, col2, col3], ["Easy", "Medium", "Hard"]):
        with col:
            is_same = diff == st.session_state.difficulty
            if st.button(diff, key=f"replay_{diff}", use_container_width=True,
                         type="primary" if is_same else "secondary"):
                start_game(diff)
                st.rerun()


def _render_leaderboard_preview():
    st.subheader("🏆 Leaderboard")
    entries = load_leaderboard()
    if not entries:
        st.caption("No scores yet — be the first!")
        return
    rows = []
    for i, e in enumerate(entries[:10]):
        rows.append(f"| {i+1} | {e['name']} | {e['difficulty']} | {e['score']} | {e['date']} |")
    table = (
        "| # | Name | Difficulty | Score | Date |\n"
        "|---|------|------------|-------|------|\n"
        + "\n".join(rows)
    )
    st.markdown(table)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    st.set_page_config(page_title="Antiquity Quiz", page_icon="🏛️", layout="centered")
    init_state()

    screen = st.session_state.screen
    if screen == "name_entry":
        render_name_entry()
    elif screen == "select":
        render_select()
    elif screen == "playing":
        render_playing()
    elif screen == "question_result":
        render_question_result()
    elif screen == "final_score":
        render_final_score()


if __name__ == "__main__":
    main()
