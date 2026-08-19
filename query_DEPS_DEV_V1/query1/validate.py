"""Validator for DEPS_DEV_V1 query 1.

    "Considering only the latest release versions for each distinct NPM package, which
     packages are the top 5 most popular based on the Github star number, as well as
     their versions?"

Applying the question literally -- System='NPM', VersionInfo.IsRelease, the highest
Ordinal per distinct Name, joined through project_packageversion to the star count in
project_info.Project_Information -- leaves four packages strictly above the cutoff and
95 packages tied at fifth place on 57779 stars. Every tied package maps to the same
GitHub project (lodash/lodash), so all of them carry identical stars, forks, issues and
project metadata; each has a single release with Ordinal=1 and a NULL UpstreamPublishedAt.
Nothing in the question or the data singles out one of them, so no single fifth row is
uniquely correct. See https://github.com/ucbepic/DataAgentBench/issues/86.

Accordingly this validator requires:

* all four above-cutoff packages, each with its correct version; and
* at least one fifth-place package, where *every* package the answer reports beyond the
  four must belong to the tied set.

An answer naming any package outside those two sets as part of its top 5 is rejected, so
returning the one tied package the old ground truth happened to record, returning a
different one, or returning all 95 are all accepted, while a genuinely wrong package
(for example one whose rank depends on aggregating stars across versions) is not.
"""

import re

# --- Ground truth -----------------------------------------------------------------
# Packages strictly above the fifth-place cutoff. All four are required.
ABOVE_CUTOFF = [
    ("@dmrvos/infrajs>0.0.6>typescript", "2.6.2"),
    ("@dmrvos/infrajs>0.0.5>typescript", "2.6.2"),
    ("@dylanvann/svelte", "3.25.4"),
    ("@dumc11/tailwindcss", "0.4.0"),]

