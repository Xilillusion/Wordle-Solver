import json

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

    Format:
    {
        "guess": "CRANE",
        "children": {
            "0": { "guess": "SLOTH", "children": { ... } },
            "242": { "guess": "WIN", "children": {} }
        }
    }
    """

    def __init__(self, solver_name: str, save_dir: str = "./trees"):
        self.solver_name = solver_name
        self.file_path = f"{save_dir}/{solver_name}.json"
        self.tree = self._load()
        self.current_node = self.tree
        self.is_dirty = False

    def _load(self) -> dict:
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f">>> Warning: Failed to load {self.file_path}: {e}")
        return {}

    def save(self):
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(self.tree, f, indent=2)

    def reset(self):
        self.current_node = self.tree

    def get_or_create_guess(self, make_guess_func, result) -> str:
        if result is None:
            if "guess" not in self.tree:
                guess = make_guess_func()
                self.tree["guess"] = guess
                self.tree["children"] = {}
                self.is_dirty = True
            self.current_node = self.tree
            return self.current_node["guess"]

        res_key = str(result)
        children = self.current_node.setdefault("children", {})

        if res_key not in children:
            guess = make_guess_func()
            children[res_key] = {"guess": guess, "children": {}}
            self.is_dirty = True

        self.current_node = children[res_key]
        return self.current_node["guess"]
