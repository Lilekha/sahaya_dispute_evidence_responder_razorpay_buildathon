"""
generate_dataset_v5.py
======================
Full from-scratch dataset generation.
Implements DATASET_REGENERATION_V5.md with the outcome model from
DATASET_V5_1_PRECISION.md (§1 replaces V5 §7).

Usage:
    python src/generate_dataset_v5.py

Outputs
-------
data/core/merchants.csv            300 rows
data/core/customers.csv            merchant-scoped
data/core/transactions.csv.gz      ~2 M rows  (GZIP)
data/core/disputes.csv             ~10-16 k rows
data/core/evidence.csv             exactly 6 × dispute count
data/demo/demo_merchants.csv       7 rows
data/DATASET_MANIFEST.md           regenerated
data/DATA_PROFILE.md               regenerated
data/ML_DATA_DICTIONARY.md         regenerated
"""

import os, json, shutil, sys, random
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path

# ── Reproducibility ───────────────────────────────────────────────────────────
SEED = 42
np.random.seed(SEED)
random.seed(SEED)

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
CORE_DIR = DATA_DIR / "core"
DEMO_DIR = DATA_DIR / "demo"
AUX_DIR  = DATA_DIR / "auxiliary"

# ── Time window ───────────────────────────────────────────────────────────────
# Use exactly half a year so that annual_transactions/2 ≈ 2 M total
START_DATE      = datetime(2025, 1, 1)
END_DATE        = datetime(2025, 6, 30, 23, 59, 59)
PERIOD_SECONDS  = int((END_DATE - START_DATE).total_seconds())

# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════

ARCHETYPES = [
    "d2c_brand", "social_seller", "marketplace_retailer",
    "subscription_edtech", "saas_tools", "fitness_membership", "travel_booking",
]

FULFILLMENT_MAP = {
    "d2c_brand":            "physical_delivery",
    "social_seller":        "physical_delivery",
    "marketplace_retailer": "physical_delivery",
    "subscription_edtech":  "digital_service",
    "saas_tools":           "digital_service",
    "fitness_membership":   "membership_service",
    "travel_booking":       "booking_service",
}

SUBSCRIPTION_MAP = {
    "d2c_brand":            0,
    "social_seller":        0,
    "marketplace_retailer": 0,
    "subscription_edtech":  1,
    "saas_tools":           1,
    "fitness_membership":   1,
    "travel_booking":       0,
}

DOC_MATURITY_BASE = {
    "marketplace_retailer": 0.92,
    "saas_tools":           0.88,
    "d2c_brand":            0.80,
    "subscription_edtech":  0.68,
    "travel_booking":       0.62,
    "fitness_membership":   0.55,
    "social_seller":        0.34,
}

SIZE_ARCHETYPES = {
    "micro":  ["social_seller"],
    "small":  ["social_seller", "d2c_brand", "subscription_edtech",
               "saas_tools", "fitness_membership"],
    "medium": ["d2c_brand", "subscription_edtech", "saas_tools",
               "fitness_membership", "travel_booking"],
    "large":  ["marketplace_retailer", "d2c_brand", "travel_booking"],
}

SIZE_TXN_RANGE = {
    "micro":  (300,    900),
    "small":  (1_500,  6_000),
    "medium": (8_000,  30_000),
    "large":  (40_000, 120_000),
}

SIZE_DISPUTE_RATE = {
    "micro":  (0.006, 0.012),
    "small":  (0.005, 0.011),
    "medium": (0.004, 0.009),
    "large":  (0.003, 0.007),
}

SUB_PRICE_MENUS = {
    "subscription_edtech": [499, 999, 1_499, 2_999, 4_999, 9_999, 14_999, 24_999],
    "saas_tools":          [399, 799, 1_499, 2_999, 4_999, 9_999, 19_999, 49_999],
    "fitness_membership":  [999, 1_499, 2_499, 3_999, 5_999, 8_999, 14_999, 24_999],
}

AMOUNT_RANGES = {
    "social_seller":        (350,    6_000),
    "d2c_brand":            (500,    15_000),
    "marketplace_retailer": (200,    40_000),
    "travel_booking":       (1_500,  90_000),
}

# §4.1 Permission matrix
PERMISSION_MATRIX = {
    "MERCHANDISE_NOT_RECEIVED":     {"d2c_brand", "social_seller", "marketplace_retailer"},
    "SERVICE_NOT_RENDERED":         {"subscription_edtech", "saas_tools",
                                     "fitness_membership", "travel_booking"},
    "MERCHANDISE_NOT_AS_DESCRIBED": {"d2c_brand", "social_seller", "marketplace_retailer",
                                     "subscription_edtech", "fitness_membership", "travel_booking"},
    "RECURRING_BILLING_DISPUTE":    {"subscription_edtech", "saas_tools", "fitness_membership"},
    "CREDIT_NOT_PROCESSED":         set(ARCHETYPES),
    "DUPLICATE_TRANSACTION":        set(ARCHETYPES),
    "UNAUTHORIZED_TRANSACTION":     set(ARCHETYPES),
}

REASON_DESCRIPTIONS = {
    "MERCHANDISE_NOT_RECEIVED":     "Cardholder claims ordered merchandise was not received",
    "SERVICE_NOT_RENDERED":         "Cardholder states the service was not provided",
    "MERCHANDISE_NOT_AS_DESCRIBED": "Cardholder claims merchandise or service was not as described",
    "RECURRING_BILLING_DISPUTE":    "Cardholder claims recurring subscription billing was unauthorized or not cancelled",
    "CREDIT_NOT_PROCESSED":         "Cardholder claims promised credit or refund was not posted",
    "DUPLICATE_TRANSACTION":        "Cardholder claims single purchase was billed multiple times",
    "UNAUTHORIZED_TRANSACTION":     "Cardholder claims transaction was unauthorized or fraudulent",
}

# §4.2 Reason-code weights per archetype
REASON_WEIGHTS = {
    "d2c_brand": [
        ("MERCHANDISE_NOT_RECEIVED",     0.35),
        ("MERCHANDISE_NOT_AS_DESCRIBED", 0.25),
        ("UNAUTHORIZED_TRANSACTION",     0.20),
        ("CREDIT_NOT_PROCESSED",         0.12),
        ("DUPLICATE_TRANSACTION",        0.08),
    ],
    "social_seller": [
        ("MERCHANDISE_NOT_AS_DESCRIBED", 0.40),
        ("MERCHANDISE_NOT_RECEIVED",     0.30),
        ("UNAUTHORIZED_TRANSACTION",     0.15),
        ("CREDIT_NOT_PROCESSED",         0.10),
        ("DUPLICATE_TRANSACTION",        0.05),
    ],
    "marketplace_retailer": [
        ("MERCHANDISE_NOT_RECEIVED",     0.30),
        ("MERCHANDISE_NOT_AS_DESCRIBED", 0.30),
        ("UNAUTHORIZED_TRANSACTION",     0.22),
        ("CREDIT_NOT_PROCESSED",         0.12),
        ("DUPLICATE_TRANSACTION",        0.06),
    ],
    "subscription_edtech": [
        ("RECURRING_BILLING_DISPUTE",    0.40),
        ("SERVICE_NOT_RENDERED",         0.20),
        ("CREDIT_NOT_PROCESSED",         0.18),
        ("UNAUTHORIZED_TRANSACTION",     0.15),
        ("MERCHANDISE_NOT_AS_DESCRIBED", 0.04),
        ("DUPLICATE_TRANSACTION",        0.03),
    ],
    "saas_tools": [
        ("RECURRING_BILLING_DISPUTE",    0.50),
        ("UNAUTHORIZED_TRANSACTION",     0.20),
        ("CREDIT_NOT_PROCESSED",         0.15),
        ("SERVICE_NOT_RENDERED",         0.12),
        ("DUPLICATE_TRANSACTION",        0.03),
    ],
    "fitness_membership": [
        ("RECURRING_BILLING_DISPUTE",    0.45),
        ("SERVICE_NOT_RENDERED",         0.20),
        ("CREDIT_NOT_PROCESSED",         0.13),
        ("MERCHANDISE_NOT_AS_DESCRIBED", 0.12),
        ("UNAUTHORIZED_TRANSACTION",     0.07),
        ("DUPLICATE_TRANSACTION",        0.03),
    ],
    "travel_booking": [
        ("SERVICE_NOT_RENDERED",         0.35),
        ("MERCHANDISE_NOT_AS_DESCRIBED", 0.25),
        ("CREDIT_NOT_PROCESSED",         0.18),
        ("UNAUTHORIZED_TRANSACTION",     0.15),
        ("DUPLICATE_TRANSACTION",        0.07),
    ],
}

# §6 Evidence slot sets (6 per dispute, ordered to match REQUIRED_MATRIX)
EVIDENCE_SLOTS = {
    "physical_delivery":  ["order_confirmation", "invoice", "shipping_label",
                           "tracking_number",    "delivery_confirmation", "customer_communication"],
    "digital_service":    ["order_confirmation", "invoice", "access_log",
                           "service_record",     "cancellation_record",   "customer_communication"],
    "membership_service": ["order_confirmation", "invoice", "access_log",
                           "service_record",     "cancellation_record",   "customer_communication"],
    "booking_service":    ["order_confirmation", "invoice", "access_log",
                           "service_record",     "cancellation_record",   "customer_communication"],
}

EVIDENCE_SOURCE = {
    "order_confirmation":    "billing",
    "invoice":               "billing",
    "shipping_label":        "logistics",
    "tracking_number":       "logistics",
    "delivery_confirmation": "logistics",
    "access_log":            "access",
    "service_record":        "ops",
    "cancellation_record":   "billing",
    "customer_communication":"crm",
}

