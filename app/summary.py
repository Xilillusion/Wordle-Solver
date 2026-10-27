from collections import Counter
from typing import Iterable

import matplotlib.pyplot as plt
from tqdm import tqdm

from core.decision_tree import DecisionTree, FakeTree
from core.game import MAX_ATTEMPTS
from core.solvers import *


SolverType = type[Handler]
Distribution = Counter[int]


def evaluate_solver(agent: Handler, tree: DecisionTree | FakeTree) -> Distribution:
    results: Distribution = Counter()
    total_attempts = 0
    progress = tqdm(ANSWERS, desc=f"Evaluating {agent}", unit="word")

    for index, answer in enumerate(progress):
        tree.reset()
        attempt = 1
        result = None

        while True:
            guess = tree.get_or_create_guess(agent.make_guess, result)
            if guess is None:
                raise RuntimeError(f"Solver {agent} returned an empty guess.")

            result = get_result(guess, answer)
            if result == WIN_RESULT:
                results[attempt] += 1
                total_attempts += attempt
                break

            agent.filter(guess, result)
            attempt += 1

        agent.reset()
        progress.set_postfix(avg=f"{total_attempts / (index + 1):.3f}")

    return results


def calculate_metrics(results: Distribution) -> tuple[float, float, float]:
    total_games = sum(results.values())
    failed_games = sum(count for attempts, count in results.items() if attempts > MAX_ATTEMPTS)
    solved_games = total_games - failed_games

    total_attempts = sum(attempts * count for attempts, count in results.items())
    solved_attempts = sum(
        attempts * count
        for attempts, count in results.items()
        if attempts <= MAX_ATTEMPTS
    )

    return (
        failed_games / total_games * 100,
        total_attempts / total_games,
        solved_attempts / solved_games,
    )


def print_summary(rows: list[tuple[str, float, float, float]]) -> None:
    headers = ("Solver", "Fail Rate", "Avg Guesses", "Avg Guesses (Solved Games)")
    rows.sort(key=lambda x: x[2])
    formatted_rows = [
        (name, f"{fail_rate:.2f}%", f"{average:.4f}", f"{solved_average:.4f}")
        for name, fail_rate, average, solved_average in rows
    ]
    widths = [
        max(len(header), *(len(row[index]) for row in formatted_rows))
        for index, header in enumerate(headers)
    ]

    def format_row(row: tuple[str, ...]) -> str:
        return "  ".join(value.ljust(width) for value, width in zip(row, widths))

    print()
    print(format_row(headers))
    print("  ".join("-" * width for width in widths))
    for row in formatted_rows:
        print(format_row(row))


def plot_boxplot(stats: dict[str, Distribution]) -> None:
    solver_data = []
    for solver_name, distribution in stats.items():
        attempts = [
            attempt
            for attempt, count in distribution.items()
            for _ in range(count)
        ]
        if not attempts:
            raise ValueError(f"Solver {solver_name} has no game results to plot.")
        mean = sum(attempts) / len(attempts)
        solver_data.append((solver_name, attempts, mean))

    solver_data.sort(key=lambda item: item[2])
    solvers = [solver_name for solver_name, _, _ in solver_data]
    data = [attempts for _, attempts, _ in solver_data]

    _, ax = plt.subplots(figsize=(10, max(5, len(solvers) * 0.6)))
    boxplot = ax.boxplot(
        data,
        vert=False,
        labels=solvers,
        showmeans=True,
        meanline=True,
        medianprops={"visible": False},
    )
    ax.invert_yaxis()

    max_attempts_line = ax.axvline(x=MAX_ATTEMPTS, label=f"Max Limit ({MAX_ATTEMPTS})")
    mean_line = boxplot["means"][0]
    mean_line.set_label("Mean")
    outlier = next(
        (flier for flier in boxplot["fliers"] if len(flier.get_xdata())),
        boxplot["fliers"][0],
    )
    outlier.set_label("Outlier")

    ax.set_title("Distribution of Guesses by Solver")
    ax.set_xlabel("Number of Guesses")
    ax.set_ylabel("Solver")
    ax.legend(
        [mean_line, max_attempts_line, outlier],
        ["Mean", f"Max Limit ({MAX_ATTEMPTS})", "Outlier"],
    )

    plt.tight_layout()
    plt.show()


def summary(
    solvers: Iterable[SolverType],
    no_tree_solvers: set[str],
    save: bool = True,
) -> None:
    stats: dict[str, Distribution] = {}
    rows = []

    for solver in solvers:
        agent = solver()
        solver_name = str(agent)
        tree = (
            FakeTree()
            if solver_name in no_tree_solvers
            else DecisionTree(solver_name)
        )
        results = evaluate_solver(agent, tree)
        stats[solver_name] = results
        metrics = calculate_metrics(results)
        rows.append((solver_name, *metrics))
        if save and isinstance(tree, DecisionTree):
            tree.save(mean_guess=metrics[1])
            print(f"{tree.file_path} saved")

    print_summary(rows)
    plot_boxplot(stats)


if __name__ == "__main__":
    solvers = [
        FixedIndex,
        BinarySplit,
        NaiveMinimax,
        Minimax,
        NaiveEntropy,
        Entropy,
        BiasedEntropy,
        LookaheadEntropy,
    ]
    no_tree_solvers = {"FixedIndex"}
    summary(solvers, no_tree_solvers)
