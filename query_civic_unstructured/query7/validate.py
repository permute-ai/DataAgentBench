import re

# After entity resolution, no project is both type 'disaster' and status
# 'not started' with accumulated funding > $1,000,000 as of 2022-11-01, so the
# ground-truth answer is the empty set. A correct response must therefore state
# that no project qualifies.
GROUND_TRUTH = []

# Entity resolution, listed explicitly here (NOT loaded from the ground-truth
# dataset): canonical project name -> every surface-name variant that refers to
# the same project. Naming a project by ANY variant counts as naming it, so an
# answer cannot evade the check in validate() by using an alias spelling.
ER = {
    "2022 Morning View Resurfacing & Storm Drain Improvements": [
        "2022 Morning View Resurfacing & Storm Drain Improvements",
    ],
    "Annual Street Maintenance": [
        "Annual Street Maintenance",
        "2021 Annual Street Maintenance",
        "2022 Annual Street Maintenance",
    ],
    "Birdview Avenue Improvements": [
        "Birdview Avenue Improvements",
        "Birdview Avenue Improvements (CalOES Project)",
        "Birdview Avenue Improvements (FEMA/CalOES Project)",
    ],
    "Bluffs Park Shade Structure": [
        "Bluffs Park Shade Structure",
    ],
    "Bluffs Park Workout Station": [
        "Bluffs Park Workout Station",
    ],
    "Broad Beach Road Water Quality Infrastructure Repairs": [
        "Broad Beach Road Water Quality Infrastructure Repairs",
        "Broad Beach Road Water Quality Infrastructure Repairs (CalJPIA Project)",
        "Broad Beach Road Water Quality Repair",
    ],
    "City Hall Roof Replacement": [
        "City Hall Roof Replacement",
    ],
    "City Hall Solar Project": [
        "City Hall Solar Project",
    ],
    "City Traffic Signals Backup Power": [
        "City Traffic Signals Backup Power",
    ],
    "Citywide Asphalt Concrete Berms Repairs": [
        "Citywide Asphalt Concrete Berms Repairs",
    ],
    "Citywide Guardrail Replacement": [
        "Citywide Guardrail Replacement",
    ],
    "Civic Center Stormwater Diversion Structure": [
        "Civic Center Stormwater Diversion Structure",
    ],
    "Civic Center Water Treatment Facility Phase 2": [
        "Civic Center Water Treatment Facility Phase 2",
    ],
    "Civic Center Way Improvements": [
        "Civic Center Way Improvements",
    ],
    "Clover Heights Storm Drain": [
        "Clover Heights Storm Drain",
        "Clover Heights Storm Drain (FEMA Project)",
        "Clover Heights Storm Drainage Improvements",
    ],
    "Corral Canyon Culvert Repairs": [
        "Corral Canyon Culvert Repairs",
        "Corral Canyon Culvert Repairs (FEMA Project)",
        "Corral Canyon Culvert Repairs (FEMA/CalOES Project)",
    ],
    "Corral Canyon Road Bridge Repairs": [
        "Corral Canyon Road Bridge Repairs",
        "Corral Canyon Road Bridge Repairs (FEMA Project)",
        "Corral Canyon Road Bridge Repairs (FEMA/CalOES Project)",
    ],
    "Dume Drive and Fernhill Drive Speed Humps Project": [
        "Dume Drive and Fernhill Drive Speed Humps Project",
    ],
    "Encinal Canyon 60-inch Storm Drain Repairs": [
        "Encinal Canyon 60-inch Storm Drain Repairs",
    ],
    "Encinal Canyon Road Drainage Improvements": [
        "Encinal Canyon Road Drainage Improvements",
        "Encinal Canyon Road Drainage Improvements (CalOES Project)",
        "Encinal Canyon Road Drainage Improvements (FEMA/CalOES Project)",
        "Encinal Canyon Road Repairs",
    ],
    "Guardrail Replacement Citywide": [
        "Guardrail Replacement Citywide",
        "Guardrail Replacement Citywide (FEMA Project)",
        "Guardrail Replacement Citywide (FEMA/CalOES Project)",
    ],
    "Harbor Vista Curb Return": [
        "Harbor Vista Curb Return",
    ],
    "Kanan Dume Biofilter": [
        "Kanan Dume Biofilter",
    ],
    "Latigo Canyon Road Culvert Repairs": [
        "Latigo Canyon Road Culvert Repairs",
        "Latigo Canyon Road Culvert Repairs (FEMA Project)",
        "Latigo Canyon Road Culvert Repairs (FEMA/CalOES Project)",
    ],
    "Latigo Canyon Road Roadway/Retaining Wall Improvements": [
        "Latigo Canyon Road Roadway/Retaining Wall Improvements",
        "Latigo Canyon Road Retaining Wall Repair Project",
        "Latigo Canyon Road Roadway/Retaining Wall Improvements (FEMA Project)",
        "Latigo Canyon Road Roadway/Retaining Wall Improvements (FEMA/CalOES Project)",
    ],
    "Legacy Park Benches and Arbors Renovation": [
        "Legacy Park Benches and Arbors Renovation",
    ],
    "Legacy Park Paver Repair Project": [
        "Legacy Park Paver Repair Project",
    ],
    "Malibu Bluffs Park South Walkway": [
        "Malibu Bluffs Park South Walkway",
        "Malibu Bluffs Park South Walkway Repairs",
    ],
    "Malibu Canyon Road Traffic Study": [
        "Malibu Canyon Road Traffic Study",
    ],
    "Malibu Park Drainage Improvements": [
        "Malibu Park Drainage Improvements",
    ],
    "Malibu Park Resurfacing Project": [
        "Malibu Park Resurfacing Project",
    ],
    "Malibu Park Storm Drain Repairs": [
        "Malibu Park Storm Drain Repairs",
    ],
    "Malibu Road Slope Repairs": [
        "Malibu Road Slope Repairs",
        "Malibu Road Slope Repairs (CalOES Project)",
    ],
    "Malibu Seafood Undercrossing": [
        "Malibu Seafood Undercrossing",
    ],
    "Marie Canyon Green Streets": [
        "Marie Canyon Green Streets",
    ],
    "Michael Landon Center HVAC Replacement Project": [
        "Michael Landon Center HVAC Replacement Project",
    ],
    "Michael Landon Center Roof Replacement Project": [
        "Michael Landon Center Roof Replacement Project",
        "Malibu Bluffs Park Roof Replacement Project",
    ],
    "Outdoor Warning Sirens": [
        "Outdoor Warning Sirens",
        "Outdoor Warning Signs",
        "Outdoor Warning Sirens (FEMA Project)",
        "Outdoor Warning Sirens (FEMA)",
        "Outdoor Warning Sirens - Design (FEMA Project)",
        "Outdoor Warningn Sirens - Design (FEMA Project)",
    ],
    "PCH Crosswalk Improvements at Big Rock Drive and 20326 PCH": [
        "PCH Crosswalk Improvements at Big Rock Drive and 20326 PCH",
        "PCH Overhead Warning Signs",
    ],
    "PCH Median Improvements Project": [
        "PCH Median Improvements Project",
    ],
    "PCH Median Improvements at Paradise Cove and Zuma Beach": [
        "PCH Median Improvements at Paradise Cove and Zuma Beach",
    ],
    "PCH Signal Synchronization System Improvements Project": [
        "PCH Signal Synchronization System Improvements Project",
    ],
    "PCH at Las Flores and Rambla Pacifico Intersection Improvements": [
        "PCH at Las Flores and Rambla Pacifico Intersection Improvements",
    ],
    "PCH at Trancas Canyon Road Right Turn Lane": [
        "PCH at Trancas Canyon Road Right Turn Lane",
    ],
    "Permanent Skate Park": [
        "Permanent Skate Park",
    ],
    "Point Dume Walkway Repairs": [
        "Point Dume Walkway Repairs",
        "Point Dume Decomposed Granite Walkway Repair Project",
    ],
    "Storm Drain Master Plan": [
        "Storm Drain Master Plan",
        "Storm Drain Master Plan (FEMA Project)",
    ],
    "Storm Drain Trash Screens": [
        "Storm Drain Trash Screens",
        "Storm Drain Trash Screens Phase Two",
    ],
    "Trancas Canyon Park Planting and Irrigation Repairs": [
        "Trancas Canyon Park Planting and Irrigation Repairs",
        "Trancas Canyon Park Planting and Irrigation Repairs (CalJPIA/FEMA Project)",
        "Trancas Canyon Park Planting and Irrigation Repairs (FEMA/CalOES Project)",
    ],
    "Trancas Canyon Park Playground Resurfacing": [
        "Trancas Canyon Park Playground Resurfacing",
        "Trancas Canyon Park Playground",
        "Trancas Playground Resurfacing",
    ],
    "Trancas Canyon Park Slope Stabilization Project": [
        "Trancas Canyon Park Slope Stabilization Project",
        "Trancas Canyon Park Slope Stabilization Project (CalJPIA Project)",
        "Trancas Canyon Park Slope Stabilization Project (CalOES Project)",
        "Trancas Canyon Park Upper and Lower Slopes Repair",
    ],
    "Vehicle Protection Devices": [
        "Vehicle Protection Devices",
    ],
    "Westward Beach Road Drainage Improvements Project": [
        "Westward Beach Road Drainage Improvements Project",
    ],
    "Westward Beach Road Repair Project": [
        "Westward Beach Road Repair Project",
        "Westward Beach Road Improvements Project",
    ],
    "Westward Beach Road Shoulder Repairs (CalOES Project)": [
        "Westward Beach Road Shoulder Repairs (CalOES Project)",
    ],
}

# Phrasings that indicate the (correct) empty result.
EMPTY_PATTERNS = [
    r'\bno\b[^.\n]*\bprojects?\b',
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


def _mentions(text_norm, canonical):
    """Entity-resolve the answer: the canonical project is named if ANY of its
    variants appears in the output."""
    return any(_norm(v) in text_norm for v in ER.get(canonical, [canonical]))


def validate(llm_output: str):
    text = llm_output.lower()
    text_norm = _norm(llm_output)

    # Naming a real project asserts that it qualifies, so the answer is not the
    # empty answer -- even when it also contains an empty-result phrase. Without
    # this check an answer that lists projects still passes on an incidental
    # match, e.g. quoting an agenda's "None at this time" or hedging with "no
    # other projects qualify". Checked before EMPTY_PATTERNS so the listing wins.
    listed = sorted(c for c in ER if _mentions(text_norm, c))
    if listed:
        return False, f"Ground truth is empty, but output names project(s): {listed}"

    if any(re.search(p, text) for p in EMPTY_PATTERNS):
        return True, "Correctly reports that no project qualifies."
    return False, ("Ground truth is empty (no project qualifies); the LLM output "
                   "did not clearly indicate an empty result.")
