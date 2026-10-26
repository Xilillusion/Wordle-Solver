import json
from pathlib import Path

from core.game import WIN_RESULT


class FakeTree:
    def __init__(self):
        self.is_dirty = False
    def save(self):
        pass
    def reset(self):
        pass
    def get_or_create_guess(self, make_guess_func, result) -> str:
        return make_guess_func()

class DecisionTree:
    """Wordle Tree manager based on JSON

    JSON format (arrays represent (guess, children) tuples):
    [
        "CRANE",
        {
            "0": ["SLOTH", { ... }],
            "1": ["HELLO", { ... }]
        }
    ]
    """

    def __init__(self, solver_name: str, save_dir: str = "./trees"):
        self.solver_name = solver_name
        self.save_dir = Path(save_dir)
        versioned_files = list(self.save_dir.glob(f"{solver_name}-*.json"))
        if versioned_files:
            self.file_path = str(max(versioned_files, key=lambda path: path.stat().st_mtime))
        else:
            self.file_path = str(self.save_dir / f"{solver_name}.json")
        self.tree = self._load()
        self.current_node: list = []
        self.is_dirty = False

    def _load(self) -> list:
        if not Path(self.file_path).exists():
            return []
        with open(self.file_path, "r") as f:
            return json.load(f)

    def save(self, mean_guess: float | None = None):
        if mean_guess is not None:
            self.file_path = str(
                self.save_dir / f"{self.solver_name}-{mean_guess:.4f}.json"
            )
        with open(self.file_path, "w", encoding="utf-8") as f:
            f.write(self._format_tree())
            f.write("\n")

    def _format_tree(self) -> str:
        if not self.tree:
            return "[]"

        lines = ["[", f"  {json.dumps(self.tree[0])},", "  {"]
        lines.extend(self._format_children(self.tree[1], 4))
        lines.extend(["  }", "]"])
        return "\n".join(lines)

    @classmethod
    def _format_children(cls, children: dict, indent: int) -> list[str]:
        lines = []
        for result, (guess, descendants) in children.items():
            prefix = " " * indent + f"{json.dumps(result)}: [{json.dumps(guess)}, "
            if descendants:
                lines.append(prefix + "{")
                lines.extend(cls._format_children(descendants, indent + 2))
                lines.append(" " * indent + "}]")
            else:
                lines.append(prefix + "{}]")
        return lines

    def reset(self):
        self.current_node = []

    def get_or_create_guess(self, make_guess_func, result: int | None) -> str:
        if result is None:
            if not self.tree:
                guess = make_guess_func()
                self.tree = [guess, {}]
                self.is_dirty = True
            self.current_node = self.tree

        if result is None or result == WIN_RESULT:
            return self.current_node[0]

        res_key = str(result)
        children = self.current_node[1]
        if res_key not in children:
            guess = make_guess_func()
            children[res_key] = [guess, {}]
            self.is_dirty = True

        self.current_node = children[res_key]
        return self.current_node[0]
