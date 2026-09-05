"""Validation checks for the final Razorpay Buildathon dataset."""

import sys
from pathlib import Path
import pandas as pd

from config import CORE_DIR, DEMO_DIR, N_DISPUTES, EVIDENCE_PER_DISPUTE

EXPECTED = {
    "merchants.csv": 300,
    "customers.csv": 178_562,
    "transactions.csv": 500_000,
    "disputes.csv": N_DISPUTES,
    "evidence.csv": N_DISPUTES * EVIDENCE_PER_DISPUTE,
}

EVIDENCE_TYPES = {
    "order_confirmation", "invoice", "shipping_label", "tracking_number",
    "delivery_confirmation", "customer_communication",
    "access_log", "service_record", "cancellation_record",
}

LEAKAGE_COLUMNS = {
    "dispute_outcome", "resolution_date",
}

def check(label, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    print(f"{status:4s}  {label}" + (f" — {detail}" if detail else ""))
    return condition

def main():
    print("=" * 72)
    print("RAZORPAY BUILDATHON DATASET VALIDATION")
    print("=" * 72)

    paths = {name: CORE_DIR / name for name in EXPECTED}
    ok = True
    for name, expected in EXPECTED.items():
        exists = paths[name].exists()
        ok &= check(f"{name} exists", exists)
        if exists:
            df = pd.read_csv(paths[name])
            ok &= check(f"{name} row count", len(df) == expected, f"{len(df):,} / {expected:,}")

    if not ok:
        return 1

    m = pd.read_csv(paths["merchants.csv"])
    c = pd.read_csv(paths["customers.csv"])
    t = pd.read_csv(paths["transactions.csv"])
    d = pd.read_csv(paths["disputes.csv"])
    e = pd.read_csv(paths["evidence.csv"])

    print("\nPrimary keys")
    ok &= check("merchant_id unique", m["merchant_id"].is_unique)
    ok &= check("merchant-scoped customer key unique",
                 ~c.duplicated(["merchant_id", "customer_id"]).any())
    ok &= check("transaction_id unique", t["transaction_id"].is_unique)
    ok &= check("dispute_id unique", d["dispute_id"].is_unique)
    ok &= check("evidence_id unique", e["evidence_id"].is_unique)

    print("\nForeign keys")
    ok &= check("transactions -> merchants",
                 t["merchant_id"].isin(m["merchant_id"]).all())
    customer_keys = set(zip(c["merchant_id"], c["customer_id"]))
    tx_customer_keys = set(zip(t["merchant_id"], t["customer_id"]))
    # Anonymous transactions are intentionally excluded from customer FK checks.
    named_tx_keys = set(zip(
        t.loc[t["customer_id"].ne(""), "merchant_id"],
        t.loc[t["customer_id"].ne(""), "customer_id"],
    ))
    ok &= check("named transactions -> customers", named_tx_keys.issubset(customer_keys))
    ok &= check("disputes -> transactions",
                 d["transaction_id"].isin(t["transaction_id"]).all())
    ok &= check("evidence -> disputes",
                 e["dispute_id"].isin(d["dispute_id"]).all())

    print("\nDispute / evidence invariants")
    ev_per_dispute = e.groupby("dispute_id")["evidence_id"].count()
    ok &= check("exactly 6 evidence rows per dispute",
                 len(ev_per_dispute) == len(d) and (ev_per_dispute == 6).all())
    ok &= check("evidence transaction_id matches dispute",
                 e.merge(d[["dispute_id", "transaction_id"]], on="dispute_id")
                  .eval("transaction_id_x == transaction_id_y").all())
    ok &= check("evidence available/status consistency",
                 not ((e["available"] == 1) & (e["applicability_status"] == "UNAVAILABLE")).any())
    ok &= check("unavailable evidence has zero quality",
                 (e.loc[e["available"] == 0, "quality_score"] == 0).all())
    ok &= check("all evidence types canonical",
                 set(e["evidence_type"]).issubset(EVIDENCE_TYPES))

    print("\nTransaction / dispute consistency")
    joined = d.merge(
        t[["transaction_id", "merchant_id", "customer_id", "amount", "timestamp"]],
        on="transaction_id", suffixes=("_d", "_t"),
    )
    ok &= check("dispute merchant matches transaction",
                 (joined["merchant_id_d"] == joined["merchant_id_t"]).all())
    ok &= check("dispute customer matches transaction",
                 (joined["customer_id_d"] == joined["customer_id_t"]).all())
    ok &= check("dispute amount matches transaction",
                 (joined["dispute_amount"] == joined["amount"]).all())
    ok &= check("transaction occurs before dispute",
                 (pd.to_datetime(joined["timestamp"]) <= pd.to_datetime(joined["dispute_created_at"])).all())

    print("\nPoint-in-time customer features")
    known = t["customer_id"].ne("")
    pt = t.loc[known].sort_values(["merchant_id", "customer_id", "timestamp"]).copy()
    expected_orders = pt.groupby(["merchant_id", "customer_id"]).cumcount()
    ok &= check("customer_previous_orders is monotonic / point-in-time",
                 (pt["customer_previous_orders"].to_numpy() == expected_orders.to_numpy()).all())
    ok &= check("customer_previous_spend is non-negative",
                 (t["customer_previous_spend"] >= 0).all())

    print("\nLeakage review")
    ok &= check("post-dispute outcome columns are identified",
                 LEAKAGE_COLUMNS.issubset(d.columns))
    ok &= check("target has only accepted/contested outcomes",
                 set(d["merchant_action"]) <= {"accepted", "contested"})

    print("\nDemo merchants")
    demo_path = DEMO_DIR / "demo_merchants.csv"
    ok &= check("demo file exists", demo_path.exists())
    if demo_path.exists():
        demo = pd.read_csv(demo_path)
        ok &= check("7 demo merchants", len(demo) == 7)
        ok &= check("demo IDs M000001-M000007",
                     list(demo["merchant_id"]) == [f"M{i:06d}" for i in range(1, 8)])

    print("\n" + "=" * 72)
    print("FINAL VERDICT:", "PASS" if ok else "FAIL")
    print("=" * 72)
    return 0 if ok else 1

if __name__ == "__main__":
    sys.exit(main())
