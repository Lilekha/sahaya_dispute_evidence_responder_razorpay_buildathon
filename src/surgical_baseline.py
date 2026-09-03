import hashlib, pandas as pd

def md5(p):
    return hashlib.md5(open(p,'rb').read()).hexdigest()

print('=== BASELINE MD5s ===')
print('disputes.csv  md5:', md5('data/core/disputes.csv'))
print('evidence.csv  md5:', md5('data/core/evidence.csv'))
print()

t = pd.read_csv('data/core/transactions.csv')
c = pd.read_csv('data/core/customers.csv')
m = pd.read_csv('data/core/merchants.csv')
d = pd.read_csv('data/core/disputes.csv')
e = pd.read_csv('data/core/evidence.csv')
dm = pd.read_csv('data/demo/demo_merchants.csv')

print('=== CURRENT STATE ===')
upi_count = (t['payment_method']=='upi').sum()
print(f'transactions: {len(t)} rows, UPI: {upi_count}')
print(f'customers: {len(c)} rows, cols: {len(c.columns)}')
print(f'merchants: {len(m)} rows')
print(f'disputes: {len(d)} rows')
print(f'evidence: {len(e)} rows')
print(f'demo_merchants: {len(dm)} rows')
print()
print('Customer column order:', list(c.columns))
print()

# FIX 1 check
actual = d.groupby(['merchant_id','customer_id']).size().rename('actual').reset_index()
ccheck = c.merge(actual, on=['merchant_id','customer_id'], how='left')
ccheck['actual'] = ccheck['actual'].fillna(0).astype(int)
mismatch = (ccheck['historical_dispute_count'] != ccheck['actual']).sum()
print(f'FIX1: historical_dispute_count mismatches: {mismatch}')

# FIX 2 check
expected = (c['historical_order_count'] > 1).astype(int)
mismatch2 = (c['is_repeat_customer'].astype(int) != expected).sum()
print(f'FIX2: is_repeat_customer mismatches: {mismatch2}')

# FIX 3: documentation_maturity check
ev = e.merge(d[['dispute_id','merchant_id']], on='dispute_id', how='inner')
applicable = ev[ev['applicability_status'] != 'NOT_APPLICABLE']
maturity = applicable.groupby('merchant_id')['applicability_status'].apply(
    lambda s: round(1 - (s=='UNAVAILABLE').mean(), 2)
).rename('evidence_maturity').reset_index()
dm_check = dm.merge(maturity, on='merchant_id', how='left')
print()
print('=== DOC MATURITY CHECK (demo merchants) ===')
for _, row in dm_check.iterrows():
    ev_mat = row['evidence_maturity'] if not pd.isna(row.get('evidence_maturity', float('nan'))) else float('nan')
    print(f"  {row['merchant_id']} {str(row['demo_merchant_name']):<30s}: current={row['documentation_maturity']:.2f}, evidence-derived={ev_mat:.2f}")

# FIX 4: check duplicate files
import os
def fmd5(p):
    if os.path.exists(p):
        return hashlib.md5(open(p,'rb').read()).hexdigest()
    return 'NOT FOUND'

print()
print('=== DUPLICATE FILE CHECK ===')
p1 = fmd5('data/auxiliary/products.csv')
p2 = fmd5('data/auxiliary/products_services.csv')
e1 = fmd5('data/auxiliary/events.csv')
e2 = fmd5('data/auxiliary/fraud_events.csv')
print(f'products.csv md5:          {p1}')
print(f'products_services.csv md5: {p2}')
print(f'Identical: {p1 == p2}')
print()
print(f'events.csv md5:       {e1}')
print(f'fraud_events.csv md5: {e2}')
print(f'Identical: {e1 == e2}')
