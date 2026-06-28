# `scr/` Hardening Design

## Goal

Harden the production orchestrators in `scr/` without changing their public
CLI arguments, successful output files, email text or subjects, Resource Pool
order, retry interval, or standard-library-only dependency policy.

Each audited finding will land as an individual commit with a regression test
that fails before the production change and passes afterward.

## Changes

### 1. Distinguish retryable results from local exceptions

`cycle_through_pools` will continue cycling only when an operation returns
`False`. Exceptions raised by subprocess startup, decoding, programming errors,
or local filesystem failures will propagate immediately to the orchestrator or
runner instead of being mislabeled as Resource Pool failures.

For bounded retries, the helper will raise `TimeoutError` immediately after the
last completed cycle. It will not emit a promise to retry or sleep for another
30 seconds when no retry remains. Actual retryable cycles retain their current
pool order and 30-second interval.

### 2. Bound SMTP operations

`send_email` will construct `smtplib.SMTP` with a finite timeout and close the
connection reliably. Email remains best-effort: SMTP errors are still logged
and swallowed so an unavailable relay cannot prevent the Impala operation.
Message sender, recipients, body, and subject remain unchanged.

### 3. Resolve only the two monthly template tokens

The monthly processor will require both `{date_inicio}` and `{date_fim}` before
building any DDL. It will replace those exact tokens rather than calling
`str.format`, so unrelated SQL braces such as regular-expression quantifiers
remain literal.

The Dispatch preview will use the same exact-token behavior to preserve
preview/execution parity. Existing valid templates produce byte-equivalent SQL
apart from surrounding code formatting.

### 4. Publish CSV output atomically

`download_to_csv.py` will ask `impala-shell` to write to a uniquely named
temporary sibling of the requested CSV. On success it will publish the file
with `os.replace`; on failure it will remove the temporary file. Consumers
therefore see either the previous complete CSV or the new complete CSV, never a
file still being written.

The public `--output-file` argument and final CSV path/content remain unchanged.
Temporary files remain in the destination directory so publication does not
cross filesystem boundaries.

### 5. Add a conservative Ruff gate for `scr/`

Add Ruff to the development dependency set and configure a narrow correctness
rule selection for `scr/`. Remove file-wide `# flake8: noqa` suppressions that
would disable the gate. Do not enable formatting, style-only rules, or broad
type checking in this change.

The gate must run as:

```text
python -m ruff check scr
```

## Testing

- Add focused unit tests for exception propagation and bounded-retry timing.
- Add SMTP tests using a fake `smtplib.SMTP` implementation; no network calls.
- Add monthly tests for missing tokens, unrelated braces, and unchanged valid
  substitution.
- Add CSV tests using a fake `subprocess.Popen` that writes partial/successful
  output and verifies atomic publication and cleanup.
- Run focused tests after each commit.
- Before completion, run the full repository test suite, `compileall`, the
  Dispatch help smoke test, and the new Ruff gate.

## Commit Boundaries

1. `fix(scr): propagate unexpected retry errors`
2. `fix(scr): bound SMTP operations`
3. `fix(scr): preserve literal braces in monthly SQL`
4. `fix(scr): publish CSV exports atomically`
5. `chore(scr): add conservative Ruff gate`

The design document is committed separately so implementation commits remain
one finding each.

## Stop Conditions

- A fix requires changing CLI flag names, exit codes for valid inputs, email
  content, Resource Pool lists, or retry intervals.
- Atomic publication cannot be guaranteed on the destination filesystem.
- Ruff requires broad source reformatting or non-stdlib runtime dependencies.
- A focused or full verification failure cannot be attributed to the intended
  behavior change.
