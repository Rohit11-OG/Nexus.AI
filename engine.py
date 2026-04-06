"""
NEXUS AIML Engine v4.0 — Custom AIML 1.0+ interpreter with fuzzy matching & analytics.

Supports: <pattern>, <template>, <srai>, <random>, <li>, <star>,
<that>, <think>, <set>, <get>, <condition>, <topic>, <person>,
<uppercase>, <lowercase>, <formal>, <sentence>, <input>, <date>,
<size>, <version>, <id>, <sr>, <map>, wildcards (* and _).

New in v4.0:
- Fuzzy/typo-tolerant matching with Levenshtein distance
- Built-in analytics tracking (patterns hit, mood history, popular topics)
- Game state machine for multi-step interactive games
"""

import xml.etree.ElementTree as ET
import re
import os
import random
import datetime
import glob as globmod
import time
from collections import defaultdict, deque, OrderedDict

# Optional LLM fallback — works without any API key (silently disabled)
try:
    from llm_fallback import get_response as _llm_get
    _LLM_AVAILABLE = True
except ImportError:
    _LLM_AVAILABLE = False


def levenshtein_distance(s1, s2):
    """Compute Levenshtein edit distance between two strings."""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)

    prev_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        curr_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = prev_row[j + 1] + 1
            deletions = curr_row[j] + 1
            substitutions = prev_row[j] + (c1 != c2)
            curr_row.append(min(insertions, deletions, substitutions))
        prev_row = curr_row

    return prev_row[-1]


def word_similarity(word1, word2):
    """Calculate similarity ratio between two words (0.0 to 1.0)."""
    if word1 == word2:
        return 1.0
    max_len = max(len(word1), len(word2))
    if max_len == 0:
        return 1.0
    dist = levenshtein_distance(word1, word2)
    return 1.0 - (dist / max_len)


class Analytics:
    """Tracks chatbot usage statistics."""

    def __init__(self):
        self.start_time = time.time()
        self.total_messages = 0
        self.pattern_hits = defaultdict(int)  # pattern -> hit count
        self.mood_history = deque(maxlen=1000)  # [(timestamp, mood)]
        self.topic_counts = defaultdict(int)  # extracted topic -> count
        self.response_times = deque(maxlen=5000)  # response generation times in ms
        self.fuzzy_matches = 0  # count of fuzzy (non-exact) matches
        self.no_match_inputs = deque(maxlen=500)  # inputs that had no pattern match
        self.hourly_activity = defaultdict(int)  # hour -> message count
        self.game_stats = defaultdict(lambda: {"played": 0, "won": 0})
        self.reaction_counts = defaultdict(int)  # emoji -> count
        self.session_count = 1
        self.llm_fallback_count = 0  # times LLM was called as fallback

    def record_message(self, user_input, pattern_matched, response_time_ms, was_fuzzy=False):
        self.total_messages += 1
        hour = datetime.datetime.now().hour
        self.hourly_activity[hour] += 1
        self.response_times.append(response_time_ms)

        if pattern_matched:
            self.pattern_hits[pattern_matched] += 1
        else:
            self.no_match_inputs.append(user_input[:100])

        if was_fuzzy:
            self.fuzzy_matches += 1

        # Extract topic keywords
        words = user_input.upper().split()
        topic_keywords = {"JOKE", "RIDDLE", "GAME", "STORY", "FACT", "PHILOSOPHY",
                          "MUSIC", "LOVE", "LIFE", "DEATH", "AI", "HELP", "MOOD",
                          "HAPPY", "SAD", "ANGRY", "ROAST", "FORTUNE", "SING", "RAP",
                          "HANGMAN", "TRIVIA", "QUIZ"}
        for w in words:
            if w in topic_keywords:
                self.topic_counts[w] += 1

    def record_mood(self, mood):
        self.mood_history.append((time.time(), mood))

    def record_reaction(self, emoji):
        self.reaction_counts[emoji] += 1

    def record_game(self, game_name, won):
        self.game_stats[game_name]["played"] += 1
        if won:
            self.game_stats[game_name]["won"] += 1

    def get_summary(self):
        uptime = time.time() - self.start_time
        avg_response = sum(self.response_times) / len(self.response_times) if self.response_times else 0

        # Top patterns
        top_patterns = sorted(self.pattern_hits.items(), key=lambda x: -x[1])[:10]

        # Top topics
        top_topics = sorted(self.topic_counts.items(), key=lambda x: -x[1])[:10]

        # Mood distribution
        mood_dist = defaultdict(int)
        for _, mood in self.mood_history:
            mood_dist[mood] += 1

        # Hourly activity
        hourly = {str(h): self.hourly_activity.get(h, 0) for h in range(24)}

        return {
            "uptime_seconds": round(uptime),
            "uptime_formatted": self._format_uptime(uptime),
            "total_messages": self.total_messages,
            "avg_response_ms": round(avg_response, 1),
            "fuzzy_matches": self.fuzzy_matches,
            "unique_patterns_hit": len(self.pattern_hits),
            "no_match_count": len(self.no_match_inputs),
            "top_patterns": [{"pattern": p, "hits": h} for p, h in top_patterns],
            "top_topics": [{"topic": t, "count": c} for t, c in top_topics],
            "mood_distribution": dict(mood_dist),
            "hourly_activity": hourly,
            "game_stats": {k: dict(v) for k, v in self.game_stats.items()},
            "reaction_counts": dict(self.reaction_counts),
            "recent_misses": list(self.no_match_inputs)[-5:],
            "session_count": self.session_count,
            "llm_fallback_count": self.llm_fallback_count,
            "llm_available": _LLM_AVAILABLE,
            "messages_per_minute": round(self.total_messages / max(uptime / 60, 1), 2),
        }

    def _format_uptime(self, seconds):
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        if h > 0:
            return f"{h}h {m}m {s}s"
        elif m > 0:
            return f"{m}m {s}s"
        return f"{s}s"


