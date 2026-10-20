# Wordle Solver

A Wordle assistant with a static browser interface, a Python Tkinter interface, an interactive command-line game, and several algorithms for choosing guesses. The website uses only the precomputed JSON decision trees; the Python solver can calculate guesses and save new branches.

## Requirements

- Python 3.12 or later
- Tkinter, typically included with Python
- `matplotlib` and `tqdm` only for running the solver comparison

No third-party packages are required for the GUI, command-line game, or interactive solver.

Run the commands below from the repository root so the application can find the word lists and decision-tree files.

## Run the app

### Website

The static website in `web\` runs in a browser and uses only the precomputed JSON decision trees in `trees\`. It does not run Python, access the word lists, or calculate new guesses. If a feedback path is missing from the selected tree, the website reports that no saved branch is available.

From the repository root, start a local web server:

```powershell
py -m http.server 8000
```

Then open <http://localhost:8000/web/>. The server is needed because browsers do not allow the website to fetch its JSON tree files when `index.html` is opened directly from disk. The same `web\` folder can be hosted on a static web host alongside `trees\`.

Select a decision tree and click **Start game**. For each guess, click each tile to cycle through gray, yellow, and green, then submit the feedback.

### Desktop GUI

Launch the GUI:

```powershell
py -m app.wordle_solver
```

Choose a solver and select **Start Game**. Enter its guess in Wordle, then click each letter tile until its color matches the feedback:

- Green: correct letter in the correct position
- Yellow: correct letter in the wrong position
- Gray: letter is not in the answer

Tiles cycle green → yellow → gray. Select **Submit Feedback** to get the next guess. The **Pre-Trained Solver** option uses the matching JSON decision tree in `trees\` when available; missing branches are calculated and saved as you play. Turn it off to calculate guesses directly. The `Fixed` solver does not use a decision tree.

## Command-line tools

Play a local Wordle game with a randomly selected answer:

```powershell
py -m core.game
```

Try a solver interactively by entering the feedback for each guess as five digits (`0` = gray, `1` = yellow, `2` = green):

```powershell
py -m core.solvers
```

The solver comparison evaluates the configured solvers against the answer list, prints summary statistics, and creates `wordle_solver_comparison.png`:

```powershell
py -m app.summary
```

The comparison uses `matplotlib` and `tqdm`. Install them if needed:

```powershell
py -m pip install matplotlib tqdm
```

## Solvers

| Solver | Strategy |
| --- | --- |
| `Bayesian` | Chooses a guess with high expected information gain (entropy), considering all allowed guesses while many answers remain. |
| `Minimax` | Chooses a guess that minimizes the size of the largest possible remaining answer group. |
| `Binary` | Scores guesses by how effectively their distinct letters divide the remaining answers. |
| `Greedy` | Scores letters by their positional frequency among remaining answers, prioritizing unresolved positions. |
| `LimitBayesian` | Uses the Bayesian entropy strategy but only considers remaining answers as guesses. |
| `LimitMinimax` | Uses the minimax strategy but only considers remaining answers as guesses. |
| `Fixed` | A deterministic baseline that selects an answer at a fixed position in the remaining list. |

Solvers filter the possible answers after each piece of feedback. The `Bayesian`, `Minimax`, `Binary`, and `Greedy` solvers can consider words outside the remaining answer candidates as guesses; the `Limit` variants cannot.

## Repository layout

| Path | Contents |
| --- | --- |
| `app\wordle_solver.py` | Tkinter Wordle assistant |
| `app\summary.py` | Solver evaluation and comparison chart |
| `web\` | Static, browser-based assistant that traverses saved decision trees |
| `core\game.py` | Word lists, feedback encoding, and command-line game |
| `core\solvers.py` | Solver algorithms and interactive solver |
| `core\decision_tree.py` | JSON decision-tree loading, traversal, and saving |
| `dict\allowed.txt` | Allowed guess words |
| `dict\answers.txt` | Possible answer words |
| `trees\` | Saved decision trees, one JSON file per solver |

The word lists are stored locally and are not updated automatically. Their source is documented in [`dict/README.md`](dict/README.md). Decision trees are local JSON data and may grow as new feedback paths are explored.
