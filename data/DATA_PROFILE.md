# Data Profile — Razorpay Chargeback Evidence Responder

> **Generated from CSV data** | All statistics calculated directly from active CSV files at write time.

---

## Table Dimensions

| Table | Rows | Columns |
| :--- | ---: | ---: |
| `merchants.csv` | 400 | 22 |
| `customers.csv` | 13,463 | 14 |
| `transactions.csv` | 100,000 | 38 |
| `disputes.csv` | 1,620 | 16 |
| `evidence.csv` | 9,720 | 11 |
| `demo_merchants.csv` | 9 | 11 |

---

## UPI Scope

> **UPI scope.** UPI transactions are present in `transactions.csv` (8,832 records), reflecting the realistic Indian payment mix. UPI **disputes** are deliberately excluded from the dispute population. Since 15 February 2025, NPCI auto-resolves UPI chargebacks through URCS using TCC (Transaction Credit Confirmation) and RET (return requests) raised by the beneficiary bank during the settlement cycle. The merchant submits no evidence and makes no contest decision, so an evidence-responder system is inapplicable to UPI by construction. This project therefore scopes to card disputes (Visa, Mastercard, RuPay), where the outcome is determined by merchant-submitted evidence.

---

## Merchant Distribution

### By Archetype

| Archetype | Count | Percentage |
| :--- | ---: | ---: |
| `d2c_brand` | 80 | 20.0% |
| `individual_social_seller` | 66 | 16.5% |
| `food_local_commerce` | 49 | 12.2% |
| `online_marketplace_retailer` | 46 | 11.5% |
| `travel_hospitality` | 38 | 9.5% |
| `digital_saas` | 38 | 9.5% |
| `education_coaching` | 34 | 8.5% |
| `healthcare_diagnostics` | 26 | 6.5% |
| `fitness_services` | 23 | 5.8% |

### By Fulfillment Type

| Fulfillment Type | Count |
| :--- | ---: |
| `physical_delivery` | 192 |
| `digital_service` | 72 |
| `food_delivery` | 49 |
| `booking_service` | 38 |
| `appointment_service` | 26 |
| `membership_service` | 23 |

---

## Customer Distribution

- Total customers: 13,463
- Unique merchants with customers: 400
- Mean historical order count: 7.4
- Mean historical total spend: ₹31,274.88
- Repeat customers (`historical_order_count > 1`): 11,351 (84.3%)

---

## Transaction Distribution

### Payment Methods

| Payment Method | Count | Percentage |
| :--- | ---: | ---: |
| `credit_card` | 62,545 | 62.5% |
| `debit_card` | 25,955 | 26.0% |
| `UPI` | 8,832 | 8.8% |
| `net_banking` | 1,238 | 1.2% |
| `wallet` | 783 | 0.8% |
| `EMI` | 647 | 0.6% |

### Payment Channels

| Payment Channel | Count | Percentage |
| :--- | ---: | ---: |
| `pos_qr` | 25,080 | 25.1% |
| `payment_link` | 25,035 | 25.0% |
| `desktop_web` | 24,968 | 25.0% |
| `mobile_app` | 24,917 | 24.9% |

### Offering Types (27 types)

| Offering Type | Count | Percentage |
| :--- | ---: | ---: |
| `footwear` | 26,613 | 26.6% |
| `food_item` | 19,557 | 19.6% |
| `saas_plan` | 8,033 | 8.0% |
| `fashion_apparel` | 6,679 | 6.7% |
| `electronic_accessory` | 5,158 | 5.2% |
| `cosmetics_kit` | 5,006 | 5.0% |
| `general_item` | 5,006 | 5.0% |
| `lab_test` | 3,405 | 3.4% |
| `home_decor` | 3,038 | 3.0% |
| `exam_course` | 2,116 | 2.1% |
| `flight_booking` | 1,837 | 1.8% |
| `gym_membership` | 1,473 | 1.5% |
| `car_rental` | 1,468 | 1.5% |
| `vacation_package` | 1,459 | 1.5% |
| `hotel_stay` | 1,422 | 1.4% |
| `diagnostic_package` | 1,082 | 1.1% |
| `tour_package` | 934 | 0.9% |
| `test_series` | 904 | 0.9% |
| `study_material` | 857 | 0.9% |
| `fitness_class` | 718 | 0.7% |
| `personal_training` | 696 | 0.7% |
| `handmade_accessory` | 654 | 0.7% |
| `crochet_toy` | 501 | 0.5% |
| `mentorship` | 496 | 0.5% |
| `handicraft_item` | 446 | 0.4% |
| `home_sample_collection` | 347 | 0.3% |
| `nutrition_plan` | 95 | 0.1% |

