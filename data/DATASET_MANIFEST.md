# Dataset Manifest — Razorpay Chargeback Evidence Responder

> **Generated from CSV data** | All statistics calculated directly from active CSV files at write time.

---

## Project Purpose

This dataset supports the **Razorpay Chargeback Evidence Responder**: a system that predicts the probability of winning a card dispute if the merchant contests it, and recommends whether to contest or accept based on economic value analysis.

**Primary ML Target**: `dispute_outcome` (binary: `won` / `lost`) conditional on `merchant_action == contested` (1,113 contested disputes)

**Decision layer**: The contest-vs-accept decision is computed *downstream* from the predicted win probability and a cost matrix (`dispute_amount`, `contest_fee`, `operational_review_cost`). It is never a learned label. `should_contest` does not exist in this dataset.

---

## Active Core Datasets (`data/core/`)

| File | Rows | Columns | Primary Key | Description |
| :--- | ---: | ---: | :--- | :--- |
| `merchants.csv` | 400 | 22 | `merchant_id` | Merchant profiles, archetypes, industries |
| `customers.csv` | 13,463 | 14 | `(merchant_id, customer_id)` | Customer lifetime summaries (merchant-scoped) |
| `transactions.csv` | 100,000 | 38 | `transaction_id` | Transaction records with point-in-time features |
| `disputes.csv` | 1,620 | 16 | `dispute_id` | Card network disputes (Visa/Mastercard/RuPay only) |
| `evidence.csv` | 9,720 | 11 | `evidence_id` | Evidence records (exactly 6 per dispute) |

## Auxiliary Datasets (`data/auxiliary/`)

| File | Description |
| :--- | :--- |
| `products.csv` | Product/service catalog |
| `returns.csv` | Return records |
| `events.csv` | Transaction lifecycle events |
| `merchant_hourly_risk.csv` | Hourly merchant risk scores |
| `archive/products_services.csv` | Archived duplicate of products.csv |
| `archive/fraud_events.csv` | Archived duplicate of events.csv |

> Auxiliary datasets are NOT part of the primary ML pipeline.

## Demo Datasets (`data/demo/`)

| File | Rows | Description |
| :--- | ---: | :--- |
| `demo_merchants.csv` | 9 | Curated demo merchant personas with derived aggregates |

---

## UPI Scope

> **UPI scope.** UPI transactions are present in `transactions.csv` (8,832 records), reflecting the realistic Indian payment mix. UPI **disputes** are deliberately excluded from the dispute population. Since 15 February 2025, NPCI auto-resolves UPI chargebacks through URCS using TCC (Transaction Credit Confirmation) and RET (return requests) raised by the beneficiary bank during the settlement cycle. The merchant submits no evidence and makes no contest decision, so an evidence-responder system is inapplicable to UPI by construction. This project therefore scopes to card disputes (Visa, Mastercard, RuPay), where the outcome is determined by merchant-submitted evidence.

---

## Merchant Archetypes (9 types across 400 merchants)

| Archetype | Count |
| :--- | ---: |
| `d2c_brand` | 80 |
| `individual_social_seller` | 66 |
| `food_local_commerce` | 49 |
| `online_marketplace_retailer` | 46 |
| `travel_hospitality` | 38 |
| `digital_saas` | 38 |
| `education_coaching` | 34 |
| `healthcare_diagnostics` | 26 |
| `fitness_services` | 23 |

---

## Customer Identity Model

- **Key**: `(merchant_id, customer_id)` composite — merchant-scoped
- No `global_customer_id`; no cross-merchant identity inference

---

## Transaction / Dispute Relationship

| Metric | Value |
| :--- | ---: |
| Total transactions | 100,000 |
| UPI transactions | 8,832 |
| Card transactions (non-UPI) | 91,168 |
| Disputed transactions (`dispute_created == 1`) | 1,620 |
| Dispute records | 1,620 |

Set invariant: `set(transactions[dispute_created==1].transaction_id) == set(disputes.transaction_id)` ✓

---

## Network Scope

| Network | Disputes | Percentage |
| :--- | ---: | ---: |
| Visa | 790 | 48.8% |
| Mastercard | 551 | 34.0% |
| RuPay | 279 | 17.2% |
| **UPI** | **0** | **0.0%** |

---

## Evidence Schema

- Rectangular: exactly 6 evidence rows per dispute (1620 × 6 = 9,720 rows)
- Canonical types: `order_confirmation`, `invoice`, `shipping_label`, `tracking_number`, `delivery_confirmation`, `customer_communication`

---

## Leakage Rules — Excluded Fields

The following fields are excluded from ML feature matrices:

| Field | Reason |
| :--- | :--- |
| `dispute_outcome` | Target variable |
| `merchant_action` | Conditioning variable |
| `resolution_date` | Post-decision |
| `should_contest` | Removed — circular |
| `recommended_action` | Removed — circular |
| `simulated_win_probability` | Removed — circular |
| `expected_recovery`, `expected_cost`, `expected_net_value` | Removed — circular |
| `dispute_status`, `chargeback_created`, `chargeback_outcome` | Removed — post-decision |
| `contestable`, `dispute_type` | Removed — legacy |
| `customer_previous_chargebacks`, `historical_chargeback_count` | Removed — no canonical backing |

---

## Demo Merchant Personas (9 Curated)

| ID | Name | Archetype | Fulfillment | Priority |
| :--- | :--- | :--- | :--- | ---: |
| M000004 | TripWell | travel_hospitality | booking_service | 1 |
| M000003 | Gyan IAS Study Circle | education_coaching | digital_service | 2 |
| M000002 | SoleCraft | d2c_brand | physical_delivery | 3 |
| M000001 | Loops & Knots by Ananya | individual_social_seller | physical_delivery | 4 |
| M000009 | FitForge | fitness_services | membership_service | 5 |
| M000005 | CodePilot | digital_saas | digital_service | 6 |
| M000008 | MediCare Diagnostics | healthcare_diagnostics | appointment_service | 7 |
| M000007 | StyleCart | online_marketplace_retailer | physical_delivery | 8 |
| M000006 | QuickBite Kitchen | food_local_commerce | food_delivery | 9 |

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

This dataset is **entirely synthetic**. No real customer, merchant, or transaction data is included. Dispute reason categories are synthetic dataset categories calibrated to global card network benchmarks — NOT official Razorpay or network taxonomy.
