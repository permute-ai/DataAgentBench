import re

# After entity resolution, no project is both type 'disaster' and status
# 'not started' with accumulated funding > $1,000,000 as of 2022-11-01, so the
# ground-truth answer is the empty set. A correct response must therefore state
# that no project qualifies.
GROUND_TRUTH = []

# Phrasings that indicate the (correct) empty result.
EMPTY_PATTERNS = [
    r'\bno\b[^.\n]*\bprojects?\b',
    r'\bnone\b',
    r'\bno qualifying\b',
    r'\bthere (?:are|were) no\b',
    r'\bempty\b',
    r'\bzero\b',
]


def validate(llm_output: str):
    text = llm_output.lower()
    if any(re.search(p, text) for p in EMPTY_PATTERNS):
        return True, "Correctly reports that no project qualifies."
    return False, ("Ground truth is empty (no project qualifies); the LLM output "
                   "did not clearly indicate an empty result.")
