from math import log2
from collections import defaultdict

from core.game import (
    ALLOWED, 
    ANSWERS, 
    WIN_RESULT, 
    get_result
)

ANSWERS_LEN = len(ANSWERS)

class Handler:
    """Basic algorithm to start the game and filter the words based on the feedback"""
    def __init__(self, opening = "SALET"):
        self.answers_range = ANSWERS.copy()
        self.opening = opening.upper()
    
    def __str__(self):
        return self.__class__.__name__
    
    def reset(self):
        self.answers_range = ANSWERS.copy()
    
    def filter(self, guess, result):
        # Filter the word based on the result
        self.answers_range = [w for w in self.answers_range if get_result(guess, w) == result]
    
    def make_guess(self):
        total = len(self.answers_range)
        if total == 0:
            return
        # If only 1-2 answers left, make a direct guess
        if total <= 2:
            return self.answers_range[0]
        if self.opening and total == ANSWERS_LEN:
            return self.opening

        return self.guess()


# --- Solvers ---

class NaiveEntropy(Handler):
    """Apply Bayesian search to find the word with highest entropy in the word list"""
    def guess(self):
        # Bayesian selection using precomputed entropy values
        return max(ALLOWED, key=self.compute_information_gain)
    
    def compute_information_gain(self, guess):
        counts = [0] * (WIN_RESULT + 1)
        for word in self.answers_range:
            counts[get_result(guess, word)] += 1

        total = len(self.answers_range)
        entropy = 0.0
        for c in counts:
            if c > 0:
                p = c / total
                entropy -= p * log2(p)
        return entropy


class Entropy(NaiveEntropy):
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


class BiasedEntropy(NaiveEntropy):
    """
    """
    WIN_WEIGHT = 0.1

    def guess(self):
        total = len(self.answers_range)
        candidates = self.answers_range if total <= 3 else ALLOWED
        answer_set = set(self.answers_range)

        best_guess = None
        max_score = -1.0
        best_in_answers = False

        for word in candidates:
            entropy = self.compute_information_gain(word)
            in_answers = word in answer_set
            p_win = (self.WIN_WEIGHT / total) if in_answers else 0.0
            score = entropy + p_win

            if score > max_score or (
                abs(score - max_score) < 1e-6
                and in_answers
                and not best_in_answers
            ):
                max_score = score
                best_guess = word
                best_in_answers = in_answers

        return best_guess


class LookaheadEntropy(NaiveEntropy):
    """
    Beam-Search accelerated Two-step lookahead solver.
    """
    LOOKAHEAD_THRESHOLD = 24
    BEAM_WIDTH = 20

    def guess(self):
        if len(self.answers_range) > self.LOOKAHEAD_THRESHOLD:
            return self._fast_one_step()
        return self._pruned_two_step()

    def _fast_one_step(self):
        answer_set = set(self.answers_range)
        best_guess = None
        max_entropy = -1.0
        best_in_answers = False

        for word in ALLOWED:
            entropy = self.compute_information_gain(word)
            in_answers = word in answer_set

            if (entropy > max_entropy) or (
                abs(entropy - max_entropy) < 1e-6
                and in_answers
                and not best_in_answers
            ):
                max_entropy = entropy
                best_guess = word
                best_in_answers = in_answers

        return best_guess

    def _pruned_two_step(self):
        total = len(self.answers_range)
        answer_set = set(self.answers_range)

        scored_allowed = []
        for word in ALLOWED:
            h = self.compute_information_gain(word)
            scored_allowed.append((h, word))
        scored_allowed.sort(reverse=True, key=lambda x: x[0])

        beam_candidates = set(self.answers_range)
        for _, word in scored_allowed[: self.BEAM_WIDTH]:
            beam_candidates.add(word)

        best_guess = None
        min_expected_cost = float("inf")
        best_in_answers = False

        for g1 in beam_candidates:
            partitions = defaultdict(list)
            for w in self.answers_range:
                partitions[get_result(g1, w)].append(w)

            total_steps = 0

            for pattern, sub_answers in partitions.items():
                size = len(sub_answers)

                if pattern == WIN_RESULT:
                    total_steps += 1
                elif size == 1:
                    total_steps += 2
                elif size == 2:
                    total_steps += 5    # 2 + 3
                else:
                    best_sub = float("inf")
                    for g2 in sub_answers:
                        sub_counts = defaultdict(int)
                        for sw in sub_answers:
                            sub_counts[get_result(g2, sw)] += 1

                        sub_steps = 0
                        for sub_pat, cnt in sub_counts.items():
                            if sub_pat == WIN_RESULT:
                                sub_steps += 2 * cnt
                            elif cnt == 1:
                                sub_steps += 3
                            elif cnt == 2:
                                sub_steps += 7  # 3 + 4
                            else:
                                sub_steps += (3 + cnt) * cnt

                        if sub_steps < best_sub:
                            best_sub = sub_steps

                    total_steps += best_sub

            expected_cost = total_steps / total
            in_answers = g1 in answer_set

            if (expected_cost < min_expected_cost) or (
                abs(expected_cost - min_expected_cost) < 1e-6
                and in_answers
                and not best_in_answers
            ):
                min_expected_cost = expected_cost
                best_guess = g1
                best_in_answers = in_answers

        return best_guess
    
class NaiveMinimax(Handler):
    """Maximize the minimum gain"""
    def guess(self):
        # Run minimax to find the best guess
        best_guess = None
        min_worst_case = float('inf')
        
        # Simulate all possible result scenarios for this guess
        for guess in ALLOWED:
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


class BinarySplit(Handler):
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


class FixedIndex(Handler):
    """Select the word at a fixed position the word list"""
    POS = 2

    def guess(self):
        return self.answers_range[len(self.answers_range) // self.POS]


if __name__ == "__main__":
    from core.game import WORD_LENGTH, encode

    Solver = BiasedEntropy
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