# Packages tied at fifth place on 57779 stars (lodash/lodash). Any non-empty subset is
# accepted as the fifth row.
TIED_AT_CUTOFF = [
    ("@dollarshaveclub/cli>1.0.0>lodash", "4.17.4"),
    ("@dollarshaveclub/cli>1.1.0>lodash", "4.17.4"),
    ("@dollarshaveclub/cli>1.10.0>lodash", "4.17.5"),
    ("@dollarshaveclub/cli>1.10.1>lodash", "4.17.5"),
    ("@dollarshaveclub/cli>1.11.0>lodash", "4.17.5"),
    ("@dollarshaveclub/cli>1.11.1>lodash", "4.17.5"),
    ("@dollarshaveclub/cli>1.11.2>lodash", "4.17.4"),
    ("@dollarshaveclub/cli>1.11.3>lodash", "4.17.4"),
    ("@dollarshaveclub/cli>1.11.4>lodash", "4.17.11"),
    ("@dollarshaveclub/cli>1.11.5-rc.1>lodash", "4.17.11"),
    ("@dollarshaveclub/cli>1.11.5>lodash", "4.17.11"),
    ("@dollarshaveclub/cli>1.12.0>lodash", "4.17.11"),
    ("@dollarshaveclub/cli>1.13.0>lodash", "4.17.11"),
    ("@dollarshaveclub/cli>1.13.1>lodash", "4.17.11"),
    ("@dollarshaveclub/cli>1.2.0>lodash", "4.17.4"),
    ("@dollarshaveclub/cli>1.3.0>lodash", "4.17.4"),
    ("@dollarshaveclub/cli>1.5.0>lodash", "4.17.4"),
    ("@dollarshaveclub/cli>1.5.1>lodash", "4.17.4"),
    ("@dollarshaveclub/cli>1.5.2>lodash", "4.17.4"),
    ("@dollarshaveclub/cli>1.5.3>lodash", "4.17.4"),
    ("@dollarshaveclub/cli>1.5.4>lodash", "4.17.4"),
    ("@dollarshaveclub/cli>1.5.5>lodash", "4.17.4"),
    ("@dollarshaveclub/cli>1.5.6>lodash", "4.17.4"),
    ("@dollarshaveclub/cli>1.5.7>lodash", "4.17.4"),
    ("@dollarshaveclub/cli>1.6.0>lodash", "4.17.4"),
    ("@dollarshaveclub/cli>1.7.1>lodash", "4.17.5"),
    ("@dollarshaveclub/cli>1.8.0>lodash", "4.17.5"),
    ("@dollarshaveclub/cli>1.9.0>lodash", "4.17.5"),
    ("@dollarshaveclub/cli>1.9.1>lodash", "4.17.5"),
    ("@dollarshaveclub/cli>2.0.0>lodash", "4.17.11"),
    ("@dollarshaveclub/cli>2.0.1>lodash", "4.17.11"),
    ("@dollarshaveclub/cli>2.1.0>lodash", "4.17.11"),
    ("@dollarshaveclub/cli>2.1.1>lodash", "4.17.11"),
    ("@dollarshaveclub/cli>2.2.0>lodash", "4.17.11"),
    ("@dollarshaveclub/cli>2.2.1>lodash", "4.17.11"),
    ("@dollarshaveclub/cli>2.2.2>lodash", "4.17.11"),
    ("@dpoineau/react-scripts>1.0.0>eslint-plugin-flowtype>lodash", "4.16.3"),
    ("@dpoineau/react-scripts>1.0.0>html-webpack-plugin>lodash", "4.16.3"),
    ("@dpoineau/react-scripts>1.0.0>http-proxy-middleware>lodash", "4.16.3"),
    ("@dpoineau/react-scripts>1.0.0>lodash", "4.9.0"),
    ("@dpoineau/react-scripts>1.0.0>lodash._arraycopy", "3.0.0"),
    ("@dpoineau/react-scripts>1.0.0>lodash._arrayeach", "3.0.0"),
    ("@dpoineau/react-scripts>1.0.0>lodash._baseassign", "3.2.0"),
    ("@dpoineau/react-scripts>1.0.0>lodash._baseclone", "3.3.0"),
    ("@dpoineau/react-scripts>1.0.0>lodash._basecopy", "3.0.1"),
    ("@dpoineau/react-scripts>1.0.0>lodash._basefor", "3.0.3"),
    ("@dpoineau/react-scripts>1.0.0>lodash._bindcallback", "3.0.1"),
    ("@dpoineau/react-scripts>1.0.0>lodash._createcompounder", "3.0.0"),
    ("@dpoineau/react-scripts>1.0.0>lodash._getnative", "3.9.1"),
    ("@dpoineau/react-scripts>1.0.0>lodash._root", "3.0.1"),
    ("@dpoineau/react-scripts>1.0.0>lodash.assign", "4.2.0"),
    ("@dpoineau/react-scripts>1.0.0>lodash.camelcase", "3.0.1"),
    ("@dpoineau/react-scripts>1.0.0>lodash.clonedeep", "4.5.0"),
    ("@dpoineau/react-scripts>1.0.0>lodash.cond", "4.5.2"),
    ("@dpoineau/react-scripts>1.0.0>lodash.deburr", "3.2.0"),
    ("@dpoineau/react-scripts>1.0.0>lodash.endswith", "4.2.1"),
    ("@dpoineau/react-scripts>1.0.0>lodash.find", "4.6.0"),
    ("@dpoineau/react-scripts>1.0.0>lodash.findindex", "4.6.0"),
    ("@dpoineau/react-scripts>1.0.0>lodash.indexof", "4.0.5"),
    ("@dpoineau/react-scripts>1.0.0>lodash.isarguments", "3.1.0"),
    ("@dpoineau/react-scripts>1.0.0>lodash.isarray", "3.0.4"),
    ("@dpoineau/react-scripts>1.0.0>lodash.keys", "3.1.2"),
    ("@dpoineau/react-scripts>1.0.0>lodash.pickby", "4.6.0"),
    ("@dpoineau/react-scripts>1.0.0>lodash.words", "3.2.0"),
    ("@dpoineau/react-scripts>1.0.0>node-notifier>lodash.clonedeep", "3.0.2"),
    ("@dummmy/pack-cli>1.0.8>lodash", "4.17.19"),
    ("@dummmy/pack-cli>1.0.9>lodash", "4.17.19"),
    ("@dummmy/webpack-cli>1.0.2>lodash", "4.17.19"),
    ("@dummmy/webpack-cli>1.0.3>lodash", "4.17.19"),
    ("@dummmy/webpack-cli>1.0.4>lodash", "4.17.19"),
    ("@dummmy/webpack-cli>1.0.5>lodash", "4.17.19"),
    ("@dummmy/webpack-cli>1.0.6>lodash", "4.17.19"),
    ("@dummmy/webpack-cli>1.0.7>lodash", "4.17.19"),
    ("@dwarvesf/react-scripts>0.7.0>lodash", "4.17.2"),
    ("@dwarvesf/react-scripts>0.7.0>lodash._arraycopy", "3.0.0"),
    ("@dwarvesf/react-scripts>0.7.0>lodash._arrayeach", "3.0.0"),
    ("@dwarvesf/react-scripts>0.7.0>lodash._baseassign", "3.2.0"),
    ("@dwarvesf/react-scripts>0.7.0>lodash._baseclone", "3.3.0"),
    ("@dwarvesf/react-scripts>0.7.0>lodash._basecopy", "3.0.1"),
    ("@dwarvesf/react-scripts>0.7.0>lodash._basefor", "3.0.3"),
    ("@dwarvesf/react-scripts>0.7.0>lodash._bindcallback", "3.0.1"),
    ("@dwarvesf/react-scripts>0.7.0>lodash._createcompounder", "3.0.0"),
    ("@dwarvesf/react-scripts>0.7.0>lodash._getnative", "3.9.1"),
    ("@dwarvesf/react-scripts>0.7.0>lodash._root", "3.0.1"),
    ("@dwarvesf/react-scripts>0.7.0>lodash.assign", "4.2.0"),
    ("@dwarvesf/react-scripts>0.7.0>lodash.camelcase", "3.0.1"),
    ("@dwarvesf/react-scripts>0.7.0>lodash.clonedeep", "3.0.2"),
    ("@dwarvesf/react-scripts>0.7.0>lodash.cond", "4.5.2"),
    ("@dwarvesf/react-scripts>0.7.0>lodash.deburr", "3.2.0"),
    ("@dwarvesf/react-scripts>0.7.0>lodash.indexof", "4.0.5"),
    ("@dwarvesf/react-scripts>0.7.0>lodash.isarguments", "3.1.0"),
    ("@dwarvesf/react-scripts>0.7.0>lodash.isarray", "3.0.4"),
    ("@dwarvesf/react-scripts>0.7.0>lodash.keys", "3.1.2"),
    ("@dwarvesf/react-scripts>0.7.0>lodash.pickby", "4.6.0"),
    ("@dwarvesf/react-scripts>0.7.0>lodash.words", "3.2.0"),]

