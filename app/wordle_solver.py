import tkinter as tk

from core.decision_tree import DecisionTree
from core.game import MAX_ATTEMPS, WORD_LENGTH, WIN_RESULT, encode
from core.solvers import (
    BiasedEntropy,
    BinarySplit,
    Entropy,
    FixedIndex,
    LookaheadEntropy,
    Minimax,
    NaiveEntropy,
    NaiveMinimax,
    PositionalFreq,
)

# --- Constants ---
SOLVERS = [
    LookaheadEntropy,
    BiasedEntropy,
    Entropy,
    NaiveEntropy,
    Minimax,
    NaiveMinimax,
    BinarySplit,
    PositionalFreq,
    FixedIndex,
]
SOLVER_MAP = {s.__name__: s for s in SOLVERS}
SOLVER_NAMES = list(SOLVER_MAP.keys())

DARK_GRAY = '#555555'
COLOR_MAP = {DARK_GRAY: 0, 'yellow': 1, 'green': 2}
COLOR_CYCLE = {
    DARK_GRAY: ('yellow', 'black'),
    'yellow': ('green', 'white'),
    'green': (DARK_GRAY, 'white'),
}

# --- Global variables ---
agent = None
tree = None
attempt = 0
result = None

# --- Functions ---
def start_game():
    """Starts or resets the game"""
    global agent, tree, attempt, result
    attempt = 0
    result = None

    selected_name = selected_solver.get()
    solver_cls = SOLVER_MAP[selected_name]

    # Initilize solver
    if agent is None or agent.__class__.__name__ != selected_name:
        agent = solver_cls()
        start_button.config(text="Restart Game")
    else:
        agent.reset()
    submit_button.config(state=tk.NORMAL, text="Submit Feedback")

    # Handle decision tree
    if decision_tree.get() and selected_name != "FixedIndex":
        if tree is None or tree.solver_name != selected_name:
            if tree is not None:
                tree.save()
            tree = DecisionTree(selected_name)
        tree.reset()
    else:
        if tree is not None:
            tree.save()
            tree = None

    make_guess()

def make_guess():
    """Makes a guess and updates the UI"""
    # Update attempts
    global attempt
    attempt += 1
    result_label.config(text=f"Attempt {attempt}/{MAX_ATTEMPS}", fg="black")

    # Make guess
    if tree is not None:
        guess = tree.get_or_create_guess(agent.make_guess, result)
    else:
        guess = agent.make_guess()

    if not guess:
        result_label.config(text="Error: No guess available")
        submit_button.config(state=tk.DISABLED)
        return

    update_feedback_buttons(guess)

def submit_feedback():
    """Processes user feedback and updates the solver"""
    if agent is None:
        result_label.config(text="Warning: Press Start Game first")
        return

    global result
    feedback_list = [COLOR_MAP[btn.cget("bg")] for btn in feedback_buttons]
    result = encode(feedback_list)

    # Handle the case where Wordle is solved
    if result == WIN_RESULT:
        global attempt
        result_label.config(text=f"Solved in {attempt} attempts!")
        submit_button.config(state=tk.DISABLED)
        if tree is not None:
            tree.save()
        return
    
    guess = "".join(button.cget("text") for button in feedback_buttons)
    agent.filter(guess, result)
    if attempt >= MAX_ATTEMPS:
        result_label.config(text=f"Out of guesses after {MAX_ATTEMPS} attempts.")
        submit_button.config(state=tk.DISABLED)
        if tree is not None:
            tree.save()
        return
    make_guess()

def update_feedback_buttons(guess):
    """Initialize the feedback buttons' text and color"""
    for i, button in enumerate(feedback_buttons):
        button.config(text=guess[i], bg=DARK_GRAY, fg='white')

def cycle_color(i):
    """Cycles through feedback colors on button click."""
    next_color, next_text_color = COLOR_CYCLE[feedback_buttons[i].cget("bg")]
    feedback_buttons[i].config(bg=next_color, fg=next_text_color)


# --- GUI Setup ---
root = tk.Tk()
root.title("Wordle Solver")

# Solver Selection
selected_solver = tk.StringVar(value=SOLVERS[0].__name__)
tk.Label(root, text="Select a Solver:\t\t    ").pack(padx=10)
tk.OptionMenu(root, selected_solver, *SOLVER_NAMES).pack()

# Decision Tree Checkbox
decision_tree = tk.IntVar(value=1)
tk.Checkbutton(root, text="Pre-Trained Solver", variable=decision_tree).pack()

# Start Game Button
start_button = tk.Button(root, text="> Start Game <", command=start_game)
start_button.pack(pady=8)

# Feedback Buttons
color_frame = tk.Frame(root)
color_frame.pack()

feedback_buttons = []
for i in range(WORD_LENGTH):
    button = tk.Button(
        color_frame, text=" ", width=3, height=1, bg=DARK_GRAY,
        font=15, fg="white", command=lambda i=i: cycle_color(i))
    button.pack(side=tk.LEFT, padx=1)
    feedback_buttons.append(button)

# Submit Button
submit_button = tk.Button(root, text="Submit Feedback", command=submit_feedback)
submit_button.pack(pady=10)

# Result Label
result_label = tk.Label(root, text="")
result_label.pack()

root.mainloop()
