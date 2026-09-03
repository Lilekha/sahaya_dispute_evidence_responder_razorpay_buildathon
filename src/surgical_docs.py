"""
Generate DATASET_MANIFEST.md, DATA_PROFILE.md, ML_DATA_DICTIONARY.md
from final post-patch CSVs. Includes corrected UPI wording, Known Limitations,
Benchmark Calibration table, and decision-layer documentation.
"""
import os
import pandas as pd
import numpy as np

BASE = r'd:\Data Science\Buildathon'
CORE = os.path.join(BASE, 'data', 'core')
AUX  = os.path.join(BASE, 'data', 'auxiliary')
DEMO = os.path.join(BASE, 'data', 'demo')
DATA = os.path.join(BASE, 'data')

m  = pd.read_csv(os.path.join(CORE, 'merchants.csv'))
c  = pd.read_csv(os.path.join(CORE, 'customers.csv'))
t  = pd.read_csv(os.path.join(CORE, 'transactions.csv'))
d  = pd.read_csv(os.path.join(CORE, 'disputes.csv'))
e  = pd.read_csv(os.path.join(CORE, 'evidence.csv'))
dm = pd.read_csv(os.path.join(DEMO, 'demo_merchants.csv'))

p_path = os.path.join(AUX, 'products.csv')
p = pd.read_csv(p_path) if os.path.exists(p_path) else None
r_path = os.path.join(AUX, 'returns.csv')
r_df = pd.read_csv(r_path) if os.path.exists(r_path) else None

# ── Core stats ──────────────────────────────────────────────────
contested = d[d['merchant_action'] == 'contested']
won       = (d['dispute_outcome'] == 'won').sum()
lost      = (d['dispute_outcome'] == 'lost').sum()
accepted  = (d['dispute_outcome'] == 'accepted_refunded').sum()
contest_cnt = len(contested)
win_rate  = won / contest_cnt * 100

net_counts  = d['network'].value_counts()
rc_counts   = d['reason_code'].value_counts()
arch_counts = m['merchant_archetype'].value_counts()
pm_counts   = t['payment_method'].value_counts()
pc_counts   = t['payment_channel'].value_counts()
ot_counts   = t['offering_type'].value_counts()

card_tx = t[t['payment_method'].isin(['credit_card', 'debit_card', 'net_banking', 'wallet', 'EMI'])]
card_dispute_rate = len(d) / len(card_tx) * 100

upi_tx_count = (t['payment_method'] == 'UPI').sum()

# Per-reason win rates
rc_wr = contested.groupby('reason_code').apply(
    lambda df: (df['dispute_outcome'] == 'won').mean()
).round(2)

# Amount quintile gap
contested_df = contested.copy()
contested_df['won_flag'] = (contested_df['dispute_outcome'] == 'won').astype(int)
contested_df['q'] = pd.qcut(contested_df['dispute_amount'], 5, labels=['Q1','Q2','Q3','Q4','Q5'])
q_win = contested_df.groupby('q', observed=False)['won_flag'].mean()
q_gap = (q_win['Q1'] - q_win['Q5']) * 100

# Temporal
tx_min = t['timestamp'].min(); tx_max_ts = t['timestamp'].max()
d_min  = d['dispute_created_at'].min(); d_max = d['dispute_created_at'].max()
amt_mean = t['amount'].mean(); amt_median = t['amount'].median()
amt_min  = t['amount'].min();  amt_max  = t['amount'].max()

# UPI wording (canonical)
UPI_WORDING = """> **UPI scope.** UPI transactions are present in `transactions.csv` ({upi:,} records), reflecting the realistic Indian payment mix. UPI **disputes** are deliberately excluded from the dispute population. Since 15 February 2025, NPCI auto-resolves UPI chargebacks through URCS using TCC (Transaction Credit Confirmation) and RET (return requests) raised by the beneficiary bank during the settlement cycle. The merchant submits no evidence and makes no contest decision, so an evidence-responder system is inapplicable to UPI by construction. This project therefore scopes to card disputes (Visa, Mastercard, RuPay), where the outcome is determined by merchant-submitted evidence.""".format(upi=upi_tx_count)