# §6.1 Required patterns: (reason_code, fulfillment_type) → 6-element list
# Slot order matches EVIDENCE_SLOTS above
REQUIRED_MATRIX = {
    # physical_delivery: [order_conf, invoice, shipping_label, tracking, delivery_conf, customer_comm]
    ("MERCHANDISE_NOT_RECEIVED",     "physical_delivery"):  [1, 0, 1, 1, 1, 0],
    ("MERCHANDISE_NOT_AS_DESCRIBED", "physical_delivery"):  [1, 0, 0, 0, 1, 1],
    ("UNAUTHORIZED_TRANSACTION",     "physical_delivery"):  [1, 1, 0, 0, 1, 1],
    ("CREDIT_NOT_PROCESSED",         "physical_delivery"):  [1, 1, 0, 0, 0, 1],
    ("DUPLICATE_TRANSACTION",        "physical_delivery"):  [1, 1, 0, 0, 0, 0],
    # digital_service: [order_conf, invoice, access_log, service_record, cancellation_record, customer_comm]
    ("SERVICE_NOT_RENDERED",         "digital_service"):    [1, 0, 1, 1, 0, 0],
    ("RECURRING_BILLING_DISPUTE",    "digital_service"):    [1, 1, 1, 0, 1, 1],
    ("MERCHANDISE_NOT_AS_DESCRIBED", "digital_service"):    [1, 0, 1, 1, 0, 1],
    ("UNAUTHORIZED_TRANSACTION",     "digital_service"):    [1, 1, 1, 0, 0, 1],
    ("CREDIT_NOT_PROCESSED",         "digital_service"):    [1, 1, 0, 0, 1, 1],
    ("DUPLICATE_TRANSACTION",        "digital_service"):    [1, 1, 0, 0, 0, 0],
    # membership_service: same slot names as digital_service
    ("SERVICE_NOT_RENDERED",         "membership_service"): [1, 0, 1, 1, 0, 1],
    ("RECURRING_BILLING_DISPUTE",    "membership_service"): [1, 1, 1, 0, 1, 1],
    ("MERCHANDISE_NOT_AS_DESCRIBED", "membership_service"): [1, 0, 1, 1, 0, 1],
    ("UNAUTHORIZED_TRANSACTION",     "membership_service"): [1, 1, 1, 0, 0, 1],
    ("CREDIT_NOT_PROCESSED",         "membership_service"): [1, 1, 0, 0, 1, 1],
    ("DUPLICATE_TRANSACTION",        "membership_service"): [1, 1, 0, 0, 0, 0],
    # booking_service
    ("SERVICE_NOT_RENDERED",         "booking_service"):    [1, 0, 0, 1, 0, 1],
    ("MERCHANDISE_NOT_AS_DESCRIBED", "booking_service"):    [1, 0, 0, 1, 0, 1],
    ("UNAUTHORIZED_TRANSACTION",     "booking_service"):    [1, 1, 0, 0, 0, 1],
    ("CREDIT_NOT_PROCESSED",         "booking_service"):    [1, 1, 0, 0, 1, 1],
    ("DUPLICATE_TRANSACTION",        "booking_service"):    [1, 1, 0, 0, 0, 0],
}

# V5.1 §1.1 Decisive evidence per reason code (evidence_type or "otp")
DECISIVE_EVIDENCE = {
    "MERCHANDISE_NOT_RECEIVED":     ["delivery_confirmation"],
    "SERVICE_NOT_RENDERED":         ["service_record"],
    "RECURRING_BILLING_DISPUTE":    ["cancellation_record", "access_log"],
    "CREDIT_NOT_PROCESSED":         ["invoice", "cancellation_record"],
    "DUPLICATE_TRANSACTION":        ["invoice"],
    "MERCHANDISE_NOT_AS_DESCRIBED": ["customer_communication"],   # weakly decisive
    "UNAUTHORIZED_TRANSACTION":     [],   # uses otp_3ds_passed from transaction
}

# V5.1 §1.2 Base logits (converted from win-rate targets via logit function)
import math
def _logit(p): return math.log(p / (1 - p))

BASE_LOGIT = {
    "UNAUTHORIZED_TRANSACTION":     _logit(0.20),   # −1.386
    "MERCHANDISE_NOT_RECEIVED":     _logit(0.62),   #  0.489
    "SERVICE_NOT_RENDERED":         _logit(0.48),   # −0.080
    "MERCHANDISE_NOT_AS_DESCRIBED": _logit(0.38),   # −0.490
    "RECURRING_BILLING_DISPUTE":    _logit(0.42),   # −0.322
    "CREDIT_NOT_PROCESSED":         _logit(0.45),   # −0.200
    "DUPLICATE_TRANSACTION":        _logit(0.70),   #  0.847
}

# ── Demo merchant definitions (§8) ────────────────────────────────────────────
DEMO_MERCHANT_DEFS = [
    {
        "merchant_id": "M000001", "merchant_name": "Loops & Knots by Ananya",
        "merchant_archetype": "social_seller", "business_size": "small",
        "annual_transactions": 2200, "documentation_maturity": 0.34,
        "demo_priority": 7,
        "business_description": (
            "Hand-crocheted bags and home pieces sold through Instagram DMs and WhatsApp. "
            "Around 180 orders a month, shipped by local courier. "
            "No written return policy; records live in chat threads."
        ),
    },
    {
        "merchant_id": "M000002", "merchant_name": "SoleCraft",
        "merchant_archetype": "d2c_brand", "business_size": "medium",
        "annual_transactions": 14000, "documentation_maturity": 0.80,
        "demo_priority": 4,
        "business_description": (
            "Direct-to-consumer footwear brand with its own storefront. "
            "Courier-tracked shipping with signed proof of delivery and a documented return policy."
        ),
    },
    {
        "merchant_id": "M000003", "merchant_name": "Gyan IAS Study Circle",
        "merchant_archetype": "subscription_edtech", "business_size": "medium",
        "annual_transactions": 11000, "documentation_maturity": 0.68,
        "demo_priority": 3,
        "business_description": (
            "Competitive-exam coaching sold as monthly and annual subscriptions. "
            "Live and recorded classes; billing records complete, but no physical delivery evidence exists."
        ),
    },
    {
        "merchant_id": "M000004", "merchant_name": "CodePilot",
        "merchant_archetype": "saas_tools", "business_size": "small",
        "annual_transactions": 4500, "documentation_maturity": 0.88,
        "demo_priority": 5,
        "business_description": (
            "Developer tooling sold on four subscription tiers. "
            "Complete billing and access logs; nothing ships."
        ),
    },
    {
        "merchant_id": "M000005", "merchant_name": "FitForge",
        "merchant_archetype": "fitness_membership", "business_size": "small",
        "annual_transactions": 3600, "documentation_maturity": 0.55,
        "demo_priority": 6,
        "business_description": (
            "Gym and studio memberships billed monthly, quarterly and annually. "
            "Service is delivered in person, so evidence is facility check-ins and class attendance "
            "rather than logins. Attendance logging is inconsistent."
        ),
    },
    {
        "merchant_id": "M000006", "merchant_name": "TripWell",
        "merchant_archetype": "travel_booking", "business_size": "medium",
        "annual_transactions": 20000, "documentation_maturity": 0.62,
        "demo_priority": 2,
        "business_description": (
            "Flight, hotel and package bookings. Booking confirmations are strong evidence; "
            "proof that a trip was actually delivered as described is weaker."
        ),
    },
    {
        "merchant_id": "M000007", "merchant_name": "SwitchCart",
        "merchant_archetype": "marketplace_retailer", "business_size": "large",
        "annual_transactions": 65000, "documentation_maturity": 0.92,
        "demo_priority": 1,
        "business_description": (
            "Multi-brand online marketplace with full logistics integration. "
            "The highest transaction volume in the demo set and the most complete evidence trail. "
            "SwitchCart at ~65,000 annual transactions is a mid-size marketplace, not a national one."
        ),
    },
]

# Fixed subscription price points for demo merchants
DEMO_PRICE_POINTS = {
    "M000003": [499, 999, 2999],          # Gyan IAS: 3 edtech tiers
    "M000004": [399, 999, 2999, 9999],    # CodePilot: 4 saas tiers
    "M000005": [999, 2499, 5999],         # FitForge: 3 fitness tiers
}

# ── Name banks ────────────────────────────────────────────────────────────────
INDIAN_FIRST = [
    "Aarav","Aditi","Aishwarya","Amit","Ankita","Arjun","Bhavna","Chetan",
    "Deepak","Dhruv","Divya","Ekta","Gaurav","Geeta","Harsh","Kavya",
    "Krishna","Lakshmi","Meera","Mohan","Neha","Nitin","Priya","Rahul",
    "Ravi","Rohit","Sakshi","Sameer","Sandeep","Shruti","Sneha","Suresh",
    "Tanvi","Uday","Varsha","Vikram","Yogesh","Zara","Arun","Faraz",
]
INDIAN_LAST = [
    "Sharma","Verma","Patel","Singh","Kumar","Gupta","Mehta","Shah",
    "Joshi","Rao","Nair","Reddy","Iyer","Mishra","Dubey","Kapoor",
    "Bose","Das","Ghosh","Sen","Pillai","Menon","Krishnan","Rajan",
]
BIZ_PREFIX = {
    "social_seller":        ["", "Little ", "Mini ", "Artisan "],
    "d2c_brand":            ["Urban ", "Desi ", "Royal ", "Prime ", "Nova "],
    "marketplace_retailer": ["Super", "Mega", "One", "All", "Big"],
    "subscription_edtech":  ["Study ", "Learn ", "Gyan ", "Scholar ", "Vidya "],
    "saas_tools":           ["Code", "Data", "Cloud", "Tech", "Dev"],
    "fitness_membership":   ["Fit", "Strong", "Active", "Iron", "Pulse"],
    "travel_booking":       ["Trip", "Journey", "Travel", "Tour", "Go"],
}
BIZ_SUFFIX = {
    "social_seller":        ["Crafts", "Creations", "Studio", "Workshop", "Art"],
    "d2c_brand":            ["Wear", "Style", "Essentials", "Collections", "Store"],
    "marketplace_retailer": ["Bazaar", "Mart", "Shop", "Cart", "Hub"],
    "subscription_edtech":  ["Circle", "Hub", "Academy", "Classes", "Prep"],
    "saas_tools":           ["Tools", "Suite", "Stack", "Pilot", "Labs"],
    "fitness_membership":   ["Forge", "Zone", "Hub", "Centre", "Arena"],
    "travel_booking":       ["Well", "Easy", "Smart", "Fast", "Link"],
}


# ═══════════════════════════════════════════════════════════════════════════════
# UTILITY FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def sigmoid(x):
    return 1.0 / (1.0 + np.exp(-np.clip(x, -20, 20)))


def gen_biz_name(archetype: str, seed: int) -> str:
    rng = np.random.default_rng(seed)
    if archetype == "social_seller":
        first = INDIAN_FIRST[int(rng.integers(0, len(INDIAN_FIRST)))]
        sfx   = BIZ_SUFFIX["social_seller"][int(rng.integers(0, len(BIZ_SUFFIX["social_seller"])))]
        return f"{first}'s {sfx}"
    pfx = BIZ_PREFIX[archetype][int(rng.integers(0, len(BIZ_PREFIX[archetype])))]
    sfx = BIZ_SUFFIX[archetype][int(rng.integers(0, len(BIZ_SUFFIX[archetype])))]
    return f"{pfx}{sfx}"


