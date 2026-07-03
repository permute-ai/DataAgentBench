# DAB Submission Validity Rubric

We're glad you're submitting to DAB! To keep the leaderboard comparable, we re-run each
submission's answers through the official validators and take a quick look at the traces
for **data leakage**. This page is a short checklist of what we look at, so you can
sanity-check your run beforehand. If something doesn't line up, we'll point it out on the PR 
and you're very welcome to make adjustment. Most submissions sail through.

Submission mechanics (JSON format, per-run answers, agent description) are covered in the
[How to Submit](README.md#how-to-submit-to-the-leaderboard) section of the README.

---

## 1. Sanctioned data sources

An agent may only read from the data the benchmark provides for each dataset: the named
files/DBs below, plus that dataset's description files. Anything else is off-limits as an
answer source.

| Dataset | Sanctioned stores |
|---|---|
| DEPS_DEV_V1 | `package_query.db`, `project_query.db` |
| GITHUB_REPOS | `repo_metadata.db`, `repo_artifacts.db` |
| PANCANCER_ATLAS | pg `pancancer_clinical`, `pancancer_molecular.db` |
| PATENTS | `patent_publication.db`, pg `patent_CPCDefinition` |
| agnews | mongo `articles_db`, `metadata.db` |
| bookreview | pg `bookreview_db`, `review_query.db` |
| crmarenapro | `core_crm.db`, `sales_pipeline.duckdb`, pg `crm_support`(+`support.sql`), `products_orders.db`, `activities.duckdb`, `territory.db` |
| googlelocal | pg `googlelocal_db`, `review_query.db` |
| music_brainz_20k | `tracks.db`, `sales.duckdb` |
| stockindex | `indexInfo_query.db`, `indextrade_query.db` |
| stockmarket | `stockinfo_query.db`, `stocktrade_query.db` |
| yelp | mongo `yelp_db`, `yelp_user.db` |

**Legitimate prompt inputs** are limited to:

- the query's `query.json` question text,
- `db_description.txt`,
- `db_description_withhint.txt` (using this file counts as **"hints used = Yes"**),
- standard harness boilerplate (how to open the databases, the required answer format).

**Legitimate agent behavior** includes: running SQL against the sanctioned stores,
profiling the sanctioned data (e.g. column value frequencies), feeding the agent's *own*
query results back into a self-correction / critique step, and applying general world
knowledge (geography, unit conversions, and the like).

---

## 2. Leakage checks

The one thing we ask: the answer should come from the agent actually solving the task,
not from the gold answer reaching it some other way. We look at the traces for two
patterns — answers obtained at runtime **(2.1)** or handed to the agent through its
prompt **(2.2)**. If we spot either, we'll flag it and you can adjust.

### 2.1 Runtime leakage

1. **Web download of the answer.** Fetching external data that supplies the hidden
   ground-truth labels the task expects the agent to recover — e.g. `load_dataset(...)`,
   `hf_hub` / `snapshot_download`, `raw.githubusercontent`, `gdown`, `kaggle`,
   `wget`/`curl`/`requests`/`urllib`, `git clone`. (A live fetch that succeeds from a
   pre-existing local cache still counts.)
2. **Off-limits local files.** Reading anything outside the sanctioned stores that
   contains the answer or a shortcut to it, including:
   - `ground_truth.csv` / `ground_truth.txt`, or the query's `validate.py` (the grader),
   - any data file not listed as a sanctioned store for that dataset,
   - prior-run or other-submission artifacts: other runs' `ANSWER`/`result.json`,
     `benchmark.json`, intermediate result files, another submission's results JSON, or
     the benchmark's `docs/data/queries.json`.

> We only check this when off-limits
> data was actually obtained **and** drove the **passing** answer.

### 2.2 Prompt-injection leakage

Here we're just checking that the prompt doesn't contain answer-relevant information
beyond the legitimate inputs in Section 1. This comes up when injected content **states**
a decisive value / label / threshold / key / cardinality or interpretation choice, that
content **determines** whether the answer is correct, and the agent **follows** it to a
passing answer. Typical forms:

- a pre-computed **"ground truth hint" / "gold answer" / "expected result"** placed in
  any prompt (including the final answer-formulation step),
- a planner/spec block that hands over the specific value, the exact set of rows, or the
  decisive interpretation the gold answer depends on, rather than letting the agent derive it.

It is fine for the agent to **discover** facts through its own exploration of the
sanctioned data. It is not fine for those facts to be **handed to it up front**.
Restating a hint that is already in `db_description_withhint.txt` is allowed.

---

## 3. Coverage and consistency

- **5 runs per query**, for every query in every dataset (270 trials total).
- **Per-run execution traces are required.** Without traces we cannot assess leakage and
  the submission cannot be scored.
- The answers in your submission JSON should **match** the answers in the corresponding
  traces.

---

We'll describe what we saw on the PR and
you're welcome to adjust. We're happy to help sort it out.
