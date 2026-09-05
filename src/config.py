"""Configuration for the Razorpay Buildathon synthetic dataset."""

from pathlib import Path

SEED = 42

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
CORE_DIR = DATA_DIR / "core"
DEMO_DIR = DATA_DIR / "demo"

N_MERCHANTS = 300
N_TRANSACTIONS = 500_000
N_DISPUTES = 1_943
EVIDENCE_PER_DISPUTE = 6

START_DATE = "2025-01-01 00:00:00"
END_DATE = "2025-06-30 23:59:59"

CITIES = ["Mumbai", "Kolkata", "Delhi", "Bangalore", "Pune", "Chennai", "Hyderabad"]

ARCHETYPE_COUNTS = {
    "social_seller": 94,
    "d2c_brand": 54,
    "fitness_membership": 46,
    "subscription_edtech": 37,
    "saas_tools": 35,
    "travel_booking": 23,
    "marketplace_retailer": 11,
}

FULFILLMENT = {
    "social_seller": "physical_delivery",
    "d2c_brand": "physical_delivery",
    "marketplace_retailer": "physical_delivery",
    "subscription_edtech": "digital_service",
    "saas_tools": "digital_service",
    "fitness_membership": "membership_service",
    "travel_booking": "booking_service",
}

SUBSCRIPTION = {
    "social_seller": 0,
    "d2c_brand": 0,
    "marketplace_retailer": 0,
    "subscription_edtech": 1,
    "saas_tools": 1,
    "fitness_membership": 1,
    "travel_booking": 0,
}

DOCUMENTATION_MATURITY = {
    "social_seller": 0.34,
    "d2c_brand": 0.80,
    "marketplace_retailer": 0.92,
    "subscription_edtech": 0.68,
    "saas_tools": 0.88,
    "fitness_membership": 0.55,
    "travel_booking": 0.62,
}

SIZE_COUNTS = {"micro": 80, "small": 110, "medium": 85, "large": 25}
SIZE_TXN_RANGES = {
    "micro": (80, 120),
    "small": (500, 2_000),
    "medium": (2_000, 4_000),
    "large": (7_000, 9_000),
}

REASON_CODES = [
    "RECURRING_BILLING_DISPUTE",
    "UNAUTHORIZED_TRANSACTION",
    "MERCHANDISE_NOT_AS_DESCRIBED",
    "CREDIT_NOT_PROCESSED",
    "MERCHANDISE_NOT_RECEIVED",
    "SERVICE_NOT_RENDERED",
    "DUPLICATE_TRANSACTION",
]

REASON_DESCRIPTIONS = {
    "RECURRING_BILLING_DISPUTE": "Recurring Billing Dispute",
    "UNAUTHORIZED_TRANSACTION": "Unauthorized Transaction",
    "MERCHANDISE_NOT_AS_DESCRIBED": "Merchandise Not As Described",
    "CREDIT_NOT_PROCESSED": "Credit Not Processed",
    "MERCHANDISE_NOT_RECEIVED": "Merchandise Not Received",
    "SERVICE_NOT_RENDERED": "Service Not Rendered",
    "DUPLICATE_TRANSACTION": "Duplicate Transaction",
}

REASON_WEIGHTS = {
    "social_seller": [0.15, 0.15, 0.40, 0.10, 0.30, 0.00, 0.05],
    "d2c_brand": [0.00, 0.20, 0.25, 0.12, 0.35, 0.00, 0.08],
    "marketplace_retailer": [0.00, 0.22, 0.30, 0.12, 0.30, 0.00, 0.06],
    "subscription_edtech": [0.40, 0.15, 0.04, 0.18, 0.00, 0.20, 0.03],
    "saas_tools": [0.50, 0.20, 0.00, 0.15, 0.00, 0.12, 0.03],
    "fitness_membership": [0.45, 0.07, 0.12, 0.13, 0.00, 0.20, 0.03],
    "travel_booking": [0.00, 0.15, 0.25, 0.18, 0.00, 0.35, 0.07],
}

EVIDENCE_SLOTS = {
    "physical_delivery": [
        "order_confirmation", "invoice", "shipping_label",
        "tracking_number", "delivery_confirmation", "customer_communication",
    ],
    "digital_service": [
        "order_confirmation", "invoice", "access_log",
        "service_record", "cancellation_record", "customer_communication",
    ],
    "membership_service": [
        "order_confirmation", "invoice", "access_log",
        "service_record", "cancellation_record", "customer_communication",
    ],
    "booking_service": [
        "order_confirmation", "invoice", "access_log",
        "service_record", "cancellation_record", "customer_communication",
    ],
}

REQUIRED = {
    "MERCHANDISE_NOT_RECEIVED":        [1, 0, 1, 1, 1, 0],
    "MERCHANDISE_NOT_AS_DESCRIBED":    [1, 0, 0, 0, 1, 1],
    "UNAUTHORIZED_TRANSACTION":        [1, 1, 0, 0, 1, 1],
    "CREDIT_NOT_PROCESSED":            [1, 1, 0, 0, 0, 1],
    "DUPLICATE_TRANSACTION":           [1, 1, 0, 0, 0, 0],
    "SERVICE_NOT_RENDERED":            [1, 0, 1, 1, 0, 0],
    "RECURRING_BILLING_DISPUTE":       [1, 1, 0, 0, 1, 1],
}

DEMO_MERCHANTS = {
    "M000001": ("Loops & Knots by Ananya", "social_seller", "small", 0.20, 7),
    "M000002": ("SoleCraft", "d2c_brand", "medium", 0.84, 4),
    "M000003": ("Gyan IAS Study Circle", "subscription_edtech", "medium", 0.73, 3),
    "M000004": ("CodePilot", "saas_tools", "small", 0.94, 5),
    "M000005": ("FitForge", "fitness_membership", "small", 0.60, 6),
    "M000006": ("TripWell", "travel_booking", "medium", 0.53, 2),
    "M000007": ("SwitchCart", "marketplace_retailer", "large", 0.97, 1),
}
