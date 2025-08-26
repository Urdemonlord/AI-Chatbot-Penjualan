from fastapi import APIRouter, Header, Query
from fastapi.responses import JSONResponse
from ..config import ADMIN_SECRET
from ..utils.logger import logger
from ..utils.db import get_supabase
from ..services.followup import run_followup_scheduler

router = APIRouter()


def _auth(secret: str | None) -> JSONResponse | None:
	if not ADMIN_SECRET:
		return JSONResponse({"error": "ADMIN_SECRET not set"}, status_code=500)
	if not secret or secret != ADMIN_SECRET:
		return JSONResponse({"error": "unauthorized"}, status_code=401)
	return None


@router.get("/health")
async def health():
	return {"status": "ok"}


@router.get("/version")
async def version():
	# Static MVP version; could be replaced with git hash
	return {"version": "0.1.0"}


@router.post("/admin/seed")
async def admin_seed(x_admin_secret: str | None = Header(default=None, alias="X-Admin-Secret")):
	err = _auth(x_admin_secret)
	if err:
		return err
	c = get_supabase()
	# Seed FAQs
	c.table("faqs").upsert([
		{"intent": "faq_harga", "question": "berapa harganya?", "answer": "Harga mulai Rp 100.000"},
		{"intent": "faq_stok", "question": "stoknya ada?", "answer": "Stok tersedia, silakan pilih varian"},
	], on_conflict="intent").execute()
	# Seed products
	c.table("products").insert([
		{"name": "Kaos Polos", "price": 120000, "stock": 20, "variants": ["Hitam", "Putih", "Abu"]},
		{"name": "Hoodie", "price": 250000, "stock": 8, "variants": ["M", "L", "XL"]},
		{"name": "Topi Trucker", "price": 75000, "stock": 15, "variants": ["Navy", "Hitam"]},
	]).execute()
	return {"status": "seeded"}


@router.post("/admin/reset")
async def admin_reset(x_admin_secret: str | None = Header(default=None, alias="X-Admin-Secret")):
	err = _auth(x_admin_secret)
	if err:
		return err
	c = get_supabase()
	# Hanya reset chat_messages agar riwayat demo bersih
	c.table("chat_messages").delete().neq("id", 0).execute()
	return {"status": "reset"}


@router.post("/admin/run-followup")
async def admin_run_followup(x_admin_secret: str | None = Header(default=None, alias="X-Admin-Secret")):
	err = _auth(x_admin_secret)
	if err:
		return err
	count = run_followup_scheduler()
	return {"status": "ok", "sent": count}


@router.post("/admin/seed-products")
async def admin_seed_products(
	x_admin_secret: str | None = Header(default=None, alias="X-Admin-Secret"),
	count: int = Query(default=50, ge=1, le=1000),
):
	"""Generate produk dummy dalam jumlah banyak untuk demo (max 1000)."""
	err = _auth(x_admin_secret)
	if err:
		return err
	c = get_supabase()
	batch = []
	for i in range(count):
		idx = i + 1
		batch.append({
			"name": f"Produk Demo {idx}",
			"price": 50000 + (idx * 1000) % 250000,
			"stock": (idx * 3) % 40 + 1,
			"variants": [f"Var{(idx%3)+1}", f"Warna{(idx%5)+1}"],
		})
	# Insert per-chunk agar tidak melewati limit PostgREST
	chunk_size = 200
	for start in range(0, len(batch), chunk_size):
		c.table("products").insert(batch[start:start+chunk_size]).execute()
	return {"status": "ok", "inserted": len(batch)}


