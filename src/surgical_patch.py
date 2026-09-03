"""
DATASET_SURGICAL_PATCH_PROMPT.md — Master Patch Script

Fixes 1-4 only (data fixes). Documentation regenerated separately.
disputes.csv and evidence.csv are NEVER touched.
"""
import os, shutil, hashlib
import pandas as pd
import numpy as np

BASE = r'd:\Data Science\Buildathon'
CORE = os.path.join(BASE, 'data', 'core')
AUX  = os.path.join(BASE, 'data', 'auxiliary')
DEMO = os.path.join(BASE, 'data', 'demo')

def md5(p):
    return hashlib.md5(open(p, 'rb').read()).hexdigest()

# ── Lock baseline MD5s ──────────────────────────────────────────
DISPUTES_MD5 = md5(os.path.join(CORE, 'disputes.csv'))
EVIDENCE_MD5 = md5(os.path.join(CORE, 'evidence.csv'))
print(f"Baseline disputes.csv MD5: {DISPUTES_MD5}")
print(f"Baseline evidence.csv MD5: {EVIDENCE_MD5}")
print()

# ── Load files ──────────────────────────────────────────────────
c = pd.read_csv(os.path.join(CORE, 'customers.csv'))
d = pd.read_csv(os.path.join(CORE, 'disputes.csv'))
t = pd.read_csv(os.path.join(CORE, 'transactions.csv'))
e = pd.read_csv(os.path.join(CORE, 'evidence.csv'))
dm = pd.read_csv(os.path.join(DEMO, 'demo_merchants.csv'))

CUSTOMER_COL_ORDER = list(c.columns)  # preserve column order

# ════════════════════════════════════════════════════════════════
# FIX 1 — Recompute customers.historical_dispute_count
# ════════════════════════════════════════════════════════════════
print("=== FIX 1: historical_dispute_count ===")
actual = (
    d.groupby(['merchant_id', 'customer_id'])
     .size()
     .rename('actual_dispute_count')
     .reset_index()
)
c = c.merge(actual, on=['merchant_id', 'customer_id'], how='left')
c['actual_dispute_count'] = c['actual_dispute_count'].fillna(0).astype(int)
n_before = (c['historical_dispute_count'] != c['actual_dispute_count']).sum()
c['historical_dispute_count'] = c['actual_dispute_count']
c = c.drop(columns=['actual_dispute_count'])
print(f"  Corrected {n_before} customer rows")

# ════════════════════════════════════════════════════════════════
# FIX 2 — Make customers.is_repeat_customer consistent
# ════════════════════════════════════════════════════════════════
print("\n=== FIX 2: is_repeat_customer ===")
expected = (c['historical_order_count'] > 1).astype(int)
n_before2 = (c['is_repeat_customer'].astype(int) != expected).sum()
c['is_repeat_customer'] = expected
print(f"  Corrected {n_before2} customer rows")

# Verify column order preserved
assert list(c.columns) == CUSTOMER_COL_ORDER, "Column order changed!"
assert len(c) == 13463, f"Row count changed: {len(c)}"

c.to_csv(os.path.join(CORE, 'customers.csv'), index=False)
print(f"  Saved customers.csv: {len(c)} rows, {len(c.columns)} cols")

# Post-fix verify
n_after1 = (c['historical_dispute_count'] != (
    d.groupby(['merchant_id','customer_id']).size()
     .rename('x').reset_index().set_index(['merchant_id','customer_id'])['x']
     .reindex(pd.MultiIndex.from_frame(c[['merchant_id','customer_id']])).fillna(0).values
)).sum()
expected2 = (c['historical_order_count'] > 1).astype(int)
n_after2 = (c['is_repeat_customer'].astype(int) != expected2).sum()
print(f"  Post-fix historical_dispute_count mismatches: {n_after1}")
print(f"  Post-fix is_repeat_customer mismatches: {n_after2}")

# ════════════════════════════════════════════════════════════════
# FIX 3 — Recompute documentation_maturity from observed evidence
# ════════════════════════════════════════════════════════════════
print("\n=== FIX 3: documentation_maturity + demo_merchants.csv ===")

ev = e.merge(d[['dispute_id', 'merchant_id']], on='dispute_id', how='inner')
applicable = ev[ev['applicability_status'] != 'NOT_APPLICABLE']

maturity = (
    applicable
    .groupby('merchant_id')['applicability_status']
    .apply(lambda s: round(1 - (s == 'UNAVAILABLE').mean(), 2))
    .rename('documentation_maturity_new')
    .reset_index()
)

print("  Before/After documentation_maturity:")
dm = dm.merge(maturity, on='merchant_id', how='left')
dm['documentation_maturity_old'] = dm['documentation_maturity']
dm['documentation_maturity'] = dm['documentation_maturity_new'].fillna(dm['documentation_maturity'])
dm = dm.drop(columns=['documentation_maturity_new'])

for _, row in dm.iterrows():
    print(f"    {row['merchant_id']} {str(row['demo_merchant_name']):<30s}: {row['documentation_maturity_old']:.2f} -> {row['documentation_maturity']:.2f}")
dm = dm.drop(columns=['documentation_maturity_old'])

# Recompute transaction_count, return_count, dispute_count from canonical tables
ret_path = os.path.join(AUX, 'returns.csv')
r_df = pd.read_csv(ret_path) if os.path.exists(ret_path) else None

dm['transaction_count'] = dm['merchant_id'].map(
    t.groupby('merchant_id').size()).fillna(0).astype(int)
