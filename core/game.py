ALLOWED_PATH = "./dict/allowed.txt"
ANSWERS_PATH = "./dict/answers.txt"

def load_words():
    for path in (ALLOWED_PATH, ANSWERS_PATH):
        with open(path, "r") as f:
            yield [line.strip().upper() for line in f if line.strip()]

ALLOWED, ANSWERS = load_words()

WORD_LENGTH = len(ALLOWED[0])
MAX_ATTEMPTS = 6
WIN_RESULT = 242

def encode(r):
    # Compress to an int of base 3: r0 + r1*3 + r2*9 + r3*27 + r4*81
    return r[0] + r[1] * 3 + r[2] * 9 + r[3] * 27 + r[4] * 81

def decode(val):
    res = [0] * 5
    for i in range(5):
        res[i] = val % 3
        val //= 3
    return res

def get_result(guess, answer):
    # 0 = gray, 1 = yellow, 2 = green
    counts = [0] * 26
    r = [-1, -1, -1, -1, -1]

    # Green matching
    for i in range(5):
        g, a = guess[i], answer[i]
        if g == a:
            r[i] = 2
        else:
            counts[ord(a) - 65] += 1

    # Yellow matching
    for i in range(5):
        if r[i] == -1:
            idx = ord(guess[i]) - 65
            if counts[idx] > 0:
                r[i] = 1
                counts[idx] -= 1
            else:
                r[i] = 0

    return encode(r)


if __name__ == "__main__":
    import random

    EMOJI_MAP = ("⬜", "🟨", "🟩")
    ALLOWED_SET = set(ALLOWED)

    print(f"Welcome to Wordle!")

    while True:
        answer = random.choice(ANSWERS)  # Select a random word

        for attempt in range(1, MAX_ATTEMPTS + 1):
            while True:
                guess = input(f"Attempt {attempt}/{MAX_ATTEMPTS}: ").strip().upper()

                # Quit validation
                if guess in ('Q', 'QUIT', 'E', "EXIT"):
                    exit()
                # Input validation
                if len(guess) != WORD_LENGTH or guess not in ALLOWED_SET:
                    print(f"Invalid input {guess}")
                    continue
                break
            
            result = get_result(guess, answer)
            print(f"Result: {"".join([EMOJI_MAP[i] for i in result])}")

            if guess == answer:
                print("Congratulations! You guessed the word correctly!\n")
                break
        else:
            print(f"You ran out of attempts! The correct word was: {answer}\n")
