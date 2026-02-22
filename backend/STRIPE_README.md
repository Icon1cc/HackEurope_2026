# Stripe Integration

## Overview

InvoiceGuard uses Stripe for three things:

1. **Vendor Payouts (Stripe Connect)** - When an invoice is approved (auto or manual), a `stripe.Transfer` sends money to the vendor's connected Stripe account.
2. **Subscription Billing (Stripe Checkout)** - Users upgrade from Free to Pro via a Stripe Checkout session.
3. **Webhooks** - Stripe sends event confirmations (transfer completed, subscription created/cancelled) to our webhook endpoint.

## Environment Variables

Add these to `backend/.env`:

```
STRIPE_SECRET_KEY=sk_test_...        # Stripe Dashboard > Developers > API keys
STRIPE_PUBLISHABLE_KEY=pk_test_...   # Same page
STRIPE_WEBHOOK_SECRET=whsec_...      # From `stripe listen` CLI or Dashboard > Webhooks
STRIPE_PRO_PRICE_ID=price_...        # Dashboard > Products > Pro plan price ID
```

## Architecture

```
Extraction Pipeline (auto-approve)
        |
        v
execute_vendor_payment()  <---  POST /invoices/{id}/approve (manual)
        |
        +---> stripe.Transfer.create()  ---> Vendor's connected account
        +---> Payment record (status=initiated)
        |
Stripe webhook (transfer.paid)
        |
        +---> Payment.status = confirmed
        +---> Invoice.status = paid
```

## API Endpoints

### POST /api/v1/invoices/{invoice_id}/approve
**Auth:** Bearer token required

Manually approves a flagged invoice and triggers vendor payment.

```bash
curl -X POST http://localhost:8000/api/v1/invoices/{id}/approve \
  -H "Authorization: Bearer <token>"
```

**Response:**
```json
{
  "approved": true,
  "invoice_id": "uuid",
  "payment": {
    "payment_id": "uuid",
    "transfer_id": "tr_...",
    "status": "initiated"
  }
}
```

### POST /api/v1/billing/create-checkout-session
**Auth:** Bearer token required

Creates a Stripe Checkout session for Pro subscription upgrade.

```bash
curl -X POST http://localhost:8000/api/v1/billing/create-checkout-session \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "uuid", "user_email": "user@example.com"}'
```

**Response:**
```json
{
  "checkout_url": "https://checkout.stripe.com/c/pay/cs_test_..."
}
```

### POST /api/v1/webhooks/stripe
**Auth:** None (Stripe sends requests directly)

Handles Stripe webhook events. Verifies the `stripe-signature` header against `STRIPE_WEBHOOK_SECRET`.

**Handled events:**
| Event | Action |
|-------|--------|
| `transfer.paid` | Payment status -> "confirmed", Invoice status -> "paid" |
| `checkout.session.completed` | Logged (no DB update yet) |
| `customer.subscription.deleted` | Logged (no DB update yet) |

## Auto-Approve Payment Flow

When the AI extraction pipeline scores an invoice >= the vendor's `auto_approve_threshold`:

1. `extraction.py` sets `invoice.status = "approved"` and `invoice.auto_approved = True`
2. After DB commit, calls `execute_vendor_payment()`
3. The service looks up the vendor's `stripe_account_id`
4. If the vendor has a connected account, creates a `stripe.Transfer`
5. Creates a `Payment` record with `status="initiated"`
6. Stripe later sends `transfer.paid` webhook -> Payment confirmed, Invoice marked as paid

## Vendor Setup

For a vendor to receive payouts, they need a `stripe_account_id` (Stripe Connect account). Set it via:

```bash
curl -X PATCH http://localhost:8000/api/v1/vendors/{id} \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"stripe_account_id": "acct_..."}'
```

Vendors without a `stripe_account_id` will still have invoices approved and Payment records created, but no actual Stripe transfer occurs.

## Local Development

### Start the webhook listener

```bash
stripe login
stripe listen --forward-to localhost:8000/api/v1/webhooks/stripe
```

Copy the `whsec_...` secret printed by `stripe listen` into your `.env` as `STRIPE_WEBHOOK_SECRET`.

### Trigger test events

```bash
stripe trigger transfer.paid
stripe trigger checkout.session.completed
stripe trigger customer.subscription.deleted
```

## Tests

Run the Stripe test suite:

```bash
cd backend
source .venv/bin/activate
python -m pytest tests/test_stripe_service.py tests/test_approve.py tests/test_billing.py tests/test_webhooks.py -v
```

**Test files:**
| File | Tests | What it covers |
|------|-------|---------------|
| `test_stripe_service.py` | 4 | `execute_vendor_payment()` - transfer success, no account, vendor not found, Stripe error |
| `test_approve.py` | 7 | Approve endpoint - pending, with payment, already approved/paid, not found, no vendor |
| `test_billing.py` | 2 | Checkout session - success, Stripe error |
| `test_webhooks.py` | 6 | Webhook handler - transfer.paid, missing metadata, checkout completed, subscription cancelled, invalid sig, no secret |

All Stripe API calls are mocked with `unittest.mock.patch` - no real Stripe calls in tests.

## Files

| File | Purpose |
|------|---------|
| `app/core/stripe_client.py` | `init_stripe()` - sets `stripe.api_key` at startup |
| `app/core/config.py` | Settings: `stripe_secret_key`, `stripe_publishable_key`, `stripe_webhook_secret`, `stripe_pro_price_id` |
| `app/services/stripe_service.py` | `execute_vendor_payment()` - creates Transfer + Payment record |
| `app/api/routers/approve.py` | `POST /invoices/{id}/approve` - manual approval + payment |
| `app/api/routers/billing.py` | `POST /billing/create-checkout-session` - subscription upgrade |
| `app/api/routers/webhooks.py` | `POST /webhooks/stripe` - event handler (no auth) |
| `app/api/routers/extraction.py` | Auto-approve trigger (lines 185-202) |
| `app/models/vendor.py` | `stripe_account_id` column |
| `app/models/payment.py` | Payment model (initiated -> confirmed lifecycle) |
