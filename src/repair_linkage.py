import os
import pandas as pd

def repair_linkage():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    core_dir = os.path.join(base_dir, 'data', 'core')

    tx_path = os.path.join(core_dir, 'transactions.csv')
    disp_path = os.path.join(core_dir, 'disputes.csv')

    transactions = pd.read_csv(tx_path)
    disputes = pd.read_csv(disp_path)

    print(f"Original transactions row count: {len(transactions)}")
    print(f"Original disputes row count: {len(disputes)}")

    dispute_tx_ids = set(disputes['transaction_id'].dropna().unique())
    print(f"Unique transaction IDs in disputes.csv: {len(dispute_tx_ids)}")

    # 1. Update dispute_created flag in transactions.csv
    transactions['dispute_created'] = transactions['transaction_id'].isin(dispute_tx_ids).astype(int)
    reconciled_count = (transactions['dispute_created'] == 1).sum()
    print(f"Reconciled transactions with dispute_created == 1: {reconciled_count}")

    # Assert set equality
    reconciled_ids = set(transactions[transactions['dispute_created'] == 1]['transaction_id'])
    assert reconciled_ids == dispute_tx_ids, "Mismatch between transaction dispute_created IDs and disputes.csv transaction_ids!"
    print("ASSERTION PASSED: set(transactions[dispute_created == 1].transaction_id) == set(disputes.transaction_id)")

    # 2. Drop legacy / stale columns from transactions.csv
    legacy_cols = ['dispute_type', 'chargeback_created', 'chargeback_outcome']
    cols_to_drop = [c for c in legacy_cols if c in transactions.columns]
    if cols_to_drop:
        transactions.drop(columns=cols_to_drop, inplace=True)
        print(f"Dropped legacy columns from transactions.csv: {cols_to_drop}")

    print(f"Final transactions schema: {len(transactions)} rows, {len(transactions.columns)} columns")

    # Save repaired transactions.csv
    transactions.to_csv(tx_path, index=False)
    print(f"Saved repaired transactions.csv to {tx_path}")

if __name__ == '__main__':
    repair_linkage()
