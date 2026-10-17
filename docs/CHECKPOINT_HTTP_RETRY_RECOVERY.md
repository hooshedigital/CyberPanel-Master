# Checkpoint HTTP retry and lost-ack recovery — offline contract

Scope: isolated CyberPanel control-plane mock only. This is not production-ready and does not connect to a real CyberPanel host.

## Ambiguous commit rule
If POST /v1/checkpoint times out, the TCP connection breaks, or the response is lost, the outcome is UNKNOWN. Re-submit the exact same request body and idempotency_key; never allocate a fresh key to recover an ambiguous commit. The mock stores the response and idempotency record in the same SQLite transaction as the checkpoint revision.

- 201 with matching revision, sequence and digest: first successful commit.
- 200 with matching fields: replay of a previously committed identical request.
- 409: definite conflict; never treat it as success, even if GET shows the same digest.
- 401/400: definite rejection, no retry with altered credentials or body.
- 500/502/503/504 and transport failures: bounded retries of the same bytes, then an explicit INDETERMINATE outcome.
- Malformed acknowledgement: INDETERMINATE; do not infer success from GET.

## Required tests
1. Inject a lost response after the SQLite transaction commits; retry must receive 200 and revision must remain 1.
2. Lose all responses; return INDETERMINATE, preserve original request and recover in a new client instance.
3. Retry after a 503; ensure identical bytes and idempotency key across attempts.
4. Reuse a key with a changed digest; reject with 409 and leave the checkpoint unchanged.
5. Reject non-loopback destinations, oversized bodies and unexpected success responses.
6. Never echo bearer tokens, server response bodies, or error payloads in exceptions.

## Reproducible companion bundle
The isolated Python client, HTTP mock, and fault-injection tests are distributed as a separate patch/bundle until executable-file writes are accepted. Run locally with Python 3.10+: `python -m unittest discover -s tests -v`. Do not label GitHub CI successful without an actual run on the exact code SHA.

## Deployment gate
Requires canonical source review, durable client-side persistence of pending idempotency requests, independent monotonic trust anchor, transport authentication, staging tests, backup/rollback validation and owner approval. No merge, deployment or production connection is authorized.