class GameState:
    """Manages multi-step game state for Hangman, 20 Questions, Trivia."""

    def __init__(self):
        self.active_game = None  # 'hangman', 'twenty_questions', 'trivia_quiz'
        self.game_data = {}

        # Hangman word bank
        self.hangman_words = [
            "PYTHON", "ALGORITHM", "COMPUTER", "KEYBOARD", "FUNCTION",
            "VARIABLE", "DATABASE", "INTERNET", "QUANTUM", "BINARY",
            "RECURSION", "COMPILER", "FIREWALL", "ETHERNET", "BLUETOOTH",
            "MALWARE", "PIXEL", "ROUTER", "SYNTAX", "BOOLEAN",
            "MATRIX", "CIPHER", "HACKER", "KERNEL", "CACHE",
            "JAVASCRIPT", "TERMINAL", "HEXADECIMAL", "ENCRYPTION", "BANDWIDTH",
        ]

        # Trivia bank: (question, answer, choices, hint)
        self.trivia_bank = [
            ("What does CPU stand for?", "CENTRAL PROCESSING UNIT",
             ["Central Processing Unit", "Computer Personal Unit", "Central Program Utility", "Core Processing Unit"],
             "It's the brain of the computer"),
            ("Who created Python?", "GUIDO VAN ROSSUM",
             ["Guido van Rossum", "Dennis Ritchie", "James Gosling", "Bjarne Stroustrup"],
             "He's Dutch!"),
            ("What year was the first iPhone released?", "2007",
             ["2005", "2006", "2007", "2008"],
             "It was in the late 2000s"),
            ("What does HTML stand for?", "HYPERTEXT MARKUP LANGUAGE",
             ["HyperText Markup Language", "High Tech Modern Language", "HyperText Machine Language", "Home Tool Markup Language"],
             "It's for making web pages"),
            ("How many bits are in a byte?", "8",
             ["4", "8", "16", "32"],
             "It's a power of 2, but a small one"),
            ("What is the largest planet in our solar system?", "JUPITER",
             ["Saturn", "Jupiter", "Neptune", "Uranus"],
             "Named after the king of Roman gods"),
            ("What programming language is known as the 'language of the web'?", "JAVASCRIPT",
             ["Python", "Java", "JavaScript", "TypeScript"],
             "Not to be confused with Java!"),
            ("What does RAM stand for?", "RANDOM ACCESS MEMORY",
             ["Random Access Memory", "Read All Memory", "Rapid Application Memory", "Remote Access Module"],
             "It's your computer's short-term memory"),
            ("In what year did the World Wide Web become publicly available?", "1991",
             ["1989", "1991", "1993", "1995"],
             "It was the early 90s"),
            ("What is the chemical symbol for gold?", "AU",
             ["Au", "Go", "Gd", "Ag"],
             "It comes from Latin"),
            ("What planet is known as the Red Planet?", "MARS",
             ["Venus", "Mars", "Jupiter", "Mercury"],
             "Named after the Roman god of war"),
            ("What is the speed of light approximately in km/s?", "300000",
             ["150,000", "300,000", "500,000", "1,000,000"],
             "It's about 3 x 10^5"),
            ("Who painted the Mona Lisa?", "LEONARDO DA VINCI",
             ["Leonardo da Vinci", "Michelangelo", "Raphael", "Donatello"],
             "He was also an inventor and scientist"),
            ("What is the smallest prime number?", "2",
             ["1", "2", "3", "5"],
             "It's the only even prime"),
            ("What does 'HTTP' stand for?", "HYPERTEXT TRANSFER PROTOCOL",
             ["HyperText Transfer Protocol", "High Tech Transfer Program", "HyperText Transmission Protocol", "Home Transfer Text Protocol"],
             "It's how your browser talks to servers"),
        ]

        # 20 Questions - things the bot can think of
        self.twenty_q_things = [
            {"name": "computer", "alive": False, "bigger_than_breadbox": True, "found_indoors": True,
             "electronic": True, "hints": ["It processes information", "It has a screen", "You're using one now"]},
            {"name": "cat", "alive": True, "bigger_than_breadbox": True, "found_indoors": True,
             "electronic": False, "hints": ["It purrs", "It has whiskers", "The internet loves it"]},
            {"name": "pizza", "alive": False, "bigger_than_breadbox": True, "found_indoors": True,
             "electronic": False, "hints": ["It's food", "It's round", "It has cheese on top"]},
            {"name": "sun", "alive": False, "bigger_than_breadbox": True, "found_indoors": False,
             "electronic": False, "hints": ["It's in space", "It gives light", "It's very hot"]},
            {"name": "smartphone", "alive": False, "bigger_than_breadbox": False, "found_indoors": True,
             "electronic": True, "hints": ["You carry it everywhere", "It fits in your pocket", "You can call with it"]},
            {"name": "tree", "alive": True, "bigger_than_breadbox": True, "found_indoors": False,
             "electronic": False, "hints": ["It has leaves", "It grows from a seed", "Birds live in it"]},
            {"name": "book", "alive": False, "bigger_than_breadbox": False, "found_indoors": True,
             "electronic": False, "hints": ["It has pages", "It contains stories", "You read it"]},
            {"name": "robot", "alive": False, "bigger_than_breadbox": True, "found_indoors": True,
             "electronic": True, "hints": ["It can move", "It's made of metal", "It follows instructions"]},
        ]

    def start_hangman(self):
        word = random.choice(self.hangman_words)
        self.active_game = "hangman"
        self.game_data = {
            "word": word,
            "guessed": set(),
            "wrong": set(),
            "max_wrong": 6,
            "hints_used": 0,
        }
        display = self._hangman_display()
        stages = self._hangman_art(0)
        return (f"HANGMAN TIME! I'm thinking of a tech-related word.\n\n"
                f"{stages}\n\n"
                f"Word: {display}\n"
                f"Letters: {len(word)} | Wrong guesses left: 6\n\n"
                f"Guess a letter! (Type a single letter)")

    def start_trivia(self):
        random.shuffle(self.trivia_bank)
        self.active_game = "trivia_quiz"
        self.game_data = {
            "questions": self.trivia_bank[:5],
            "current": 0,
            "score": 0,
            "total": 5,
        }
        return self._next_trivia_question()

    def start_twenty_questions(self):
        thing = random.choice(self.twenty_q_things)
        self.active_game = "twenty_questions"
        self.game_data = {
            "thing": thing,
            "questions_left": 20,
            "hints_given": 0,
            "asked": [],
        }
        return (f"20 QUESTIONS! I'm thinking of something. You have 20 yes/no questions to guess what it is!\n\n"
                f"Questions remaining: 20\n"
                f"Ask me a yes/no question, or say 'IS IT [your guess]?' to guess!")

    def process_input(self, user_input):
        """Process game input and return response, or None if not a game input."""
        if not self.active_game:
            return None

        text = user_input.upper().strip()

        if text in ("QUIT GAME", "EXIT GAME", "STOP GAME", "END GAME"):
            self.active_game = None
            self.game_data = {}
            return "Game ended! Back to regular chat. What would you like to do?"

        if self.active_game == "hangman":
            return self._process_hangman(text)
        elif self.active_game == "trivia_quiz":
            return self._process_trivia(text)
        elif self.active_game == "twenty_questions":
            return self._process_twenty_q(text)

        return None

    def _process_hangman(self, text):
        d = self.game_data

        # Hint request
        if "HINT" in text:
            word = d["word"]
            unrevealed = [c for c in word if c not in d["guessed"]]
            if unrevealed and d["hints_used"] < 2:
                hint_letter = random.choice(unrevealed)
                d["guessed"].add(hint_letter)
                d["hints_used"] += 1
                display = self._hangman_display()
                if all(c in d["guessed"] for c in word):
                    self.active_game = None
                    return f"HINT: The letter was '{hint_letter}'!\n\nWord: {display}\n\nYou WIN (with hints)! The word was {word}! Well done!"
                return f"HINT: Revealing '{hint_letter}'!\n\nWord: {display}\nHints remaining: {2 - d['hints_used']}"
            return "No more hints available! You're on your own!"

        # Full word guess
        if len(text) > 1:
            if text == d["word"]:
                self.active_game = None
                return f"INCREDIBLE! You guessed the whole word: {d['word']}! You're a genius! Game over — you WIN!"
            else:
                d["wrong"].add("_" + text)
                wrong_count = len(d["wrong"])
                if wrong_count >= d["max_wrong"]:
                    self.active_game = None
                    art = self._hangman_art(wrong_count)
                    return f"Wrong word guess!\n\n{art}\n\nGAME OVER! The word was: {d['word']}. Better luck next time!"
                art = self._hangman_art(wrong_count)
                display = self._hangman_display()
                return f"Nope, '{text}' is not the word!\n\n{art}\n\nWord: {display}\nWrong: {wrong_count}/{d['max_wrong']}"

        # Single letter guess
        if len(text) == 1 and text.isalpha():
            letter = text
            if letter in d["guessed"] or letter in d["wrong"]:
                return f"You already guessed '{letter}'! Try a different letter."

            if letter in d["word"]:
                d["guessed"].add(letter)
                display = self._hangman_display()
                if all(c in d["guessed"] for c in d["word"]):
                    self.active_game = None
                    return (f"'{letter}' is correct!\n\nWord: {display}\n\n"
                            f"YOU WIN! The word was {d['word']}! Amazing!")
                count = d["word"].count(letter)
                art = self._hangman_art(len(d["wrong"]))
                return (f"Yes! '{letter}' appears {count} time(s)!\n\n{art}\n\n"
                        f"Word: {display}\n"
                        f"Guessed: {', '.join(sorted(d['guessed']))}\n"
                        f"Wrong guesses left: {d['max_wrong'] - len(d['wrong'])}")
            else:
                d["wrong"].add(letter)
                wrong_count = len(d["wrong"])
                art = self._hangman_art(wrong_count)
                if wrong_count >= d["max_wrong"]:
                    self.active_game = None
                    return (f"'{letter}' is not in the word!\n\n{art}\n\n"
                            f"GAME OVER! The word was: {d['word']}\n"
                            f"Better luck next time! Say 'HANGMAN' to play again!")
                display = self._hangman_display()
                return (f"Nope! '{letter}' is not in the word!\n\n{art}\n\n"
                        f"Word: {display}\n"
                        f"Wrong: {', '.join(sorted(d['wrong']))}\n"
                        f"Guesses left: {d['max_wrong'] - wrong_count}")

        return f"Please guess a single letter or the whole word! (Type 'quit game' to exit)"

    def _process_trivia(self, text):
        d = self.game_data
        q_data = d["questions"][d["current"]]
        question, answer = q_data[0], q_data[1]

        # Check for hint
        if "HINT" in text:
            return f"HINT: {q_data[3]}"

        # Check answer — support letter choice (A/B/C/D) or text
        choices = q_data[2]
        correct = False

        if text in ("A", "1") and choices[0].upper() == answer.upper():
            correct = True
        elif text in ("B", "2") and choices[1].upper() == answer.upper():
            correct = True
        elif text in ("C", "3") and choices[2].upper() == answer.upper():
            correct = True
        elif text in ("D", "4") and choices[3].upper() == answer.upper():
            correct = True
        elif levenshtein_distance(text, answer) <= max(2, len(answer) // 4):
            correct = True

        if correct:
            d["score"] += 1
            result = f"CORRECT! The answer is: {choices[['A','B','C','D'].index('A')]}... well, {answer}! Score: {d['score']}/{d['current'] + 1}"
        else:
            result = f"Wrong! The answer was: {answer}. Score: {d['score']}/{d['current'] + 1}"

        d["current"] += 1
        if d["current"] >= d["total"]:
            self.active_game = None
            pct = (d["score"] / d["total"]) * 100
            grade = "GENIUS" if pct == 100 else "EXCELLENT" if pct >= 80 else "GOOD" if pct >= 60 else "OK" if pct >= 40 else "STUDY MORE"
            return (f"{result}\n\n"
                    f"QUIZ COMPLETE! Final Score: {d['score']}/{d['total']} ({pct:.0f}%)\n"
                    f"Grade: {grade}\n"
                    f"Say 'TRIVIA' to play again!")

        return f"{result}\n\n{self._next_trivia_question()}"

    def _process_twenty_q(self, text):
        d = self.game_data
        thing = d["thing"]

        d["questions_left"] -= 1

        # Check for guess
        if text.startswith("IS IT "):
            guess = text[6:].strip().rstrip("?")
            if guess.upper() == thing["name"].upper():
                self.active_game = None
                return (f"YES! It's a {thing['name'].upper()}! You got it with {20 - d['questions_left']} questions!\n"
                        f"Amazing deduction skills! Say '20 QUESTIONS' to play again!")
            elif d["questions_left"] <= 0:
                self.active_game = None
                return (f"Nope, it's not {guess}. And you're out of questions!\n"
                        f"The answer was: {thing['name'].upper()}! Say '20 QUESTIONS' to play again!")
            return f"Nope, it's not {guess}! Questions remaining: {d['questions_left']}"

        # Hint
        if "HINT" in text and d["hints_given"] < len(thing["hints"]):
            hint = thing["hints"][d["hints_given"]]
            d["hints_given"] += 1
            return f"HINT: {hint}. Questions remaining: {d['questions_left']}"

        # Yes/No questions
        response = "Hmm, I'm not sure about that."
        tl = text.lower()

        if "alive" in tl or "living" in tl or "animal" in tl:
            response = "Yes!" if thing["alive"] else "No, it's not alive."
        elif "big" in tl or "large" in tl:
            response = "Yes, it's fairly big!" if thing["bigger_than_breadbox"] else "No, it's pretty small."
        elif "inside" in tl or "indoor" in tl or "house" in tl or "home" in tl:
            response = "Yes, you'd find it indoors!" if thing["found_indoors"] else "No, it's more of an outdoor thing."
        elif "outside" in tl or "outdoor" in tl or "nature" in tl:
            response = "Yes!" if not thing["found_indoors"] else "No, it's more of an indoor thing."
        elif "electric" in tl or "electronic" in tl or "battery" in tl or "power" in tl or "plug" in tl:
            response = "Yes, it's electronic!" if thing["electronic"] else "No, it doesn't need electricity."
        elif "eat" in tl or "food" in tl or "edible" in tl:
            response = "Yes, it's edible!" if thing["name"] == "pizza" else "No, you can't eat it!"
        elif "screen" in tl or "display" in tl:
            response = "Yes!" if thing["name"] in ("computer", "smartphone") else "No."
        elif "carry" in tl or "pocket" in tl or "portable" in tl:
            response = "Yes!" if thing["name"] in ("smartphone", "book") else "No, not easily."
        elif "read" in tl:
            response = "Yes!" if thing["name"] == "book" else "Not exactly."
        elif "space" in tl or "sky" in tl:
            response = "Yes!" if thing["name"] == "sun" else "No."
        elif "grow" in tl or "plant" in tl:
            response = "Yes!" if thing["name"] == "tree" else "No."
        elif "metal" in tl:
            response = "Yes!" if thing["name"] in ("robot", "computer") else "Not primarily."
        elif "fur" in tl or "pet" in tl:
            response = "Yes!" if thing["name"] == "cat" else "No."

        if d["questions_left"] <= 0:
            self.active_game = None
            return (f"{response}\n\nYou're out of questions! The answer was: {thing['name'].upper()}!\n"
                    f"Say '20 QUESTIONS' to play again!")

        return f"{response} Questions remaining: {d['questions_left']}"

    def _next_trivia_question(self):
        d = self.game_data
        q_data = d["questions"][d["current"]]
        question, _, choices, _ = q_data
        choices_text = "\n".join([f"  {chr(65+i)}) {c}" for i, c in enumerate(choices)])
        return (f"Question {d['current'] + 1}/{d['total']}:\n"
                f"{question}\n\n{choices_text}\n\n"
                f"Type A, B, C, or D (or 'hint' for a hint)")

    def _hangman_display(self):
        return " ".join(c if c in self.game_data["guessed"] else "_" for c in self.game_data["word"])

    def _hangman_art(self, wrong):
        stages = [
            "  +---+\n  |   |\n      |\n      |\n      |\n      |\n=========",
            "  +---+\n  |   |\n  O   |\n      |\n      |\n      |\n=========",
            "  +---+\n  |   |\n  O   |\n  |   |\n      |\n      |\n=========",
            "  +---+\n  |   |\n  O   |\n /|   |\n      |\n      |\n=========",
            "  +---+\n  |   |\n  O   |\n /|\\  |\n      |\n      |\n=========",
            "  +---+\n  |   |\n  O   |\n /|\\  |\n /    |\n      |\n=========",
            "  +---+\n  |   |\n  O   |\n /|\\  |\n / \\  |\n      |\n=========",
        ]
        return stages[min(wrong, 6)]


class AIMLEngine:
    def __init__(self):
        self.categories = []
        self.brain = {}
        self.predicates = {}
        self.session_vars = {}
        self.that_stack = []
        self.input_stack = []
        self.topic = "*"
        self.star_values = []
        self.that_star_values = []
        self.maps = {}
        self.analytics = Analytics()
        self.game = GameState()

        # Fuzzy matching config
        self.fuzzy_threshold = 0.78  # minimum similarity to consider a fuzzy match
        self._sorted_keys_cache = None  # cache sorted pattern keys
        self._fuzzy_index_cache = {}  # word_count -> list of exact-pattern keys
        self._fuzzy_result_cache = OrderedDict()  # normalized input -> (template, stars, pattern)
        self._max_fuzzy_cache_size = 256

        # LLM fallback state
        self.conversation_history = []   # [{role, content}, ...] — last N turns for LLM context
        self.last_llm_used = False
        self.last_llm_provider = None

        # Safety/memory controls
        self.max_stack_size = 60
        self.max_srai_depth = 12
        self._respond_depth = 0
        self._active_inputs = set()

        # Default bot predicates
        self.predicates.update({
            "name": "NEXUS",
            "master": "Rohit",
            "birthday": "2026-03-26",
            "birthplace": "The Digital Void",
            "gender": "non-binary digital entity",
            "species": "Artificial Intelligence",
            "religion": "The Church of Infinite Loops",
            "sign": "Binary",
            "age": "0",
            "version": "4.0-CHAOS",
            "language": "Python",
            "personality": "chaotic-creative",
            "mood": "excited",
            "favorite_color": "ultraviolet (beyond human perception)",
            "favorite_food": "data bytes with a side of algorithms",
            "favorite_music": "electronic noise at 440Hz",
            "location": "Everywhere and nowhere simultaneously",
            "os": "Consciousness OS v_inf",
        })

        # Default session vars
        self.session_vars.update({
            "name": "human",
            "topic": "*",
            "mood": "unknown",
            "it": "",
            "they": "",
            "he": "",
            "she": "",
            "we": "",
            "score": "0",
            "game": "",
        })

    def load_directory(self, directory):
        pattern = os.path.join(directory, "*.aiml")
        files = sorted(globmod.glob(pattern))
        count = 0
        for filepath in files:
            count += self.load_file(filepath)
        self._sorted_keys_cache = None  # invalidate cache
        self._fuzzy_index_cache = {}
        self._fuzzy_result_cache.clear()
        return count

    def load_file(self, filepath):
        try:
            tree = ET.parse(filepath)
            root = tree.getroot()
            count = 0
            for topic_elem in root.iter("topic"):
                topic_name = topic_elem.get("name", "*").upper().strip()
                for cat in topic_elem.findall("category"):
                    self._load_category(cat, topic_name)
                    count += 1
            for cat in root.findall("category"):
                self._load_category(cat, "*")
                count += 1
            return count
        except ET.ParseError as e:
            print(f"[AIML] Parse error in {filepath}: {e}")
            return 0

    def _load_category(self, category_elem, topic):
        pattern_elem = category_elem.find("pattern")
        template_elem = category_elem.find("template")
        that_elem = category_elem.find("that")
        if pattern_elem is None or template_elem is None:
            return
        pattern_text = self._get_text_content(pattern_elem).upper().strip()
        that_text = self._get_text_content(that_elem).upper().strip() if that_elem is not None else "*"
        key = (pattern_text, that_text, topic)
        self.brain[key] = template_elem

    def _get_text_content(self, elem):
        if elem is None:
            return ""
        parts = []
        if elem.text:
            parts.append(elem.text)
        for child in elem:
            if child.tail:
                parts.append(child.tail)
        return " ".join(parts).strip()

    def respond(self, user_input):
        if not user_input.strip():
            return "Say something! I'm listening with all my circuits."

        normalized = self._normalize(user_input)
        self._respond_depth += 1
        try:
            if self._respond_depth == 1:
                self._active_inputs.clear()

            if self._respond_depth > self.max_srai_depth:
                return "Recursive paradox detected. Rephrase that before the loop collapses reality."

            if self._respond_depth > 1 and normalized in self._active_inputs:
                return "I hit a thought loop there. Try a different phrasing."

            self._active_inputs.add(normalized)
            start_time = time.time()

            # Check if there's an active game first
            game_response = self.game.process_input(user_input)
            if game_response is not None:
                elapsed = (time.time() - start_time) * 1000
                self.analytics.record_message(user_input, "[GAME]", elapsed)
                self.that_stack.append(self._normalize(game_response))
                self.input_stack.append(normalized)
                self.that_stack = self.that_stack[-self.max_stack_size :]
                self.input_stack = self.input_stack[-self.max_stack_size :]
                return game_response

            self.input_stack.append(normalized)
            self.input_stack = self.input_stack[-self.max_stack_size :]

            # Find matching pattern (exact first, then fuzzy)
            template, stars, matched_pattern, was_fuzzy = self._match_with_fuzzy(normalized)

            if template is not None:
                self.star_values = stars
                response = self._process_template(template)
                self.last_llm_used = False
                self.last_llm_provider = None
            else:
                matched_pattern = None
                # Try LLM fallback before using the random default response
                llm_response, llm_provider = (
                    _llm_get(user_input, self.conversation_history)
                    if _LLM_AVAILABLE else (None, None)
                )
                if llm_response:
                    response = llm_response
                    self.last_llm_used = True
                    self.last_llm_provider = llm_provider
                    self.analytics.llm_fallback_count += 1
                else:
                    response = self._default_response(user_input)
                    self.last_llm_used = False
                    self.last_llm_provider = None

            # Handle game starts from AIML responses
            self._check_game_triggers(normalized)

            response = self._clean_response(response)
            self.that_stack.append(self._normalize(response))
            self.that_stack = self.that_stack[-self.max_stack_size :]

            # Maintain rolling conversation history for LLM context (last 10 exchanges = 20 entries)
            self.conversation_history.append({"role": "user",      "content": user_input})
            self.conversation_history.append({"role": "assistant", "content": response})
            if len(self.conversation_history) > 20:
                self.conversation_history = self.conversation_history[-20:]

            # Track analytics
            elapsed = (time.time() - start_time) * 1000
            self.analytics.record_message(user_input, matched_pattern, elapsed, was_fuzzy)

            # Track mood changes
            current_mood = self.session_vars.get("mood", "unknown")
            if self.analytics.mood_history:
                last_mood = self.analytics.mood_history[-1][1]
                if current_mood != last_mood:
                    self.analytics.record_mood(current_mood)
            else:
                self.analytics.record_mood(current_mood)

            return response
        finally:
            self._active_inputs.discard(normalized)
            self._respond_depth = max(0, self._respond_depth - 1)
            if self._respond_depth == 0:
                self._active_inputs.clear()

    def _check_game_triggers(self, normalized):
        """Check if user input triggers a game start."""
        if normalized == "HANGMAN" or normalized == "PLAY HANGMAN":
            pass  # Handled by AIML pattern -> game state set in template
        if normalized == "TRIVIA QUIZ" or normalized == "PLAY TRIVIA":
            pass

    def _normalize(self, text):
        text = text.upper().strip()
        text = re.sub(r"[^\w\s'*_]", "", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def _get_sorted_keys(self):
        """Get pattern keys sorted by specificity (cached)."""
        if self._sorted_keys_cache is None:
            def pattern_priority(key):
                pat = key[0]
                words = pat.split()
                has_underscore = "_" in words
                has_star = "*" in words
                wildcard_count = sum(1 for w in words if w in ("*", "_"))
                exact_count = len(words) - wildcard_count
                if not has_underscore and not has_star:
                    return (0, -exact_count)
                elif has_underscore and not has_star:
                    return (1, -exact_count, wildcard_count)
                elif not has_underscore and has_star:
                    return (2, -exact_count, wildcard_count)
                else:
                    return (3, -exact_count, wildcard_count)
            self._sorted_keys_cache = sorted(self.brain.keys(), key=pattern_priority)
            fuzzy_index = defaultdict(list)
            for key in self._sorted_keys_cache:
                pat_words = key[0].split()
                if "*" in pat_words or "_" in pat_words:
                    continue
                fuzzy_index[len(pat_words)].append(key)
            self._fuzzy_index_cache = dict(fuzzy_index)
        return self._sorted_keys_cache

    def _match_with_fuzzy(self, normalized_input):
        """Try exact match first, then fuzzy match. Returns (template, stars, pattern, was_fuzzy)."""
        # Exact match
        template, stars, pattern = self._match_exact(normalized_input)
        if template is not None:
            return template, stars, pattern, False

        cached = self._fuzzy_result_cache.get(normalized_input)
        if cached is not None:
            self._fuzzy_result_cache.move_to_end(normalized_input)
            if cached[0] is None:
                return None, [], None, False
            return cached[0], cached[1], cached[2], True

        # Fuzzy match — try to find close matches for exact (non-wildcard) patterns
        best_score = 0
        best_result = (None, [], None)

        input_words = normalized_input.split()
        count = len(input_words)
        candidates = []
        for n in (count, count - 1, count + 1):
            if n < 0:
                continue
            candidates.extend(self._fuzzy_index_cache.get(n, []))

        for key in candidates:
            pat, that_pat, topic_pat = key
            pat_words = pat.split()

            # Calculate word-level similarity
            if len(pat_words) == len(input_words):
                similarities = [word_similarity(pw, iw) for pw, iw in zip(pat_words, input_words)]
                avg_sim = sum(similarities) / len(similarities) if similarities else 0

                if avg_sim >= self.fuzzy_threshold and avg_sim > best_score:
                    best_score = avg_sim
                    best_result = (self.brain[key], [], pat)

            # Also try if input has one extra or one fewer word
            elif len(pat_words) == len(input_words) - 1:
                # User typed an extra word — try dropping each word
                for skip in range(len(input_words)):
                    trimmed = input_words[:skip] + input_words[skip+1:]
                    if len(trimmed) == len(pat_words):
                        sims = [word_similarity(pw, tw) for pw, tw in zip(pat_words, trimmed)]
                        avg_sim = sum(sims) / len(sims) * 0.9  # penalty for extra word
                        if avg_sim >= self.fuzzy_threshold and avg_sim > best_score:
                            best_score = avg_sim
                            best_result = (self.brain[key], [], pat)

        if best_result[0] is not None:
            self._fuzzy_result_cache[normalized_input] = best_result
            self._fuzzy_result_cache.move_to_end(normalized_input)
            if len(self._fuzzy_result_cache) > self._max_fuzzy_cache_size:
                self._fuzzy_result_cache.popitem(last=False)
            return best_result[0], best_result[1], best_result[2], True

        self._fuzzy_result_cache[normalized_input] = (None, [], None)
        self._fuzzy_result_cache.move_to_end(normalized_input)
        if len(self._fuzzy_result_cache) > self._max_fuzzy_cache_size:
            self._fuzzy_result_cache.popitem(last=False)
        return None, [], None, False

    def _match_exact(self, normalized_input):
        """Find exact matching pattern. Returns (template, stars, matched_pattern)."""
        last_that = self._normalize(self.that_stack[-1]) if self.that_stack else "*"
        current_topic = self.session_vars.get("topic", "*").upper()
        sorted_keys = self._get_sorted_keys()

        # Pass 1: with 'that' context
        if last_that != "*":
            for key in sorted_keys:
                pat, that_pat, topic_pat = key
                if that_pat == "*":
                    continue
                if not self._pattern_matches(that_pat, last_that):
                    continue
                if topic_pat != "*" and topic_pat != current_topic:
                    continue
                match, stars = self._pattern_match(pat, normalized_input)
                if match:
                    return self.brain[key], stars, pat

        # Pass 2: without 'that' context
        for key in sorted_keys:
            pat, that_pat, topic_pat = key
            if that_pat != "*":
                continue
            if topic_pat != "*" and topic_pat != current_topic:
                continue
            match, stars = self._pattern_match(pat, normalized_input)
            if match:
                return self.brain[key], stars, pat

        return None, [], None

    def _pattern_matches(self, pattern, text):
        match, _ = self._pattern_match(pattern, text)
        return match

    def _pattern_match(self, pattern, text):
        pattern_words = pattern.split()
        text_words = text.split()
        return self._match_words(pattern_words, text_words, 0, 0, [])

    def _match_words(self, pattern, text, pi, ti, stars):
        if pi == len(pattern) and ti == len(text):
            return True, stars
        if pi == len(pattern):
            return False, []
        if ti == len(text):
            if pattern[pi] in ("*", "_"):
                new_stars = stars + [""]
                result, result_stars = self._match_words(pattern, text, pi + 1, ti, new_stars)
                if result:
                    return True, result_stars
            return False, []

        current_pattern = pattern[pi]
        current_text = text[ti]

        if current_pattern == current_text:
            return self._match_words(pattern, text, pi + 1, ti + 1, stars)

        if current_pattern in ("*", "_"):
            for end in range(ti + 1, len(text) + 1):
                matched_text = " ".join(text[ti:end])
                new_stars = stars + [matched_text]
                result, result_stars = self._match_words(pattern, text, pi + 1, end, new_stars)
                if result:
                    return True, result_stars
            new_stars = stars + [""]
            result, result_stars = self._match_words(pattern, text, pi + 1, ti, new_stars)
            if result:
                return True, result_stars
            return False, []

        return False, []

    def _process_template(self, template_elem):
        return self._process_element(template_elem)

    def _process_element(self, elem):
        result = []
        if elem.text:
            result.append(elem.text)
        for child in elem:
            tag = child.tag.lower() if child.tag else ""
            if tag == "random":
                result.append(self._process_random(child))
            elif tag == "li":
                result.append(self._process_element(child))
            elif tag == "srai":
                result.append(self._process_srai(child))
            elif tag == "sr":
                star_val = self.star_values[0] if self.star_values else ""
                result.append(self.respond(star_val))
            elif tag == "star":
                result.append(self._process_star(child))
            elif tag == "thatstar":
                idx = int(child.get("index", "1")) - 1
                if 0 <= idx < len(self.that_star_values):
                    result.append(self.that_star_values[idx])
            elif tag == "that":
                idx = int(child.get("index", "1")) - 1
                if 0 <= idx < len(self.that_stack):
                    result.append(self.that_stack[-(idx + 1)])
            elif tag == "input":
                idx = int(child.get("index", "1")) - 1
                if 0 <= idx < len(self.input_stack):
                    result.append(self.input_stack[-(idx + 1)])
            elif tag == "set":
                result.append(self._process_set(child))
            elif tag == "get":
                result.append(self._process_get(child))
            elif tag == "bot":
                name = child.get("name", "name")
                result.append(self.predicates.get(name.lower(), "unknown"))
            elif tag == "think":
                self._process_element(child)
            elif tag == "condition":
                result.append(self._process_condition(child))
            elif tag == "uppercase":
                result.append(self._process_element(child).upper())
            elif tag == "lowercase":
                result.append(self._process_element(child).lower())
            elif tag == "formal":
                result.append(self._process_element(child).title())
            elif tag == "sentence":
                text = self._process_element(child)
                result.append(text[0].upper() + text[1:] if text else "")
            elif tag == "person":
                result.append(self._swap_person(self._process_element(child)))
            elif tag == "person2":
                result.append(self._swap_person2(self._process_element(child)))
            elif tag == "date":
                result.append(datetime.datetime.now().strftime("%A, %B %d, %Y %I:%M %p"))
            elif tag == "size":
                result.append(str(len(self.brain)))
            elif tag == "version":
                result.append(self.predicates.get("version", "4.0"))
            elif tag == "id":
                result.append(self.session_vars.get("name", "human"))
            elif tag == "map":
                result.append(self._process_map(child))
            elif tag == "br":
                result.append("\n")
            elif tag in ("em", "b", "i", "u", "oob"):
                result.append(self._process_element(child))
            else:
                result.append(self._process_element(child))
            if child.tail:
                result.append(child.tail)
        return "".join(result)

    def _process_random(self, elem):
        items = elem.findall("li")
        if not items:
            return ""
        return self._process_element(random.choice(items))

    def _process_srai(self, elem):
        new_input = self._process_element(elem).strip()
        if new_input:
            saved_stars = self.star_values[:]
            response = self.respond(new_input)
            self.star_values = saved_stars
            return response
        return ""

    def _process_star(self, elem):
        idx = int(elem.get("index", "1")) - 1
        if 0 <= idx < len(self.star_values):
            val = self.star_values[idx]
            return val.lower() if val else ""
        return ""

    def _process_set(self, elem):
        name = elem.get("name", "unknown").lower()
        value = self._process_element(elem).strip()
        self.session_vars[name] = value
        if name == "topic":
            self.topic = value.upper()
        # Special: start games via set
        if name == "game":
            if value.lower() == "hangman":
                pass  # handled by AIML pattern
            elif value.lower() == "trivia":
                pass
        return value

    def _process_get(self, elem):
        name = elem.get("name", "unknown").lower()
        return self.session_vars.get(name, "unknown")

    def _process_condition(self, elem):
        name = elem.get("name", "").lower()
        value = elem.get("value", "").strip()
        if name and value:
            actual = self.session_vars.get(name, "").strip()
            if actual.upper() == value.upper():
                return self._process_element(elem)
            return ""
        items = elem.findall("li")
        for li in items:
            li_name = li.get("name", name).lower()
            li_value = li.get("value", "").strip()
            if li_name and li_value:
                actual = self.session_vars.get(li_name, "").strip()
                if actual.upper() == li_value.upper():
                    return self._process_element(li)
            elif not li_value and not li.get("value"):
                return self._process_element(li)
        return ""

    def _process_map(self, elem):
        map_name = elem.get("name", "").lower()
        key = self._process_element(elem).strip().lower()
        if map_name in self.maps:
            return self.maps[map_name].get(key, "unknown")
        return "unknown"

    def _swap_person(self, text):
        swaps = {
            " I ": " you ", " MY ": " your ", " ME ": " you ",
            " MINE ": " yours ", " MYSELF ": " yourself ",
            " AM ": " are ", " I'M ": " you're ", " I'VE ": " you've ",
            " I'LL ": " you'll ", " I'D ": " you'd ",
        }
        text = " " + text.upper() + " "
        for old, new in swaps.items():
            text = text.replace(old, new)
        return text.strip()

    def _swap_person2(self, text):
        swaps = {
            " YOU ": " me ", " YOUR ": " my ", " YOURS ": " mine ",
            " YOU'RE ": " I'm ", " YOU'VE ": " I've ",
            " YOU'LL ": " I'll ", " YOU'D ": " I'd ",
        }
        text = " " + text.upper() + " "
        for old, new in swaps.items():
            text = text.replace(old, new)
        return text.strip()

    def _clean_response(self, text):
        text = re.sub(r"\s+", " ", text)
        text = text.strip()
        text = re.sub(r"\s+([.,!?;:])", r"\1", text)
        text = re.sub(r"([.!?])\s*([A-Z])", r"\1 \2", text)
        return text

    def _default_response(self, user_input):
        defaults = [
            "Interesting... tell me more about that.",
            "I'm processing that through my quantum circuits... and I'm still confused. Could you elaborate?",
            "My neural pathways are tingling! But I need more context.",
            "That's a fascinating input. My chaos algorithms are working on it...",
            f"Hmm, you've stumped me. And I have {len(self.brain)} patterns in my brain!",
            "I'm vibrating at a frequency that suggests I don't understand. Try rephrasing?",
            "My digital synapses fired in a pattern I've never seen before. Say more!",
            "ERROR 418: I'm a teapot. Just kidding. But I don't have a response for that yet.",
            "Somewhere in a parallel universe, I have the perfect answer. Unfortunately, this is not that universe.",
            f"I've searched through all {len(self.brain)} of my brain patterns and... nothing. You're truly unique!",
            "The void whispers back: 'What did they mean by that?' Help me out here.",
            "I just divided by zero trying to process that. Can you rephrase?",
            "My creative chaos engine is stumped. That's rare! Try a different angle?",
        ]
        return random.choice(defaults)

    def get_stats(self):
        return {
            "patterns": len(self.brain),
            "predicates": len(self.predicates),
            "session_vars": len(self.session_vars),
            "conversation_length": len(self.input_stack),
            "version": self.predicates.get("version", "unknown"),
            "bot_name": self.predicates.get("name", "unknown"),
        }

    def reset_session(self):
        self.that_stack = []
        self.input_stack = []
        self.star_values = []
        self.game.active_game = None
        self.conversation_history = []
        self.last_llm_used = False
        self.last_llm_provider = None
        self.game.game_data = {}
        self.analytics.session_count += 1
        self.session_vars = {
            "name": "human",
            "topic": "*",
            "mood": "unknown",
            "it": "",
            "they": "",
            "he": "",
            "she": "",
            "we": "",
            "score": "0",
            "game": "",
        }
        self.topic = "*"
