# Opik evaluation: offline source-verification traces

## Purpose and current result

The runtime already emits `aift.verification.v1` evidence through
`scripts/run_runtime_verification.py`. The first reuse experiment translates that
existing evidence into arguments for Opik's manual `Opik.trace` API. It does not
replace the evidence generator or introduce a second runtime tracing framework.

`scripts/export_opik_verification.py` is a dependency-free, offline adapter. It
does not import the Opik SDK, open a network connection, start services, collect
computer activity, or change agent execution. No CI upload is enabled. Its JSON
output is a set of SDK method arguments, **not an Opik REST request or an uploaded
trace**.

## Reproduce

From a clean committed checkout, choose fresh paths outside the repository:

```sh
python3 -B scripts/run_runtime_verification.py --output /tmp/aift-runtime-verification.json
python3 -B scripts/export_opik_verification.py /tmp/aift-runtime-verification.json --output /tmp/aift-opik-trace.json
python3 -B -m unittest discover -s tests -p 'test_opik_verification_export.py'
```

The exporter refuses existing output paths, paths within the checkout, and
overwriting the input. A valid failed verification record can still be exported;
successful export means conversion succeeded, not that QA passed. The verification
generator itself returns nonzero when its checks fail.

The output includes only the fixed repository name, validated full commit SHA,
the two known check outcomes and integer exit codes, a binary source-QA feedback
score, and fixed scope labels. Commands, logs, errors, source URLs, arbitrary
metadata, free-form limitations and timestamps are not copied. This is field
selection, not a general-purpose secret detector. Repository and commit identity
remain visible to whoever receives the payload.

## Demonstrated results

On 2026-10-25, the local source gate passed 51 unit tests and validated 76 shell
scripts, 50 Python sources, one JSON document and one model pointer. The adapter
suite covers five baseline outcome combinations: `(0,0)`, `(7,0)`, `(0,1)`,
`(127,1)`, and `(-9,0)` for source/worktree exit codes. All retain their original
pass/fail classification and exit codes. Tests also cover contradictory and
malformed records, duplicate checks/JSON keys, free-text exclusion and refusal
to overwrite output.

All seven emitted top-level argument names were checked against the explicit
`Opik.trace` signature in upstream commit
[`763a2ec2568f71f7957aa33e0a9b10cb2b2d3ba2`](https://github.com/comet-ml/opik/blob/763a2ec2568f71f7957aa33e0a9b10cb2b2d3ba2/sdks/python/src/opik/api_objects/opik_client.py).
This is a source-signature compatibility check, not installed-SDK or server
validation. Opik's [license at that revision](https://github.com/comet-ml/opik/blob/763a2ec2568f71f7957aa33e0a9b10cb2b2d3ba2/LICENSE)
is Apache-2.0. No upstream code is vendored here.

## Limits and next experiment

No agent reliability gain, token saving, latency improvement, inference quality,
Termux integration, dashboard ingestion, retention policy or network isolation
has been demonstrated. Source QA is not agent evaluation or a security audit.
Input records are unsigned; structural checks do not authenticate evidence.
The output explicitly retains `security` and `dependencies` as `not_checked`,
`deployment` as `not_applicable`, and `evidence_authenticated` as false. No
execution duration is invented; an SDK would timestamp ingestion by default.

The next experiment is an isolated self-hosted Opik instance with a pinned SDK,
verified telemetry configuration and controlled network access. Send synthetic
passing and failing records, retrieve them, and compare stored fields, feedback
scores, duplicates and error behavior against the original records. Measure
overhead before instrumenting a real agent workflow. Explicitly select the
self-hosted endpoint: the upstream client defaults to a hosted endpoint.

After observability is measured, evaluate Serena on a disposable code-editing
fixture and DSPy on a fixed task dataset with a local model. Compare correctness,
tokens and latency against actual AIFT baselines. Neither candidate has been
installed, benchmarked or adopted by this change. The
[awesome-ai-agents catalog](https://github.com/slavakurilyak/awesome-ai-agents)
remains a discovery source; inclusion does not establish superiority, security,
or a shared license for its entries.
