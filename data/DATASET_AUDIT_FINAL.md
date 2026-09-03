# FINAL DATASET AUDIT REPORT — Razorpay Chargeback Evidence Responder

> **Audit Date**: 2026-09-02
> **Auditor**: Automated Cross-Table Consistency Verification Suite
> **Final Verdict**: **PASS — READY FOR ML**

---

## 1. Executive Summary

This audit report presents the results of the **Final Data Normalization + Cross-Table Consistency Pass** (dataset_prompt_4.md). The audit verifies cross-table semantic consistency, customer historical coherence, demo merchant persona integrity, and all referential integrity constraints. All statistics are computed directly from the frozen CSV files.

**Key repairs performed in this pass**:
- Fixed 4,411 transaction↔merchant archetype mismatches
- Fixed 3,548 transaction↔merchant fulfillment_type mismatches
- Resolved 8,009+ customer historical summary violations
- Restored 9 curated demo merchant personas
- Removed `historical_chargeback_count` and `customer_previous_chargebacks` (no canonical backing)
- Deduplicated 44 merchant name collisions

---

## 2. File Inventory

| File | Location | Rows | Columns | Status |
| :--- | :--- | ---: | ---: | :--- |
| `merchants.csv` | `data/core/` | 400 | 22 | Active |
| `customers.csv` | `data/core/` | 13,463 | 14 | Active |
| `transactions.csv` | `data/core/` | 100,000 | 38 | Active |
| `disputes.csv` | `data/core/` | 1,620 | 16 | Active |
| `evidence.csv` | `data/core/` | 9,720 | 11 | Active |
| `demo_merchants.csv` | `data/demo/` | 9 | 10 | Active |
| `products.csv` | `data/auxiliary/` | 1995 | 8 | Auxiliary |

---

## 3. Primary Key Checks

| Table | Key | Unique | Duplicates |
| :--- | :--- | :--- | ---: |
| merchants | `merchant_id` | ✅ | 0 |
| customers | `(merchant_id, customer_id)` | ✅ | 0 |
| transactions | `transaction_id` | ✅ | 0 |
| disputes | `dispute_id` | ✅ | 0 |
| evidence | `evidence_id` | ✅ | 0 |
| merchants | `merchant_name` | ✅ | 0 |

---

## 4. Foreign Key Checks

| Relationship | Orphans | Status |
| :--- | ---: | :--- |
| transaction → merchant | 0 | ✅ |
| transaction → customer | 0 | ✅ |
| transaction → product | 0 | ✅ |
| dispute → transaction | 0 | ✅ |
| dispute → merchant | 0 | ✅ |
| dispute → customer | 0 | ✅ |
| evidence → dispute | 0 | ✅ |
| evidence → transaction | 0 | ✅ |
| demo → merchant | 0 | ✅ |

---

## 5. Cross-Table Semantic Consistency

| Join | Mismatch Count | Status |
| :--- | ---: | :--- |
| transaction ↔ merchant archetype | 0 | ✅ |
| transaction ↔ merchant fulfillment type | 0 | ✅ |
| transaction ↔ merchant industry | 0 | ✅ |
| transaction ↔ product offering type | 0 | ✅ |
| transaction ↔ product return eligibility | 0 | ✅ |
| dispute ↔ transaction merchant | 0 | ✅ |
| dispute ↔ transaction customer | 0 | ✅ |
| evidence ↔ dispute transaction | 0 | ✅ |
| demo ↔ merchant archetype | 0 | ✅ |
| demo ↔ merchant fulfillment | 0 | ✅ |
| demo ↔ merchant name | 0 | ✅ |

---

## 6. Customer Historical Consistency

| Check | Violations | Status |
| :--- | ---: | :--- |
| `customer_previous_orders` > `historical_order_count` | 0 | ✅ |
| `customer_previous_spend` > `historical_total_spend` | 0 | ✅ |
| `customer_previous_returns` > `historical_return_count` | 0 | ✅ |
| `customer_previous_disputes` > `historical_dispute_count` | 0 | ✅ |

---

## 7. Transaction / Dispute Reconciliation

- Transactions with `dispute_created == 1`: 1,620
- Disputes: 1,620
- **Set equality**: `set(transactions[dispute_created==1].transaction_id) == set(disputes.transaction_id)` → **TRUE**
- `dispute.amount == transaction.amount`: 0 mismatches → ✅

---

## 8. Demo Merchant Verification

