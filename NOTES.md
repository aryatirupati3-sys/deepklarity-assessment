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
a