# Chunking Problems

## Summary

The current passage chunking is too brittle for some factoid questions. We now
have a live repro where retrieval finds the right section, answer generation is
working, and the system still fails because the chunk boundary drops the value
needed to answer the question.

This is not an Ollama availability problem anymore. Disabling model thinking
fixed the timeout path. The remaining failure is that the retrieved evidence is
incomplete.

## Reproduced Symptom

Live smoke check:

```bash
uv run poe demo-qa-smoke
```

Current result:

- Question 1 passes:
  `What is the interactive target for the full retrieval and answer generation path?`
- Question 2 fails the evidence assertion:
  `What is the current base path for the primary API?`

The smoke check failure is:

```text
No source passage contained expected evidence '/v1/context/assemble' for question
'What is the current base path for the primary API?'.
```

## What the System Returned

The answer endpoint returns `state="answered"` for the failing question, but the
answer text explicitly says the evidence is cut off:

```json
{
  "state": "answered",
  "answer": "The provided evidence does not state the current base path for the primary API. Passage 1 mentions the base path but cuts off before providing the actual value."
}
```

Top retrieved source passage:

```text
Heading Path: Context Assembly Service API and Configuration Reference
> 3. Base Endpoint and Versioning
> 3.1 Base path

Text: The current base path for the primary API is:
```

The expected value, `/v1/context/assemble`, is not present in any returned
source passage for that answer request.

## Why This Points to Chunking

Retrieval is not missing the topic. It is finding the correct document and the
correct section heading with a high score.

Observed retrieval for the failing question:

- corpus: `default`
- top score: about `0.977`
- top document: `3526a1c1cccec84994c19a97`
- top section: `3.1 Base path`

The failure is that the passage text stops at the lead-in sentence and excludes
the next line containing the actual base path value. The model is therefore
behaving reasonably when it says the evidence is insufficient.

This means the current passage construction is splitting semantically single
units across chunk boundaries. A label like:

```text
The current base path for the primary API is:
```

is being separated from the immediately following literal value that completes
the fact.

## Practical Symptoms

- Retrieval can report a strong match while still returning unusable evidence.
- The answer generator can produce a fast, grounded response and still fail to
  answer because the supporting chunk is incomplete.
- `state="answered"` can currently coexist with an answer that effectively says
  "the evidence is incomplete", because answer-state gating is based on
  retrieval score rather than chunk completeness.
- Smoke checks that assert on evidence content fail even when the retrieval
  score looks healthy.

## Problem Statement

The chunking strategy for Markdown passages needs to preserve short, tightly
coupled fact structures such as:

- lead-in sentence followed by a literal value on the next line
- heading plus immediately following single-value body
- label/value pairs split across adjacent lines
- short list items whose meaning depends on the next line or continuation

Right now the system can index and retrieve a passage that names the fact being
asked about, but not the value needed to answer it. That makes retrieval scores
look better than the actual usable evidence quality.

## Immediate Implication for Follow-up Work

Work on chunking should focus on passage-boundary rules, not the generator:

- inspect how `3.1 Base path` was split into passages
- identify whether blank lines, literal blocks, or short sections are forcing a
  boundary too early
- adjust passage construction so short declarative lead-ins stay attached to the
  value they introduce
- re-run `uv run poe demo-qa-smoke` after changes and require the returned
  `source_passages` to contain `/v1/context/assemble`
