"""
backend/issues/ordering.py

Hand-rolled fractional/lexicographic ordering key generation — per
Spadework_Tier2_Kanban_Spec_v1.md's "ordering-key decision" section:
deliberately NOT a library, for teachability. Each issue's `order` is a
string of lowercase letters; moving a card only ever touches that one
row (no renumbering cascade), which is what makes this concurrency-
robust compared to integer resequencing.

Alphabet is a-z (26 "digits"). A missing character in `before` is
treated as the lowest possible value ('a'); a missing character in
`after` is treated as one past the highest ('z' + 1) — this is what
lets key_between('', '') produce a sensible starting midpoint, and
lets either bound be omitted entirely (inserting at the very start or
very end of a list).
"""

ALPHABET_SIZE = 26


def key_between(before: str = '', after: str = '') -> str:
    """
    Returns a string that sorts strictly between `before` and `after`.
    Pass before='' to insert at the start of a list, after='' to insert
    at the end, both '' for the first key in an empty list.
    """
    result = []
    i = 0
    while True:
        b_val = ord(before[i]) - ord('a') if i < len(before) else 0
        a_val = ord(after[i]) - ord('a') if i < len(after) else ALPHABET_SIZE

        if a_val - b_val > 1:
            # Room between the two digits at this position — pick the
            # midpoint and we're done.
            mid = (a_val + b_val) // 2
            result.append(chr(mid + ord('a')))
            return ''.join(result)

        # No room here (adjacent or equal digits) — carry `before`'s
        # digit forward and go one character deeper to find room.
        result.append(chr(b_val + ord('a')))
        i += 1
