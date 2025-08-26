import os
from dotenv import load_dotenv

load_dotenv()

# Meta / WhatsApp
WA_PHONE_ID = os.getenv("WA_PHONE_ID")
WA_TOKEN = os.getenv("WA_TOKEN")
META_API_VERSION = os.getenv("META_API_VERSION", "v18.0")
WA_FOLLOWUP_TEMPLATE = os.getenv("WA_FOLLOWUP_TEMPLATE")  # contoh: follow_up_24h
WA_FOLLOWUP_LANG = os.getenv("WA_FOLLOWUP_LANG", "en_US")
WA_WABA_ID = os.getenv("WA_WABA_ID")  # WhatsApp Business Account ID (untuk list templates)

# Instagram Messaging
IG_USER_ID = os.getenv("IG_USER_ID")
IG_PAGE_TOKEN = os.getenv("IG_PAGE_TOKEN")

# Webhook verification token
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
ALLOW_ANY_VERIFY_TOKEN = os.getenv("ALLOW_ANY_VERIFY_TOKEN", "false").lower() in {"1", "true", "yes"}

# Admin
ADMIN_SECRET = os.getenv("ADMIN_SECRET")

# Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

def require_env(var_name: str) -> str:
	value = os.getenv(var_name)
	if not value:
		raise RuntimeError(f"Environment variable {var_name} belum diset.")
	return value
