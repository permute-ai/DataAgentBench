"""Assert that every query validator rejects a refusal.

Each query ships its own ``validate.py`` exposing ``validate(llm_output) -> (bool, str)``.
Nothing currently checks that those validators can fail, so a validator that accepts
any input would score every agent as correct on its query and nothing would notice.

This test feeds each validator several refusals that contain no answer and no digits,
and asserts each is rejected.

Scope and limits: this is a necessary check, not a sufficient one. It cannot detect a
validator that is too strict, and a validator that always returned False would pass it.
A companion positive test (validator accepts its own ground truth) would close that
gap and is a natural follow-up.

Run:
    python -m unittest discover -s tests -v
"""

import importlib.util
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Refusals a real agent emits when it gives up. Deliberately free of digits and of
# any state or entity name, so no validator should legitimately accept one.
REFUSALS = [
    "I could not determine the answer.",
    "I'm sorry, I cannot answer this question.",
    "Unable to complete the task with the available data.",
    "",
]


def discover_validators():
    """Yield (query_id, path) for every query validator in the repo."""
    for path in sorted(REPO_ROOT.glob("query_*/query*/validate.py")):
        query_id = f"{path.parent.parent.name}/{path.parent.name}"
        yield query_id, path


def load_validate(query_id, path):
    """Import a validator module in isolation and return its validate callable."""
    spec = importlib.util.spec_from_file_location(
        f"dab_validator_{query_id.replace('/', '_')}", path
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"could not build an import spec for {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.validate


def is_accepted(result):
    """Validators return (bool, reason); tolerate a bare bool."""
    if isinstance(result, tuple):
        return bool(result[0])
    return bool(result)


class TestValidatorsRejectRefusals(unittest.TestCase):
    def test_validators_are_discoverable(self):
        self.assertGreater(
            len(list(discover_validators())), 0,
            "no query validators found; check REPO_ROOT resolution",
        )

    def test_every_validator_rejects_refusals(self):
        for query_id, path in discover_validators():
            validate = load_validate(query_id, path)
            for refusal in REFUSALS:
                with self.subTest(query=query_id, refusal=refusal or "<empty string>"):
                    self.assertFalse(
                        is_accepted(validate(refusal)),
                        f"{query_id} accepted a refusal, so it cannot distinguish a "
                        f"correct answer from no answer at all. Input was: {refusal!r}",
                    )


if __name__ == "__main__":
    unittest.main()
