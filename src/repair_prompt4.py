"""
Master repair script for dataset_prompt_4.md
Final Data Normalization + Cross-Table Consistency Pass

Fixes:
  1. Demo merchant personas (M000001-M000009) in merchants.csv
  2. Transaction <-> merchant denormalized field sync
  3. Customer historical summary recomputation
  4. Remove historical_chargeback_count / customer_previous_chargebacks
  5. Duplicate merchant name deduplication
  6. Rebuild demo_merchants.csv to 9 rows with derived aggregates
"""
import os
import pandas as pd
import numpy as np

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORE = os.path.join(BASE, 'data', 'core')
AUX = os.path.join(BASE, 'data', 'auxiliary')
DEMO = os.path.join(BASE, 'data', 'demo')


def load_all():
    m = pd.read_csv(os.path.join(CORE, 'merchants.csv'))
    c = pd.read_csv(os.path.join(CORE, 'customers.csv'))
    t = pd.read_csv(os.path.join(CORE, 'transactions.csv'))
    d = pd.read_csv(os.path.join(CORE, 'disputes.csv'))
    e = pd.read_csv(os.path.join(CORE, 'evidence.csv'))
    return m, c, t, d, e


def fix_demo_merchant_personas(m):
    """Fix M000001-M000009 to match the authoritative 9-merchant specification."""
    print("\n=== 1. FIXING DEMO MERCHANT PERSONAS ===")

    # Authoritative specification from dataset_prompt_4.md Section 6
    spec = {
        'M000001': {
            'merchant_name': 'Loops & Knots by Ananya',
            'merchant_archetype': 'individual_social_seller',
            'industry': 'crochet_accessories',
            'fulfillment_type': 'physical_delivery',
            'sales_channel': 'Instagram, WhatsApp, payment links',
        },
        'M000002': {
            'merchant_name': 'SoleCraft',
            'merchant_archetype': 'd2c_brand',
            'industry': 'footwear',
            'fulfillment_type': 'physical_delivery',
            'sales_channel': 'website',
        },
        'M000003': {
            'merchant_name': 'Gyan IAS Study Circle',
            'merchant_archetype': 'education_coaching',
            'industry': 'exam_prep',
            'fulfillment_type': 'digital_service',
            'sales_channel': 'website, app',
        },
        'M000004': {
            'merchant_name': 'TripWell',
            'merchant_archetype': 'travel_hospitality',
            'industry': 'travel_agency',
            'fulfillment_type': 'booking_service',
            'sales_channel': 'website, app',
        },
        'M000005': {
            'merchant_name': 'CodePilot',
            'merchant_archetype': 'digital_saas',
            'industry': 'b2b_software',
            'fulfillment_type': 'digital_service',
            'sales_channel': 'website',
        },
        'M000006': {
            'merchant_name': 'QuickBite Kitchen',
            'merchant_archetype': 'food_local_commerce',
            'industry': 'local_restaurant',
            'fulfillment_type': 'food_delivery',
            'sales_channel': 'app, food platforms',
        },
        'M000007': {
            'merchant_name': 'StyleCart',
            'merchant_archetype': 'online_marketplace_retailer',
            'industry': 'beauty_marketplace',
            'fulfillment_type': 'physical_delivery',
            'sales_channel': 'website, app',
        },
        'M000008': {
            'merchant_name': 'MediCare Diagnostics',
            'merchant_archetype': 'healthcare_diagnostics',
            'industry': 'telehealth',
            'fulfillment_type': 'appointment_service',
            'sales_channel': 'website, app, clinic',
        },
        'M000009': {
            'merchant_name': 'FitForge',
            'merchant_archetype': 'fitness_services',
            'industry': 'fitness_program',
            'fulfillment_type': 'membership_service',
            'sales_channel': 'app, in-person',
        },
    }

    for mid, fields in spec.items():
        mask = m['merchant_id'] == mid
        if mask.sum() == 0:
            print(f"  WARNING: {mid} not found in merchants.csv!")
            continue
        old_name = m.loc[mask, 'merchant_name'].values[0]
        for col, val in fields.items():
            old_val = m.loc[mask, col].values[0]
            if str(old_val) != str(val):
                print(f"  {mid}: {col} '{old_val}' -> '{val}'")
            m.loc[mask, col] = val

    return m


