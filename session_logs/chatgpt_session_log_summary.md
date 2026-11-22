# ChatGPT AI Session Log — Deep Klarity Assessment

**Candidate:** Arya Sree  
**Project:** Tillpoint Python/SQLite order-desk assessment  
**AI tool:** ChatGPT  
**Date:** 22 November 2026

## Important scope note

This document is an honest work summary reconstructed from the project context available in this chat. It is **not a verbatim export of every message** from the earlier ChatGPT conversation. The earlier conversation is not fully available in the current chat, so missing messages have not been invented or presented as an exact transcript.

The assessment brief requests the full AI conversation. If a complete transcript is required, it should be exported from the original ChatGPT conversation using the platform's available export/copy options.

## Work discussed and completed

The assessment involved investigating six reported issues in a Python application using SQLite. The guidance emphasized understanding each issue, writing regression tests, applying focused fixes, running the test suite, documenting decisions, and keeping Git history.

### Issue 1 — Payments exceeding the order total
- Added cumulative payment validation.
- A payment that would cause recorded payments to exceed the order total is rejected with `PaymentError`.
- Added a regression test.
- Commit: `40d836e` — `Reject payments exceeding order totals`

### Issue 2 — Stock not restored when a pending order is cancelled
- Updated cancellation handling to restore stock for pending as well as paid orders.
- Added a regression test confirming that stock returns to its original quantity.
- Commit: `d8e272f` — `Fix stock restoration when cancelling pending orders`

### Issue 3 — Coupon discount and tax calculation
- Changed the calculation order so the coupon discount is applied before tax.
- Added a regression test for a discounted order in a taxed region.
- Commit: `6150d41` — `Calculate tax after coupon discount`

### Issue 4 — Local-day sales report timezone boundaries
- Corrected UTC boundary calculation by subtracting the UTC offset.
- Added a regression test for India Standard Time (UTC+05:30).
- Commits:
  - `a26abc2` — `Fix daily sales timezone calculation`
  - `aec0b2a` — `Add regression tests for pricing and timezone fixes`

### Issue 5 — Concurrent orders and overselling
- Tested concurrent order attempts using separate SQLite connections and threads.
- The test observed one successful order and one `OutOfStock` result, with stock not becoming negative.
- The reported issue was not reproduced in this test, so no speculative code change was made.
- This limitation and the need for further testing in the actual multi-worker deployment were documented in `NOTES.md`.
- No fix commit was made for this issue.

### Issue 6 — Duplicate payment notifications and separate payments
- Added unique payment event ID protection so a repeated delivery of the same event is ignored.
- Retained cumulative payment validation to reject a separate event that would exceed the order total.
- Added regression tests.
- Commits:
  - `1d0f520` — `Fix duplicate payment webhook handling`
  - `40d836e` — `Reject payments exceeding order totals`
  - `d2e355c` — `Test rejection of separate duplicate payments`

## Verification and documentation

- The project test suite was reported as passing **14 tests**.
- `NOTES.md` was completed and committed:
  - `fb3989d` — `Complete assessment notes`
- The notes document the observed behavior, root cause, fix or reason no fix was made, verification, and relevant commits.
- A database migration consideration was also documented: an existing database may need a migration for the new unique `event_id` constraint, because `CREATE TABLE IF NOT EXISTS` does not alter an existing table.

## Submission reminder

Before submission:
1. Keep this file in the project's `session_logs/` folder only if the evaluator accepts an honest session summary in place of a verbatim transcript.
2. Do not describe this file as a complete verbatim conversation export.
3. Recreate the submission ZIP after adding the required session log.
4. Submit the ZIP and complete the confirmation form before the stated deadline.
