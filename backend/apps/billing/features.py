ALL_FEATURES = [
    "dashboard", "members", "members.packages", "members.attendance", "payments", "payments.invoices",
    "expenses", "settings", "settings.preferences", "pos", "crm.contacts", "crm.inquiries", "classes",
    "instructors", "discount", "reports", "email_config",
    "attendance.devices", "attendance.fingerprints", "attendance.iclock", "attendance.access_gate",
]
CORE = ["dashboard", "members", "members.packages", "members.attendance", "payments", "payments.invoices", "expenses", "settings", "settings.preferences"]
GROWTH = CORE + ["pos", "crm.contacts", "crm.inquiries", "classes", "instructors", "discount", "reports", "email_config"]
NEVER_HIDE = {"dashboard", "settings"}   # hiding these would lock the owner out
PLAN_SEED = [
    dict(code="starter", name="Starter", trial_days=14, price_month=3490, price_year=34900, features=CORE, limits={"max_members": 300, "max_staff": 3}),
    dict(code="growth", name="Growth", trial_days=0, price_month=5490, price_year=54900, features=GROWTH, limits={"max_members": 2000, "max_staff": 15}),
    dict(code="enterprise", name="Enterprise", trial_days=0, price_month=None, price_year=None, features=ALL_FEATURES, limits={}),
]
