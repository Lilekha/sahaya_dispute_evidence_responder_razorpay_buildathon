"""Deep audit script for dataset_prompt_4.md — identifies all cross-table inconsistencies."""
import pandas as pd
import os
import json

base = r'd:\Data Science\Buildathon'
core = os.path.join(base, 'data', 'core')
aux = os.path.join(base, 'data', 'auxiliary')
demo_dir = os.path.join(base, 'data', 'demo')

m = pd.read_csv(os.path.join(core, 'merchants.csv'))
c = pd.read_csv(os.path.join(core, 'customers.csv'))
t = pd.read_csv(os.path.join(core, 'transactions.csv'))
d = pd.read_csv(os.path.join(core, 'disputes.csv'))
e = pd.read_csv(os.path.join(core, 'evidence.csv'))
dm = pd.read_csv(os.path.join(demo_dir, 'demo_merchants.csv'))

print("=" * 60)
print("DEEP CROSS-TABLE AUDIT")
print("=" * 60)

# 1. Demo merchants
print("\n--- DEMO MERCHANTS (current) ---")
print(dm.to_string(index=False))

print("\n--- CORE MERCHANTS M000001-M000009 ---")
demo_ids = [f'M00000{i}' for i in range(1, 10)]
core_demo = m[m['merchant_id'].isin(demo_ids)][['merchant_id', 'merchant_name', 'merchant_archetype', 'industry', 'fulfillment_type', 'subscription_supported', 'international_sales']]
print(core_demo.to_string(index=False))

# 2. Merchant-Transaction semantic joins
print("\n--- TRANSACTION <-> MERCHANT SEMANTIC JOINS ---")
merged = t.merge(m[['merchant_id', 'merchant_archetype', 'fulfillment_type', 'industry', 'subscription_supported', 'international_sales']], on='merchant_id', suffixes=('_tx', '_m'))
for col in ['merchant_archetype', 'fulfillment_type', 'industry']:
    mm = (merged[f'{col}_tx'] != merged[f'{col}_m']).sum()
    print(f"  {col} mismatch: {mm}")

# 3. Subscription consistency
print("\n--- SUBSCRIPTION CONSISTENCY ---")
# Check if any subscription-like offering_types exist for non-subscription merchants
if 'offering_type' in t.columns:
    sub_offerings = t[t['offering_type'].str.contains('subscription', case=False, na=False)]
    if len(sub_offerings) > 0:
        sub_merged = sub_offerings.merge(m[['merchant_id', 'subscription_supported']], on='merchant_id')
        no_sub = sub_merged[sub_merged['subscription_supported'] == False]
        print(f"  Subscription offerings from non-subscription merchants: {len(no_sub)}")
    else:
        print("  No subscription offerings found in transactions")
    print(f"  Total offering_type values: {t['offering_type'].value_counts().to_dict()}")

# 4. Customer historical consistency
print("\n--- CUSTOMER HISTORICAL CONSISTENCY ---")
# Check customer_previous_* vs historical_*
tx_max = t.groupby(['merchant_id', 'customer_id']).agg(
    max_prev_orders=('customer_previous_orders', 'max'),
    max_prev_spend=('customer_previous_spend', 'max'),
    max_prev_returns=('customer_previous_returns', 'max'),
    max_prev_disputes=('customer_previous_disputes', 'max'),
    tx_count=('transaction_id', 'count')
).reset_index()

cust_merged = tx_max.merge(c, on=['merchant_id', 'customer_id'], how='inner')
violations = {
    'prev_orders > hist_orders': (cust_merged['max_prev_orders'] > cust_merged['historical_order_count']).sum(),
    'prev_spend > hist_spend': (cust_merged['max_prev_spend'] > cust_merged['historical_total_spend'] + 0.01).sum(),
    'prev_returns > hist_returns': (cust_merged['max_prev_returns'] > cust_merged['historical_return_count']).sum(),
    'prev_disputes > hist_disputes': (cust_merged['max_prev_disputes'] > cust_merged['historical_dispute_count']).sum(),
}
for k, v in violations.items():
    print(f"  {k}: {v}")

# 5. Point-in-time monotonicity
print("\n--- POINT-IN-TIME MONOTONICITY ---")
t_sorted = t.sort_values(['merchant_id', 'customer_id', 'timestamp'])
for col in ['customer_previous_orders', 'customer_previous_spend', 'customer_previous_returns', 'customer_previous_disputes']:
    grouped = t_sorted.groupby(['merchant_id', 'customer_id'])[col]
    non_mono = 0
    for name, group in grouped:
        vals = group.values
        if len(vals) > 1:
            for i in range(1, len(vals)):
                if vals[i] < vals[i-1]:
                    non_mono += 1
                    break
    print(f"  {col} non-monotonic customers: {non_mono}")

