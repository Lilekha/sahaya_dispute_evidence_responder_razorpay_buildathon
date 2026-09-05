"""Clean, reproducible generator for the final Razorpay Buildathon dataset.

This is a consolidated reconstruction of the generation pipeline. It intentionally
combines the useful logic from the earlier generation/repair iterations into one
canonical script rather than reproducing every historical patch file.
"""

import json
import hashlib
from datetime import timedelta
from pathlib import Path

import numpy as np
import pandas as pd

from config import (
    SEED, CORE_DIR, DEMO_DIR, N_MERCHANTS, N_TRANSACTIONS, N_DISPUTES,
    START_DATE, END_DATE, CITIES, ARCHETYPE_COUNTS, FULFILLMENT, SUBSCRIPTION,
    DOCUMENTATION_MATURITY, SIZE_COUNTS, SIZE_TXN_RANGES, REASON_CODES,
    REASON_DESCRIPTIONS, REASON_WEIGHTS, EVIDENCE_SLOTS, REQUIRED,
    DEMO_MERCHANTS,
)

FIRST_NAMES = ["Ananya", "Arjun", "Aarav", "Ishita", "Riya", "Neha", "Rahul", "Karan",
               "Meera", "Priya", "Vikram", "Nikhil", "Aditi", "Rohan", "Sana", "Kabir"]
LAST_NAMES = ["Sharma", "Patel", "Iyer", "Gupta", "Singh", "Nair", "Mehta", "Reddy",
              "Das", "Kapoor", "Joshi", "Bose"]

PRICE_MENUS = {
    "subscription_edtech": [499, 999, 2999, 9999, 14999],
    "saas_tools": [399, 799, 1499, 2999, 9999, 19999],
    "fitness_membership": [999, 1499, 3999, 5999, 14999],
}
AMOUNT_RANGES = {
    "social_seller": (350, 6000),
    "d2c_brand": (500, 15000),
    "marketplace_retailer": (200, 40000),
    "travel_booking": (1500, 90000),
}

def stable_seed(value: str) -> int:
    digest = hashlib.sha256(f"{SEED}:{value}".encode()).hexdigest()
    return int(digest[:12], 16) % 2_000_000_000

def rng_for(value: str) -> np.random.Generator:
    return np.random.default_rng(stable_seed(value))

def merchant_name(archetype: str, i: int) -> str:
    if i <= 7:
        return DEMO_MERCHANTS[f"M{i:06d}"][0]
    prefixes = {
        "social_seller": ["Urban", "Desi", "Ananya", "Mira"],
        "d2c_brand": ["Prime", "Nova", "Royal", "Indie"],
        "marketplace_retailer": ["Super", "Mega", "One", "All"],
        "subscription_edtech": ["Gyan", "Study", "Learn", "Scholar"],
        "saas_tools": ["Code", "Data", "Cloud", "Tech"],
        "fitness_membership": ["Fit", "Active", "Strong", "Pulse"],
        "travel_booking": ["Trip", "Travel", "Journey", "Go"],
    }
    suffixes = {
        "social_seller": ["Crafts", "Studio", "Creations", "Workshop"],
        "d2c_brand": ["Wear", "Style", "Essentials", "Store"],
        "marketplace_retailer": ["Mart", "Bazaar", "Cart", "Hub"],
        "subscription_edtech": ["Academy", "Prep", "Classes", "Hub"],
        "saas_tools": ["Tools", "Suite", "Stack", "Pilot"],
        "fitness_membership": ["Forge", "Zone", "Centre", "Arena"],
        "travel_booking": ["Well", "Easy", "Smart", "Link"],
    }
    r = rng_for(f"name:{i}")
    if archetype == "social_seller":
        return f"{FIRST_NAMES[r.integers(len(FIRST_NAMES))]}'s {suffixes[archetype][r.integers(4)]}"
    return f"{prefixes[archetype][r.integers(4)]}{suffixes[archetype][r.integers(4)]}"

def allocate_archetypes() -> list[str]:
    result = []
    for archetype, count in ARCHETYPE_COUNTS.items():
        result.extend([archetype] * count)
    # Preserve demo archetypes in slots 1-7 and shuffle the rest deterministically.
    tail = result[:]
    demo_arch = [DEMO_MERCHANTS[f"M{i:06d}"][1] for i in range(1, 8)]
    for a in demo_arch:
        tail.remove(a)
    rng = rng_for("archetype-order")
    rng.shuffle(tail)
    return demo_arch + tail