CUTOFF_STARS = 57779

# Kept for callers that expect the historical name.
gt_pairs = ABOVE_CUTOFF + TIED_AT_CUTOFF

# Characters that may continue a package name. A candidate match is only a real match
# when the next character is not one of these, otherwise ">lodash" would match inside
# ">lodash._arraycopy" and a shorter tied name would be found in a longer one.
_NAME_CHAR = re.compile(r"[\w.\-/>@]")

# How far after a name the version may appear. Wide enough for ", " / " | " / '", "'
# separators, narrow enough not to reach the next row of a table.
_VERSION_WINDOW = 25

# A package name as reported in an answer, used to spot packages outside both sets.
_CANDIDATE = re.compile(r"@[\w.\-]+/[\w.\-]+(?:>[\w.\-]+)*")


def _version_follows(text, end, version):
    """True when `version` appears as a standalone token just after position `end`."""
    window = text[end:end + _VERSION_WINDOW]
    return re.search(r"(?<![\w.])" + re.escape(version) + r"(?![\w.])", window) is not None


def _find_reported(text, name, version):
    """True when `name` appears at a name boundary and is followed by `version`."""
    start = 0
    while True:
        idx = text.find(name, start)
        if idx == -1:
            return False
        end = idx + len(name)
        at_boundary = end >= len(text) or not _NAME_CHAR.match(text[end])
        if at_boundary and _version_follows(text, end, version):
            return True
        start = idx + 1


def validate(llm_output: str):
    """Validate an answer to DEPS_DEV_V1 query 1.

    Returns (True, reason) if the answer reports all four above-cutoff packages with
    their versions plus at least one package from the fifth-place tie and no package
    from outside those sets; (False, reason) otherwise.
    """
    text = (llm_output or "").lower()

    for name, version in ABOVE_CUTOFF:
        if not _find_reported(text, name.lower(), version.lower()):
            return False, f"Missing or mis-versioned above-cutoff package: {name} {version}"

    matched_tied = [
        name for name, version in TIED_AT_CUTOFF
        if _find_reported(text, name.lower(), version.lower())
    ]
    if not matched_tied:
        return False, (
            f"No fifth-place package reported. Any of the {len(TIED_AT_CUTOFF)} packages "
            f"tied at {CUTOFF_STARS} stars is acceptable, with its correct version."
        )

    # Reject packages from outside both sets, but only where the answer reports one as a
    # result row (name followed by a version), not where it merely mentions one in prose.
    allowed = {name.lower() for name, _ in gt_pairs}
    for match in _CANDIDATE.finditer(text):
        name = match.group(0)
        if name in allowed:
            continue
        if any(a.startswith(name) for a in allowed):
            continue  # a prefix of a real name, e.g. a truncated table cell
        window = text[match.end():match.end() + _VERSION_WINDOW]
        if re.search(r"(?<![\w.])\d+\.\d+(?:\.[\w.\-]+)?(?![\w.])", window):
            return False, (
                f"Reported package outside the top 4 and the fifth-place tie: {name}"
            )

    return True, (
        f"All 4 above-cutoff packages validated; fifth place satisfied by "
        f"{len(matched_tied)} package(s) from the {len(TIED_AT_CUTOFF)}-way tie at "
        f"{CUTOFF_STARS} stars."
    )
