# ML Data Dictionary — Razorpay Chargeback Evidence Responder

> **Generated from CSV data** | All statistics calculated directly from active CSV files at write time.

---

## Model Overview

- **Target**: `dispute_outcome` (`won` / `lost`)
- **Conditioning**: `merchant_action == contested` (1,113 records)
- **Model**: P(win | contested)
- **Decision layer**: The contest-vs-accept decision is computed *downstream* from the predicted win probability and the cost matrix (`dispute_amount`, `contest_fee`, `operational_review_cost`). It is **never a learned label**. `should_contest` does not exist in this dataset.

---

## Feature Guidance

> **Use point-in-time features from `transactions.csv`** (`customer_previous_orders`, `customer_previous_spend`, `customer_previous_disputes`, etc.) as ML inputs.
>
> **The lifetime aggregate fields in `customers.csv` (`historical_order_count`, `historical_total_spend`, etc.) are descriptive only and must not be used as features**, since they include post-dispute activity and would constitute data leakage.

---

## UPI Scope

> **UPI scope.** UPI transactions are present in `transactions.csv` (8,832 records), reflecting the realistic Indian payment mix. UPI **disputes** are deliberately excluded from the dispute population. Since 15 February 2025, NPCI auto-resolves UPI chargebacks through URCS using TCC (Transaction Credit Confirmation) and RET (return requests) raised by the beneficiary bank during the settlement cycle. The merchant submits no evidence and makes no contest decision, so an evidence-responder system is inapplicable to UPI by construction. This project therefore scopes to card disputes (Visa, Mastercard, RuPay), where the outcome is determined by merchant-submitted evidence.

---

## ML Role Classification

| Role | Description |
| :--- | :--- |
| **FEATURE** | Available at decision time; safe for ML input |
| **TARGET** | The label to predict |
| **IDENTIFIER** | Entity key; not a feature |
| **POST-DECISION** | Available only after the outcome; must be excluded |
| **METADATA** | Timestamps, descriptions |
| **LIFETIME SUMMARY** | Customer-level aggregates that may contain future information — descriptive only |

---

## transactions.csv (100,000 rows, 38 columns)

| Column | Dtype | ML Role |
| :--- | :--- | :--- |
| `transaction_id` | object | IDENTIFIER |
| `merchant_id` | object | IDENTIFIER |
| `customer_id` | object | IDENTIFIER |
| `product_id` | object | IDENTIFIER |
| `return_eligible` | int64 | FEATURE |
| `timestamp` | object | METADATA |
| `amount` | float64 | FEATURE |
| `currency` | object | FEATURE |
| `payment_method` | object | FEATURE |
| `payment_channel` | object | FEATURE |
| `offering_type` | object | FEATURE |
| `customer_account_age_days` | int64 | FEATURE |
| `customer_previous_orders` | int64 | FEATURE |
| `customer_previous_spend` | float64 | FEATURE |
| `customer_previous_returns` | int64 | FEATURE |
| `customer_previous_disputes` | int64 | FEATURE |
| `days_since_customer_last_purchase` | int64 | FEATURE |
| `device_age_days` | int64 | FEATURE |
| `is_new_device` | int64 | FEATURE |
| `device_transaction_count` | int64 | FEATURE |
| `ip_risk_score` | float64 | FEATURE |
| `location_distance_from_typical_customer_location` | float64 | FEATURE |
| `authentication_status` | object | FEATURE |
| `authentication_method` | object | FEATURE |
| `payment_attempt_count` | int64 | FEATURE |
| `is_international` | int64 | FEATURE |
| `billing_shipping_mismatch` | float64 | FEATURE |
| `order_processing_time_hours` | float64 | FEATURE |
| `fulfillment_status` | object | FEATURE |
| `delivery_status` | object | FEATURE |
| `delivery_confirmation` | float64 | FEATURE |
| `delivery_otp_verified` | float64 | FEATURE |
| `return_requested` | int64 | FEATURE |
| `return_reason` | object | FEATURE |
| `dispute_created` | int64 | FEATURE |
| `merchant_archetype` | object | FEATURE |
| `fulfillment_type` | object | FEATURE |
| `industry` | object | FEATURE |