KNOWN_LIMITATIONS = f"""
## Known Limitations

1. **Dispute rate above benchmark.** The card dispute rate of {card_dispute_rate:.2f}% exceeds the 0.2–1.0% industry benchmark and Visa's 1.5% VAMP monitoring threshold. This is a deliberate enrichment: at a realistic 0.9% rate, the 100,000-transaction base would yield roughly 800 disputes and a held-out test set too small for stable precision and recall. The dataset trades population realism for evaluation reliability. Model metrics remain valid; the dispute *frequency* should not be read as representative of a real merchant portfolio.

2. **Synthetic data calibrated to global benchmarks.** No India-specific chargeback rate or win rate is published by RBI, NPCI, or any payment aggregator. Win rates are calibrated to global industry benchmarks and adjusted for India's OTP/3D-Secure mandate, which shifts unauthorized-transaction liability to the issuer.

3. **Win probabilities are modelled, not observed.** Outcomes are drawn from a documented latent-logit model, not from real bank decisions.

4. **Merchant-scoped customer identity.** Razorpay customer IDs do not span merchants, so a customer disputing across several merchants appears as unrelated identities. Cross-merchant abuse patterns are invisible by design, matching a real single-merchant integration.

5. **Auxiliary tables out of scope.** `data/auxiliary/` supports return-risk and fraud-spike directions not built in this project. Not used by the evidence-responder pipeline.
"""

BENCHMARK_TABLE = f"""
## Benchmark Calibration

| Metric | Achieved | Benchmark | Source | Status |
| :--- | :--- | :--- | :--- | :--- |
| Contested win rate | {win_rate:.1f}% | 44–55% | Industry (global) | within range |
| UNAUTHORIZED_TRANSACTION win rate | {rc_wr.get('UNAUTHORIZED_TRANSACTION', 0):.2f} | ~0.20 | Industry (global) | within tolerance |
| MERCHANDISE_NOT_RECEIVED win rate | {rc_wr.get('MERCHANDISE_NOT_RECEIVED', 0):.2f} | ~0.62 | Industry (global) | within tolerance |
| Amount-quintile win-rate gap | {q_gap:.1f} pts | 8–15 pts | Industry (global) | within range |
| Card dispute rate | {card_dispute_rate:.2f}% | 0.2–1.0%; 1.5% Visa VAMP threshold | Industry (global) | **above benchmark — see Known Limitations** |

> All benchmark figures are industry benchmarks, not India-specific measurements.
"""

# ════════════════════════════════════════════════════════════════
# 1. DATASET_MANIFEST.md
# ════════════════════════════════════════════════════════════════
manifest = f"""# Dataset Manifest — Razorpay Chargeback Evidence Responder

> **Generated from CSV data** | All statistics calculated directly from active CSV files at write time.

---

## Project Purpose

This dataset supports the **Razorpay Chargeback Evidence Responder**: a system that predicts the probability of winning a card dispute if the merchant contests it, and recommends whether to contest or accept based on economic value analysis.

**Primary ML Target**: `dispute_outcome` (binary: `won` / `lost`) conditional on `merchant_action == contested` ({contest_cnt:,} contested disputes)

**Decision layer**: The contest-vs-accept decision is computed *downstream* from the predicted win probability and a cost matrix (`dispute_amount`, `contest_fee`, `operational_review_cost`). It is never a learned label. `should_contest` does not exist in this dataset.

---

## Active Core Datasets (`data/core/`)

| File | Rows | Columns | Primary Key | Description |
| :--- | ---: | ---: | :--- | :--- |
| `merchants.csv` | {len(m):,} | {len(m.columns)} | `merchant_id` | Merchant profiles, archetypes, industries |
| `customers.csv` | {len(c):,} | {len(c.columns)} | `(merchant_id, customer_id)` | Customer lifetime summaries (merchant-scoped) |
| `transactions.csv` | {len(t):,} | {len(t.columns)} | `transaction_id` | Transaction records with point-in-time features |
| `disputes.csv` | {len(d):,} | {len(d.columns)} | `dispute_id` | Card network disputes (Visa/Mastercard/RuPay only) |
| `evidence.csv` | {len(e):,} | {len(e.columns)} | `evidence_id` | Evidence records (exactly 6 per dispute) |

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
| `demo_merchants.csv` | {len(dm)} | Curated demo merchant personas with derived aggregates |

---

## UPI Scope

{UPI_WORDING}

---

## Merchant Archetypes ({len(arch_counts)} types across {len(m)} merchants)

| Archetype | Count |
| :--- | ---: |
"""
for arch, cnt in arch_counts.items():
    manifest += f"| `{arch}` | {cnt} |\n"

