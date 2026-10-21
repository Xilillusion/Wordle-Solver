from math import log2
from collections import Counter

from core.game import ALLOWED, ANSWERS, WORD_LENGTH, WIN_RESULT, get_result


class Handler:
    """Basic algorithm to start the game and filter the words based on the feedback"""
    def __init__(self):
        self.answers_range = ANSWERS.copy()
    
    def __str__(self):
        return self.__class__.__name__
    
    def reset(self):
        self.answers_range = ANSWERS.copy()
    
    def filter(self, guess, result):
        # Filter the word based on the result
        self.answers_range = [w for w in self.answers_range if get_result(guess, w) == result]
    
    def make_guess(self):
        len_words = len(self.answers_range)
        if len_words == 0:
            return
        # If only 1-2 answers left, make a direct guess
        if len_words <= 2:
            return self.answers_range[0]

        return self.guess()

# --- Solvers ---

class LimitBayesian(Handler):
    """Apply Bayesian search to find the word with highest entropy in the word list"""
    def guess(self):
        # Bayesian selection using precomputed entropy values
        return max(self.answers_range, key=self.compute_information_gain)
    
    def compute_information_gain(self, guess):
        counts = [0] * (WIN_RESULT + 1)
        for word in ANSWERS:
            counts[get_result(guess, word)] += 1

        total = len(self.answers_range)
        entropy = 0.0
        for c in counts:
            if c > 0:
                p = c / total
                entropy -= p * log2(p)
        return entropy

class Bayesian(LimitBayesian):
    """Apply Bayesian search to find the word with highest entropy in the word list"""
    def guess(self):
        candidates = self.answers_range if len(self.answers_range) <= 3 else ALLOWED
        answer_set = set(self.answers_range)

        best_guess = None
        max_entropy = -1.0
        best_in_answers = False

        for word in candidates:
            entropy = self.compute_information_gain(word)
            in_answers = word in answer_set

            # Choose the one with higher entropy; if same, return the one in answers
            if (entropy > max_entropy) or (
                abs(entropy - max_entropy) < 1e-6
                and in_answers
                and not best_in_answers
            ):
                max_entropy = entropy
                best_guess = word
                best_in_answers = in_answers

        return best_guess

class LimitMinimax(Handler):
    """Maximize the minimum gain"""
    def guess(self):
        # Run minimax to find the best guess
        best_guess = None
        min_worst_case = float('inf')
        
        # Simulate all possible result scenarios for this guess
        for guess in ANSWERS:
            counts = [0] * (WIN_RESULT + 1)
            for word in self.answers_range:
                counts[get_result(guess, word)] += 1

            # Select the guess with the best worst-case outcome
            worst_case = max(counts)
            if worst_case < min_worst_case:
                min_worst_case = worst_case
                best_guess = guess
        
        return best_guess

class Minimax(Handler):
    def guess(self):
        candidates = self.answers_range if len(self.answers_range) <= 3 else ALLOWED
        answer_set = set(self.answers_range)

        best_guess = None
        min_worst_case = float("inf")
        best_in_answers = False

        for guess in candidates:
            counts = [0] * (WIN_RESULT + 1)
            for word in self.answers_range:
                counts[get_result(guess, word)] += 1

            worst_case = max(counts)
            in_answers = guess in answer_set

            if (worst_case < min_worst_case) or (
                worst_case == min_worst_case
                and in_answers
                and not best_in_answers
            ):
                min_worst_case = worst_case
                best_guess = guess
                best_in_answers = in_answers

        return best_guess

class Greedy(Handler):
    """Positional Frequency Frequency Heuristic Solver. Greedy for green positions as human"""
    def __init__(self):
        super().__init__()
        self.green_mask = 0 # Track the result of the green position

    def reset(self):
        super().reset()
        self.green_mask = 0
    
    def filter(self, guess, result):
        super().filter(guess, result)
        val = result
        for i in range(WORD_LENGTH):
            if val % 3 == 2:  # 2 for green
                self.green_mask |= 1 << i
            val //= 3

    def guess(self):
        pos_letter_freq = [Counter() for _ in range(WORD_LENGTH)]
        active_indices = [i for i in range(WORD_LENGTH) if not ((self.green_mask >> i) & 1)]

        for i in active_indices:
            for word in self.answers_range:
                pos_letter_freq[i][word[i]] += 1
                
        candidates = self.answers_range if len(self.answers_range) <= 3 else ALLOWED
        answer_set = set(self.answers_range)

        def score(word):
            seen = set()
            val = 0
            for i in active_indices:
                c = word[i]
                if c not in seen:
                    val += pos_letter_freq[i][word[i]]
                    seen.add(c)
            return (val, word in answer_set)

        return max(candidates, key=score)

class Binary(Handler):
    def guess(self):
        total_left = len(self.answers_range)
        if total_left <= 2:
            return self.answers_range[0]

        # 1. Document Frequency
        letter_doc_counts = [0] * 26
        for word in self.answers_range:
            for c in set(word):
                letter_doc_counts[ord(c) - 65] += 1

        # 2. Seperate in half, the closer to 50%, the higher score
        split_score = [0] * 26
        for i in range(26):
            count = letter_doc_counts[i]
            if 0 < count < total_left:
                split_score[i] = count * (total_left - count)

        candidates = self.answers_range if total_left <= 3 else ALLOWED
        answer_set = set(self.answers_range)

        # 3. Compute score for each candidate
        def score(word):
            unique_chars = set(word)
            val = sum(split_score[ord(c) - 65] for c in unique_chars)
            return (val, word in answer_set)

        return max(candidates, key=score)

class Fixed(Handler):
    """Select the word at a fixed position the word list"""
    def guess(self, pos=2):
        return self.answers_range[len(self.answers_range) // pos]


if __name__ == "__main__":
    from core.game import encode
    Solver = Bayesian   # Bayesian, Minimax, Greedy, Binary
    agent = Solver()

    print("Current solver:", agent)

    while True:
        attempt = 1
        while True:
            guess = agent.make_guess()
            print(f"Attempt {attempt}: {guess}")
            if guess is None:
                print("No words left matching criteria!")
                break

            # Result promot
            while True:
                input_result = input(
                    "Pls enter the result (5 digits, 0:gray, 1:yellow, 2:green): "
                ).strip()
                result_list = [int(ch) for ch in input_result if ch in "012"]
                if len(result_list) != WORD_LENGTH:
                    print(f"Invalid input {result_list}. Must be 5 digits (0, 1, or 2).")
                    continue
                break

            result = encode(result_list)
            if result == WIN_RESULT:
                print(f"Solved in {attempt} attempts!")
                break
            
            print(f"Result: {result_list}")
            agent.filter(guess, result)

            attempt += 1

        if input("Press Enter to play again... "):
            break
        agent.reset()
        print()
