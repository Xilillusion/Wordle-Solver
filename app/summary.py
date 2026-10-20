from collections import defaultdict
import matplotlib.pyplot as plt
from tqdm import tqdm

from core.solvers import *
from core.decision_tree import DecisionTree, FakeTree


ANSWERS_LEN = len(ANSWERS)
ATTEMPTS = 6  # Wordle allows 6 guesses

def run(agent, tree):
    stat = defaultdict(int)
    total_attempts = 0

    pbar = tqdm(ANSWERS, desc=f"Evaluating {agent}", unit="word")
    for idx, answer in enumerate(pbar):
        # Reset tree pointer
        tree.reset()
        
        attempt = 1
        result = None

        while True:
            guess = tree.get_or_create_guess(agent.make_guess, result)

            if guess is None:
                raise RuntimeError(f"Solver {agent} returned an empty guess.")

            result = get_result(guess, answer)

            # Terminal if win
            if result == WIN_RESULT:
                stat[attempt] += 1
                total_attempts += attempt
                break

            agent.filter(guess, result)
            attempt += 1
    
        agent.reset()
        pbar.set_postfix(avg=f"{total_attempts / (idx+2):.3f}")

    if tree.is_dirty:
        tree.save()
        print(f"{tree.file_path} saved")
    return stat, total_attempts


def plot_comparison(stats):
    solvers = list(stats.keys())
    x_labels = [str(i) for i in range(1, ATTEMPTS + 1)] + [">6 (Fail)"]

    plt.figure(figsize=(10, 5))

    # Line plot for distribution of guesses
    for solver_name in solvers:
        counts = [stats[solver_name].get(k, 0) for k in range(1, ATTEMPTS + 2)]
        percentages = [(c / ANSWERS_LEN) * 100 for c in counts]
        plt.plot(x_labels, percentages, marker="o", linewidth=2, label=solver_name)

    plt.title("Distribution of Guesses per Solver")
    plt.xlabel("Number of Guesses")
    plt.ylabel("Percentage of Games (%)")
    plt.legend()
    plt.grid(True, linestyle="--", alpha=0.7)

    plt.tight_layout()
    plt.savefig("wordle_solver_comparison.png", dpi=300)
    plt.show()


def summary(solvers, no_tree_solvers):
    stats = {}
    table_data = []

    for Solver in solvers:
        agent = Solver()
        solver_name = str(agent)

        # Apply tree to non Fixed / Random solvers
        tree = FakeTree() if solver_name in no_tree_solvers else DecisionTree(solver_name)

        stat, total_attempts = run(agent, tree)

        stats[agent] = stat

        # Metrics calculation
        failed = sum(count for attempts, count in stat.items() if attempts > ATTEMPTS)
        solved = sum(stat.get(i, 0) for i in range(1, ATTEMPTS + 1))
        death_rate = (failed / ANSWERS_LEN) * 100

        # Average guesses for successful games
        success_guesses = sum(i * stat.get(i, 0) for i in range(1, ATTEMPTS + 1)) / solved
        avg_guesses = total_attempts / ANSWERS_LEN

        table_data.append(
            [
                solver_name,
                f"{death_rate:.2f}%",
                f"{avg_guesses:.2f}",
                f"{success_guesses:.2f}",
            ]
        )

    headers = ["Solver", "Fail Rate", "Avg Guesses", "Avg Guesses (Solved Games)"]

    # Print markdown or tabulated table
    row_format = "{:<16} {:<12} {:<12} {:<15}"
    print("\n" + row_format.format(*headers))
    print("-" * 70)
    for row in table_data:
        print(row_format.format(*row))

    plot_comparison(stats)


if __name__ == "__main__":
    solvers = [
        Fixed,
        Greedy,
        Binary,
        Minimax,
        Bayesian,
        #LimitMinimax,
        #LimitBayesian,
    ]
    no_tree_solvers = {
        "Fixed",
        #"Greedy",
        #"Binary",
        #"Minimax",
        #"Bayesian",
        #"LimitMinimax",
        #"LimitBayesian",
    }
    summary(solvers, no_tree_solvers)