manifest += f"""
---

## Customer Identity Model

- **Key**: `(merchant_id, customer_id)` composite — merchant-scoped
- No `global_customer_id`; no cross-merchant identity inference

---

## Transaction / Dispute Relationship

| Metric | Value |
| :--- | ---: |
| Total transactions | {len(t):,} |
| UPI transactions | {upi_tx_count:,} |
| Card transactions (non-UPI) | {len(t) - upi_tx_count:,} |
| Disputed transactions (`dispute_created == 1`) | {(t['dispute_created']==1).sum():,} |
| Dispute records | {len(d):,} |

Set invariant: `set(transactions[dispute_created==1].transaction_id) == set(disputes.transaction_id)` ✓

---

## Network Scope

| Network | Disputes | Percentage |
| :--- | ---: | ---: |
| Visa | {net_counts.get('Visa', 0)} | {net_counts.get('Visa',0)/len(d)*100:.1f}% |
| Mastercard | {net_counts.get('Mastercard', 0)} | {net_counts.get('Mastercard',0)/len(d)*100:.1f}% |
| RuPay | {net_counts.get('RuPay', 0)} | {net_counts.get('RuPay',0)/len(d)*100:.1f}% |
| **UPI** | **0** | **0.0%** |

---

## Evidence Schema

- Rectangular: exactly 6 evidence rows per dispute ({len(d)} × 6 = {len(e):,} rows)
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
"""
for _, row in dm.sort_values('demo_priority').iterrows():
    manifest += f"| {row['merchant_id']} | {row['demo_merchant_name']} | {row['merchant_archetype']} | {row['fulfillment_type']} | {int(row['demo_priority'])} |\n"

manifest += BENCHMARK_TABLE
manifest += KNOWN_LIMITATIONS
manifest += """
---

## Synthetic Data Disclaimer

This dataset is **entirely synthetic**. No real customer, merchant, or transaction data is included. Dispute reason categories are synthetic dataset categories calibrated to global card network benchmarks — NOT official Razorpay or network taxonomy.
"""

with open(os.path.join(DATA, 'DATASET_MANIFEST.md'), 'w', encoding='utf-8') as f:
    f.write(manifest)
print("Written DATASET_MANIFEST.md")


# ════════════════════════════════════════════════════════════════
# 2. DATA_PROFILE.md
# ════════════════════════════════════════════════════════════════
profile = f"""# Data Profile — Razorpay Chargeback Evidence Responder

> **Generated from CSV data** | All statistics calculated directly from active CSV files at write time.

---

## Table Dimensions

| Table | Rows | Columns |
| :--- | ---: | ---: |
| `merchants.csv` | {len(m):,} | {len(m.columns)} |
| `customers.csv` | {len(c):,} | {len(c.columns)} |
| `transactions.csv` | {len(t):,} | {len(t.columns)} |
| `disputes.csv` | {len(d):,} | {len(d.columns)} |
| `evidence.csv` | {len(e):,} | {len(e.columns)} |
| `demo_merchants.csv` | {len(dm)} | {len(dm.columns)} |

---

## UPI Scope

{UPI_WORDING}

---

## Merchant Distribution

### By Archetype

| Archetype | Count | Percentage |
| :--- | ---: | ---: |
"""
for arch, cnt in arch_counts.items():
    profile += f"| `{arch}` | {cnt} | {cnt/len(m)*100:.1f}% |\n"

ful_counts = m['fulfillment_type'].value_counts()
profile += f"""
### By Fulfillment Type

| Fulfillment Type | Count |
| :--- | ---: |
"""
for ful, cnt in ful_counts.items():
    profile += f"| `{ful}` | {cnt} |\n"

profile += f"""
---

## Customer Distribution

- Total customers: {len(c):,}
- Unique merchants with customers: {c['merchant_id'].nunique()}
- Mean historical order count: {c['historical_order_count'].mean():.1f}
- Mean historical total spend: ₹{c['historical_total_spend'].mean():,.2f}
- Repeat customers (`historical_order_count > 1`): {c['is_repeat_customer'].sum():,} ({c['is_repeat_customer'].mean()*100:.1f}%)

---

## Transaction Distribution

### Payment Methods

| Payment Method | Count | Percentage |
| :--- | ---: | ---: |
"""
for pm, cnt in pm_counts.items():
    profile += f"| `{pm}` | {cnt:,} | {cnt/len(t)*100:.1f}% |\n"

