from typing import List, Dict, Any
import re
from ..utils.db import get_supabase


PRICE_RE = re.compile(r"(\d[\d\.]{2,})")


def _parse_terms(text: str) -> List[str]:
	terms = re.findall(r"[A-Za-z0-9_]+", text.lower())
	return [t for t in terms if len(t) >= 3]


def _extract_price_numbers(text: str) -> List[int]:
	nums: List[int] = []
	for m in PRICE_RE.findall(text.replace(",", ".")):
		try:
			val = int(re.sub(r"\D", "", m))
			if val > 0:
				nums.append(val)
		except Exception:
			pass
	return nums


def search_products_freeform(text: str, limit: int = 5) -> List[Dict[str, Any]]:
	client = get_supabase()
	terms = _parse_terms(text)
	query = client.table("products").select("*").limit(limit)
	# Apply basic OR ilike filters over name and variants
	for i, term in enumerate(terms[:4]):
		pattern = f"%{term}%"
		if i == 0:
			query = query.or_(f"name.ilike.{pattern},variants.cs.{{{term}}}")
		else:
			query = query.or_(f"name.ilike.{pattern},variants.cs.{{{term}}}")
	res = query.execute()
	return res.data or []


def answer_product_query(text: str) -> str:
	# Heuristik sederhana: cari produk, tampilkan harga dan stok
	products = search_products_freeform(text, limit=5)
	if not products:
		return "Maaf, saya belum menemukan produk yang cocok. Coba sebutkan nama/varian produk."
	lines: List[str] = []
	for p in products:
		name = p.get("name")
		price = p.get("price") or 0
		stock = p.get("stock")
		variants = p.get("variants") or []
		line = f"{name} - Rp{int(price):,} (stok: {stock})"
		if variants:
			line += f" | varian: {', '.join(variants[:5])}"
		lines.append(line)
	return "Berikut yang saya temukan:\n" + "\n".join(lines)