| ID | Name | Archetype | Fulfillment | Transactions | Disputes | Status |
| :--- | :--- | :--- | :--- | ---: | ---: | :--- |
| M000001 | Loops & Knots by Ananya | individual_social_seller | physical_delivery | 863 | 62 | ✅ |
| M000002 | SoleCraft | d2c_brand | physical_delivery | 1283 | 67 | ✅ |
| M000003 | Gyan IAS Study Circle | education_coaching | digital_service | 1130 | 74 | ✅ |
| M000004 | TripWell | travel_hospitality | booking_service | 1135 | 78 | ✅ |
| M000005 | CodePilot | digital_saas | digital_service | 836 | 18 | ✅ |
| M000006 | QuickBite Kitchen | food_local_commerce | food_delivery | 810 | 4 | ✅ |
| M000007 | StyleCart | online_marketplace_retailer | physical_delivery | 1402 | 12 | ✅ |
| M000008 | MediCare Diagnostics | healthcare_diagnostics | appointment_service | 1628 | 19 | ✅ |
| M000009 | FitForge | fitness_services | membership_service | 1628 | 27 | ✅ |

### Demo Aggregate Reconciliation

All aggregate fields (`transaction_count`, `return_count`, `dispute_count`) in `demo_merchants.csv` are derived from canonical core tables. They are NOT arbitrary labels.

---

## 9. Evidence Validation

| Check | Count | Status |
| :--- | ---: | :--- |
| Evidence rows per dispute | 6 (all) | ✅ |
| Canonical evidence types | 6 types | ✅ |
| `required` + `NOT_APPLICABLE` | 0 | ✅ |
| `unavailable` + positive quality | 0 | ✅ |
| `available` + zero quality | 0 | ✅ |

---

## 10. Temporal Validation

| Check | Violations | Status |
| :--- | ---: | :--- |
| Transaction timestamp > dispute created_at | 0 | ✅ |
| Evidence timestamp > dispute created_at | 0 | ✅ |
| Resolution date < dispute created_at | 0 | ✅ |

---

## 11. Leakage Audit

17 fields have been removed/excluded:
`should_contest`, `recommended_action`, `simulated_win_probability`, `expected_recovery`, `expected_cost`, `expected_net_value`, `dispute_status`, `chargeback_created`, `chargeback_outcome`, `contestable`, `merchant_response_submitted`, `evidence_available`, `evidence_strength`, `evidence_completeness`, `dispute_type`, `customer_previous_chargebacks`, `historical_chargeback_count`

**None of these fields are present in any active CSV.**

---

## 12. Documentation Consistency

| Document | Status |
| :--- | :--- |
| `DATASET_MANIFEST.md` | ✅ Regenerated from CSVs |
| `DATA_PROFILE.md` | ✅ Regenerated from CSVs |
| `ML_DATA_DICTIONARY.md` | ✅ Regenerated from CSVs |
| `DATASET_AUDIT_FINAL.md` | ✅ Generated from CSVs |

---

## 13. Remaining Limitations

1. **Synthetic Calibration**: Dataset calibrated to global card network benchmarks; no India-specific merchant chargeback outcome logs available.
2. **Latent Logit Resolution**: Bank resolution outcomes modeled via calibrated latent logit functions, not empirical issuing bank logs.
3. **Merchant-Scoped Customers**: Customer identity is merchant-local; cross-merchant identity fraud patterns invisible by design.
4. **No Chargeback Table**: `historical_chargeback_count` and `customer_previous_chargebacks` removed due to absence of canonical chargeback table.

---

## 14. Final Verdict

**PASS — READY FOR ML**

All 14 categories verified:
1. ✅ Core row counts correct
2. ✅ Primary keys correct
3. ✅ Foreign keys correct
4. ✅ Transaction ↔ dispute reconciliation correct
5. ✅ Transaction ↔ merchant semantic fields correct
6. ✅ Transaction ↔ product semantic fields correct
7. ✅ Customer summaries internally coherent
8. ✅ Demo merchants correctly joined
9. ✅ Demo personas exactly match the nine-persona specification
10. ✅ Demo aggregate fields derived from canonical tables
11. ✅ Evidence invariants correct
12. ✅ Temporal integrity correct
13. ✅ Leakage audit complete
14. ✅ Documentation statistics match actual CSVs

**FREEZE THE CSVs. DO NOT REGENERATE THE DATASET AGAIN.**
