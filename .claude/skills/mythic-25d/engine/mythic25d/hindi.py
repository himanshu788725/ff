"""Devanagari helpers: tokenising, akshara (syllable) weights, line splitting."""
from __future__ import annotations

import re
import unicodedata

CONS = set(range(0x0915, 0x093A)) | set(range(0x0958, 0x0960))
IND_VOWELS = set(range(0x0904, 0x0915)) | {0x0960, 0x0961}
VIRAMA = 0x094D
PUNCT = "।॥,.!?;:—–-\"'“”‘’()…"


def words(text: str):
    """Split into display words, keeping punctuation attached to the word."""
    return [w for w in re.split(r"\s+", text.strip()) if w]


def strip_punct(w: str) -> str:
    return w.strip(PUNCT + " ")


def aksharas(word: str) -> int:
    """Approximate syllable count of a Devanagari (or Latin) word."""
    w = strip_punct(word)
    if not w:
        return 0
    if not any(0x0900 <= ord(c) <= 0x097F for c in w):
        return max(1, len(re.findall(r"[aeiouyAEIOUY]+", w)))
    n = 0
    chars = [ord(c) for c in w]
    for i, c in enumerate(chars):
        if c in IND_VOWELS:
            n += 1
        elif c in CONS:
            nxt = chars[i + 1] if i + 1 < len(chars) else None
            if nxt == VIRAMA:
                continue
            n += 1
    return max(1, n)


def weight(word: str) -> float:
    """Relative spoken duration weight; punctuation adds a pause."""
    w = aksharas(word) + 0.35
    if word and word[-1] in "।॥.!?":
        w += 1.4
    elif word and word[-1] in ",;:—":
        w += 0.7
    return w


def estimate_duration(text: str, rate=1.0) -> float:
    """Seconds a Hindi narrator needs (~6.6 aksharas/s at a calm storytelling pace)."""
    return sum(weight(w) for w in words(text)) / (6.6 * rate) + 0.2


def split_lines(ws, max_chars=34, max_words=7):
    """Group word dicts [{'w':..}] into balanced subtitle lines.

    1) cut into clauses at sentence punctuation (and commas when long),
    2) split each clause into the minimum number of lines that respects the
       limits, balancing characters so no line is a lonely word.
    """
    import math
    clauses, cur = [], []
    for w in ws:
        cur.append(w)
        end = w["w"][-1:]
        if end in "।॥.!?" or (end in ",;:—" and sum(len(x["w"]) + 1 for x in cur) > max_chars * 0.6):
            clauses.append(cur)
            cur = []
    if cur:
        clauses.append(cur)
    # merge tiny clauses into their neighbour when they fit together
    merged = []
    for c in clauses:
        if merged:
            prev = merged[-1]
            tot = sum(len(x["w"]) + 1 for x in prev + c)
            if (len(c) == 1 or len(prev) == 1) and tot <= max_chars and len(prev) + len(c) <= max_words:
                merged[-1] = prev + c
                continue
        merged.append(c)
    lines = []
    for c in merged:
        chars = sum(len(x["w"]) + 1 for x in c)
        n = max(1, math.ceil(chars / max_chars), math.ceil(len(c) / max_words))
        if n == 1:
            lines.append(c)
            continue
        target = chars / n
        cur, acc = [], 0
        for i, w in enumerate(c):
            cur.append(w)
            acc += len(w["w"]) + 1
            left_words = len(c) - i - 1
            if len(lines) < 10_000 and acc >= target * 0.92 and left_words >= 1 and n > 1:
                lines.append(cur)
                cur, acc = [], 0
                n -= 1
                target = sum(len(x["w"]) + 1 for x in c[i + 1:]) / max(1, n)
        if cur:
            lines.append(cur)
    return lines


def nfc(s: str) -> str:
    return unicodedata.normalize("NFC", s)