---

## disputes.csv (1,620 rows, 16 columns)

| Column | Dtype | ML Role |
| :--- | :--- | :--- |
| `dispute_id` | object | IDENTIFIER |
| `transaction_id` | object | IDENTIFIER |
| `merchant_id` | object | IDENTIFIER |
| `customer_id` | object | IDENTIFIER |
| `network` | object | FEATURE |
| `reason_code` | object | FEATURE |
| `reason_description` | object | METADATA |
| `dispute_created_at` | object | METADATA |
| `dispute_amount` | float64 | FEATURE |
| `contest_fee` | float64 | POST-DECISION |
| `operational_review_cost` | float64 | POST-DECISION |
| `respond_by` | object | METADATA |
| `days_to_deadline` | int64 | FEATURE |
| `merchant_action` | object | POST-DECISION |
| `dispute_outcome` | object | TARGET |
| `resolution_date` | object | POST-DECISION |

---

## evidence.csv (9,720 rows, 11 columns)

| Column | Dtype | ML Role |
| :--- | :--- | :--- |
| `evidence_id` | object | IDENTIFIER |
| `dispute_id` | object | IDENTIFIER |
| `transaction_id` | object | IDENTIFIER |
| `evidence_type` | object | FEATURE |
| `applicability_status` | object | FEATURE |
| `available` | int64 | FEATURE |
| `required` | int64 | FEATURE |
| `relevant` | int64 | FEATURE |
| `quality_score` | float64 | FEATURE |
| `evidence_timestamp` | object | METADATA |
| `source_system` | object | METADATA |

---

## customers.csv (13,463 rows, 14 columns)

> **Lifetime summary fields** — do not use as ML features (may include future information relative to the prediction timestamp). Use point-in-time fields from `transactions.csv` instead.

| Column | Dtype | ML Role |
| :--- | :--- | :--- |
| `merchant_id` | object | IDENTIFIER |
| `customer_id` | object | IDENTIFIER |
| `customer_account_age_days` | int64 | LIFETIME SUMMARY (use point-in-time tx features instead) |
| `customer_segment` | object | LIFETIME SUMMARY (use point-in-time tx features instead) |
| `activity_tier` | object | LIFETIME SUMMARY (use point-in-time tx features instead) |
| `historical_order_count` | int64 | LIFETIME SUMMARY (use point-in-time tx features instead) |
| `historical_total_spend` | float64 | LIFETIME SUMMARY (use point-in-time tx features instead) |
| `historical_average_order_value` | float64 | LIFETIME SUMMARY (use point-in-time tx features instead) |
| `historical_return_count` | int64 | LIFETIME SUMMARY (use point-in-time tx features instead) |
| `historical_return_rate` | float64 | LIFETIME SUMMARY (use point-in-time tx features instead) |
| `historical_dispute_count` | int64 | LIFETIME SUMMARY (use point-in-time tx features instead) |
| `historical_successful_payment_count` | int64 | LIFETIME SUMMARY (use point-in-time tx features instead) |
| `days_since_last_purchase` | int64 | LIFETIME SUMMARY (use point-in-time tx features instead) |
| `is_repeat_customer` | int64 | LIFETIME SUMMARY (use point-in-time tx features instead) |

---

## merchants.csv (400 rows, 22 columns)

| Column | Dtype | ML Role |
| :--- | :--- | :--- |
| `merchant_id` | object | IDENTIFIER |
| `merchant_name` | object | FEATURE |
| `merchant_archetype` | object | FEATURE |
| `industry` | object | FEATURE |
| `business_size` | object | FEATURE |
| `sales_channel` | object | FEATURE |
| `fulfillment_type` | object | FEATURE |
| `subscription_supported` | int64 | FEATURE |
| `international_sales` | int64 | FEATURE |
| `monthly_transaction_volume` | int64 | FEATURE |
| `average_order_value` | float64 | FEATURE |
| `median_order_value` | float64 | FEATURE |
| `baseline_return_rate` | float64 | FEATURE |
| `baseline_dispute_rate` | float64 | FEATURE |
| `baseline_chargeback_rate` | float64 | FEATURE |
| `baseline_repeat_customer_rate` | float64 | FEATURE |
| `merchant_age_months` | int64 | FEATURE |
| `customer_base_size` | int64 | FEATURE |
| `documentation_maturity` | float64 | FEATURE |
| `fulfillment_tracking_available` | int64 | FEATURE |
| `customer_support_channel` | object | FEATURE |
| `refund_policy_documented` | int64 | FEATURE |

