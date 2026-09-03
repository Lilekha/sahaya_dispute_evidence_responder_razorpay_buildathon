import os
import random
import numpy as np
import pandas as pd

def generate_dataset():
    np.random.seed(42)
    random.seed(42)

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, 'data')
    core_dir = os.path.join(data_dir, 'core')
    demo_dir = os.path.join(data_dir, 'demo')

    # Load existing datasets
    merchants_df = pd.read_csv(os.path.join(core_dir, 'merchants.csv'))
    customers_df = pd.read_csv(os.path.join(core_dir, 'customers.csv'))
    transactions_df = pd.read_csv(os.path.join(core_dir, 'transactions.csv'))

    print("--- STEP 1: Updating Merchants ---")
    demo_updates = {
        'M000001': {'merchant_name': 'Wonderloon Bags', 'merchant_archetype': 'd2c_brand', 'fulfillment_type': 'physical_delivery', 'documentation_maturity': 0.90},
        'M000002': {'merchant_name': 'Gyan IAS Prep', 'merchant_archetype': 'education_coaching', 'fulfillment_type': 'digital_service', 'documentation_maturity': 0.65},
        'M000003': {'merchant_name': 'Zari and Zest by Mira', 'merchant_archetype': 'individual_social_seller', 'fulfillment_type': 'physical_delivery', 'documentation_maturity': 0.40},
        'M000004': {'merchant_name': 'Fit Circle Coaching', 'merchant_archetype': 'fitness_services', 'fulfillment_type': 'digital_service', 'documentation_maturity': 0.30}
    }

    doc_mat_map = {'high': 0.85, 'moderate': 0.60, 'low': 0.35}

    mat_list = []
    for idx, row in merchants_df.iterrows():
        mid = row['merchant_id']
        if mid in demo_updates:
            for k, v in demo_updates[mid].items():
                merchants_df.at[idx, k] = v
            mat_list.append(demo_updates[mid]['documentation_maturity'])
        else:
            curr_val = row['documentation_maturity']
            if isinstance(curr_val, str) and curr_val in doc_mat_map:
                val = doc_mat_map[curr_val] + np.random.uniform(-0.05, 0.05)
            elif isinstance(curr_val, (int, float)):
                val = float(curr_val)
            else:
                val = 0.60
            val = float(np.clip(val, 0.25, 0.95))
            merchants_df.at[idx, 'documentation_maturity'] = val
            mat_list.append(val)

    merchants_df.to_csv(os.path.join(core_dir, 'merchants.csv'), index=False)
    print(f"Updated {len(merchants_df)} merchants in merchants.csv")

    print("\n--- STEP 2: Updating Transactions Payment Methods ---")
    card_methods = ['credit_card', 'debit_card']

    payment_methods = transactions_df['payment_method'].values
    n_tx = len(transactions_df)
    target_card_count = 88500

    current_card_indices = [i for i, pm in enumerate(payment_methods) if pm in card_methods]
    current_non_card_indices = [i for i, pm in enumerate(payment_methods) if pm not in card_methods]

    needed_cards = target_card_count - len(current_card_indices)
    if needed_cards > 0:
        convert_indices = np.random.choice(current_non_card_indices, size=needed_cards, replace=False)
        for idx in convert_indices:
            payment_methods[idx] = np.random.choice(['credit_card', 'debit_card'], p=[0.7, 0.3])

    transactions_df['payment_method'] = payment_methods
    transactions_df.to_csv(os.path.join(core_dir, 'transactions.csv'), index=False)
    card_tx_count = (transactions_df['payment_method'].isin(card_methods)).sum()
    print(f"Updated transactions.csv: {card_tx_count} card transactions out of {n_tx} total ({card_tx_count/n_tx*100:.1f}%)")

    print("\n--- STEP 3: Generating Card Disputes ---")
    card_txs = transactions_df[transactions_df['payment_method'].isin(card_methods)].copy()
    card_txs['timestamp_dt'] = pd.to_datetime(card_txs['timestamp'])

    demo_mids = ['M000001', 'M000002', 'M000003', 'M000004']
    selected_tx_ids = []

    for dmid in demo_mids:
        dtxs = card_txs[card_txs['merchant_id'] == dmid]
        n_sample = min(len(dtxs), 52)
        selected_tx_ids.extend(np.random.choice(dtxs['transaction_id'].values, size=n_sample, replace=False))

    rem_card_txs = card_txs[~card_txs['transaction_id'].isin(selected_tx_ids)]
    target_total_disputes = 1620
    rem_needed = target_total_disputes - len(selected_tx_ids)

    archetype_weights = {
        'digital_saas': 1.8,
        'education_coaching': 1.6,
        'fitness_services': 1.5,
        'travel_hospitality': 1.4,
        'd2c_brand': 1.0,
        'online_marketplace_retailer': 1.0,
        'food_local_commerce': 0.8,
        'individual_social_seller': 0.9,
        'healthcare_diagnostics': 0.7
    }

    rem_weights = rem_card_txs['merchant_archetype'].map(archetype_weights).fillna(1.0).values
    rem_weights /= rem_weights.sum()

    sampled_rem_tx_ids = np.random.choice(rem_card_txs['transaction_id'].values, size=rem_needed, replace=False, p=rem_weights)
    selected_tx_ids.extend(sampled_rem_tx_ids)

    disputed_txs = card_txs[card_txs['transaction_id'].isin(selected_tx_ids)].copy()
    disputed_txs = disputed_txs.sort_values('timestamp_dt').reset_index(drop=True)

    print(f"Total sampled disputes: {len(disputed_txs)} (Demo merchants: {[len(disputed_txs[disputed_txs['merchant_id']==m]) for m in demo_mids]})")

    reason_codes = [
        'UNAUTHORIZED_TRANSACTION',
        'MERCHANDISE_NOT_RECEIVED',
        'MERCHANDISE_NOT_AS_DESCRIBED',
        'CREDIT_NOT_PROCESSED',
        'RECURRING_BILLING_DISPUTE',
        'DUPLICATE_TRANSACTION'
    ]
    reason_probs = [0.22, 0.26, 0.20, 0.15, 0.12, 0.05]

    reason_descriptions = {
        'UNAUTHORIZED_TRANSACTION': 'Cardholder claims transaction was unauthorized or fraudulent',
        'MERCHANDISE_NOT_RECEIVED': 'Cardholder claims ordered merchandise or service was not received',
        'MERCHANDISE_NOT_AS_DESCRIBED': 'Cardholder claims merchandise arrived damaged, defective, or not as described',
        'CREDIT_NOT_PROCESSED': 'Cardholder claims promised credit or refund was not posted',
        'RECURRING_BILLING_DISPUTE': 'Cardholder claims recurring subscription billing was canceled or unauthorized',
        'DUPLICATE_TRANSACTION': 'Cardholder claims single purchase was billed multiple times'
    }

    networks = ['Visa', 'Mastercard', 'RuPay']
    network_probs = [0.50, 0.33, 0.17]

    ev_types = ['order_confirmation', 'invoice', 'shipping_label', 'tracking_number', 'delivery_confirmation', 'customer_communication']
    shipping_ev_types = {'shipping_label', 'tracking_number', 'delivery_confirmation'}

    req_matrix = {
        'UNAUTHORIZED_TRANSACTION':      [1, 1, 0, 0, 0, 1],
        'MERCHANDISE_NOT_RECEIVED':      [1, 0, 1, 1, 1, 0],
        'MERCHANDISE_NOT_AS_DESCRIBED':  [1, 0, 0, 0, 1, 1],
        'CREDIT_NOT_PROCESSED':          [1, 1, 0, 0, 0, 1],
        'RECURRING_BILLING_DISPUTE':     [1, 1, 0, 0, 0, 1],
        'DUPLICATE_TRANSACTION':         [1, 1, 0, 0, 0, 0]
    }

    # Calibrated intercepts to hit per-reason win targets precisely
    # Target win rates: UNAUTHORIZED 0.20, NOT_RECEIVED 0.62, NOT_AS_DESCRIBED 0.38, CREDIT 0.45, RECURRING 0.42, DUPLICATE 0.70
    reason_intercepts = {
        'UNAUTHORIZED_TRANSACTION': -2.05,
        'MERCHANDISE_NOT_RECEIVED': 0.00,
        'MERCHANDISE_NOT_AS_DESCRIBED': -0.95,
        'CREDIT_NOT_PROCESSED': -0.90,
        'RECURRING_BILLING_DISPUTE': -0.40,
        'DUPLICATE_TRANSACTION': 0.48
    }

    merchant_dict = merchants_df.set_index('merchant_id').to_dict(orient='index')

    disputes_list = []
    evidence_list = []

    for idx, tx in disputed_txs.iterrows():
        disp_id = f"DSP{idx+1:06d}"
        tx_id = tx['transaction_id']
        mid = tx['merchant_id']
        cid = tx['customer_id']
        tx_dt = tx['timestamp_dt']
        m_info = merchant_dict.get(mid, {})

        fulfillment = m_info.get('fulfillment_type', 'physical_delivery')
        is_physical = (fulfillment == 'physical_delivery')
        doc_maturity = float(m_info.get('documentation_maturity', 0.60))

        disp_created_dt = tx_dt + pd.Timedelta(days=random.randint(3, 45), hours=random.randint(0, 23))
        respond_by_dt = disp_created_dt + pd.Timedelta(days=random.randint(10, 21))
        days_to_deadline = (respond_by_dt - disp_created_dt).days

        r_code = np.random.choice(reason_codes, p=reason_probs)
        r_desc = reason_descriptions[r_code]
        net = np.random.choice(networks, p=network_probs)

        disp_amt = round(float(tx['amount']), 2)

        # Contest rate 60-70% overall (target ~65%)
        p_contest = np.clip(0.40 + 0.40 * doc_maturity, 0.45, 0.85)
        is_contested = (np.random.random() < p_contest)
        merchant_action = 'contested' if is_contested else 'accepted'

        if is_contested:
            contest_fee = float(np.random.choice([500.0, 450.0, 350.0, 150.0, 15.0], p=[0.75, 0.10, 0.08, 0.05, 0.02]))
            op_cost = float(round(contest_fee * 0.50, 2))
        else:
            contest_fee = 0.0
            op_cost = 0.0

        # Generate Evidence records (exactly 6)
        req_pattern = req_matrix[r_code]
        req_scores = []
        has_missing_req = False

        for ev_idx, ev_type in enumerate(ev_types):
            ev_id = f"EVID{(idx*6 + ev_idx + 1):07d}"

            is_req_raw = req_pattern[ev_idx]
            is_shipping = (ev_type in shipping_ev_types)

            if is_shipping and not is_physical:
                app_status = 'NOT_APPLICABLE'
                available = 0
                is_req = 0
                is_rel = 0
                q_score = 0.0
            else:
                is_req = is_req_raw
                is_rel = 1 if is_req == 1 else (1 if np.random.random() < 0.6 else 0)

                p_avail = np.clip(0.35 + 0.60 * doc_maturity, 0.20, 0.98)
                if np.random.random() < p_avail:
                    app_status = 'APPLICABLE'
                    available = 1
                    q_score = round(float(np.random.uniform(0.60, 0.98) * (0.8 + 0.2 * doc_maturity)), 2)
                    q_score = float(np.clip(q_score, 0.60, 0.98))
                else:
                    app_status = 'UNAVAILABLE'
                    available = 0
                    q_score = 0.0

            if is_req == 1:
                req_scores.append(available * q_score)
                if available == 0:
                    has_missing_req = True

            ev_dt = tx_dt + pd.Timedelta(seconds=random.randint(0, int((disp_created_dt - tx_dt).total_seconds())))
            source_sys = 'logistics' if is_shipping else ('crm' if ev_type == 'customer_communication' else ('billing' if ev_type in ('invoice', 'order_confirmation') else 'ops'))

            evidence_list.append({
                'evidence_id': ev_id,
                'dispute_id': disp_id,
                'transaction_id': tx_id,
                'evidence_type': ev_type,
                'applicability_status': app_status,
                'available': available,
                'required': is_req,
                'relevant': is_rel,
                'quality_score': q_score,
                'evidence_timestamp': ev_dt.strftime('%Y-%m-%d %H:%M:%S'),
                'source_system': source_sys
            })

        if not is_contested:
            disp_outcome = 'accepted_refunded'
            res_date_str = ""
        else:
            base_intercept = reason_intercepts[r_code]
            # Amount penalty log(dispute_amount) tuned for 8-15 pt quintile gap
            amount_penalty = -0.13 * np.log(disp_amt / 2500.0)

            avg_req_score = np.mean(req_scores) if len(req_scores) > 0 else 0.5
            ev_bonus = 1.4 * avg_req_score
            missing_penalty = -1.20 if has_missing_req else 0.20

            noise = np.random.normal(0, 0.40)

            latent_logit = base_intercept + amount_penalty + ev_bonus + missing_penalty + noise
            win_prob = 1.0 / (1.0 + np.exp(-latent_logit))

            is_won = (np.random.random() < win_prob)
            disp_outcome = 'won' if is_won else 'lost'

            res_dt = disp_created_dt + pd.Timedelta(days=random.randint(7, 45))
            res_date_str = res_dt.strftime('%Y-%m-%d %H:%M:%S')

        disputes_list.append({
            'dispute_id': disp_id,
            'transaction_id': tx_id,
            'merchant_id': mid,
            'customer_id': cid,
            'network': net,
            'reason_code': r_code,
            'reason_description': r_desc,
            'dispute_created_at': disp_created_dt.strftime('%Y-%m-%d %H:%M:%S'),
            'dispute_amount': disp_amt,
            'contest_fee': contest_fee,
            'operational_review_cost': op_cost,
            'respond_by': respond_by_dt.strftime('%Y-%m-%d %H:%M:%S'),
            'days_to_deadline': days_to_deadline,
            'merchant_action': merchant_action,
            'dispute_outcome': disp_outcome,
            'resolution_date': res_date_str
        })

    disputes_df = pd.DataFrame(disputes_list)
    evidence_df = pd.DataFrame(evidence_list)

    print("\n--- STEP 4: Saving disputes.csv and evidence.csv ---")
    disputes_df.to_csv(os.path.join(core_dir, 'disputes.csv'), index=False)
    evidence_df.to_csv(os.path.join(core_dir, 'evidence.csv'), index=False)
    print(f"Saved disputes.csv ({len(disputes_df)} rows, {len(disputes_df.columns)} cols)")
    print(f"Saved evidence.csv ({len(evidence_df)} rows, {len(evidence_df.columns)} cols)")

    print("\n--- STEP 5: Updating demo_merchants.csv ---")
    demo_df = pd.DataFrame([
        {
            'merchant_id': 'M000001',
            'demo_merchant_name': 'Wonderloon Bags',
            'merchant_archetype': 'd2c_brand',
            'fulfillment_type': 'physical_delivery',
            'documentation_maturity': 0.90,
            'demo_description': 'Strong evidence: tracked shipping, signed delivery, documented policy. High maturity.'
        },
        {
            'merchant_id': 'M000002',
            'demo_merchant_name': 'Gyan IAS Prep',
            'merchant_archetype': 'education_coaching',
            'fulfillment_type': 'digital_service',
            'documentation_maturity': 0.65,
            'demo_description': 'Subscription disputes, no shipping evidence. Medium maturity.'
        },
        {
            'merchant_id': 'M000003',
            'demo_merchant_name': 'Zari and Zest by Mira',
            'merchant_archetype': 'individual_social_seller',
            'fulfillment_type': 'physical_delivery',
            'documentation_maturity': 0.40,
            'demo_description': 'Informal courier, often unsigned delivery, no written policy. Low maturity.'
        },
        {
            'merchant_id': 'M000004',
            'demo_merchant_name': 'Fit Circle Coaching',
            'merchant_archetype': 'fitness_services',
            'fulfillment_type': 'digital_service',
            'documentation_maturity': 0.30,
            'demo_description': 'No physical evidence at all. Minimal maturity.'
        }
    ])
    demo_df.to_csv(os.path.join(demo_dir, 'demo_merchants.csv'), index=False)
    print(f"Saved demo_merchants.csv ({len(demo_df)} rows)")

    print("\n--- DATASET REGENERATION COMPLETE ---")

if __name__ == '__main__':
    generate_dataset()
