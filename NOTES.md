# NOTES

Fill in every field below before you submit. We read this file first: a submission with an empty field is not graded.

## 1. Report

> Finance says that on some days the revenue in the daily report is higher than what the payment provider paid out, and a few orders show more money received than their total.

**Status:** fixed

**What I saw:**  
The payment handler accepted a payment amount greater than the order total. This could cause the recorded payments for an order to exceed the expected amount.

**Root cause:**  
There was no validation to check whether the cumulative payments would exceed the order total.

**Fix and why:**  
Added cumulative payment validation. A payment that would make the total payments exceed the order total is rejected with PaymentError. This prevents excess payments from being recorded.

**How I verified it:**  
Added a test that sends a payment greater than the order total. Verified that PaymentError is raised and the payment is not recorded. The test passed.

**Commits:**  
40d836e

## 2. Report

> Products show as sold out, or nearly, while the shelf is full. Staff say it gets worse on days when many customers abandon checkout.

**Status:** fixed

**What I saw:**  
Stock was not restored when a pending order was cancelled. This left stock reserved even though the checkout was abandoned.

**Root cause:**  
The cancellation logic restored stock only when the order status was paid. Pending orders were not included.

**Fix and why:**  
Updated the cancellation logic to restore stock for both pending and paid orders. This releases reserved stock when an order is cancelled.

**How I verified it:**  
Added a test that creates a pending order, cancels it, and checks that stock returns to its original quantity. The test passed.

**Commits:**  
d8e272f

## 3. Report

> Customers in taxed regions who used a coupon say the tax on their receipt is too high. Receipts without a coupon are right.

**Status:** fixed

**What I saw:**  
Tax was calculated on the original subtotal before applying the coupon discount.

**Root cause:**  
The pricing logic calculated tax before subtracting the coupon discount.

**Fix and why:**  
Changed the calculation order so the coupon discount is applied first and tax is calculated on the discounted subtotal. This produces the correct tax amount for discounted orders.

**How I verified it:**  
Added a regression test for a coupon in a taxed region. Checked the expected discount, tax, and final total. The test passed.

**Commits:**  
6150d41

## 4. Report

> Our shop in India (UTC+5:30) says sales taken in the morning do not appear in that day's report and turn up under the day before.

**Status:** fixed

**What I saw:**  
The UTC boundaries for a local reporting day were calculated incorrectly when a timezone offset was provided.

**Root cause:**  
The timezone offset was added instead of subtracted when converting local day boundaries to UTC.

**Fix and why:**  
Changed the calculation to subtract the UTC offset when determining the start and end of the local reporting day.

**How I verified it:**  
Added a test for the India UTC+5:30 timezone. Verified that a payment at 20:00 UTC appears in the correct local day's report. The test passed.

**Commits:**  
a26abc2, aec0b2a

## 5. Report

> On busy days, two workers sometimes sell the same last unit and inventory becomes negative.

**Status:** not fixed

**What I saw:**  
I tested two concurrent orders attempting to purchase the last available unit. Only one order succeeded, while the other received OutOfStock. Stock remained zero. I could not reproduce the reported overselling issue in this test.

**Root cause:**  
The exact cause of the reported issue was not confirmed. The existing order creation flow uses a SQLite BEGIN IMMEDIATE transaction before checking and reserving stock, which serialized the two tested order attempts.

**Fix and why:**  
No additional code change was made because the tested scenario did not reproduce the issue. Further testing in the actual two-worker deployment may be needed.

**How I verified it:**  
Added a concurrency test using two separate SQLite connections and threads. Verified that exactly one order succeeds, the other receives OutOfStock, and stock does not become negative.

**Commits:**  
none

## 6. Open question

> A payment provider retries a successful payment webhook. Sometimes a second, separate payment also arrives for an order that is already fully paid. Decide how to handle both cases.

**My decision:**  
Reject a separate payment if it would make the cumulative payments exceed the order total. Ignore repeated deliveries of the same payment event.

**Why:**  
This prevents the same webhook event from being counted twice and prevents a second full payment from being recorded as additional revenue for an already-paid order.

**What it costs:**  
A genuine extra payment is rejected by the application. If the payment provider has already collected the money, it may require manual investigation or a refund. Automatic refunds are not implemented.

**What I built:**  
Added duplicate webhook event protection using a unique event ID and cumulative payment validation. Repeated delivery of the same event is ignored, and a separate payment with a different event ID is rejected if it exceeds the order total.

**How I verified it:**  
Added tests for repeated delivery of the same event ID, a payment greater than the order total, and a second payment with a different event ID. Verified that payments are not counted twice or allowed to exceed the order total. The tests passed.

**Commits:**  
1d0f520, 40d836e, d2e355c

## Other things I noticed

The payment event_id UNIQUE constraint is defined in the database schema. Existing databases created before this schema change may need a database migration because CREATE TABLE IF NOT EXISTS does not modify an existing table.

## Session logs

AI tool used: ChatGPT.  
A ChatGPT AI session summary was saved as `session_logs/chatgpt_session_log_summary.md`. This is a summary, not a verbatim full conversation export. The assessment brief requests the full conversation, so this summary should not be represented as a complete transcript.
