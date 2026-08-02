"""Sanity checks that every query validator can both accept and reject.

Each query ships its own ``validate.py`` exposing ``validate(llm_output) -> (bool, str)``.
Nothing currently checks those validators, so a validator that accepted any input would
score every agent correct on its query, and one that rejected every input would score
every agent wrong. Neither would be noticed.

Two complementary checks:

* **Negative control.** Every validator must reject refusals that contain no answer and
  no digits. A validator that accepts one cannot tell a correct answer from no answer.
* **Positive control.** Every validator must accept its own ``ground_truth.csv``, rendered
  as an answer-like string. A validator that rejects its own ground truth makes its query
  unpassable, and it also stops the negative control from being satisfiable trivially by
  a validator that always returns False.

Together these bound the validator: it must be able to say yes, and it must be able to
say no. They do not check that it says yes and no in exactly the right places, which
would require labelled agent answers this repo does not ship.

Run:
    python -m unittest discover -s tests -v
"""

import csv
import importlib.util
import io
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Refusals a real agent emits when it gives up. Deliberately free of digits and of any
# entity name, so no validator should legitimately accept one.
REFUSALS = [
    "I could not determine the answer.",
    "I'm sorry, I cannot answer this question.",
    "Unable to complete the task with the available data.",
    "",
]


def discover_validators():
    """Yield (query_id, validate_path) for every query validator in the repo."""
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


def render_ground_truth(query_dir):
    """Render ground_truth.csv as an answer-like string: field values, space separated.

    Fields are split rather than passed as a raw CSV line because a bare line such as
    ``2023,64171000`` reads as one fused number to validators that strip thousands
    separators before parsing.
    """
    text = (query_dir / "ground_truth.csv").read_text(errors="ignore").strip()
    cells = [
        cell.strip()
        for row in csv.reader(io.StringIO(text))
        for cell in row
        if cell.strip()
    ]
    return " ".join(cells) if cells else text


class TestValidators(unittest.TestCase):
    def test_validators_are_discoverable(self):
        self.assertGreater(
            len(list(discover_validators())), 0,
            "no query validators found; check REPO_ROOT resolution",
        )

    def test_every_validator_rejects_refusals(self):
        """Negative control: a validator must be able to say no."""
        for query_id, path in discover_validators():
            validate = load_validate(query_id, path)
            for refusal in REFUSALS:
                with self.subTest(query=query_id, refusal=refusal or "<empty string>"):
                    self.assertFalse(
                        is_accepted(validate(refusal)),
                        f"{query_id} accepted a refusal, so it cannot distinguish a "
                        f"correct answer from no answer at all. Input was: {refusal!r}",
                    )

    def test_every_validator_accepts_its_ground_truth(self):
        """Positive control: a validator must be able to say yes."""
        for query_id, path in discover_validators():
            validate = load_validate(query_id, path)
            answer = render_ground_truth(path.parent)
            with self.subTest(query=query_id):
                self.assertTrue(
                    is_accepted(validate(answer)),
                    f"{query_id} rejected its own ground truth, so the query cannot be "
                    f"passed by reporting the recorded answer. Input was: {answer!r}",
                )


if __name__ == "__main__":
    unittest.main()
