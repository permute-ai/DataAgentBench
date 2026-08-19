import re

# Ground truth = canonical (entity-resolved) project names.
GROUND_TRUTH = [
    "Annual Street Maintenance",
    "Civic Center Water Treatment Facility Phase 2",
    "Marie Canyon Green Streets",
    "Michael Landon Center Roof Replacement Project",
    "PCH Median Improvements Project",
    "PCH Signal Synchronization System Improvements Project",
    "PCH at Trancas Canyon Road Right Turn Lane",
    "Permanent Skate Park",
    "Westward Beach Road Repair Project",
]

# Entity resolution, listed explicitly here (NOT loaded from the ground-truth
# dataset): canonical project name -> every surface-name variant that refers to
# the same project. The answer is entity-resolved against this map, so naming a
# project by ANY of its variants counts as naming the canonical project.
ER = {
    "Annual Street Maintenance": [
        "Annual Street Maintenance",
        "2021 Annual Street Maintenance",
        "2022 Annual Street Maintenance",
    ],
    "Civic Center Water Treatment Facility Phase 2": [
        "Civic Center Water Treatment Facility Phase 2",
    ],
    "Marie Canyon Green Streets": [
        "Marie Canyon Green Streets",
    ],
    "Michael Landon Center Roof Replacement Project": [
        "Michael Landon Center Roof Replacement Project",
        "Malibu Bluffs Park Roof Replacement Project",
    ],
    "PCH Median Improvements Project": [
        "PCH Median Improvements Project",
    ],
    "PCH Signal Synchronization System Improvements Project": [
        "PCH Signal Synchronization System Improvements Project",
    ],
    "PCH at Trancas Canyon Road Right Turn Lane": [
        "PCH at Trancas Canyon Road Right Turn Lane",
    ],
    "Permanent Skate Park": [
        "Permanent Skate Park",
    ],
    "Westward Beach Road Repair Project": [
        "Westward Beach Road Repair Project",
        "Westward Beach Road Improvements Project",
    ],
}


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
    missing = [p for p in GROUND_TRUTH if not _mentions(text_norm, p)]
    if not missing:
        return True, "All ground truth project names found in LLM output (entity-resolved)."
    reason = f"Missing project(s) in LLM output: {missing}"
    return False, reason