def sync_transaction_merchant_fields(t, m):
    """Synchronize denormalized merchant fields in transactions from merchants.csv."""
    print("\n=== 2. SYNCING TRANSACTION <-> MERCHANT FIELDS ===")

    merge_cols = ['merchant_archetype', 'fulfillment_type', 'industry']
    m_lookup = m[['merchant_id'] + merge_cols].copy()

    before_arch = (t.merge(m_lookup, on='merchant_id', suffixes=('_tx', '_m'))['merchant_archetype_tx'] !=
                   t.merge(m_lookup, on='merchant_id', suffixes=('_tx', '_m'))['merchant_archetype_m']).sum()
    before_ful = (t.merge(m_lookup, on='merchant_id', suffixes=('_tx', '_m'))['fulfillment_type_tx'] !=
                  t.merge(m_lookup, on='merchant_id', suffixes=('_tx', '_m'))['fulfillment_type_m']).sum()

    # Drop old columns and re-merge from merchant
    t = t.drop(columns=merge_cols)
    t = t.merge(m_lookup, on='merchant_id', how='left')

    # Verify
    merged_check = t.merge(m_lookup, on='merchant_id', suffixes=('_tx', '_m'))
    after_arch = (merged_check['merchant_archetype_tx'] != merged_check['merchant_archetype_m']).sum()
    after_ful = (merged_check['fulfillment_type_tx'] != merged_check['fulfillment_type_m']).sum()
    after_ind = (merged_check['industry_tx'] != merged_check['industry_m']).sum()

    print(f"  merchant_archetype mismatch: {before_arch} -> {after_arch}")
    print(f"  fulfillment_type mismatch: {before_ful} -> {after_ful}")
    print(f"  industry mismatch: {after_ind}")

    return t


def recompute_customer_historical(c, t, d):
    """Recompute customer historical summary fields from canonical tables."""
    print("\n=== 3. RECOMPUTING CUSTOMER HISTORICAL SUMMARIES ===")

    # Load returns if available
    returns_path = os.path.join(AUX, 'returns.csv')
    if os.path.exists(returns_path):
        r = pd.read_csv(returns_path)
        ret_counts = r.groupby(['merchant_id', 'customer_id']).size().reset_index(name='ret_count')
    else:
        ret_counts = pd.DataFrame(columns=['merchant_id', 'customer_id', 'ret_count'])

    # Compute from transactions
    tx_agg = t.groupby(['merchant_id', 'customer_id']).agg(
        tx_count=('transaction_id', 'count'),
        tx_total_spend=('amount', 'sum')
    ).reset_index()

    # Compute from disputes
    disp_counts = d.groupby(['merchant_id', 'customer_id']).size().reset_index(name='disp_count')

    # Merge into customers
    c = c.merge(tx_agg, on=['merchant_id', 'customer_id'], how='left')
    c = c.merge(ret_counts, on=['merchant_id', 'customer_id'], how='left')
    c = c.merge(disp_counts, on=['merchant_id', 'customer_id'], how='left')

    c['tx_count'] = c['tx_count'].fillna(0).astype(int)
    c['tx_total_spend'] = c['tx_total_spend'].fillna(0.0)
    c['ret_count'] = c['ret_count'].fillna(0).astype(int)
    c['disp_count'] = c['disp_count'].fillna(0).astype(int)

    # Compute max point-in-time values per customer from transactions
    # These may reflect prior-window history that canonical tables don't cover
    tx_pit_max = t.groupby(['merchant_id', 'customer_id']).agg(
        max_po=('customer_previous_orders', 'max'),
        max_ps=('customer_previous_spend', 'max'),
        max_pr=('customer_previous_returns', 'max'),
        max_pd=('customer_previous_disputes', 'max'),
    ).reset_index()

    c = c.merge(tx_pit_max, on=['merchant_id', 'customer_id'], how='left')
    c['max_po'] = c['max_po'].fillna(0)
    c['max_ps'] = c['max_ps'].fillna(0)
    c['max_pr'] = c['max_pr'].fillna(0)
    c['max_pd'] = c['max_pd'].fillna(0)

    # Update historical fields: lifetime must be >= max(point-in-time, canonical count)
    c['historical_order_count'] = np.maximum(c['tx_count'], c['max_po']).astype(int)
    c['historical_total_spend'] = np.maximum(c['tx_total_spend'], c['max_ps']).round(2)
    c['historical_return_count'] = np.maximum(c['ret_count'], c['max_pr']).astype(int)
    c['historical_dispute_count'] = np.maximum(c['disp_count'], c['max_pd']).astype(int)
    c['historical_average_order_value'] = (c['historical_total_spend'] / c['historical_order_count'].replace(0, np.nan)).round(2).fillna(0.0)
    c['historical_return_rate'] = (c['historical_return_count'] / c['historical_order_count'].replace(0, np.nan)).round(4).fillna(0.0)
    c['historical_successful_payment_count'] = c['historical_order_count']

    # Drop temp columns
    c = c.drop(columns=['tx_count', 'tx_total_spend', 'ret_count', 'disp_count',
                        'max_po', 'max_ps', 'max_pr', 'max_pd'])

    # Drop historical_chargeback_count — no canonical chargeback table
    if 'historical_chargeback_count' in c.columns:
        c = c.drop(columns=['historical_chargeback_count'])
        print("  Removed historical_chargeback_count (no canonical chargeback table)")

    # Verify: max prev_* <= hist_* for every customer
    tx_max = t.groupby(['merchant_id', 'customer_id']).agg(
        max_po=('customer_previous_orders', 'max'),
        max_ps=('customer_previous_spend', 'max'),
        max_pr=('customer_previous_returns', 'max'),
        max_pd=('customer_previous_disputes', 'max'),
    ).reset_index()

    check = c.merge(tx_max, on=['merchant_id', 'customer_id'], how='left')
    check['max_po'] = check['max_po'].fillna(0)
    check['max_ps'] = check['max_ps'].fillna(0)
    check['max_pr'] = check['max_pr'].fillna(0)
    check['max_pd'] = check['max_pd'].fillna(0)

    v1 = (check['max_po'] > check['historical_order_count']).sum()
    v2 = (check['max_ps'] > check['historical_total_spend'] + 0.01).sum()  # float tolerance
    v3 = (check['max_pr'] > check['historical_return_count']).sum()
    v4 = (check['max_pd'] > check['historical_dispute_count']).sum()

    print(f"  prev_orders > hist_orders violations: {v1}")
    print(f"  prev_spend > hist_spend violations: {v2}")
    print(f"  prev_returns > hist_returns violations: {v3}")
    print(f"  prev_disputes > hist_disputes violations: {v4}")

    return c


