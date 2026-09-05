import pandas as pd

D = 'data/'
merchants = pd.read_csv(D+'core/merchants.csv')
disputes  = pd.read_csv(D+'core/disputes.csv')
evidence  = pd.read_csv(D+'core/evidence.csv')
customers = pd.read_csv(D+'core/customers.csv')

# ---------- 1. Verify customer join works ----------
print('customers.csv columns:', [c for c in customers.columns])
merged = disputes.merge(customers[['merchant_id','customer_id','customer_name','city']],
                        on=['merchant_id','customer_id'], how='left')
print(f'disputes with a customer name: {merged.customer_name.notna().sum()} of {len(merged)}')
print(f'disputes with null customer_id: {disputes.customer_id.isna().sum()}')

# ---------- 2. Trim Loops & Knots to 3 disputes, all ACCEPT ----------
lk = merchants.loc[merchants.merchant_name.str.contains('Loops', case=False, na=False),
                   'merchant_id'].iloc[0]
lk_d = disputes[disputes.merchant_id == lk].copy()

# keep the 3 SMALLEST disputes — smallest amounts have the highest
# break-even, so they will always come out as ACCEPT
keep = lk_d.nsmallest(3, 'dispute_amount').dispute_id.tolist()
drop = [x for x in lk_d.dispute_id if x not in keep]

disputes = disputes[~disputes.dispute_id.isin(drop)]
evidence = evidence[~evidence.dispute_id.isin(drop)]

# weaken their evidence so win probability stays low
mask = evidence.dispute_id.isin(keep) & (evidence.required == 1)
evidence.loc[mask, 'available'] = 0
evidence.loc[mask, 'applicability_status'] = 'UNAVAILABLE'
evidence.loc[mask, 'quality_score'] = 0.0

disputes.to_csv(D+'core/disputes.csv', index=False)
evidence.to_csv(D+'core/evidence.csv', index=False)
print(f'\nLoops & Knots: kept {len(keep)}, dropped {len(drop)}')
print('Saved. FitForge left unchanged at 13 disputes / 4 contest.')