def allocate_sizes() -> list[str]:
    sizes = []
    for size, count in SIZE_COUNTS.items():
        sizes.extend([size] * count)
    # First seven are the demo sizes.
    demos = [DEMO_MERCHANTS[f"M{i:06d}"][2] for i in range(1, 8)]
    tail = sizes[:]
    for s in demos:
        tail.remove(s)
    rng = rng_for("size-order")
    rng.shuffle(tail)
    return demos + tail

def generate_merchants() -> pd.DataFrame:
    archetypes = allocate_archetypes()
    sizes = allocate_sizes()
    rows = []

    for i in range(1, N_MERCHANTS + 1):
        mid = f"M{i:06d}"
        arch, size = archetypes[i - 1], sizes[i - 1]
        r = rng_for(f"merchant:{mid}")
        lo, hi = SIZE_TXN_RANGES[size]
        annual = int(r.integers(lo, hi + 1))
        if i <= 7:
            annual = {
                1: 1800, 2: 3800, 3: 3800, 4: 860, 5: 1600, 6: 3800, 7: 8500
            }[i]
            maturity = DEMO_MERCHANTS[mid][3]
        else:
            maturity = float(np.clip(
                DOCUMENTATION_MATURITY[arch] + r.uniform(-0.08, 0.08), 0.15, 0.98
            ))

        subscription = SUBSCRIPTION[arch]
        price_points = (
            sorted(r.choice(PRICE_MENUS[arch], size=min(4, len(PRICE_MENUS[arch])), replace=False).tolist())
            if subscription else []
        )

        rows.append({
            "merchant_id": mid,
            "merchant_name": merchant_name(arch, i),
            "archetype": arch,
            "industry": arch,
            "city": CITIES[r.integers(len(CITIES))],
            "business_size": size,
            "fulfillment_type": FULFILLMENT[arch],
            "subscription_supported": subscription,
            "documentation_maturity": round(maturity, 6),
            "price_points": json.dumps(price_points),
            "merchant_age_months": int(r.integers(12, 121)),
            "refund_policy_documented": int(r.random() < maturity),
            "fulfillment_tracking_available": int(FULFILLMENT[arch] == "physical_delivery" and r.random() < 0.95),
            "annual_transactions": annual,
        })

    return pd.DataFrame(rows)

