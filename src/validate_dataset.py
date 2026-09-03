"""
Comprehensive dataset validation suite for dataset_prompt_4.md
Final Data Normalization + Cross-Table Consistency Pass

Produces the Section 25 FINAL DATA QUALITY REPORT output format.
"""
import os
import sys
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import average_precision_score


def run_validation():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, 'data')
    core_dir = os.path.join(data_dir, 'core')
    aux_dir = os.path.join(data_dir, 'auxiliary')
    demo_dir = os.path.join(data_dir, 'demo')

    # ── Load all datasets ──
    m = pd.read_csv(os.path.join(core_dir, 'merchants.csv'))
    c = pd.read_csv(os.path.join(core_dir, 'customers.csv'))
    t = pd.read_csv(os.path.join(core_dir, 'transactions.csv'))
    d = pd.read_csv(os.path.join(core_dir, 'disputes.csv'))
    e = pd.read_csv(os.path.join(core_dir, 'evidence.csv'))
    dm = pd.read_csv(os.path.join(demo_dir, 'demo_merchants.csv'))

    # Load auxiliary for FK checks
    aux_files = {}
    for f in ['returns.csv', 'events.csv', 'fraud_events.csv', 'merchant_hourly_risk.csv', 'products.csv', 'products_services.csv']:
        fp = os.path.join(aux_dir, f)
        if os.path.exists(fp):
            aux_files[f] = pd.read_csv(fp)

    all_pass = True

    def check(name, condition):
        nonlocal all_pass
        status = "PASS" if condition else "FAIL"
        if not condition:
            all_pass = False
        return status

    # ══════════════════════════════════════════════════════════
    print("=" * 60)
    print("FINAL DATA QUALITY REPORT")
    print("=" * 60)

    # ── Core population ──
    print("\nCore population:")
    print(f"  merchants:     {len(m):>7,}  {check('merchants', len(m) == 400)}")
    print(f"  customers:     {len(c):>7,}  {check('customers', len(c) == 13463)}")
    print(f"  transactions:  {len(t):>7,}  {check('transactions', len(t) == 100000)}")
    print(f"  disputes:      {len(d):>7,}  {check('disputes', len(d) == 1620)}")
    print(f"  evidence:      {len(e):>7,}  {check('evidence', len(e) == 9720)}")

    # ── Cross-table FK consistency ──
    print("\nCross-table consistency:")
    fk_tx_m = t['merchant_id'].isin(m['merchant_id']).all()
    print(f"  transaction -> merchant:   {check('tx_m', fk_tx_m)}  (orphans: {(~t['merchant_id'].isin(m['merchant_id'])).sum()})")

    # transaction -> customer: check (merchant_id, customer_id) pair
    tc_pairs = set(zip(t['merchant_id'], t['customer_id']))
    cc_pairs = set(zip(c['merchant_id'], c['customer_id']))
    fk_tx_c = tc_pairs.issubset(cc_pairs)
    print(f"  transaction -> customer:   {check('tx_c', fk_tx_c)}  (orphans: {len(tc_pairs - cc_pairs)})")

    # transaction -> product
    if 'products.csv' in aux_files:
        p = aux_files['products.csv']
        tx_prods = t[['merchant_id', 'product_id']].dropna(subset=['product_id'])
        p_prods = set(zip(p['merchant_id'], p['product_id']))
        tx_prod_pairs = set(zip(tx_prods['merchant_id'], tx_prods['product_id']))
        fk_tx_p = tx_prod_pairs.issubset(p_prods)
        print(f"  transaction -> product:    {check('tx_p', fk_tx_p)}  (orphans: {len(tx_prod_pairs - p_prods)})")
    else:
        print(f"  transaction -> product:    SKIP  (no products.csv)")

    fk_d_t = d['transaction_id'].isin(t['transaction_id']).all()
    print(f"  dispute -> transaction:    {check('d_t', fk_d_t)}  (orphans: {(~d['transaction_id'].isin(t['transaction_id'])).sum()})")

    fk_d_m = d['merchant_id'].isin(m['merchant_id']).all()
    print(f"  dispute -> merchant:       {check('d_m', fk_d_m)}  (orphans: {(~d['merchant_id'].isin(m['merchant_id'])).sum()})")

    fk_d_c = set(zip(d['merchant_id'], d['customer_id'])).issubset(cc_pairs)
    print(f"  dispute -> customer:       {check('d_c', fk_d_c)}  (orphans: {len(set(zip(d['merchant_id'], d['customer_id'])) - cc_pairs)})")

    fk_e_d = e['dispute_id'].isin(d['dispute_id']).all()
    print(f"  evidence -> dispute:       {check('e_d', fk_e_d)}  (orphans: {(~e['dispute_id'].isin(d['dispute_id'])).sum()})")

    fk_e_t = e['transaction_id'].isin(t['transaction_id']).all()
    print(f"  evidence -> transaction:   {check('e_t', fk_e_t)}  (orphans: {(~e['transaction_id'].isin(t['transaction_id'])).sum()})")

    # demo -> merchant
    fk_dm_m = dm['merchant_id'].isin(m['merchant_id']).all()
    print(f"  demo -> merchant:          {check('dm_m', fk_dm_m)}  (orphans: {(~dm['merchant_id'].isin(m['merchant_id'])).sum()})")

    # ── Semantic consistency ──
    print("\nSemantic consistency:")
    merged_tm = t.merge(m[['merchant_id', 'merchant_archetype', 'fulfillment_type', 'industry']], on='merchant_id', suffixes=('_tx', '_m'))
    arch_mm = (merged_tm['merchant_archetype_tx'] != merged_tm['merchant_archetype_m']).sum()
    ful_mm = (merged_tm['fulfillment_type_tx'] != merged_tm['fulfillment_type_m']).sum()
    ind_mm = (merged_tm['industry_tx'] != merged_tm['industry_m']).sum()
    print(f"  merchant_archetype mismatch: {arch_mm}  {check('arch', arch_mm == 0)}")
    print(f"  fulfillment_type mismatch:   {ful_mm}  {check('ful', ful_mm == 0)}")
    print(f"  industry mismatch:           {ind_mm}  {check('ind', ind_mm == 0)}")

    # offering_type vs product
    if 'products.csv' in aux_files:
        p = aux_files['products.csv']
        tp = t[['product_id', 'merchant_id', 'offering_type']].dropna(subset=['product_id']).merge(
            p[['product_id', 'merchant_id', 'offering_type']], on=['product_id', 'merchant_id'], suffixes=('_tx', '_p'), how='inner')
        ot_mm = (tp['offering_type_tx'] != tp['offering_type_p']).sum()
        print(f"  offering_type mismatch:      {ot_mm}  {check('ot', ot_mm == 0)}")

        tp2 = t[['product_id', 'merchant_id', 'return_eligible']].dropna(subset=['product_id']).merge(
            p[['product_id', 'merchant_id', 'return_eligible']], on=['product_id', 'merchant_id'], suffixes=('_tx', '_p'), how='inner')
        re_mm = (tp2['return_eligible_tx'] != tp2['return_eligible_p']).sum()
        print(f"  return_eligible mismatch:    {re_mm}  {check('re', re_mm == 0)}")
    else:
        print(f"  offering_type mismatch:      SKIP")
        print(f"  return_eligible mismatch:    SKIP")

    # ── Customer consistency ──
    print("\nCustomer consistency:")
    tx_max = t.groupby(['merchant_id', 'customer_id']).agg(
        max_po=('customer_previous_orders', 'max'),
        max_ps=('customer_previous_spend', 'max'),
        max_pr=('customer_previous_returns', 'max'),
        max_pd=('customer_previous_disputes', 'max'),
    ).reset_index()
    ccheck = c.merge(tx_max, on=['merchant_id', 'customer_id'], how='left')
    for col in ['max_po', 'max_ps', 'max_pr', 'max_pd']:
        ccheck[col] = ccheck[col].fillna(0)

    v_orders = (ccheck['max_po'] > ccheck['historical_order_count']).sum()
    v_spend = (ccheck['max_ps'] > ccheck['historical_total_spend'] + 0.01).sum()
    v_returns = (ccheck['max_pr'] > ccheck['historical_return_count']).sum()
    v_disputes = (ccheck['max_pd'] > ccheck['historical_dispute_count']).sum()

    print(f"  previous orders > lifetime orders:     {v_orders}  {check('co', v_orders == 0)}")
    print(f"  previous spend > lifetime spend:       {v_spend}  {check('cs', v_spend == 0)}")
    print(f"  previous returns > lifetime returns:    {v_returns}  {check('cr', v_returns == 0)}")
    print(f"  previous disputes > lifetime disputes:  {v_disputes}  {check('cd', v_disputes == 0)}")

    # ── Demo merchants ──
    print("\nDemo merchants:")
    demo_spec = {
        'M000001': ('Loops & Knots by Ananya', 'individual_social_seller', 'physical_delivery'),
        'M000002': ('SoleCraft', 'd2c_brand', 'physical_delivery'),
        'M000003': ('Gyan IAS Study Circle', 'education_coaching', 'digital_service'),
        'M000004': ('TripWell', 'travel_hospitality', 'booking_service'),
        'M000005': ('CodePilot', 'digital_saas', 'digital_service'),
        'M000006': ('QuickBite Kitchen', 'food_local_commerce', 'food_delivery'),
        'M000007': ('StyleCart', 'online_marketplace_retailer', 'physical_delivery'),
        'M000008': ('MediCare Diagnostics', 'healthcare_diagnostics', 'appointment_service'),
        'M000009': ('FitForge', 'fitness_services', 'membership_service'),
    }

    demo_all_ok = True
    for mid, (exp_name, exp_arch, exp_ful) in demo_spec.items():
        mr = m[m['merchant_id'] == mid]
        dmr = dm[dm['merchant_id'] == mid]

        if len(mr) == 0:
            print(f"  {mid}: MISSING from merchants.csv")
            demo_all_ok = False
            continue
        if len(dmr) == 0:
            print(f"  {mid}: MISSING from demo_merchants.csv")
            demo_all_ok = False
            continue

        mr = mr.iloc[0]
        dmr = dmr.iloc[0]

        name_ok = mr['merchant_name'] == exp_name
        arch_ok = mr['merchant_archetype'] == exp_arch and dmr['merchant_archetype'] == exp_arch
        ful_ok = mr['fulfillment_type'] == exp_ful and dmr['fulfillment_type'] == exp_ful

        tx_count = len(t[t['merchant_id'] == mid])
        disp_count = len(d[d['merchant_id'] == mid])

        status = "PASS" if (name_ok and arch_ok and ful_ok) else "FAIL"
        if status == "FAIL":
            demo_all_ok = False
        print(f"  {mid} {mr['merchant_name']:<30s} arch={exp_arch:<30s} ful={exp_ful:<20s} tx={tx_count} disp={disp_count}  {status}")

    check('demo', demo_all_ok)

    # ── Primary keys ──
    print("\nPrimary keys:")
    pk_m = m['merchant_id'].is_unique
    pk_c = c.set_index(['merchant_id', 'customer_id']).index.is_unique
    pk_t = t['transaction_id'].is_unique
    pk_d = d['dispute_id'].is_unique
    pk_e = e['evidence_id'].is_unique
    print(f"  merchant_id unique:                {check('pk_m', pk_m)}")
    print(f"  (merchant_id, customer_id) unique: {check('pk_c', pk_c)}")
    print(f"  transaction_id unique:             {check('pk_t', pk_t)}")
    print(f"  dispute_id unique:                 {check('pk_d', pk_d)}")
    print(f"  evidence_id unique:                {check('pk_e', pk_e)}")
    print(f"  merchant_name unique:              {check('mn', m['merchant_name'].is_unique)}")

    # ── Evidence ──
    print("\nEvidence:")
    ev_per_disp = e.groupby('dispute_id')['evidence_id'].count()
    ev_exact_6 = (ev_per_disp == 6).all() and len(ev_per_disp) == len(d)
    print(f"  rows/dispute: 6  {check('ev6', ev_exact_6)}")

    canon_types = {'order_confirmation', 'invoice', 'shipping_label', 'tracking_number', 'delivery_confirmation', 'customer_communication'}
    actual_types = set(e['evidence_type'].unique())
    print(f"  canonical types: {actual_types == canon_types}  {check('evt', actual_types == canon_types)}")

    # Invalid combos
    req_na = ((e['required'] == 1) & (e['applicability_status'] == 'NOT_APPLICABLE')).sum()
    unavail_qual = ((e['available'] == 0) & (e['quality_score'] > 0)).sum()
    avail_zq = ((e['available'] == 1) & (e['quality_score'] == 0)).sum()
    invalid_combos = req_na + unavail_qual + avail_zq
    print(f"  invalid combinations: {invalid_combos}  {check('evc', invalid_combos == 0)}")

    # Evidence transaction_id matches dispute transaction_id
    ed = e.merge(d[['dispute_id', 'transaction_id']], on='dispute_id', suffixes=('_e', '_d'))
    ev_tx_mm = (ed['transaction_id_e'] != ed['transaction_id_d']).sum()
    print(f"  evidence.tx_id == dispute.tx_id mismatch: {ev_tx_mm}  {check('evtx', ev_tx_mm == 0)}")

    # ── Transaction/Dispute reconciliation ──
    print("\nTransaction/Dispute reconciliation:")
    tx_disp_ids = set(t[t['dispute_created'] == 1]['transaction_id'])
    disp_tx_ids = set(d['transaction_id'])
    recon_ok = tx_disp_ids == disp_tx_ids
    print(f"  set equality: {check('recon', recon_ok)}  (tx flagged: {len(tx_disp_ids)}, disputes: {len(disp_tx_ids)})")

    # Dispute <-> transaction field consistency
    dt = d.merge(t[['transaction_id', 'merchant_id', 'customer_id', 'amount']], on='transaction_id', suffixes=('_d', '_t'))
    dm_mm = (dt['merchant_id_d'] != dt['merchant_id_t']).sum()
    dc_mm = (dt['customer_id_d'] != dt['customer_id_t']).sum()
    da_mm = (dt['dispute_amount'] != dt['amount']).sum()
    print(f"  dispute.merchant_id == tx.merchant_id:  {check('dm2', dm_mm == 0)}  (mismatch: {dm_mm})")
    print(f"  dispute.customer_id == tx.customer_id:  {check('dc2', dc_mm == 0)}  (mismatch: {dc_mm})")
    print(f"  dispute.amount == tx.amount:             {check('da2', da_mm == 0)}  (mismatch: {da_mm})")

    # ── Temporal ──
    print("\nTemporal:")
    merged_tx_d = d.merge(t[['transaction_id', 'timestamp']], on='transaction_id')
    tx_after_disp = (pd.to_datetime(merged_tx_d['timestamp']) > pd.to_datetime(merged_tx_d['dispute_created_at'])).sum()
    print(f"  transaction after dispute: {tx_after_disp}  {check('temp1', tx_after_disp == 0)}")

    merged_ev_d = e.merge(d[['dispute_id', 'dispute_created_at']], on='dispute_id')
    ev_after_disp = (pd.to_datetime(merged_ev_d['evidence_timestamp']) > pd.to_datetime(merged_ev_d['dispute_created_at'])).sum()
    print(f"  evidence after dispute: {ev_after_disp}  {check('temp2', ev_after_disp == 0)}")

    contested = d[d['merchant_action'] == 'contested']
    contested_res = contested[contested['resolution_date'].notna() & (contested['resolution_date'] != '')]
    res_before_disp = (pd.to_datetime(contested_res['resolution_date']) < pd.to_datetime(contested_res['dispute_created_at'])).sum()
    print(f"  resolution before dispute: {res_before_disp}  {check('temp3', res_before_disp == 0)}")

    # ── Leakage ──
    print("\nLeakage:")
    removed_cols = ['should_contest', 'recommended_action', 'simulated_win_probability',
                    'expected_recovery', 'expected_cost', 'expected_net_value', 'dispute_status',
                    'chargeback_created', 'chargeback_outcome', 'contestable',
                    'merchant_response_submitted', 'evidence_available', 'evidence_strength',
                    'evidence_completeness', 'dispute_type', 'customer_previous_chargebacks',
                    'historical_chargeback_count']
    present_leaked = [col for col in removed_cols if col in t.columns or col in d.columns or col in e.columns or col in c.columns]
    print(f"  leakage fields excluded: {check('leak', len(present_leaked) == 0)}  (remaining: {present_leaked})")

    suspicious = []
    for col in t.columns:
        if 'outcome' in col.lower() or 'result' in col.lower() or 'chargeback' in col.lower():
            suspicious.append(col)
    for col in d.columns:
        if col in ['dispute_outcome', 'merchant_action', 'resolution_date']:
            continue  # Expected target/post-decision
        if 'outcome' in col.lower() or 'result' in col.lower():
            suspicious.append(col)
    print(f"  suspicious fields requiring exclusion: {suspicious}")

    # ── Documentation ──
    print("\nDocumentation:")
    for doc in ['DATASET_MANIFEST.md', 'DATA_PROFILE.md', 'ML_DATA_DICTIONARY.md', 'DATASET_AUDIT_FINAL.md']:
        exists = os.path.exists(os.path.join(data_dir, doc))
        print(f"  {doc}: {'PRESENT' if exists else 'MISSING'}")

    # ── Network distribution ──
    print("\nNetwork distribution:")
    net = d['network'].value_counts()
    print(f"  Visa:       {net.get('Visa', 0)}")
    print(f"  Mastercard: {net.get('Mastercard', 0)}")
    print(f"  RuPay:      {net.get('RuPay', 0)}")
    print(f"  UPI:        {net.get('UPI', 0)}  {check('upi', net.get('UPI', 0) == 0)}")

    # ── Outcome distribution ──
    print("\nOutcome distribution:")
    contested_mask = d['merchant_action'] == 'contested'
    won = (d['dispute_outcome'] == 'won').sum()
    lost = (d['dispute_outcome'] == 'lost').sum()
    acc = (d['dispute_outcome'] == 'accepted_refunded').sum()
    contested_cnt = contested_mask.sum()
    win_rate = won / contested_cnt if contested_cnt > 0 else 0
    print(f"  Won: {won}, Lost: {lost}, Accepted: {acc}, Contested: {contested_cnt}")
    print(f"  Contested win rate: {win_rate*100:.2f}%")

    # ── GBDT Baseline ──
    print("\nBaseline model:")
    contested_df = d[contested_mask].copy()
    contested_df['target_won'] = (contested_df['dispute_outcome'] == 'won').astype(int)
    ev_agg = e.groupby('dispute_id').agg(
        n_avail=('available', 'sum'),
        n_req=('required', 'sum'),
        mean_q=('quality_score', 'mean')
    ).reset_index()
    m_df = contested_df.merge(ev_agg, on='dispute_id').merge(m[['merchant_id', 'documentation_maturity']], on='merchant_id')
    feature_candidates = ['dispute_amount', 'days_to_deadline', 'n_avail', 'n_req', 'mean_q', 'documentation_maturity']
    X_base = pd.get_dummies(m_df[feature_candidates + ['network', 'reason_code']], drop_first=True)
    y_base = m_df['target_won']
    X_tr, X_te, y_tr, y_te = train_test_split(X_base, y_base, test_size=0.2, random_state=42, stratify=y_base)
    clf = HistGradientBoostingClassifier(random_state=42, max_iter=100)
    clf.fit(X_tr, y_tr)
    p_te = clf.predict_proba(X_te)[:, 1]
    pr_auc = average_precision_score(y_te, p_te)
    print(f"  GBDT PR-AUC: {pr_auc:.4f}  {check('prauc', 0.50 <= pr_auc <= 0.85)}")

    # ── Final Verdict ──
    print("\n" + "=" * 60)
    print("FINAL VERDICT:")
    if all_pass:
        print("PASS — READY FOR ML")
    else:
        print("FAIL — CORRECTIONS REQUIRED")
        sys.exit(1)
    print("=" * 60)


if __name__ == "__main__":
    run_validation()