dm['dispute_count'] = dm['merchant_id'].map(
    d.groupby('merchant_id').size()).fillna(0).astype(int)
if r_df is not None and 'merchant_id' in r_df.columns:
    dm['return_count'] = dm['merchant_id'].map(
        r_df.groupby('merchant_id').size()).fillna(0).astype(int)
else:
    dm['return_count'] = 0

# Update business_description to match recomputed maturity
# For each merchant: high maturity (≥0.80) → strong record-keeping, low (≤0.60) → informal
desc_map = {
    'M000001': (
        "Crochet clothing, bags, amigurumi toys, and handmade accessories sold via Instagram and WhatsApp. "
        "High documentation maturity: most orders have tracked delivery and invoiced receipts."
    ),
    'M000002': (
        "Online-first D2C footwear brand with a catalogued website. "
        "Strong documentation: shipping labels, tracking updates, and delivery confirmations routinely available."
    ),
    'M000003': (
        "Online and offline preparation for competitive exams (UPSC, IAS). "
        "Moderate documentation: digital-service delivery with course access logs; no physical shipping evidence."
    ),
    'M000004': (
        "Travel bookings and holiday packages. "
        "Moderate documentation: booking confirmations and itineraries available; physical delivery evidence not applicable."
    ),
    'M000005': (
        "Fictional B2B SaaS platform for small businesses. "
        "Good documentation: subscription invoices and access logs routinely maintained."
    ),
    'M000006': (
        "Cloud kitchen delivering food via app and food-delivery platforms. "
        "Moderate documentation: order confirmations available; physical delivery tracking limited to platform handoff."
    ),
    'M000007': (
        "Multi-brand fashion, beauty, and lifestyle marketplace. "
        "High documentation maturity: marketplace-level tracking, return labels, and delivery confirmations."
    ),
    'M000008': (
        "Diagnostic tests and health check-up packages booked online. "
        "Good documentation: appointment confirmations and test reports available; physical delivery limited to home-collection."
    ),
    'M000009': (
        "Gym and fitness studio with membership-based access. "
        "Moderate documentation: membership invoices and check-in logs available; no physical delivery evidence."
    ),
}
dm['business_description'] = dm['merchant_id'].map(desc_map)

# Add demo_priority column
# Rank 1 = most disputes + highest unavailable-evidence share (most useful for dashboard walkthrough)
# Compute unavailable share per merchant
unavail_share = (
    applicable[applicable['applicability_status'] == 'UNAVAILABLE']
    .groupby('merchant_id').size()
    .div(applicable.groupby('merchant_id').size())
    .rename('unavail_share')
    .reset_index()
)
dm = dm.merge(unavail_share, on='merchant_id', how='left')
dm['unavail_share'] = dm['unavail_share'].fillna(0)

# Score: weighted by dispute_count and unavail_share
dm['_priority_score'] = dm['dispute_count'] * (1 + dm['unavail_share'])
dm['demo_priority'] = dm['_priority_score'].rank(ascending=False, method='first').astype(int)
dm = dm.drop(columns=['_priority_score', 'unavail_share'])

assert len(dm) == 9, f"demo_merchants row count changed: {len(dm)}"
print(f"\n  demo_priority assignments:")
for _, row in dm.sort_values('demo_priority').iterrows():
    print(f"    {int(row['demo_priority'])}. {row['merchant_id']} {row['demo_merchant_name']} (disp={row['dispute_count']})")

dm.to_csv(os.path.join(DEMO, 'demo_merchants.csv'), index=False)
print(f"\n  Saved demo_merchants.csv: {len(dm)} rows")

# ════════════════════════════════════════════════════════════════
# FIX 4 — Archive duplicate auxiliary tables
# ════════════════════════════════════════════════════════════════
print("\n=== FIX 4: archive duplicate auxiliary tables ===")
archive_dir = os.path.join(AUX, 'archive')
os.makedirs(archive_dir, exist_ok=True)

files_to_archive = [
    ('products_services.csv', 'products.csv'),
    ('fraud_events.csv',      'events.csv'),
]
for to_move, keep in files_to_archive:
    src = os.path.join(AUX, to_move)
    dst = os.path.join(archive_dir, to_move)
    if os.path.exists(src):
        shutil.move(src, dst)
        print(f"  Moved {to_move} -> archive/ (keeping {keep})")
    elif os.path.exists(dst):
        print(f"  {to_move} already in archive/")
    else:
        print(f"  {to_move} not found — skipping")

archive_contents = os.listdir(archive_dir)
print(f"  archive/ contents: {sorted(archive_contents)}")

# ════════════════════════════════════════════════════════════════
# FINAL MD5 VERIFICATION
# ════════════════════════════════════════════════════════════════
print("\n=== FINAL MD5 VERIFICATION ===")
new_disputes_md5 = md5(os.path.join(CORE, 'disputes.csv'))
new_evidence_md5 = md5(os.path.join(CORE, 'evidence.csv'))
print(f"disputes.csv MD5: {new_disputes_md5}  {'UNCHANGED' if new_disputes_md5 == DISPUTES_MD5 else 'CHANGED — FAIL'}")
print(f"evidence.csv MD5: {new_evidence_md5}  {'UNCHANGED' if new_evidence_md5 == EVIDENCE_MD5 else 'CHANGED — FAIL'}")

assert new_disputes_md5 == DISPUTES_MD5, "disputes.csv was modified — ABORT"
assert new_evidence_md5 == EVIDENCE_MD5, "evidence.csv was modified — ABORT"
print("\nData patch complete.")