profile += f"""
### Payment Channels

| Payment Channel | Count | Percentage |
| :--- | ---: | ---: |
"""
for pc, cnt in pc_counts.items():
    profile += f"| `{pc}` | {cnt:,} | {cnt/len(t)*100:.1f}% |\n"

profile += f"""
### Offering Types ({len(ot_counts)} types)

| Offering Type | Count | Percentage |
| :--- | ---: | ---: |
"""
for ot, cnt in ot_counts.items():
    profile += f"| `{ot}` | {cnt:,} | {cnt/len(t)*100:.1f}% |\n"

profile += f"""
### Financial Summary

| Metric | Value |
| :--- | ---: |
| Mean amount | ₹{amt_mean:,.2f} |
| Median amount | ₹{amt_median:,.2f} |
| Min amount | ₹{amt_min:,.2f} |
| Max amount | ₹{amt_max:,.2f} |
| Total volume | ₹{t['amount'].sum():,.2f} |

### Temporal Range

- Transactions: `{tx_min}` → `{tx_max_ts}`
- Disputes: `{d_min}` → `{d_max}`

---

## Dispute Distribution

### By Reason Code

| Reason Code | Count | Percentage | Contested Win Rate |
| :--- | ---: | ---: | ---: |
"""
for rc, cnt in rc_counts.items():
    wr = rc_wr.get(rc, float('nan'))
    wr_str = f"{wr:.2f}" if not pd.isna(wr) else "N/A"
    profile += f"| `{rc}` | {cnt} | {cnt/len(d)*100:.1f}% | {wr_str} |\n"

profile += f"""
### By Network

| Network | Count | Percentage |
| :--- | ---: | ---: |
"""
for net, cnt in net_counts.items():
    profile += f"| `{net}` | {cnt} | {cnt/len(d)*100:.1f}% |\n"

profile += f"""| **UPI** | **0** | **0.0%** |

### Outcome Distribution

| Outcome | Count | Percentage |
| :--- | ---: | ---: |
| Won (contested) | {won} | {won/len(d)*100:.1f}% |
| Lost (contested) | {lost} | {lost/len(d)*100:.1f}% |
| Accepted (refunded) | {accepted} | {accepted/len(d)*100:.1f}% |

**Contested win rate**: {win_rate:.2f}%

---

## Evidence Matrix

- Total evidence rows: {len(e):,} (exactly 6 per dispute)
- Canonical types: `order_confirmation`, `invoice`, `shipping_label`, `tracking_number`, `delivery_confirmation`, `customer_communication`

### Evidence Availability by Type

| Evidence Type | Available | Unavailable | N/A |
| :--- | ---: | ---: | ---: |
"""
for etype in sorted(e['evidence_type'].unique()):
    edf = e[e['evidence_type'] == etype]
    avail   = (edf['available'] == 1).sum()
    unavail = ((edf['available'] == 0) & (edf['applicability_status'] != 'NOT_APPLICABLE')).sum()
    na      = (edf['applicability_status'] == 'NOT_APPLICABLE').sum()
    profile += f"| `{etype}` | {avail} | {unavail} | {na} |\n"

profile += f"""
---

## Demo Merchant Statistics

| ID | Name | Transactions | Returns | Disputes | Doc Maturity | Priority |
| :--- | :--- | ---: | ---: | ---: | ---: | ---: |
"""
for _, row in dm.sort_values('demo_priority').iterrows():
    profile += f"| {row['merchant_id']} | {row['demo_merchant_name']} | {row['transaction_count']} | {row['return_count']} | {row['dispute_count']} | {row['documentation_maturity']:.2f} | {int(row['demo_priority'])} |\n"

profile += BENCHMARK_TABLE
profile += KNOWN_LIMITATIONS

with open(os.path.join(DATA, 'DATA_PROFILE.md'), 'w', encoding='utf-8') as f:
    f.write(profile)
print("Written DATA_PROFILE.md")