def remove_chargeback_from_transactions(t):
    """Remove customer_previous_chargebacks from transactions — no canonical backing."""
    print("\n=== 4. REMOVING CHARGEBACK FIELDS FROM TRANSACTIONS ===")
    if 'customer_previous_chargebacks' in t.columns:
        t = t.drop(columns=['customer_previous_chargebacks'])
        print("  Removed customer_previous_chargebacks from transactions.csv")
    else:
        print("  customer_previous_chargebacks already absent")
    return t


def dedup_merchant_names(m):
    """Deduplicate merchant names. Protect demo merchant names (M000001-M000009)."""
    print("\n=== 5. DEDUPLICATING MERCHANT NAMES ===")

    demo_ids = {f'M00000{i}' for i in range(1, 10)}
    dup_names = m['merchant_name'].value_counts()
    dups = dup_names[dup_names > 1]

    if len(dups) == 0:
        print("  No duplicate names found")
        return m

    print(f"  Found {len(dups)} duplicate name groups")

    # For each duplicate group, rename non-demo merchants with a suffix
    suffixes = ['II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X']

    for name in dups.index:
        rows = m[m['merchant_name'] == name]
        # Separate demo and non-demo
        demo_rows = rows[rows['merchant_id'].isin(demo_ids)]
        non_demo_rows = rows[~rows['merchant_id'].isin(demo_ids)]

        if len(demo_rows) > 0:
            # Keep demo name, rename all non-demo
            to_rename = non_demo_rows
        else:
            # Keep first, rename rest
            to_rename = rows.iloc[1:]

        for i, (idx, row) in enumerate(to_rename.iterrows()):
            arch_label = row['merchant_archetype'].replace('_', ' ').title().split()[-1]
            new_name = f"{name} ({arch_label})"
            # If still not unique, add index
            if new_name in m['merchant_name'].values:
                new_name = f"{name} {suffixes[i]}"
            m.loc[idx, 'merchant_name'] = new_name

    remaining_dups = m['merchant_name'].value_counts()
    remaining = remaining_dups[remaining_dups > 1]
    print(f"  Remaining duplicates after fix: {len(remaining)}")

    # Second pass if any remain
    if len(remaining) > 0:
        for name in remaining.index:
            rows = m[m['merchant_name'] == name]
            demo_rows = rows[rows['merchant_id'].isin(demo_ids)]
            non_demo_rows = rows[~rows['merchant_id'].isin(demo_ids)]

            if len(demo_rows) > 0:
                to_rename = non_demo_rows
            else:
                to_rename = rows.iloc[1:]

            for i, (idx, row) in enumerate(to_rename.iterrows()):
                mid = row['merchant_id']
                new_name = f"{name} ({mid})"
                m.loc[idx, 'merchant_name'] = new_name

        final_dups = m['merchant_name'].value_counts()
        final = final_dups[final_dups > 1]
        print(f"  Remaining duplicates after second pass: {len(final)}")

    return m