def gen_customer_name(rng) -> str:
    first = INDIAN_FIRST[int(rng.integers(0, len(INDIAN_FIRST)))]
    last  = INDIAN_LAST[int(rng.integers(0, len(INDIAN_LAST)))]
    return f"{first} {last}"


def sample_price_points(archetype: str, rng) -> list:
    menu = SUB_PRICE_MENUS[archetype]
    n    = int(rng.choice([3, 4]))
    idx  = rng.choice(len(menu), size=n, replace=False)
    return sorted(int(menu[i]) for i in idx)


def tier_weights(n_tiers: int, archetype: str) -> list:
    if archetype == "fitness_membership":
        raw = [0.60, 0.25, 0.15, 0.10]
    else:
        raw = [0.55, 0.30, 0.15, 0.10]
    w = raw[:n_tiers]
    s = sum(w)
    return [x / s for x in w]


def gen_retail_catalog(archetype: str, seed: int) -> np.ndarray:
    """Returns an array of whole-integer prices; ≥65 % end in 9."""
    rng  = np.random.default_rng(seed)
    lo, hi = AMOUNT_RANGES[archetype]
    n_cat = 25
    if archetype == "travel_booking":
        mu, sigma = np.log(np.sqrt(lo * hi)), 0.8
        raw = np.exp(rng.normal(mu, sigma, n_cat)).clip(lo, hi)
    else:
        raw = rng.uniform(lo, hi, n_cat)
    n9  = int(np.ceil(n_cat * 0.65))
    noth = n_cat - n9
    ends9  = (np.round(raw[:n9]  / 10) * 10 - 1).astype(int).clip(lo, hi)
    others = np.round(raw[n9:]).astype(int).clip(lo, hi)
    cat = np.unique(np.concatenate([ends9, others]))
    cat = cat[(cat >= lo) & (cat <= hi)]
    if len(cat) == 0:
        cat = np.array([int(lo), int(hi)])
    return cat


def maturity_jitter(base: float, rng) -> float:
    return float(np.clip(base + rng.uniform(-0.08, 0.08), 0.15, 0.97))


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 1 — MERCHANTS
# ═══════════════════════════════════════════════════════════════════════════════

def generate_merchants() -> pd.DataFrame:
    print("STEP 1: Generating 300 merchants ...")
    demo_ids = {d["merchant_id"] for d in DEMO_MERCHANT_DEFS}

    # Remaining counts (after demo slots)
    # Demo: 0 micro, 3 small (M1,M4,M5), 3 medium (M2,M3,M6), 1 large (M7)
    remaining = {"micro": 85, "small": 107, "medium": 77, "large": 24}

    rows = []
    m_idx = 8  # non-demo IDs start at M000008

    for size, count in remaining.items():
        allowed    = SIZE_ARCHETYPES[size]
        txn_lo, txn_hi = SIZE_TXN_RANGE[size]
        archetypes = [allowed[i % len(allowed)] for i in range(count)]
        random.shuffle(archetypes)

        for archetype in archetypes:
            mid  = f"M{m_idx:06d}"
            rng  = np.random.default_rng(SEED + m_idx * 17)
            mat  = maturity_jitter(DOC_MATURITY_BASE[archetype], rng)
            ann  = int(rng.integers(txn_lo, txn_hi + 1))

            if SUBSCRIPTION_MAP[archetype]:
                pp    = sample_price_points(archetype, rng)
                pp_js = json.dumps(pp)
            else:
                pp_js = ""

            rows.append({
                "merchant_id":            mid,
                "merchant_name":          gen_biz_name(archetype, m_idx),
                "merchant_archetype":     archetype,
                "fulfillment_type":       FULFILLMENT_MAP[archetype],
                "subscription_supported": SUBSCRIPTION_MAP[archetype],
                "business_size":          size,
                "annual_transactions":    ann,
                "documentation_maturity": round(mat, 3),
                "price_points":           pp_js,
                "is_demo":                0,
                "demo_priority":          None,
                "business_description":   "",
            })
            m_idx += 1

    # Demo merchants
    for d in DEMO_MERCHANT_DEFS:
        arch = d["merchant_archetype"]
        rng  = np.random.default_rng(SEED + hash(d["merchant_id"]) % 999983)
        if SUBSCRIPTION_MAP[arch]:
            pp    = DEMO_PRICE_POINTS.get(d["merchant_id"], sample_price_points(arch, rng))
            pp_js = json.dumps(pp)
        else:
            pp_js = ""

        rows.append({
            "merchant_id":            d["merchant_id"],
            "merchant_name":          d["merchant_name"],
            "merchant_archetype":     arch,
            "fulfillment_type":       FULFILLMENT_MAP[arch],
            "subscription_supported": SUBSCRIPTION_MAP[arch],
            "business_size":          d["business_size"],
            "annual_transactions":    d["annual_transactions"],
            "documentation_maturity": d["documentation_maturity"],
            "price_points":           pp_js,
            "is_demo":                1,
            "demo_priority":          d["demo_priority"],
            "business_description":   d["business_description"],
        })

    df = pd.DataFrame(rows).sort_values("merchant_id").reset_index(drop=True)

    # Hard assertions
    assert len(df) == 300,                      f"Expected 300 merchants, got {len(df)}"
    micro_max = df[df["business_size"] == "micro"]["annual_transactions"].max()
    assert micro_max <= 900,                    f"Micro merchant exceeds 900 txns: {micro_max}"
    mkt_min = df[df["merchant_archetype"] == "marketplace_retailer"]["annual_transactions"].min()
    assert mkt_min >= 40_000,                   f"Marketplace below 40k txns: {mkt_min}"
    for a in ["subscription_edtech", "saas_tools", "fitness_membership"]:
        assert (df[df["merchant_archetype"] == a]["subscription_supported"] == 1).all(), \
            f"subscription_supported != 1 for {a}"

    print(f"  {len(df)} merchants | sizes: {df['business_size'].value_counts().to_dict()}")
    print(f"  Archetypes: {df['merchant_archetype'].value_counts().to_dict()}")
    return df


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 2 — CUSTOMERS
# ═══════════════════════════════════════════════════════════════════════════════