def generate_customers(merchants: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for m in merchants.itertuples():
        r = rng_for(f"customers:{m.merchant_id}")
        # Customer volume is proportional to merchant activity, with repeat purchasing.
        n = max(5, int(m.annual_transactions * r.uniform(0.30, 0.42)))
        for j in range(n):
            rows.append({
                "customer_id": f"CUST_{m.merchant_id}_{j+1:05d}",
                "merchant_id": m.merchant_id,
                "customer_name": f"{FIRST_NAMES[r.integers(len(FIRST_NAMES))]} {LAST_NAMES[r.integers(len(LAST_NAMES))]}",
                "city": CITIES[r.integers(len(CITIES))],
                "created_at": (
                    pd.Timestamp(START_DATE) - pd.Timedelta(days=int(r.integers(30, 730)))
                ).strftime("%Y-%m-%d"),
                "email_domain": r.choice(["gmail.com", "outlook.com", "yahoo.com", "corporate.com"], p=[.45, .25, .20, .10]),
                "contact_present": int(r.random() < .653),
                "city_tier": int(r.choice([1, 2, 3], p=[.35, .40, .25])),
            })
    return pd.DataFrame(rows)

def generate_transactions(merchants: pd.DataFrame, customers: pd.DataFrame) -> pd.DataFrame:
    # Use annual_transactions as the transaction count contract and adjust the
    # final merchant counts proportionally so the final dataset is exactly 500k.
    counts = merchants["annual_transactions"].astype(int).to_numpy()
    counts = np.maximum(counts, 1)
    scaled = np.floor(counts / counts.sum() * N_TRANSACTIONS).astype(int)
    scaled[np.argmax(counts)] += N_TRANSACTIONS - scaled.sum()

    customer_map = customers.groupby("merchant_id")["customer_id"].apply(list).to_dict()
    chunks = []
    tx_counter = 1
    start = pd.Timestamp(START_DATE)
    end = pd.Timestamp(END_DATE)
    seconds = int((end - start).total_seconds())

    for idx, m in enumerate(merchants.itertuples()):
        n = int(scaled[idx])
        r = rng_for(f"transactions:{m.merchant_id}")
        custs = customer_map[m.merchant_id]

        if m.subscription_supported:
            prices = json.loads(m.price_points)
            amounts = r.choice(prices, size=n, replace=True)
        else:
            lo, hi = AMOUNT_RANGES.get(m.archetype, (300, 10000))
            amounts = r.integers(lo, hi + 1, size=n)

        ts = np.sort(r.integers(0, seconds + 1, size=n))
        payment = r.choice(
            ["credit_card", "upi", "debit_card", "netbanking", "wallet"],
            size=n, p=[.34024, .300142, .27929, .050192, .030136]
        )
        card_mask = np.isin(payment, ["credit_card", "debit_card"])
        network = np.array([None] * n, dtype=object)
        network[card_mask] = r.choice(["Visa", "Mastercard", "RuPay"], size=card_mask.sum(), p=[.50, .33, .17])
        otp = np.where(
            card_mask,
            np.where(r.random(n) < .917, "passed", "failed"),
            "not_applicable",
        )
        attempts = r.choice([1, 2, 3, 4, 5], size=n, p=[.699, .180, .080, .030, .011])
        international = (r.random(n) < .04).astype(int)
        mismatch = (r.random(n) < .08).astype(int)
        customer_ids = r.choice(custs, size=n)
        # Anonymous customers are represented by missing/empty customer IDs.
        anon = r.random(n) < .20
        customer_ids = np.where(anon, "", customer_ids)

        delivery = np.array([None] * n, dtype=object)
        signed = np.array([None] * n, dtype=object)
        delivered_at = np.array([None] * n, dtype=object)
        if m.fulfillment_type == "physical_delivery":
            u = r.random(n)
            delivery = np.where(u < .80, "delivered",
                        np.where(u < .92, "in_transit",
                        np.where(u < .96, "rto", "lost")))
            delivered_mask = delivery == "delivered"
            signed[delivered_mask] = (r.random(delivered_mask.sum()) < .616).astype(int)
            for j in np.flatnonzero(delivered_mask):
                delivered_at[j] = (start + pd.Timedelta(seconds=int(ts[j] + r.integers(1, 7 * 86400)))).strftime("%Y-%m-%d %H:%M:%S")

        chunk = pd.DataFrame({
            "transaction_id": [f"TXN{tx_counter+i:08d}" for i in range(n)],
            "merchant_id": m.merchant_id,
            "customer_id": customer_ids,
            "amount": amounts.astype(int),
            "payment_method": payment,
            "network": network,
            "otp_3ds_status": otp,
            "avs_match": (r.random(n) < .849).astype(int),
            "device_id": [f"DEV{int(x):08d}" for x in r.integers(1, 9_000_000, size=n)],
            "ip_risk_score": np.round(r.beta(2, 8, size=n), 4),
            "payment_attempt_count": attempts,
            "is_international": international,
            "billing_shipping_mismatch": mismatch,
            "delivery_status": delivery,
            "delivered_at": delivered_at,
            "has_signed_proof": signed,
            "timestamp": [start + pd.Timedelta(seconds=int(x)) for x in ts],
        })
        chunks.append(chunk)
        tx_counter += n

    tx = pd.concat(chunks, ignore_index=True)
    tx = tx.sort_values(["merchant_id", "timestamp"]).reset_index(drop=True)

    known = tx["customer_id"].ne("")
    tx["customer_previous_orders"] = 0
    tx["customer_previous_spend"] = 0
    tx["customer_previous_disputes"] = 0
    tx["days_since_customer_last_purchase"] = 0

    tx.loc[known, "customer_previous_orders"] = tx.loc[known].groupby(["merchant_id", "customer_id"]).cumcount()
    tx.loc[known, "customer_previous_spend"] = (
        tx.loc[known].groupby(["merchant_id", "customer_id"])["amount"].cumsum()
        - tx.loc[known, "amount"]
    ).astype(int)
    previous_ts = tx.loc[known].groupby(["merchant_id", "customer_id"])["timestamp"].shift(1)
    tx.loc[known, "days_since_customer_last_purchase"] = (
        (tx.loc[known, "timestamp"] - previous_ts).dt.total_seconds().div(86400).fillna(0).astype(int)
    )

    return tx.sort_values("timestamp").reset_index(drop=True)

def generate_disputes(transactions: pd.DataFrame, merchants: pd.DataFrame) -> pd.DataFrame:
    card = transactions[transactions["payment_method"].isin(["credit_card", "debit_card"])].copy()
    # A single deterministic sample creates the exact final dispute count.
    r = rng_for("disputes:sample")
    selected_idx = r.choice(card.index.to_numpy(), size=N_DISPUTES, replace=False)
    dtx = card.loc[selected_idx].copy().reset_index(drop=True)

    merchant_lookup = merchants.set_index("merchant_id")
    reasons = []
    for row in dtx.itertuples():
        weights = REASON_WEIGHTS[row.merchant_id and merchant_lookup.loc[row.merchant_id, "archetype"]]
        reasons.append(r.choice(REASON_CODES, p=weights))

    r = rng_for("disputes:fields")
    created = []
    for ts in pd.to_datetime(dtx["timestamp"]):
        created.append(ts + pd.Timedelta(days=int(r.integers(3, 121)), hours=int(r.integers(0, 24))))

    dispute_created = pd.Series(created)
    respond_by = dispute_created + pd.to_timedelta(r.integers(7, 22, N_DISPUTES), unit="D")
    contested = r.random(N_DISPUTES) < .655
    networks = dtx["network"].to_numpy()

    fees = np.where(contested, np.where(networks == "Visa", r.integers(600, 751, N_DISPUTES),
                         np.where(networks == "Mastercard", r.integers(500, 651, N_DISPUTES),
                                  r.integers(400, 501, N_DISPUTES))), 0)
    op_cost = np.where(contested, r.integers(150, 301, N_DISPUTES), 0)

    # Documentation maturity influences contested outcomes, but outcome columns
    # are generated independently of any post-dispute decision fields.
    maturity = dtx["merchant_id"].map(merchants.set_index("merchant_id")["documentation_maturity"]).to_numpy()
    won_prob = np.clip(.28 + .40 * maturity, .15, .72)
    won = contested & (r.random(N_DISPUTES) < won_prob)

    outcome = np.where(~contested, "accepted_refunded", np.where(won, "won", "lost"))
    resolution = np.where(contested, respond_by, dispute_created + pd.Timedelta(days=2))

    return pd.DataFrame({
        "dispute_id": [f"DSP{i:06d}" for i in range(1, N_DISPUTES + 1)],
        "transaction_id": dtx["transaction_id"].to_numpy(),
        "merchant_id": dtx["merchant_id"].to_numpy(),
        "customer_id": dtx["customer_id"].to_numpy(),
        "network": networks,
        "reason_code": reasons,
        "reason_description": [REASON_DESCRIPTIONS[x] for x in reasons],
        "dispute_created_at": dispute_created.dt.strftime("%Y-%m-%d %H:%M:%S"),
        "dispute_amount": dtx["amount"].astype(int).to_numpy(),
        "contest_fee": fees.astype(int),
        "operational_review_cost": op_cost.astype(int),
        "respond_by": respond_by.dt.strftime("%Y-%m-%d %H:%M:%S"),
        "days_to_deadline": (respond_by - dispute_created).dt.days,
        "merchant_action": np.where(contested, "contested", "accepted"),
        "dispute_outcome": outcome,
        "resolution_date": pd.Series(resolution).dt.strftime("%Y-%m-%d %H:%M:%S"),
    })

def generate_evidence(disputes: pd.DataFrame, merchants: pd.DataFrame) -> pd.DataFrame:
    merchant_map = merchants.set_index("merchant_id")
    rows = []
    evidence_id = 1
    r = rng_for("evidence")
    for d in disputes.itertuples():
        fulfil = merchant_map.loc[d.merchant_id, "fulfillment_type"]
        maturity = float(merchant_map.loc[d.merchant_id, "documentation_maturity"])
        slots = EVIDENCE_SLOTS[fulfil]
        required = REQUIRED[d.reason_code]
        dispute_time = pd.Timestamp(d.dispute_created_at)
        tx_time = pd.Timestamp(
            # transaction timestamp is not stored in disputes, so use a safe pre-dispute timestamp.
            dispute_time - pd.Timedelta(days=int(r.integers(1, 90)))
        )
        for i, ev_type in enumerate(slots):
            req = int(required[i])
            available = int(r.random() < np.clip(maturity + .08, .05, .98))
            quality = round(float(r.uniform(.55, .98) * (.75 + .25 * maturity)), 2) if available else 0.0
            if available:
                status = "APPLICABLE"
            else:
                status = "UNAVAILABLE"
            rows.append({
                "evidence_id": f"EVID{evidence_id:07d}",
                "dispute_id": d.dispute_id,
                "transaction_id": d.transaction_id,
                "evidence_type": ev_type,
                "applicability_status": status,
                "available": available,
                "required": req,
                "relevant": int(available and (r.random() < .92)),
                "quality_score": quality,
                "source_system": r.choice(["erp", "support", "crm", "payment_gateway", "shipping"]),
                "evidence_timestamp": (
                    tx_time + (dispute_time - tx_time) * r.random()
                ).strftime("%Y-%m-%d %H:%M:%S"),
            })
            evidence_id += 1
    return pd.DataFrame(rows)

def save_demo_merchants(merchants: pd.DataFrame, disputes: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for mid, (name, arch, size, maturity, priority) in DEMO_MERCHANTS.items():
        m = merchants.loc[merchants["merchant_id"] == mid].iloc[0]
        count = int((disputes["merchant_id"] == mid).sum())
        descriptions = {
            "M000001": "Hand-crocheted bags sold through Instagram DMs, ~60 orders/month, no written return policy.",
            "M000002": "Direct-to-consumer footwear brand with ergonomic designs, clear return policy, full tracking.",
            "M000003": "Online civil-services test-prep platform with tiered subscription plans.",
            "M000004": "Developer productivity and code-optimisation SaaS with monthly/annual tiers.",
            "M000005": "Neighbourhood gym chain with monthly, quarterly, and annual memberships.",
            "M000006": "Online travel agency for domestic tourism; booking-only, no subscription.",
            "M000007": "Multi-category marketplace: electronics, fashion, home goods; robust SLA tracking.",
        }
        rows.append({
            "merchant_id": mid,
            "merchant_name": name,
            "merchant_archetype": arch,
            "fulfillment_type": FULFILLMENT[arch],
            "subscription_supported": SUBSCRIPTION[arch],
            "business_size": size,
            "documentation_maturity": maturity,
            "demo_priority": priority,
            "business_description": descriptions[mid],
            "annual_transactions": int(m["annual_transactions"]),
            "dispute_count": count,
        })
    return pd.DataFrame(rows)

def main():
    CORE_DIR.mkdir(parents=True, exist_ok=True)
    DEMO_DIR.mkdir(parents=True, exist_ok=True)

    merchants = generate_merchants()
    customers = generate_customers(merchants)
    transactions = generate_transactions(merchants, customers)
    disputes = generate_disputes(transactions, merchants)
    evidence = generate_evidence(disputes, merchants)
    demo = save_demo_merchants(merchants, disputes)

    merchants.to_csv(CORE_DIR / "merchants.csv", index=False)
    customers.to_csv(CORE_DIR / "customers.csv", index=False)
    transactions.to_csv(CORE_DIR / "transactions.csv", index=False)
    disputes.to_csv(CORE_DIR / "disputes.csv", index=False)
    evidence.to_csv(CORE_DIR / "evidence.csv", index=False)
    demo.to_csv(DEMO_DIR / "demo_merchants.csv", index=False)

    print("\nGenerated:")
    for name, df in [
        ("merchants", merchants), ("customers", customers),
        ("transactions", transactions), ("disputes", disputes),
        ("evidence", evidence), ("demo_merchants", demo),
    ]:
        print(f"  {name:16s} {len(df):,} rows")
    print("\nRun validate_dataset.py next.")

if __name__ == "__main__":
    main()
