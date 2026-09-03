"""
Final verification for DATASET_SURGICAL_PATCH_PROMPT.md
Prints PASS/FAIL table for all required checks.
"""
import os, hashlib
import pandas as pd

BASE = r'd:\Data Science\Buildathon'
CORE = os.path.join(BASE, 'data', 'core')
AUX  = os.path.join(BASE, 'data', 'auxiliary')
DEMO = os.path.join(BASE, 'data', 'demo')
DATA = os.path.join(BASE, 'data')

BASELINE_DISPUTES_MD5 = '1a255fe01817426acc1da1bb21e6d5ec'
BASELINE_EVIDENCE_MD5 = '2cdea708d3c0446eb68044d1cde9ac34'

def md5(p):
    return hashlib.md5(open(p, 'rb').read()).hexdigest()

m  = pd.read_csv(os.path.join(CORE, 'merchants.csv'))
c  = pd.read_csv(os.path.join(CORE, 'customers.csv'))
t  = pd.read_csv(os.path.join(CORE, 'transactions.csv'))
d  = pd.read_csv(os.path.join(CORE, 'disputes.csv'))
e  = pd.read_csv(os.path.join(CORE, 'evidence.csv'))
dm = pd.read_csv(os.path.join(DEMO, 'demo_merchants.csv'))

results = []
def check(label, condition, detail=''):
    status = 'PASS' if condition else 'FAIL'
    results.append((label, status, detail))
    return condition

print("=" * 70)
print("SURGICAL PATCH VERIFICATION")
print("=" * 70)

# MD5 checks
check('disputes.csv MD5 unchanged',
      md5(os.path.join(CORE, 'disputes.csv')) == BASELINE_DISPUTES_MD5,
      md5(os.path.join(CORE, 'disputes.csv')))
check('evidence.csv MD5 unchanged',
      md5(os.path.join(CORE, 'evidence.csv')) == BASELINE_EVIDENCE_MD5,
      md5(os.path.join(CORE, 'evidence.csv')))

# Row counts
upi_count = (t['payment_method'] == 'UPI').sum()
check('transactions.csv rows == 100,000', len(t) == 100000, str(len(t)))
check('transactions UPI == 8,832',        upi_count == 8832, str(upi_count))
check('customers.csv rows == 13,463',     len(c) == 13463,   str(len(c)))
check('merchants.csv rows == 400',        len(m) == 400,      str(len(m)))
check('disputes.csv rows == 1,620',       len(d) == 1620,     str(len(d)))
check('evidence.csv rows == 9,720',       len(e) == 9720,     str(len(e)))
check('demo_merchants.csv rows == 9',     len(dm) == 9,       str(len(dm)))

# Demo merchant IDs and names unchanged
expected_ids   = ['M000001','M000002','M000003','M000004','M000005',
                  'M000006','M000007','M000008','M000009']
expected_names = ['Loops & Knots by Ananya','SoleCraft','Gyan IAS Study Circle',
                  'TripWell','CodePilot','QuickBite Kitchen',
                  'StyleCart','MediCare Diagnostics','FitForge']
check('demo_merchants IDs M000001-M000009',
      list(dm['merchant_id']) == expected_ids, str(list(dm['merchant_id'])))
check('demo_merchants names unchanged',
      list(dm['demo_merchant_name']) == expected_names,
      str(list(dm['demo_merchant_name'])))
check('demo_merchants has demo_priority column',
      'demo_priority' in dm.columns, str(list(dm.columns)))

# historical_dispute_count
actual = (d.groupby(['merchant_id','customer_id']).size()
           .rename('actual').reset_index())
ccheck = c.merge(actual, on=['merchant_id','customer_id'], how='left')
ccheck['actual'] = ccheck['actual'].fillna(0).astype(int)
hdc_mm = (ccheck['historical_dispute_count'] != ccheck['actual']).sum()
check('historical_dispute_count mismatches == 0', hdc_mm == 0, str(hdc_mm))