def generate_customers(merchants_df: pd.DataFrame) -> pd.DataFrame:
    print("\nSTEP 2: Generating merchant-scoped customers ...")
    rows = []
    for m in merchants_df.itertuples():
        mid  = m.merchant_id
        ann  = int(m.annual_transactions)
        # 65 % of transactions are named customers; each customer buys 2-5 ×
        rng  = np.random.default_rng(SEED + abs(hash(mid)) % 999_983)
        rpt  = float(rng.uniform(2.0, 5.0))
        n_cu = max(5, int(ann * 0.65 / 2 / rpt))  # half-year data
        for i in range(n_cu):
            reg_days = int(rng.integers(30, 730))
            reg_date = (START_DATE - timedelta(days=reg_days)).strftime("%Y-%m-%d")
            rows.append({
                "customer_id":      f"CUST_{mid}_{i+1:04d}",
                "merchant_id":      mid,
                "customer_name":    gen_customer_name(rng),
                "registration_date": reg_date,
            })

    df = pd.DataFrame(rows)
    print(f"  {len(df):,} customers across 300 merchants.")
    return df


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 3 — TRANSACTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def generate_transactions(merchants_df: pd.DataFrame,
                          customers_df: pd.DataFrame) -> pd.DataFrame:
    print("\nSTEP 3: Generating transactions (targeting ~2 M rows) ...")

    cust_map = (customers_df.groupby("merchant_id")["customer_id"]
                .apply(list).to_dict())

    chunks = []
    txn_ctr = 1

    for m in merchants_df.itertuples():
        mid   = m.merchant_id
        arch  = m.merchant_archetype
        fulfil= m.fulfillment_type
        mat   = float(m.documentation_maturity)
        sub   = int(m.subscription_supported)
        ann   = int(m.annual_transactions)
        # Generate half a year's worth
        n_txn = max(1, ann // 2)

        rng = np.random.default_rng(SEED + abs(hash(mid)) % 999_983)

        # Amounts
        if sub:
            pp   = json.loads(m.price_points)
            w    = tier_weights(len(pp), arch)
            amts = rng.choice(pp, size=n_txn, p=w).astype(int)
        else:
            cat  = gen_retail_catalog(arch, abs(hash(mid)) % 999_983 + SEED)
            amts = rng.choice(cat, size=n_txn, replace=True).astype(int)

        # Timestamps: sorted uniform across period
        offsets  = np.sort(rng.integers(0, PERIOD_SECONDS, n_txn))
        ts_strs  = [(START_DATE + timedelta(seconds=int(o))).strftime("%Y-%m-%d %H:%M:%S")
                    for o in offsets]

        # Payment methods: 70 % card (60/40 credit/debit), 30 % UPI
        pm_arr = rng.choice(
            ["credit_card", "debit_card", "upi"],
            size=n_txn,
            p=[0.42, 0.28, 0.30],
        )
        # Card network (only meaningful for non-UPI)
        net_arr = rng.choice(
            ["Visa", "Mastercard", "RuPay", ""],
            size=n_txn,
            p=[0.35, 0.2310, 0.119, 0.30],   # scaled so card rows ≈ 50/33/17
        )
        # Force UPI rows to have empty network
        net_arr[pm_arr == "upi"] = ""

        # OTP/3DS: 88 % of card txns authenticated
        otp_arr = np.zeros(n_txn, dtype=int)
        card_mask = pm_arr != "upi"
        otp_arr[card_mask] = (rng.random(card_mask.sum()) < 0.88).astype(int)

        # Customer IDs (35 % anonymous)
        custs_this = cust_map.get(mid, [])
        if custs_this:
            sampled_c = rng.choice(custs_this, size=n_txn, replace=True)
        else:
            sampled_c = np.full(n_txn, "", dtype=object)
        anon_mask = rng.random(n_txn) < 0.35
        cust_arr  = np.where(anon_mask, "", sampled_c)

        chunk = pd.DataFrame({
            "transaction_id":    [f"TXN{txn_ctr + i:08d}" for i in range(n_txn)],
            "merchant_id":       mid,
            "customer_id":       cust_arr,
            "timestamp":         ts_strs,
            "amount":            amts,
            "payment_method":    pm_arr,
            "card_network":      net_arr,
            "otp_3ds_passed":    otp_arr,
            "merchant_archetype":arch,
            "fulfillment_type":  fulfil,
        })
        chunks.append(chunk)
        txn_ctr += n_txn

    print("  Concatenating chunks …")
    txns = pd.concat(chunks, ignore_index=True)

    print("  Computing point-in-time customer features …")
    txns["_ts"] = pd.to_datetime(txns["timestamp"])
    txns = txns.sort_values(["customer_id", "_ts"]).reset_index(drop=True)

    txns["customer_previous_orders"] = txns.groupby("customer_id").cumcount()
    txns["customer_previous_spend"]  = (
        txns.groupby("customer_id")["amount"].cumsum() - txns["amount"]
    ).astype(int)

    anon = txns["customer_id"] == ""
    txns.loc[anon, "customer_previous_orders"] = 0
    txns.loc[anon, "customer_previous_spend"]  = 0

    txns = txns.sort_values("timestamp").reset_index(drop=True)
    txns.drop(columns=["_ts"], inplace=True)

    # Assertions
    assert (txns["amount"] % 1 == 0).all(), "Non-integer amounts found in transactions!"
    upi_pct = (txns["payment_method"] == "upi").mean() * 100
    print(f"  {len(txns):,} transactions | UPI: {upi_pct:.1f}%  Card: {100 - upi_pct:.1f}%")
    return txns


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 4 — DISPUTES (initial, outcomes TBD)
# ═══════════════════════════════════════════════════════════════════════════════

def generate_disputes_initial(transactions_df: pd.DataFrame,
                               merchants_df: pd.DataFrame) -> pd.DataFrame:
    print("\nSTEP 4: Sampling disputes …")

    card_txns = transactions_df[
        transactions_df["payment_method"].isin(["credit_card", "debit_card"])
    ].copy()
    card_txns["_ts"] = pd.to_datetime(card_txns["timestamp"])

    merch_idx = merchants_df.set_index("merchant_id")
    chunks    = []
    disp_ctr  = 1

    for m in merchants_df.itertuples():
        mid   = m.merchant_id
        arch  = m.merchant_archetype
        size  = m.business_size
        sub   = int(m.subscription_supported)
        mat   = float(m.documentation_maturity)
        fulfil= m.fulfillment_type

        m_card = card_txns[card_txns["merchant_id"] == mid]
        if m_card.empty:
            continue

        rng = np.random.default_rng(SEED + abs(hash(mid)) % 999_983 + 1)

        rate_lo, rate_hi = SIZE_DISPUTE_RATE[size]
        base_rate = float(rng.uniform(rate_lo, rate_hi))
        if sub:
            base_rate *= 1.4
        base_rate = min(base_rate, 0.015)

        n_disp = max(0, int(len(m_card) * base_rate))
        if n_disp == 0:
            continue
        n_disp = min(n_disp, len(m_card))

        sampled = m_card.sample(n=n_disp, random_state=int(SEED + abs(hash(mid)) % 99991))
        sampled = sampled.reset_index(drop=True)

        pairs  = REASON_WEIGHTS[arch]
        codes  = [p[0] for p in pairs]
        wts    = np.array([p[1] for p in pairs], dtype=float); wts /= wts.sum()
        reason_codes = rng.choice(codes, size=n_disp, p=wts)

        networks  = rng.choice(["Visa", "Mastercard", "RuPay"], size=n_disp,
                                p=[0.50, 0.33, 0.17])
        delay_d   = rng.integers(3, 121, size=n_disp).astype(int)
        delay_h   = rng.integers(0, 24,  size=n_disp).astype(int)
        resp_d    = rng.integers(10, 22,  size=n_disp).astype(int)

        p_contest = float(np.clip(0.50 + 0.25 * mat, 0.60, 0.70))
        contested = rng.random(n_disp) < p_contest

        fees    = np.zeros(n_disp, dtype=int)
        op_cost = np.zeros(n_disp, dtype=int)
        for i, (is_c, net) in enumerate(zip(contested, networks)):
            if is_c:
                if net == "Visa":        fees[i] = int(rng.integers(600, 751))
                elif net == "Mastercard":fees[i] = int(rng.integers(500, 651))
                else:                    fees[i] = int(rng.integers(400, 501))
                op_cost[i] = int(rng.integers(150, 301))

        disp_dts   = []
        resp_dts   = []
        tx_ts_strs = []
        for i in range(n_disp):
            tx_dt   = sampled.at[i, "_ts"]
            d_dt    = tx_dt + timedelta(days=int(delay_d[i]), hours=int(delay_h[i]))
            r_dt    = d_dt  + timedelta(days=int(resp_d[i]))
            disp_dts.append(d_dt)
            resp_dts.append(r_dt)
            tx_ts_strs.append(tx_dt.strftime("%Y-%m-%d %H:%M:%S"))

        disp_ids = [f"DSP{disp_ctr + i:06d}" for i in range(n_disp)]
        disp_ctr += n_disp

        chunk = pd.DataFrame({
            "dispute_id":               disp_ids,
            "transaction_id":           sampled["transaction_id"].values,
            "merchant_id":              mid,
            "customer_id":              sampled["customer_id"].values,
            "network":                  networks,
            "reason_code":              reason_codes,
            "reason_description":       [REASON_DESCRIPTIONS[rc] for rc in reason_codes],
            "dispute_created_at":       [d.strftime("%Y-%m-%d %H:%M:%S") for d in disp_dts],
            "dispute_amount":           sampled["amount"].astype(int).values,
            "contest_fee":              fees,
            "operational_review_cost":  op_cost,
            "respond_by":               [r.strftime("%Y-%m-%d %H:%M:%S") for r in resp_dts],
            "days_to_deadline":         [(r - d).days for r, d in zip(resp_dts, disp_dts)],
            "merchant_action":          ["contested" if c else "accepted" for c in contested],
            "dispute_outcome":          ["TBD" if c else "accepted_refunded" for c in contested],
            "resolution_date":          ["TBD" if c else "" for c in contested],
            # ── internal fields (dropped before saving) ───────────────────────
            "_mat":         mat,
            "_fulfillment": fulfil,
            "_archetype":   arch,
            "_otp_passed":  sampled["otp_3ds_passed"].values,
            "_tx_ts":       tx_ts_strs,
            "_customer_previous_disputes": 0,   # filled in step 6
        })
        chunks.append(chunk)

    if not chunks:
        raise RuntimeError("No disputes generated — check dispute rates.")

    df = pd.concat(chunks, ignore_index=True)
    # Re-number IDs sequentially after concat
    df["dispute_id"] = [f"DSP{i+1:06d}" for i in range(len(df))]
    print(f"  {len(df):,} disputes | contested: {(df['merchant_action']=='contested').sum():,} "
          f"({(df['merchant_action']=='contested').mean()*100:.1f}%)")
    return df


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 5 — EVIDENCE
# ═══════════════════════════════════════════════════════════════════════════════

def generate_evidence(disputes_df: pd.DataFrame) -> pd.DataFrame:
    print("\nSTEP 5: Generating evidence (6 rows per dispute) …")

    n_disp = len(disputes_df)
    n_ev   = n_disp * 6

    # Pre-allocate output arrays
    ev_ids   = [None] * n_ev
    disp_ids = [None] * n_ev
    tx_ids   = [None] * n_ev
    ev_types = [None] * n_ev
    app_stat = [None] * n_ev
    avail_a  = np.zeros(n_ev, dtype=np.int8)
    req_a    = np.zeros(n_ev, dtype=np.int8)
    q_a      = np.zeros(n_ev, dtype=float)
    ev_ts    = [None] * n_ev
    src_sys  = [None] * n_ev

    # Pre-draw randoms for all evidence rows
    rng_all       = np.random.default_rng(SEED + 7)
    r_mat_jitter  = rng_all.uniform(-0.12, 0.12, n_ev)
    r_avail       = rng_all.random(n_ev)
    r_qual_base   = rng_all.uniform(0.55, 0.98, n_ev)
    r_ev_frac     = rng_all.random(n_ev)

    ei = 0
    for i, row in disputes_df.iterrows():
        disp_id = row["dispute_id"]
        tx_id   = row["transaction_id"]
        rc      = row["reason_code"]
        fulfil  = row["_fulfillment"]
        mat     = float(row["_mat"])
        disp_dt = datetime.strptime(row["dispute_created_at"], "%Y-%m-%d %H:%M:%S")
        tx_dt   = datetime.strptime(row["_tx_ts"], "%Y-%m-%d %H:%M:%S")

        slots   = EVIDENCE_SLOTS[fulfil]
        req_pat = REQUIRED_MATRIX[(rc, fulfil)]
        window  = max(3600, int((disp_dt - tx_dt).total_seconds()))

        for slot_idx in range(6):
            ev_type = slots[slot_idx]
            is_req  = req_pat[slot_idx]
            p_av    = float(np.clip(mat + r_mat_jitter[ei] + 0.02, 0.05, 0.98))

            if r_avail[ei] < p_av:
                avail  = 1
                q_sc   = round(float(np.clip(r_qual_base[ei] * (0.75 + 0.25 * mat), 0.55, 0.98)), 2)
                app    = "APPLICABLE"
            else:
                avail  = 0
                q_sc   = 0.0
                app    = "UNAVAILABLE"

            ev_offset = int(r_ev_frac[ei] * window)
            ev_time   = (tx_dt + timedelta(seconds=ev_offset)).strftime("%Y-%m-%d %H:%M:%S")

            ev_ids[ei]   = f"EVID{ei+1:07d}"
            disp_ids[ei] = disp_id
            tx_ids[ei]   = tx_id
            ev_types[ei] = ev_type
            app_stat[ei] = app
            avail_a[ei]  = avail
            req_a[ei]    = is_req
            q_a[ei]      = q_sc
            ev_ts[ei]    = ev_time
            src_sys[ei]  = EVIDENCE_SOURCE[ev_type]
            ei += 1

    df = pd.DataFrame({
        "evidence_id":          ev_ids,
        "dispute_id":           disp_ids,
        "transaction_id":       tx_ids,
        "evidence_type":        ev_types,
        "applicability_status": app_stat,
        "available":            avail_a,
        "required":             req_a,
        "quality_score":        q_a,
        "evidence_timestamp":   ev_ts,
        "source_system":        src_sys,
    })
    assert len(df) == n_ev, f"Expected {n_ev} evidence rows, got {len(df)}"
    print(f"  {len(df):,} evidence rows.")
    return df


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 6 — OUTCOMES (V5.1 §1.2 outcome model)
# ═══════════════════════════════════════════════════════════════════════════════

def compute_outcomes(disputes_df: pd.DataFrame,
                     evidence_df:  pd.DataFrame) -> pd.DataFrame:
    print("\nSTEP 6: Computing outcomes (V5.1 logit model) …")

    # ── Pre-compute decisive evidence flags ──────────────────────────────────
    # For each dispute: build a dict evidence_type → (available, quality_score)
    ev_lookup = (evidence_df
                 .groupby(["dispute_id", "evidence_type"])
                 .agg(available=("available", "first"),
                      quality_score=("quality_score", "first"))
                 .reset_index())
    ev_map = {}
    for row in ev_lookup.itertuples(index=False):
        ev_map.setdefault(row.dispute_id, {})[row.evidence_type] = (
            row.available, row.quality_score
        )

    # Per-dispute: required count, present count, missing count
    req_ev = evidence_df[evidence_df["required"] == 1]
    req_counts  = req_ev.groupby("dispute_id")["required"].count()
    pres_counts = req_ev[req_ev["available"] == 1].groupby("dispute_id")["available"].count()
    miss_counts = req_ev[req_ev["available"] == 0].groupby("dispute_id")["available"].count()

    # Average quality of present required docs
    avg_req_q = (req_ev[req_ev["available"] == 1]
                 .groupby("dispute_id")["quality_score"].mean())

    # Customer prior disputes (count disputes filed before this one per customer)
    disp_sorted = disputes_df.sort_values("dispute_created_at").copy()
    named_mask  = disp_sorted["customer_id"] != ""
    cpd_series  = (disp_sorted[named_mask]
                   .groupby("customer_id").cumcount())
    disp_sorted["_cpd"] = 0
    disp_sorted.loc[cpd_series.index, "_cpd"] = cpd_series
    disputes_df = disp_sorted.sort_values("dispute_id").reset_index(drop=True)

    contested_mask = disputes_df["merchant_action"] == "contested"
    contested      = disputes_df[contested_mask].copy()

    if contested.empty:
        print("  WARNING: no contested disputes found.")
        return disputes_df

    # Join aggregated evidence stats via merge (avoids index-alignment pitfalls)
    ev_stats = pd.DataFrame({
        "dispute_id": req_counts.index,
        "req_count":  req_counts.values,
    }).merge(
        pres_counts.rename("pres_count").reset_index(), on="dispute_id", how="outer"
    ).merge(
        miss_counts.rename("miss_count").reset_index(), on="dispute_id", how="outer"
    ).merge(
        avg_req_q.rename("avg_req_q").reset_index(), on="dispute_id", how="outer"
    ).fillna({"req_count": 0, "pres_count": 0, "miss_count": 0, "avg_req_q": 0.7})
    ev_stats[["req_count","pres_count","miss_count"]] = \
        ev_stats[["req_count","pres_count","miss_count"]].astype(int)

    contested = contested.merge(ev_stats, on="dispute_id", how="left")
    contested["req_count"]  = contested["req_count"].fillna(0).astype(int)
    contested["pres_count"] = contested["pres_count"].fillna(0).astype(int)
    contested["miss_count"] = contested["miss_count"].fillna(0).astype(int)
    contested["avg_req_q"]  = contested["avg_req_q"].fillna(0.7)

    outcomes    = []
    res_dates   = []
    rng_out     = np.random.default_rng(SEED + 13)
    res_day_off = rng_out.integers(7, 46, len(contested))

    for i, (_, c) in enumerate(contested.iterrows()):
        rc      = c["reason_code"]
        fulfil  = c["_fulfillment"]
        mat     = float(c["_mat"])
        amt     = float(c["dispute_amount"])
        otp     = int(c["_otp_passed"])
        cpd     = int(c.get("_cpd", 0))
        pres    = int(c["pres_count"])
        miss    = int(c["miss_count"])
        avg_q   = float(c["avg_req_q"])
        disp_id = c["dispute_id"]

        # Base logit from target win rate
        logit = BASE_LOGIT[rc]

        # ── DECISIVE_TERM ────────────────────────────────────────────────────
        decisive_types = DECISIVE_EVIDENCE[rc]
        decisive_adj = 0.0
        
        if rc == "UNAUTHORIZED_TRANSACTION":
            if otp == 1: decisive_adj = 2.4
            else:        decisive_adj = -1.4
        elif decisive_types:
            adj_sum = 0.0
            for d_type in decisive_types:
                ev_info = ev_map.get(disp_id, {}).get(d_type)
                if ev_info is None or ev_info[0] == 0:
                    adj_sum += -2.1
                else:
                    q = ev_info[1]
                    adj_sum += 2.2 if q >= 0.80 else 1.3

            if rc == "MERCHANDISE_NOT_AS_DESCRIBED":
                adj_sum *= 0.5
            decisive_adj = adj_sum

        # ── COMPLETENESS_TERM ────────────────────────────────────────────────
        completeness_adj = 0.0
        decisive_set = set(decisive_types)
        
        slots = EVIDENCE_SLOTS[fulfil]
        req_pat = REQUIRED_MATRIX[(rc, fulfil)]
        for slot_idx in range(6):
            if req_pat[slot_idx] == 1:
                ev_type = slots[slot_idx]
                if ev_type not in decisive_set:
                    ev_info = ev_map.get(disp_id, {}).get(ev_type)
                    if ev_info and ev_info[0] == 1:
                        completeness_adj += 0.45
                    else:
                        completeness_adj += -0.75

        # ── QUALITY_TERM ─────────────────────────────────────────────────────
        quality_adj = 0.9 * (avg_q - 0.7)

        # ── AMOUNT_TERM ──────────────────────────────────────────────────────
        amount_adj = -0.32 * (math.log10(max(amt, 1)) - 3.4) if amt > 0 else 0.0

        # ── CUSTOMER_TERM ────────────────────────────────────────────────────
        customer_adj = -0.30 * min(cpd, 4)

        raw_sum = decisive_adj + completeness_adj + quality_adj + amount_adj + customer_adj
        contested.at[i, "_raw_adj"] = raw_sum
        
    target_wr = {
        "UNAUTHORIZED_TRANSACTION":     0.20,
        "MERCHANDISE_NOT_RECEIVED":     0.62,
        "SERVICE_NOT_RENDERED":         0.48,
        "MERCHANDISE_NOT_AS_DESCRIBED": 0.38,
        "RECURRING_BILLING_DISPUTE":    0.42,
        "CREDIT_NOT_PROCESSED":         0.45,
        "DUPLICATE_TRANSACTION":        0.70,
    }

    noise_vals = pd.Series(rng_out.normal(0, 0.85, len(contested)), index=contested.index)
    contested["_final_logit"] = 0.0
    
    for rc_val, grp in contested.groupby("reason_code"):
        idx = grp.index
        if rc_val == "UNAUTHORIZED_TRANSACTION":
            tgt = target_wr[rc_val] - 0.01
        else:
            tgt = target_wr[rc_val] + 0.02
        low, high = -10.0, 10.0
        best_c = BASE_LOGIT[rc_val]
        for _ in range(25):
            mid = (low + high) / 2.0
            p_mean = sigmoid(mid + contested.loc[idx, "_raw_adj"] + noise_vals.loc[idx]).mean()
            if p_mean > tgt:
                high = mid
            else:
                low = mid
            best_c = mid
        contested.loc[idx, "_final_logit"] = best_c + contested.loc[idx, "_raw_adj"] + noise_vals.loc[idx]
    
    # Compute final outcome
    for i, (idx, c) in enumerate(contested.iterrows()):
        logit = c["_final_logit"]

        win_prob = sigmoid(np.array([logit]))[0]
        won = bool(rng_out.random() < win_prob)
        outcomes.append("won" if won else "lost")

        d_dt  = datetime.strptime(c["dispute_created_at"], "%Y-%m-%d %H:%M:%S")
        r_dt  = d_dt + timedelta(days=int(res_day_off[i]))
        res_dates.append(r_dt.strftime("%Y-%m-%d %H:%M:%S"))

    contested["dispute_outcome"] = outcomes
    contested["resolution_date"] = res_dates

    # Merge outcomes back
    disputes_df = disputes_df.set_index("dispute_id")
    disputes_df.update(contested.set_index("dispute_id")[["dispute_outcome", "resolution_date"]])
    disputes_df = disputes_df.reset_index()

    won  = (disputes_df[contested_mask]["dispute_outcome"] == "won").sum()
    tot_c = contested_mask.sum()
    print(f"  Contested win rate: {won/tot_c*100:.1f}%  ({won}/{tot_c})")
    return disputes_df


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 7 — DEMO MERCHANTS CSV
# ═══════════════════════════════════════════════════════════════════════════════

def save_demo_merchants(merchants_df: pd.DataFrame) -> None:
    demo = merchants_df[merchants_df["is_demo"] == 1][[
        "merchant_id", "merchant_name", "merchant_archetype",
        "fulfillment_type", "subscription_supported", "business_size",
        "annual_transactions", "documentation_maturity",
        "price_points", "demo_priority", "business_description",
    ]].sort_values("demo_priority").reset_index(drop=True)
    demo.to_csv(DEMO_DIR / "demo_merchants.csv", index=False)
    print(f"\nSTEP 7: Saved demo_merchants.csv ({len(demo)} rows).")


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 8 — SEMANTIC AUDIT (§11 gates + V5.1 calibration)
# ═══════════════════════════════════════════════════════════════════════════════

def run_semantic_audit(merchants_df: pd.DataFrame,
                       transactions_df: pd.DataFrame,
                       disputes_df: pd.DataFrame,
                       evidence_df: pd.DataFrame) -> None:
    print("\n" + "=" * 65)
    print("STEP 8: SEMANTIC AUDIT — All V5 §11 gates must be zero")
    print("=" * 65)

    failures = 0

    def gate(n, label, count):
        nonlocal failures
        flag = "[PASS]" if count == 0 else "[FAIL]"
        print(f"  {flag} Gate {n:<4} {label:<55} {count}")
        if count != 0:
            failures += 1

    # Merge disputes with merchant info
    dm = disputes_df.merge(
        merchants_df[["merchant_id", "fulfillment_type",
                       "merchant_archetype", "subscription_supported"]],
        on="merchant_id", how="left",
    )

    # Gate 1 – MNR at non-physical merchants
    gate(1, "MNR at non-physical merchants",
         int(((dm["reason_code"] == "MERCHANDISE_NOT_RECEIVED") &
              (dm["fulfillment_type"] != "physical_delivery")).sum()))

    # Gate 2 – SNR at physical merchants
    gate(2, "SNR at physical merchants",
         int(((dm["reason_code"] == "SERVICE_NOT_RENDERED") &
              (dm["fulfillment_type"] == "physical_delivery")).sum()))

    # Gate 3 – RBD at non-subscription merchants
    gate(3, "RBD at non-subscription merchants",
         int(((dm["reason_code"] == "RECURRING_BILLING_DISPUTE") &
              (dm["subscription_supported"] == 0)).sum()))

    # Gate 4 – Permission matrix
    bad = ~dm.apply(
        lambda r: r["merchant_archetype"] in PERMISSION_MATRIX.get(r["reason_code"], set()),
        axis=1,
    )
    gate(4, "Forbidden reason_code for archetype", int(bad.sum()))

    # Gate 5 – Non-integer amounts in transactions
    gate(5, "Non-integer transaction amounts",
         int((transactions_df["amount"] % 1 != 0).sum()))

    # Gate 6 – Subscription amounts not in price_points
    sub_pp = {}
    for m in merchants_df[merchants_df["subscription_supported"] == 1].itertuples():
        pp = json.loads(m.price_points) if m.price_points else []
        sub_pp[m.merchant_id] = set(pp)
    sub_txns = transactions_df[transactions_df["merchant_id"].isin(sub_pp)].copy()
    bad6 = sub_txns.apply(
        lambda r: int(r["amount"]) not in sub_pp.get(r["merchant_id"], set()), axis=1
    ).sum()
    gate(6, "Subscription amount not in price_points", int(bad6))

    # Gate 7 – NOT_APPLICABLE evidence types in wrong fulfillment_type
    ev_dm = evidence_df.merge(
        dm[["dispute_id", "fulfillment_type"]].drop_duplicates(), on="dispute_id", how="left"
    )
    phys_only    = {"shipping_label", "tracking_number", "delivery_confirmation"}
    non_phys_only= {"access_log", "service_record", "cancellation_record"}
    bad7a = ((ev_dm["fulfillment_type"] != "physical_delivery") &
             ev_dm["evidence_type"].isin(phys_only)).sum()
    bad7b = ((ev_dm["fulfillment_type"] == "physical_delivery") &
             ev_dm["evidence_type"].isin(non_phys_only)).sum()
    gate(7, "NOT_APPLICABLE evidence rows", int(bad7a + bad7b))

    # Gate 8 – Merchant dispute rate > 1.5 %
    card_cnts   = transactions_df[transactions_df["payment_method"].isin(
                      ["credit_card", "debit_card"])].groupby("merchant_id").size()
    disp_cnts   = disputes_df.groupby("merchant_id").size()
    rates       = (disp_cnts / card_cnts).fillna(0)
    gate(8, "Merchant dispute rate > 1.5%", int((rates > 0.015).sum()))

    # Gate 9 – Micro > 900 annual transactions
    micro = merchants_df[merchants_df["business_size"] == "micro"]
    gate(9, "Micro merchant > 900 annual txns",
         int((micro["annual_transactions"] > 900).sum()))

    # Gate 10 – Marketplace < 40 k annual transactions
    mkt = merchants_df[merchants_df["merchant_archetype"] == "marketplace_retailer"]
    gate(10, "Marketplace retailer < 40k annual txns",
         int((mkt["annual_transactions"] < 40_000).sum()))

    # Gate 10b – fitness_membership subscription_supported != 1
    fit = merchants_df[merchants_df["merchant_archetype"] == "fitness_membership"]
    gate("10b", "Fitness merchants subscription_supported != 1",
         int((fit["subscription_supported"] != 1).sum()))

    # Gate 10c – Shipping evidence at membership/booking disputes
    non_phys_fulfil = {"membership_service", "booking_service"}
    bad10c = (ev_dm[ev_dm["fulfillment_type"].isin(non_phys_fulfil)]["evidence_type"]
              .isin(phys_only)).sum()
    gate("10c", "Shipping evidence at membership/booking disputes", int(bad10c))

    # Gate 11 – Disputes with wrong 6-slot set
    expected = {ft: frozenset(slots) for ft, slots in EVIDENCE_SLOTS.items()}
    slot_check = (ev_dm.groupby("dispute_id")
                  .agg(ev_set=("evidence_type", frozenset),
                       ft=("fulfillment_type", "first")))
    bad11 = slot_check.apply(
        lambda r: r["ev_set"] != expected.get(r["ft"], frozenset()), axis=1
    ).sum()
    gate(11, "Disputes with wrong evidence slot set", int(bad11))

    # Gate 12 – Multiple required patterns per (reason_code, fulfillment_type)
    ev_with_rc = evidence_df.merge(
        disputes_df[["dispute_id", "reason_code"]], on="dispute_id", how="left"
    ).merge(
        merchants_df[["merchant_id", "fulfillment_type"]]
        .merge(disputes_df[["dispute_id", "merchant_id"]].drop_duplicates(), on="merchant_id"),
        on="dispute_id", how="left"
    )
    pat_check = (
        ev_with_rc.sort_values(["dispute_id", "evidence_type"])
        .groupby(["dispute_id", "reason_code", "fulfillment_type"])["required"]
        .apply(tuple)
        .reset_index()
        .groupby(["reason_code", "fulfillment_type"])["required"]
        .nunique()
    )
    gate(12, "(reason_code, fulfillment_type) with > 1 required pattern",
         int((pat_check > 1).sum()))

    # -- V5.1 calibration ----------------------------------------------------
    print("\n  -- V5.1 Calibration targets --")
    contested = disputes_df[disputes_df["merchant_action"] == "contested"].copy()
    
    # We map decisive_any directly using ev_map logic or by iterating
    decisive_any_dict = {}
    ev_map_audit = (evidence_df.groupby(["dispute_id", "evidence_type"])["available"].first().to_dict())
    
    for row in contested.itertuples():
        d_id = row.dispute_id
        rc_val = row.reason_code
        otp_val = getattr(row, "_otp_passed", 0)
        
        if rc_val == "UNAUTHORIZED_TRANSACTION":
            decisive_any_dict[d_id] = (otp_val == 1)
        else:
            d_types = DECISIVE_EVIDENCE.get(rc_val, [])
            if not d_types:
                decisive_any_dict[d_id] = False
            else:
                decisive_any_dict[d_id] = all(ev_map_audit.get((d_id, dt), 0) == 1 for dt in d_types)
                
    contested["decisive_any"] = contested["dispute_id"].map(decisive_any_dict)

    wins = contested["dispute_outcome"] == "won"

    overall_wr = wins.mean() * 100
    flag_wr = "[PASS]" if 45 <= overall_wr <= 52 else "[FAIL]"
    print(f"  {flag_wr} Overall win rate (contested):         {overall_wr:.1f}%   [target 45-52%]")
    if not (45 <= overall_wr <= 52):
        failures += 1

    dec_pres  = contested["decisive_any"] == True
    dec_miss  = contested["decisive_any"] == False

    if dec_pres.sum() > 0:
        wr_pres = wins[dec_pres].mean() * 100
        flag_p  = "[PASS]" if 72 <= wr_pres <= 86 else "[FAIL]"
        print(f"  {flag_p} Win rate decisive evidence PRESENT:   {wr_pres:.1f}%   [target 72-86%]")
        if not (72 <= wr_pres <= 86):
            failures += 1
    if dec_miss.sum() > 0:
        wr_miss = wins[dec_miss].mean() * 100
        flag_m  = "[PASS]" if 12 <= wr_miss <= 25 else "[FAIL]"
        print(f"  {flag_m} Win rate decisive evidence MISSING:    {wr_miss:.1f}%   [target 12-25%]")
        if not (12 <= wr_miss <= 25):
            failures += 1

    gap = (wr_pres if dec_pres.sum() else 0) - (wr_miss if dec_miss.sum() else 0)
    flag_g = "[PASS]" if 45 <= gap <= 75 else "[FAIL]"
    print(f"  {flag_g} Present-vs-missing gap:                {gap:.1f}pp  [target 45-75 pp]")

    contest_rate = (disputes_df["merchant_action"] == "contested").mean() * 100
    flag_cr = "[PASS]" if 60 <= contest_rate <= 70 else "[FAIL]"
    print(f"  {flag_cr} Contest rate:                           {contest_rate:.1f}%   [target 60-70%]")

    # Evidence completeness distribution
    req_ev   = evidence_df[evidence_df["required"] == 1]
    req_cnt  = req_ev.groupby("dispute_id")["required"].count()
    pres_cnt = req_ev[req_ev["available"] == 1].groupby("dispute_id")["available"].count()
    miss_cnt = (req_cnt - pres_cnt.reindex(req_cnt.index, fill_value=0)).clip(lower=0)
    all_disp_ids = disputes_df["dispute_id"]
    miss_cnt = miss_cnt.reindex(all_disp_ids, fill_value=0)
    all_pct    = (miss_cnt == 0).mean() * 100
    one_pct    = (miss_cnt == 1).mean() * 100
    two_pct    = (miss_cnt >= 2).mean() * 100
    flag_comp  = "[PASS]" if 38 <= all_pct <= 45 else "[FAIL]"
    print(f"\n  Evidence completeness:")
    print(f"  {flag_comp} All required present: {all_pct:.1f}%   [target 38-45%]")
    print(f"       Exactly one missing: {one_pct:.1f}%   [target 30-36%]")
    print(f"       Two or more missing: {two_pct:.1f}%   [target 22-28%]")

    # Win rates by reason code
    print(f"\n  Win rates by reason code (target ± 0.06 of base):")
    target_wr = {
        "UNAUTHORIZED_TRANSACTION":     0.20,
        "MERCHANDISE_NOT_RECEIVED":     0.62,
        "SERVICE_NOT_RENDERED":         0.48,
        "MERCHANDISE_NOT_AS_DESCRIBED": 0.38,
        "RECURRING_BILLING_DISPUTE":    0.42,
        "CREDIT_NOT_PROCESSED":         0.45,
        "DUPLICATE_TRANSACTION":        0.70,
    }
    for rc, tgt in target_wr.items():
        sub = contested[contested["reason_code"] == rc]
        if sub.empty:
            continue
        wr  = (sub["dispute_outcome"] == "won").mean()
        ok  = abs(wr - tgt) <= 0.06
        flag= "[PASS]" if ok else "[FAIL]"
        print(f"    {flag} {rc:<40} {wr:.3f}  (target {tgt:.2f})")

    print("=" * 65)
    if failures > 0:
        print(f"[FAIL] AUDIT FAILED - {failures} gate(s) violated.\n")
        sys.exit(1)
    else:
        print("[PASS] All semantic gates PASSED.\n")





# ═══════════════════════════════════════════════════════════════════════════════
# STEP 8b — HUMAN-READABLE REPORT
# ═══════════════════════════════════════════════════════════════════════════════

def print_human_report(merchants_df: pd.DataFrame,
                       transactions_df: pd.DataFrame,
                       disputes_df: pd.DataFrame,
                       evidence_df: pd.DataFrame) -> None:
    print("\n" + "=" * 65)
    print("HUMAN-READABLE REPORT - Read every line as a person would")
    print("=" * 65)

    demo_ids = [d["merchant_id"] for d in DEMO_MERCHANT_DEFS]
    merch_d  = merchants_df.set_index("merchant_id").to_dict("index")

    card_cnts = transactions_df[
        transactions_df["payment_method"].isin(["credit_card", "debit_card"])
    ].groupby("merchant_id").size()

    for mid in demo_ids:
        m   = merch_d.get(mid, {})
        m_disputes = disputes_df[disputes_df["merchant_id"] == mid]
        n_disp     = len(m_disputes)
        n_card     = card_cnts.get(mid, 1)
        dr         = n_disp / max(n_card, 1) * 100

        print(f"\n{'-'*55}")
        print(f"  {m.get('merchant_name', mid)}")
        print(f"  {m.get('merchant_archetype')} | {m.get('business_size')} | "
              f"annual: {m.get('annual_transactions'):,}")
        print(f"  Disputes: {n_disp}  |  Rate: {dr:.2f}%  |  "
              f"Maturity: {m.get('documentation_maturity')}")
        if m.get("price_points"):
            print(f"  Price points: {m.get('price_points')}")
        else:
            # Show amount range from transactions
            m_txns = transactions_df[transactions_df["merchant_id"] == mid]
            if not m_txns.empty:
                print(f"  Amount range: Rs{m_txns['amount'].min():,} - Rs{m_txns['amount'].max():,}")

        if m_disputes.empty:
            print("  (no disputes)")
            continue

        # Reason-code mix
        rc_mix = m_disputes["reason_code"].value_counts(normalize=True) * 100
        print(f"  Reason-code mix:")
        for rc, pct in rc_mix.items():
            print(f"    {rc:<42} {pct:5.1f}%")

        # One fully rendered dispute
        sample_disp = m_disputes.sample(1, random_state=SEED).iloc[0]
        _render_dispute(sample_disp, evidence_df, m.get("fulfillment_type", ""), label="  Example dispute")

    # 20 random disputes across the portfolio
    print(f"\n{'='*65}")
    print("RANDOM SAMPLE - 20 disputes across the portfolio")
    print("=" * 65)
    all_c = disputes_df[disputes_df["merchant_action"] == "contested"]
    sample20 = all_c.sample(min(20, len(all_c)), random_state=SEED + 1)
    for _, d in sample20.iterrows():
        mid  = d["merchant_id"]
        m    = merch_d.get(mid, {})
        fulfil = FULFILLMENT_MAP.get(m.get("merchant_archetype", ""), "")
        _render_dispute(d, evidence_df, fulfil, label=f"  [{m.get('merchant_archetype','?')}] {m.get('merchant_name','?')}")


def _render_dispute(d, evidence_df, fulfil, label="  Dispute"):
    print(f"\n{label}")
    print(f"    ID: {d['dispute_id']} | RC: {d['reason_code']} | "
          f"Amount: Rs{d['dispute_amount']:,} | Outcome: {d['dispute_outcome']}")
    evs = evidence_df[evidence_df["dispute_id"] == d["dispute_id"]].sort_values("evidence_type")
    for _, e in evs.iterrows():
        req_flag  = "REQ" if e["required"] == 1 else "opt"
        avail_str = f"avail(q={e['quality_score']:.2f})" if e["available"] == 1 else "MISSING"
        print(f"    [{req_flag}] {e['evidence_type']:<30} {avail_str:<26} [{e['applicability_status']}]")


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 8c — BASELINE ML MODEL CHECK (V5.1 §3)
# ═══════════════════════════════════════════════════════════════════════════════

def run_baseline_model(merchants_df: pd.DataFrame,
                       disputes_df: pd.DataFrame,
                       evidence_df: pd.DataFrame) -> None:
    print("\n" + "=" * 65)
    print("STEP 8c: Baseline ML model check (V5.1 §3)")
    print("=" * 65)

    try:
        from sklearn.ensemble import GradientBoostingClassifier
        from sklearn.preprocessing import LabelEncoder
        from sklearn.model_selection import train_test_split
        from sklearn.metrics import (roc_auc_score, average_precision_score,
                                     precision_score, recall_score)
    except ImportError:
        print("  sklearn not available — skipping ML gate.")
        return

    contested = disputes_df[disputes_df["merchant_action"] == "contested"].copy()
    if len(contested) < 50:
        print("  Too few contested disputes for baseline — skipping.")
        return

    # Evidence aggregates per dispute
    req_ev   = evidence_df[evidence_df["required"] == 1]
    ev_agg   = (req_ev.groupby("dispute_id")
                .agg(req_count=("required","count"),
                     pres_count=("available","sum"),
                     mean_q=("quality_score","mean"))
                .reset_index())
    ev_agg["miss_count"] = ev_agg["req_count"] - ev_agg["pres_count"]

    # Decisive-present flag
    ev_map_bm = (evidence_df.groupby(["dispute_id", "evidence_type"])["available"].first().to_dict())
    dec_dict = {}
    for row in contested.itertuples():
        d_id = row.dispute_id
        rc_val = row.reason_code
        otp_val = getattr(row, "_otp_passed", 0)
        if rc_val == "UNAUTHORIZED_TRANSACTION":
            dec_dict[d_id] = int(otp_val == 1)
        else:
            d_types = DECISIVE_EVIDENCE.get(rc_val, [])
            if not d_types:
                dec_dict[d_id] = 0
            else:
                dec_dict[d_id] = int(all(ev_map_bm.get((d_id, dt), 0) == 1 for dt in d_types))
    dec_flag = pd.DataFrame({"dispute_id": list(dec_dict.keys()), "decisive_present": list(dec_dict.values())})

    # Merge dispute with merchant info and evidence
    merch_cols = merchants_df[["merchant_id","merchant_archetype","fulfillment_type",
                                "documentation_maturity"]].copy()
    df = contested.merge(merch_cols, on="merchant_id", how="left")
    df = df.merge(ev_agg,  on="dispute_id", how="left")
    df = df.merge(dec_flag, on="dispute_id", how="left")

    for col in ["req_count","pres_count","miss_count","mean_q","decisive_present"]:
        df[col] = df[col].fillna(0)

    # Categorical features
    cat_cols = ["reason_code","network","merchant_archetype","fulfillment_type"]
    for col in cat_cols:
        le = LabelEncoder()
        df[col + "_enc"] = le.fit_transform(df[col].astype(str))

    # Authentication from disputes internal column (fallback 0)
    df["otp"] = df["_otp_passed"].fillna(0).astype(int) if "_otp_passed" in df.columns else 0

    feat_cols = (
        [c + "_enc" for c in cat_cols]
        + ["dispute_amount","contest_fee","days_to_deadline",
           "documentation_maturity","req_count","pres_count",
           "miss_count","mean_q","decisive_present","otp"]
    )
    feat_cols = [c for c in feat_cols if c in df.columns]

    X = df[feat_cols].fillna(0)
    y = (df["dispute_outcome"] == "won").astype(int)

    if len(X) < 20 or y.nunique() < 2:
        print("  Insufficient data for baseline — skipping.")
        return

    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=0.20, stratify=y, random_state=SEED
    )

    clf = GradientBoostingClassifier(n_estimators=200, max_depth=4,
                                     learning_rate=0.05, random_state=SEED)
    clf.fit(X_tr, y_tr)
    proba = clf.predict_proba(X_te)[:, 1]
    pred  = (proba >= 0.5).astype(int)

    roc  = roc_auc_score(y_te, proba)
    pr   = average_precision_score(y_te, proba)
    prec = precision_score(y_te, pred, zero_division=0)
    rec  = recall_score(y_te, pred, zero_division=0)

    print(f"  ROC-AUC:                 {roc:.3f}   [target 0.80-0.87]")
    print(f"  PR-AUC:                  {pr:.3f}   [target 0.75-0.88]")
    print(f"  Precision @ 0.5:         {prec:.3f}  [target 0.70-0.82]")
    print(f"  Recall    @ 0.5:         {rec:.3f}  [target 0.65-0.85]")

    if roc > 0.92:
        print("  [FAIL] ROC-AUC > 0.92 - POSSIBLE LEAKAGE. Inspect features.")
    elif roc < 0.76:
        print("  [FAIL] ROC-AUC < 0.76 - signal too weak.")
    else:
        print("  [PASS] ROC-AUC in target range.")

    # Per-feature PR-AUC scan for leakage
    print("\n  Single-feature PR-AUC (leakage check):")
    for col in feat_cols:
        try:
            sc = average_precision_score(y_te, X_te[col])
            if sc > 0.85:
                print(f"    [FAIL] {col:<35} PR-AUC={sc:.3f}  <-- LEAKAGE CANDIDATE")
            elif sc > 0.70:
                print(f"    [WARN] {col:<35} PR-AUC={sc:.3f}")
        except Exception:
            pass

    # Column correlations with dispute_outcome
    print("\n  Column correlations with dispute_outcome (|r| must be < 0.5):")
    out_enc = y_te.reset_index(drop=True)
    for col in feat_cols:
        try:
            r = np.corrcoef(X_te[col].values, out_enc.values)[0, 1]
            flag = "[FAIL]" if abs(r) > 0.5 else ""
            if abs(r) > 0.20 or flag:
                print(f"    {flag} {col:<35} r={r:.3f}")
        except Exception:
            pass

    print("=" * 65)


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 9 — DOCUMENTATION
# ═══════════════════════════════════════════════════════════════════════════════

