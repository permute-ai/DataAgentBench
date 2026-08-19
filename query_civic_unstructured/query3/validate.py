import re

# After entity resolution, no funding source has >= 25% of its distinct projects
# at status 'completed' as of 2022-08-01, so the ground-truth answer is the empty
# set. A correct response must therefore state that no funding source qualifies.
GROUND_TRUTH = []

# Real funding-source names; if the output lists any, it is not the empty answer.
FUNDING_SOURCES = [
    "Public-Private Partnership", "Municipal Fund", "Municipal Bond",
    "Emergency Relief Fund", "Private Donation", "County Grant",
    "State Grant", "Federal Grant",
]

# Phrasings that indicate the (correct) empty result.
EMPTY_PATTERNS = [
    r'\bno\b[^.\n]*\bfunding sources?\b',
    r'\bno\b[^.\n]*\bsources?\b',
    r'\bnone\b',
    r'\bno qualifying\b',
    r'\bthere (?:are|were) no\b',
    r'\bempty\b',
    r'\bzero\b',
]


def _norm(s):
    """Lowercase, underscores→spaces, strip non-alphanumeric, collapse whitespace."""
    s = s.lower().replace('_', ' ')
    s = re.sub(r'[^a-z0-9\s]', ' ', s)
    return re.sub(r'\s+', ' ', s).strip()


def validate(llm_output: str):
    text = llm_output.lower()
    text_norm = _norm(llm_output)

    listed = [s for s in FUNDING_SOURCES if _norm(s) in text_norm]
    if listed:
        return False, f"Ground truth is empty, but output lists funding source(s): {listed}"
    if any(re.search(p, text) for p in EMPTY_PATTERNS):
        return True, "Correctly reports that no funding source qualifies."
    return False, ("Ground truth is empty (no funding source qualifies); the LLM "
                   "output did not clearly indicate an empty result.")