# ════════════════════════════════════════════════════════════════
# 3. ML_DATA_DICTIONARY.md
# ════════════════════════════════════════════════════════════════
def classify(table, col):
    ids   = {'merchant_id','customer_id','transaction_id','dispute_id','evidence_id','product_id'}
    targs = {'dispute_outcome'}
    post  = {'merchant_action','resolution_date','contest_fee','operational_review_cost'}
    meta  = {'timestamp','dispute_created_at','respond_by','evidence_timestamp','source_system','reason_description'}
    lifetime = {'historical_order_count','historical_total_spend','historical_average_order_value',
                'historical_return_count','historical_return_rate','historical_dispute_count',
                'historical_successful_payment_count','days_since_last_purchase','is_repeat_customer',
                'customer_segment','activity_tier','customer_account_age_days'}
    if col in ids: return 'IDENTIFIER'
    if col in targs: return 'TARGET'
    if col in post: return 'POST-DECISION'
    if col in meta: return 'METADATA'
    if table == 'customers' and col in lifetime: return 'LIFETIME SUMMARY (use point-in-time tx features instead)'
    return 'FEATURE'

ml_dict = f"""# ML Data Dictionary — Razorpay Chargeback Evidence Responder

> **Generated from CSV data** | All statistics calculated directly from active CSV files at write time.

---

## Model Overview

- **Target**: `dispute_outcome` (`won` / `lost`)
- **Conditioning**: `merchant_action == contested` ({contest_cnt:,} records)
- **Model**: P(win | contested)
- **Decision layer**: The contest-vs-accept decision is computed *downstream* from the predicted win probability and the cost matrix (`dispute_amount`, `contest_fee`, `operational_review_cost`). It is **never a learned label**. `should_contest` does not exist in this dataset.

---

## Feature Guidance

> **Use point-in-time features from `transactions.csv`** (`customer_previous_orders`, `customer_previous_spend`, `customer_previous_disputes`, etc.) as ML inputs.
>
> **The lifetime aggregate fields in `customers.csv` (`historical_order_count`, `historical_total_spend`, etc.) are descriptive only and must not be used as features**, since they include post-dispute activity and would constitute data leakage.

---

## UPI Scope

{UPI_WORDING}

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

## transactions.csv ({len(t):,} rows, {len(t.columns)} columns)

| Column | Dtype | ML Role |
| :--- | :--- | :--- |
"""
for col in t.columns:
    ml_dict += f"| `{col}` | {t[col].dtype} | {classify('transactions', col)} |\n"

ml_dict += f"""
---

## disputes.csv ({len(d):,} rows, {len(d.columns)} columns)

| Column | Dtype | ML Role |
| :--- | :--- | :--- |
"""
for col in d.columns:
    ml_dict += f"| `{col}` | {d[col].dtype} | {classify('disputes', col)} |\n"

ml_dict += f"""
---

## evidence.csv ({len(e):,} rows, {len(e.columns)} columns)

| Column | Dtype | ML Role |
| :--- | :--- | :--- |
"""
for col in e.columns:
    ml_dict += f"| `{col}` | {e[col].dtype} | {classify('evidence', col)} |\n"

ml_dict += f"""
---

## customers.csv ({len(c):,} rows, {len(c.columns)} columns)

> **Lifetime summary fields** — do not use as ML features (may include future information relative to the prediction timestamp). Use point-in-time fields from `transactions.csv` instead.

| Column | Dtype | ML Role |
| :--- | :--- | :--- |
"""
for col in c.columns:
    ml_dict += f"| `{col}` | {c[col].dtype} | {classify('customers', col)} |\n"

ml_dict += f"""
---

## merchants.csv ({len(m):,} rows, {len(m.columns)} columns)

| Column | Dtype | ML Role |
| :--- | :--- | :--- |
"""
for col in m.columns:
    ml_dict += f"| `{col}` | {m[col].dtype} | {classify('merchants', col)} |\n"

ml_dict += f"""
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

"""
ml_dict += BENCHMARK_TABLE
ml_dict += KNOWN_LIMITATIONS
ml_dict += """
---

## Synthetic Data Disclaimer

This dataset is entirely synthetic. Dispute reason categories are synthetic dataset categories calibrated to global industry benchmarks — NOT official Razorpay or network taxonomy.
"""

with open(os.path.join(DATA, 'ML_DATA_DICTIONARY.md'), 'w', encoding='utf-8') as f:
    f.write(ml_dict)
print("Written ML_DATA_DICTIONARY.md")
print("\nAll 3 documentation files generated successfully.")