def rebuild_demo_merchants(m, t, d):
    """Rebuild demo_merchants.csv to exactly 9 rows with derived aggregates."""
    print("\n=== 6. REBUILDING DEMO_MERCHANTS.CSV ===")

    demo_ids = [f'M00000{i}' for i in range(1, 10)]

    # Authoritative descriptions and sales channels
    demo_spec = {
        'M000001': {
            'business_description': 'crochet clothes, crochet bags, amigurumi toys, handmade accessories',
            'sales_channel': 'Instagram, WhatsApp, payment links',
        },
        'M000002': {
            'business_description': 'online footwear brand',
            'sales_channel': 'website',
        },
        'M000003': {
            'business_description': 'online/offline competitive-exam preparation',
            'sales_channel': 'website, app',
        },
        'M000004': {
            'business_description': 'travel bookings and packages',
            'sales_channel': 'website, app',
        },
        'M000005': {
            'business_description': 'fictional B2B SaaS platform for small businesses',
            'sales_channel': 'website',
        },
        'M000006': {
            'business_description': 'cloud kitchen / food delivery',
            'sales_channel': 'app, food platforms',
        },
        'M000007': {
            'business_description': 'multi-brand fashion/beauty/lifestyle marketplace',
            'sales_channel': 'website, app',
        },
        'M000008': {
            'business_description': 'diagnostic tests and health check-up packages',
            'sales_channel': 'website, app, clinic',
        },
        'M000009': {
            'business_description': 'gym and fitness studio',
            'sales_channel': 'app, in-person',
        },
    }

    # Load returns for return counts
    returns_path = os.path.join(AUX, 'returns.csv')
    if os.path.exists(returns_path):
        r = pd.read_csv(returns_path)
    else:
        r = pd.DataFrame(columns=['merchant_id', 'transaction_id'])

    rows = []
    for mid in demo_ids:
        mr = m[m['merchant_id'] == mid].iloc[0]
        spec = demo_spec[mid]

        tx_count = len(t[t['merchant_id'] == mid])
        ret_count = len(r[r['merchant_id'] == mid]) if 'merchant_id' in r.columns else 0
        disp_count = len(d[d['merchant_id'] == mid])

        rows.append({
            'merchant_id': mid,
            'demo_merchant_name': mr['merchant_name'],
            'merchant_archetype': mr['merchant_archetype'],
            'fulfillment_type': mr['fulfillment_type'],
            'business_description': spec['business_description'],
            'sales_channel': spec['sales_channel'],
            'documentation_maturity': mr['documentation_maturity'],
            'transaction_count': tx_count,
            'return_count': ret_count,
            'dispute_count': disp_count,
        })

        print(f"  {mid} ({mr['merchant_name']}): tx={tx_count}, ret={ret_count}, disp={disp_count}")

    dm = pd.DataFrame(rows)
    dm.to_csv(os.path.join(DEMO, 'demo_merchants.csv'), index=False)
    print(f"  Saved demo_merchants.csv with {len(dm)} rows")
    return dm


def save_all(m, c, t):
    """Save repaired core CSVs."""
    print("\n=== SAVING REPAIRED CSVs ===")
    m.to_csv(os.path.join(CORE, 'merchants.csv'), index=False)
    print(f"  merchants.csv: {len(m)} rows, {len(m.columns)} cols")
    c.to_csv(os.path.join(CORE, 'customers.csv'), index=False)
    print(f"  customers.csv: {len(c)} rows, {len(c.columns)} cols")
    t.to_csv(os.path.join(CORE, 'transactions.csv'), index=False)
    print(f"  transactions.csv: {len(t)} rows, {len(t.columns)} cols")


def main():
    print("=" * 60)
    print("DATASET PROMPT 4 — MASTER REPAIR")
    print("=" * 60)

    m, c, t, d, e = load_all()

    # 1. Fix demo merchant personas
    m = fix_demo_merchant_personas(m)

    # 2. Sync transaction denormalized fields
    t = sync_transaction_merchant_fields(t, m)

    # 3. Remove chargeback field from transactions
    t = remove_chargeback_from_transactions(t)

    # 4. Recompute customer historical summaries
    c = recompute_customer_historical(c, t, d)

    # 5. Deduplicate merchant names
    m = dedup_merchant_names(m)

    # 6. Save repaired CSVs
    save_all(m, c, t)

    # 7. Rebuild demo merchants
    rebuild_demo_merchants(m, t, d)

    print("\n" + "=" * 60)
    print("REPAIR COMPLETE")
    print("=" * 60)


if __name__ == '__main__':
    main()