---

## Excluded / Removed Fields

| Field | Reason |
| :--- | :--- |
| `should_contest` | Circular — derived from target |
| `recommended_action` | Circular — derived from target |
| `simulated_win_probability` | Circular — derived from target |
| `expected_recovery`, `expected_cost`, `expected_net_value` | Circular — derived from target |
| `dispute_status`, `chargeback_created`, `chargeback_outcome` | Post-decision leakage |
| `contestable`, `dispute_type` | Legacy fields |
| `customer_previous_chargebacks`, `historical_chargeback_count` | No canonical backing table |

---

## Point-in-Time vs Lifetime Features

| Feature | Source | Semantics | ML Safe? |
| :--- | :--- | :--- | :--- |
| `customer_previous_orders` | transactions | Orders before this tx | ✅ Yes |
| `customer_previous_spend` | transactions | Spend before this tx | ✅ Yes |
| `customer_previous_returns` | transactions | Returns before this tx | ✅ Yes |
| `customer_previous_disputes` | transactions | Disputes before this tx | ✅ Yes |
| `historical_order_count` | customers | Lifetime total | ⚠️ No — may include future |
| `historical_total_spend` | customers | Lifetime total | ⚠️ No — may include future |
| `historical_dispute_count` | customers | Lifetime total | ⚠️ No — may include future |

---


## Benchmark Calibration

| Metric | Achieved | Benchmark | Source | Status |
| :--- | :--- | :--- | :--- | :--- |
| Contested win rate | 45.6% | 44–55% | Industry (global) | within range |
| UNAUTHORIZED_TRANSACTION win rate | 0.23 | ~0.20 | Industry (global) | within tolerance |
| MERCHANDISE_NOT_RECEIVED win rate | 0.65 | ~0.62 | Industry (global) | within tolerance |
| Amount-quintile win-rate gap | 13.0 pts | 8–15 pts | Industry (global) | within range |
| Card dispute rate | 1.78% | 0.2–1.0%; 1.5% Visa VAMP threshold | Industry (global) | **above benchmark — see Known Limitations** |

> All benchmark figures are industry benchmarks, not India-specific measurements.

## Known Limitations

1. **Dispute rate above benchmark.** The card dispute rate of 1.78% exceeds the 0.2–1.0% industry benchmark and Visa's 1.5% VAMP monitoring threshold. This is a deliberate enrichment: at a realistic 0.9% rate, the 100,000-transaction base would yield roughly 800 disputes and a held-out test set too small for stable precision and recall. The dataset trades population realism for evaluation reliability. Model metrics remain valid; the dispute *frequency* should not be read as representative of a real merchant portfolio.

2. **Synthetic data calibrated to global benchmarks.** No India-specific chargeback rate or win rate is published by RBI, NPCI, or any payment aggregator. Win rates are calibrated to global industry benchmarks and adjusted for India's OTP/3D-Secure mandate, which shifts unauthorized-transaction liability to the issuer.

3. **Win probabilities are modelled, not observed.** Outcomes are drawn from a documented latent-logit model, not from real bank decisions.

4. **Merchant-scoped customer identity.** Razorpay customer IDs do not span merchants, so a customer disputing across several merchants appears as unrelated identities. Cross-merchant abuse patterns are invisible by design, matching a real single-merchant integration.

5. **Auxiliary tables out of scope.** `data/auxiliary/` supports return-risk and fraud-spike directions not built in this project. Not used by the evidence-responder pipeline.

---

## Synthetic Data Disclaimer

This dataset is entirely synthetic. Dispute reason categories are synthetic dataset categories calibrated to global industry benchmarks — NOT official Razorpay or network taxonomy.
