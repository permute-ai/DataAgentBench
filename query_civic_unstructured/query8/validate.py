import re

GT_PROJECT = "City Hall Roof Replacement"
GT_AMOUNT = 1340000

# Entity resolution, listed explicitly here (NOT loaded from the ground-truth
# dataset): canonical project name -> every surface-name variant. The answer is
# entity-resolved, so naming the project by ANY variant counts. (This project has
# no variants, but the ER map is kept for consistency across the project-name
# validators.)
ER = {
    "City Hall Roof Replacement": [
        "City Hall Roof Replacement",
    ],
}


def extract_numeric_values(text):
    values = []
    for num in re.findall(r'\b[\d,]+(?:\.\d+)?\b', text):
        try:
            values.append(float(num.replace(",", "")))
        except ValueError:
            pass
    return values


def _norm(s):
    """Lowercase, underscores→spaces, strip non-alphanumeric, collapse whitespace."""
    s = s.lower().replace('_', ' ')
    s = re.sub(r'[^a-z0-9\s]', ' ', s)
    return re.sub(r'\s+', ' ', s).strip()


def _mentions(text_norm, canonical):
    """Entity-resolve the answer: the canonical project is named if ANY of its
    variants appears in the output."""
    return any(_norm(v) in text_norm for v in ER.get(canonical, [canonical]))


def validate(llm_output: str):
    text_norm = _norm(llm_output)

    name_found = _mentions(text_norm, GT_PROJECT)
    amount_found = any(abs(v - GT_AMOUNT) == 0 for v in extract_numeric_values(llm_output))

    if name_found and amount_found:
        return True, "Ground truth project name (entity-resolved) and amount found in LLM output."
    missing = []
    if not name_found:
        missing.append(f"project name '{GT_PROJECT}'")
    if not amount_found:
        missing.append(f"amount '{GT_AMOUNT}'")
    return False, f"Missing in LLM output: {', '.join(missing)}"