### Financial Summary

| Metric | Value |
| :--- | ---: |
| Mean amount | ₹4,210.54 |
| Median amount | ₹2,284.28 |
| Min amount | ₹76.67 |
| Max amount | ₹124,615.71 |
| Total volume | ₹421,053,725.81 |

### Temporal Range

- Transactions: `2025-01-01 00:20:32` → `2025-12-30 23:57:15`
- Disputes: `2025-01-08 20:45:31` → `2026-02-09 18:48:26`

---

## Dispute Distribution

### By Reason Code

| Reason Code | Count | Percentage | Contested Win Rate |
| :--- | ---: | ---: | ---: |
| `MERCHANDISE_NOT_RECEIVED` | 428 | 26.4% | 0.65 |
| `UNAUTHORIZED_TRANSACTION` | 367 | 22.7% | 0.23 |
| `MERCHANDISE_NOT_AS_DESCRIBED` | 323 | 19.9% | 0.41 |
| `CREDIT_NOT_PROCESSED` | 245 | 15.1% | 0.45 |
| `RECURRING_BILLING_DISPUTE` | 180 | 11.1% | 0.43 |
| `DUPLICATE_TRANSACTION` | 77 | 4.8% | 0.71 |

### By Network

| Network | Count | Percentage |
| :--- | ---: | ---: |
| `Visa` | 790 | 48.8% |
| `Mastercard` | 551 | 34.0% |
| `RuPay` | 279 | 17.2% |
| **UPI** | **0** | **0.0%** |

### Outcome Distribution

| Outcome | Count | Percentage |
| :--- | ---: | ---: |
| Won (contested) | 507 | 31.3% |
| Lost (contested) | 606 | 37.4% |
| Accepted (refunded) | 507 | 31.3% |

**Contested win rate**: 45.55%

---

## Evidence Matrix

- Total evidence rows: 9,720 (exactly 6 per dispute)
- Canonical types: `order_confirmation`, `invoice`, `shipping_label`, `tracking_number`, `delivery_confirmation`, `customer_communication`

### Evidence Availability by Type

| Evidence Type | Available | Unavailable | N/A |
| :--- | ---: | ---: | ---: |
| `customer_communication` | 1251 | 369 | 0 |
| `delivery_confirmation` | 595 | 154 | 871 |
| `invoice` | 1254 | 366 | 0 |
| `order_confirmation` | 1266 | 354 | 0 |
| `shipping_label` | 612 | 137 | 871 |
| `tracking_number` | 612 | 137 | 871 |

---

## Demo Merchant Statistics

| ID | Name | Transactions | Returns | Disputes | Doc Maturity | Priority |
| :--- | :--- | ---: | ---: | ---: | ---: | ---: |
| M000004 | TripWell | 1135 | 0 | 78 | 0.52 | 1 |
| M000003 | Gyan IAS Study Circle | 1130 | 0 | 74 | 0.60 | 2 |
| M000002 | SoleCraft | 1283 | 392 | 67 | 0.76 | 3 |
| M000001 | Loops & Knots by Ananya | 863 | 156 | 62 | 0.89 | 4 |
| M000009 | FitForge | 1628 | 0 | 27 | 0.70 | 5 |
| M000005 | CodePilot | 836 | 0 | 18 | 0.70 | 6 |
| M000008 | MediCare Diagnostics | 1628 | 0 | 19 | 0.79 | 7 |
| M000007 | StyleCart | 1402 | 346 | 12 | 0.92 | 8 |
| M000006 | QuickBite Kitchen | 810 | 0 | 4 | 0.75 | 9 |

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