# 6. Product table check
print("\n--- PRODUCT TABLE ---")
for pf in ['products.csv', 'products_services.csv']:
    pp = os.path.join(aux, pf)
    if os.path.exists(pp):
        p = pd.read_csv(pp)
        print(f"  {pf}: {len(p)} rows, {len(p.columns)} cols")
        print(f"    Columns: {list(p.columns)}")
        # Check FK
        if 'merchant_id' in p.columns:
            orphan_m = (~p['merchant_id'].isin(m['merchant_id'])).sum()
            print(f"    Orphan merchant_ids: {orphan_m}")
        if 'product_id' in p.columns and 'product_id' in t.columns:
            # Check tx product_id FK
            tx_prods = t[['merchant_id', 'product_id']].dropna(subset=['product_id'])
            p_prods = p[['merchant_id', 'product_id']].drop_duplicates()
            tx_in_p = tx_prods.merge(p_prods, on=['merchant_id', 'product_id'], how='left', indicator=True)
            orphan_tx_prod = (tx_in_p['_merge'] == 'left_only').sum()
            print(f"    Transaction product_ids not in product table: {orphan_tx_prod}")
        if 'offering_type' in p.columns and 'offering_type' in t.columns:
            # Check offering_type agreement
            tp = t[['product_id', 'merchant_id', 'offering_type']].dropna(subset=['product_id']).merge(
                p[['product_id', 'merchant_id', 'offering_type']], on=['product_id', 'merchant_id'], suffixes=('_tx', '_p'), how='inner')
            ot_mismatch = (tp['offering_type_tx'] != tp['offering_type_p']).sum()
            print(f"    offering_type mismatch (tx vs product): {ot_mismatch}")
        if 'return_eligible' in p.columns and 'return_eligible' in t.columns:
            tp2 = t[['product_id', 'merchant_id', 'return_eligible']].dropna(subset=['product_id']).merge(
                p[['product_id', 'merchant_id', 'return_eligible']], on=['product_id', 'merchant_id'], suffixes=('_tx', '_p'), how='inner')
            re_mismatch = (tp2['return_eligible_tx'] != tp2['return_eligible_p']).sum()
            print(f"    return_eligible mismatch (tx vs product): {re_mismatch}")
    else:
        print(f"  {pf}: NOT FOUND")

# 7. Auxiliary FK checks
print("\n--- AUXILIARY FK CHECKS ---")
for fname in ['returns.csv', 'events.csv', 'fraud_events.csv', 'merchant_hourly_risk.csv']:
    fp = os.path.join(aux, fname)
    if os.path.exists(fp):
        df = pd.read_csv(fp)
        print(f"  {fname}: {len(df)} rows")
        if 'transaction_id' in df.columns:
            orphan = (~df['transaction_id'].isin(t['transaction_id'])).sum()
            print(f"    Orphan transaction_ids: {orphan}")
        if 'merchant_id' in df.columns:
            orphan_m = (~df['merchant_id'].isin(m['merchant_id'])).sum()
            print(f"    Orphan merchant_ids: {orphan_m}")
    else:
        print(f"  {fname}: NOT FOUND")

# 8. Dispute consistency
print("\n--- DISPUTE <-> TRANSACTION CONSISTENCY ---")
dt = d.merge(t[['transaction_id', 'merchant_id', 'customer_id', 'amount']], on='transaction_id', suffixes=('_d', '_t'))
print(f"  merchant_id mismatch: {(dt['merchant_id_d'] != dt['merchant_id_t']).sum()}")
print(f"  customer_id mismatch: {(dt['customer_id_d'] != dt['customer_id_t']).sum()}")
print(f"  amount mismatch: {(dt['dispute_amount'] != dt['amount']).sum()}")

# 9. Evidence consistency
print("\n--- EVIDENCE <-> DISPUTE CONSISTENCY ---")
ed = e.merge(d[['dispute_id', 'transaction_id']], on='dispute_id', suffixes=('_e', '_d'))
print(f"  transaction_id mismatch (evidence vs dispute): {(ed['transaction_id_e'] != ed['transaction_id_d']).sum()}")

# 10. Merchant name uniqueness
print("\n--- MERCHANT NAME UNIQUENESS ---")
dup_names = m['merchant_name'].value_counts()
dups = dup_names[dup_names > 1]
print(f"  Duplicate merchant names: {len(dups)}")
if len(dups) > 0:
    print(f"  Examples: {dups.head(10).to_dict()}")

print("\n" + "=" * 60)
print("END DEEP AUDIT")
print("=" * 60)