# is_repeat_customer
expected_repeat = (c['historical_order_count'] > 1).astype(int)
irc_mm = (c['is_repeat_customer'].astype(int) != expected_repeat).sum()
check('is_repeat_customer mismatches == 0', irc_mm == 0, str(irc_mm))

# documentation_maturity within ±0.01
ev = e.merge(d[['dispute_id','merchant_id']], on='dispute_id', how='inner')
applicable = ev[ev['applicability_status'] != 'NOT_APPLICABLE']
maturity = (applicable.groupby('merchant_id')['applicability_status']
             .apply(lambda s: round(1 - (s=='UNAVAILABLE').mean(), 2), include_groups=False)
             .rename('ev_mat').reset_index())
dm_check = dm.merge(maturity, on='merchant_id', how='left')
max_diff = (dm_check['documentation_maturity'] - dm_check['ev_mat']).abs().max()
check("doc_maturity within ±0.01 of evidence-derived", max_diff <= 0.01, f"max_diff={max_diff:.3f}")

# Rank correlation: maturity ordering agrees with unavailable share
unavail_share = (
    applicable[applicable['applicability_status'] == 'UNAVAILABLE']
    .groupby('merchant_id').size()
    .div(applicable.groupby('merchant_id').size())
    .rename('unavail_share').reset_index()
)
dm_rc = dm.merge(unavail_share, on='merchant_id', how='left').fillna(0)
from scipy.stats import spearmanr
corr, pval = spearmanr(dm_rc['documentation_maturity'], dm_rc['unavail_share'])
check("doc_maturity rank-corr with unavail share is negative and strong",
      corr < -0.5, f"r={corr:.3f}, p={pval:.3f}")

# Archive contents
archive_dir = os.path.join(AUX, 'archive')
archive_files = sorted(os.listdir(archive_dir)) if os.path.exists(archive_dir) else []
check("archive/ contains exactly products_services.csv and fraud_events.csv",
      set(archive_files) == {'products_services.csv', 'fraud_events.csv'},
      str(archive_files))

# FK orphans (core joins)
fk_tx_m = t['merchant_id'].isin(m['merchant_id']).all()
fk_d_t  = d['transaction_id'].isin(t['transaction_id']).all()
fk_e_d  = e['dispute_id'].isin(d['dispute_id']).all()
check("zero FK orphans (tx->merchant, disp->tx, ev->disp)",
      fk_tx_m and fk_d_t and fk_e_d,
      f"tx->m:{fk_tx_m} d->t:{fk_d_t} e->d:{fk_e_d}")

# Contested win rate
contested = d[d['merchant_action'] == 'contested']
wr = (contested['dispute_outcome'] == 'won').mean() * 100
check("contested win rate 45.6% ± 0.1", abs(wr - 45.6) <= 0.1, f"{wr:.2f}%")

# UPI wording in all 3 docs
upi_phrase = "NPCI auto-resolves UPI chargebacks"
for doc in ['DATASET_MANIFEST.md', 'DATA_PROFILE.md', 'ML_DATA_DICTIONARY.md']:
    path = os.path.join(DATA, doc)
    content = open(path, encoding='utf-8').read()
    check(f"{doc} contains corrected UPI wording",
          upi_phrase in content, '')

# Known Limitations in all 3 docs
lim_phrase = "Dispute rate above benchmark"
for doc in ['DATASET_MANIFEST.md', 'DATA_PROFILE.md', 'ML_DATA_DICTIONARY.md']:
    path = os.path.join(DATA, doc)
    content = open(path, encoding='utf-8').read()
    check(f"{doc} contains Known Limitations",
          lim_phrase in content, '')

# Print table
print()
print(f"{'Check':<60s} {'Status':<6s} {'Detail'}")
print("-" * 100)
all_pass = True
for label, status, detail in results:
    print(f"  {label:<58s} {status:<6s} {detail[:30]}")
    if status == 'FAIL':
        all_pass = False

print()
print("=" * 70)
if all_pass:
    print("FINAL VERDICT: PASS — SURGICAL PATCH COMPLETE")
else:
    print("FINAL VERDICT: FAIL — CORRECTIONS REQUIRED")
print("=" * 70)