def generate_documentation(merchants_df, transactions_df, disputes_df, evidence_df):
    print("\nSTEP 9: Generating documentation …")
    n_merch  = len(merchants_df)
    n_txn    = len(transactions_df)
    n_disp   = len(disputes_df)
    n_ev     = len(evidence_df)
    n_cust   = len(pd.read_csv(CORE_DIR / "customers.csv"))
    card_txns= transactions_df[transactions_df["payment_method"].isin(["credit_card","debit_card"])]
    disp_rate= len(disputes_df) / max(len(card_txns), 1)

    contested    = disputes_df[disputes_df["merchant_action"] == "contested"]
    win_rate     = (contested["dispute_outcome"] == "won").mean() if len(contested) else 0
    contest_rate = (disputes_df["merchant_action"] == "contested").mean()

    # ── DATASET_MANIFEST.md ─────────────────────────────────────────────────
    manifest = f"""# SaHaYa Dataset Manifest
*Generated by generate_dataset_v5.py - DATASET_REGENERATION_V5.md + V5_1_PRECISION overlay*

## Files

| File | Rows | Notes |
|---|---|---|
| `data/core/merchants.csv` | {n_merch:,} | 300 merchants, 7 archetypes |
| `data/core/customers.csv` | {n_cust:,} | Merchant-scoped, not cross-merchant |
| `data/core/transactions.csv.gz` | {n_txn:,} | GZIP; ~70% card, ~30% UPI |
| `data/core/disputes.csv` | {n_disp:,} | Card disputes only |
| `data/core/evidence.csv` | {n_ev:,} | Exactly 6 rows per dispute |
| `data/demo/demo_merchants.csv` | 7 | One per archetype |

## Archetypes

| # | archetype | fulfillment_type | subscription |
|---|---|---|---|
| 1 | `d2c_brand` | `physical_delivery` | no |
| 2 | `social_seller` | `physical_delivery` | no |
| 3 | `marketplace_retailer` | `physical_delivery` | no |
| 4 | `subscription_edtech` | `digital_service` | **yes** |
| 5 | `saas_tools` | `digital_service` | **yes** |
| 6 | `fitness_membership` | `membership_service` | **yes** |
| 7 | `travel_booking` | `booking_service` | no |

## §4.1 Reason-Code Permission Matrix

| reason_code | d2c | social | marketplace | edtech | saas | fitness | travel |
|---|---|---|---|---|---|---|---|
| `MERCHANDISE_NOT_RECEIVED` | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| `SERVICE_NOT_RENDERED` | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ |
| `MERCHANDISE_NOT_AS_DESCRIBED` | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ |
| `RECURRING_BILLING_DISPUTE` | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ | ❌ |
| `CREDIT_NOT_PROCESSED` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `DUPLICATE_TRANSACTION` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `UNAUTHORIZED_TRANSACTION` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

## Benchmark Calibration

| Metric | Achieved |
|---|---|
| Portfolio card dispute rate | {disp_rate*100:.2f}% |
| Contest rate | {contest_rate*100:.1f}% |
| Overall win rate (contested) | {win_rate*100:.1f}% |
| Total disputes | {n_disp:,} |

## Known Limitations

- Synthetic data calibrated to global card-network benchmarks; no India-specific chargeback statistics are published.
- Outcomes are modelled (latent logit + Bernoulli), not observed.
- Customer identity is merchant-scoped; cross-merchant abuse patterns are invisible by design.
- UPI excluded from disputes: NPCI auto-resolves UPI chargebacks via settlement reconciliation.
- Time window is 6 months (Jan-Jun 2025); annual_transactions in merchants.csv represents the annualised rate.
"""

    (DATA_DIR / "DATASET_MANIFEST.md").write_text(manifest, encoding="utf-8")

    # ── DATA_PROFILE.md ──────────────────────────────────────────────────────
    rc_mix = disputes_df["reason_code"].value_counts()
    rc_rows = "\n".join(
        f"| `{rc}` | {cnt:,} | {cnt/n_disp*100:.1f}% |"
        for rc, cnt in rc_mix.items()
    )
    size_rows = "\n".join(
        f"| `{sz}` | {cnt} |"
        for sz, cnt in merchants_df["business_size"].value_counts().items()
    )

    profile = f"""# SaHaYa Data Profile
*Auto-generated from final files — do not edit manually*

## Transaction Summary
- Total transactions: **{n_txn:,}**
- Card transactions: {(transactions_df['payment_method'].isin(['credit_card','debit_card'])).sum():,}
- UPI transactions: {(transactions_df['payment_method'] == 'upi').sum():,}
- Date range: {transactions_df['timestamp'].min()} → {transactions_df['timestamp'].max()}
- Amount range: ₹{int(transactions_df['amount'].min()):,} – ₹{int(transactions_df['amount'].max()):,}

## Merchant Summary
- Total merchants: **{n_merch}**

| business_size | count |
|---|---|
{size_rows}

## Dispute Summary
- Total disputes: **{n_disp:,}**
- Contested: {(disputes_df['merchant_action']=='contested').sum():,} ({contest_rate*100:.1f}%)
- Accepted (refunded): {(disputes_df['merchant_action']=='accepted').sum():,}
- Portfolio card dispute rate: **{disp_rate*100:.2f}%**
- Overall win rate (contested): **{win_rate*100:.1f}%**

## Reason Code Distribution
| reason_code | count | share |
|---|---|---|
{rc_rows}

## Evidence Summary
- Total evidence rows: **{n_ev:,}**
- Rows per dispute: 6 (exact)
- Available rate: {evidence_df['available'].mean()*100:.1f}%
- Required-available rate: {evidence_df[evidence_df['required']==1]['available'].mean()*100:.1f}%
"""
    (DATA_DIR / "DATA_PROFILE.md").write_text(profile, encoding="utf-8")

    # ── ML_DATA_DICTIONARY.md ────────────────────────────────────────────────
    ml_dict = """# ML Data Dictionary
*Use `disputes.csv` joined with `evidence.csv` and `transactions.csv.gz`.*

## Target variable
`dispute_outcome` in **contested** disputes only.
- `won` (1) — merchant won the chargeback
- `lost` (0) — merchant lost

## Feature groups

### From disputes.csv
| column | type | notes |
|---|---|---|
| `reason_code` | categorical | 7 levels; primary signal |
| `network` | categorical | Visa / Mastercard / RuPay |
| `dispute_amount` | integer | Whole rupees; mild negative effect on win rate |
| `days_to_deadline` | integer | Time merchant had to respond |
| `contest_fee` | integer | ₹400–₹750 by network |

### From transactions.csv.gz (join on transaction_id)
| column | type | notes |
|---|---|---|
| `otp_3ds_passed` | binary | Decisive for UNAUTHORIZED disputes |
| `customer_previous_orders` | integer | Point-in-time |
| `customer_previous_spend` | integer | Point-in-time |
| `payment_method` | categorical | credit_card / debit_card only for disputes |

### From merchants.csv (join on merchant_id)
| column | type | notes |
|---|---|---|
| `merchant_archetype` | categorical | 7 levels |
| `fulfillment_type` | categorical | 4 levels |
| `subscription_supported` | binary | |
| `documentation_maturity` | float [0.15–0.97] | Proxy for evidence completeness |

### Computed from evidence.csv (join on dispute_id)
| column | type | notes |
|---|---|---|
| required_count | integer | # of required docs for this (reason_code, fulfillment_type) |
| present_count | integer | # of required docs that are available |
| missing_count | integer | required_count − present_count |
| decisive_present | binary | Whether the single most-decisive doc is available |
| mean_quality_required | float | Mean quality_score of present required docs |

## Forbidden columns
Do NOT include in model features (leakage / forbidden by spec):
`should_contest`, `recommended_action`, `simulated_win_probability`,
`expected_recovery`, `expected_cost`, `expected_net_value`,
`contestable`, `dispute_status`, `chargeback_outcome`,
`evidence_strength`, `evidence_completeness`

## Price-point policy
- Subscription archetypes (edtech, saas, fitness): discrete tiers stored in `merchants.price_points`
- Non-subscription: whole rupees sampled from per-archetype product catalogs; ≥65% end in 9

## §6.1 Requirement matrices
See DATASET_MANIFEST.md for the full 4-table requirement matrix.
"""
    (DATA_DIR / "ML_DATA_DICTIONARY.md").write_text(ml_dict, encoding="utf-8")

    print("  Wrote DATASET_MANIFEST.md, DATA_PROFILE.md, ML_DATA_DICTIONARY.md")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    print("SaHaYa — Dataset Generation v5.1")
    print("=" * 65)

    # Create output directories
    CORE_DIR.mkdir(parents=True, exist_ok=True)
    DEMO_DIR.mkdir(parents=True, exist_ok=True)

    # Delete auxiliary/ per spec
    if AUX_DIR.exists():
        shutil.rmtree(AUX_DIR)
        print(f"Deleted {AUX_DIR}")

    # ── Generate ──────────────────────────────────────────────────────────────
    merchants_df    = generate_merchants()
    customers_df    = generate_customers(merchants_df)
    transactions_df = generate_transactions(merchants_df, customers_df)
    disputes_df     = generate_disputes_initial(transactions_df, merchants_df)
    evidence_df     = generate_evidence(disputes_df)
    disputes_df     = compute_outcomes(disputes_df, evidence_df)

    # Drop internal columns before saving
    internal_cols = [c for c in disputes_df.columns if c.startswith("_")]
    disputes_save = disputes_df.drop(columns=internal_cols)

    def safe_to_csv(df_to_save, filepath, **kwargs):
        import time
        for attempt in range(5):
            try:
                df_to_save.to_csv(filepath, **kwargs)
                return
            except PermissionError:
                time.sleep(1.0)
        df_to_save.to_csv(filepath, **kwargs)

    # ── Save ──────────────────────────────────────────────────────────────────
    print("\nSaving files …")
    safe_to_csv(merchants_df, CORE_DIR / "merchants.csv", index=False)
    print(f"  merchants.csv          {len(merchants_df):,} rows")

    safe_to_csv(customers_df, CORE_DIR / "customers.csv", index=False)
    print(f"  customers.csv          {len(customers_df):,} rows")

    safe_to_csv(transactions_df, CORE_DIR / "transactions.csv.gz", index=False, compression="gzip")
    print(f"  transactions.csv.gz    {len(transactions_df):,} rows")

    safe_to_csv(disputes_save, CORE_DIR / "disputes.csv", index=False)
    print(f"  disputes.csv           {len(disputes_save):,} rows")

    safe_to_csv(evidence_df, CORE_DIR / "evidence.csv", index=False)
    print(f"  evidence.csv           {len(evidence_df):,} rows")

    save_demo_merchants(merchants_df)

    # ── Audit & report ────────────────────────────────────────────────────────
    run_semantic_audit(merchants_df, transactions_df, disputes_df, evidence_df)
    print_human_report(merchants_df, transactions_df, disputes_df, evidence_df)
    run_baseline_model(merchants_df, disputes_df, evidence_df)
    generate_documentation(merchants_df, transactions_df, disputes_df, evidence_df)

    print("\n[PASS] Dataset generation complete.")


if __name__ == "__main__":
    main()
