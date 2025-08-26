from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from ..utils.db import get_supabase


class Product(BaseModel):
	id: Optional[int] = None
	name: str
	price: float
	stock: int
	variants: Optional[List[str]] = None


def list_products(limit: int = 10) -> List[Dict[str, Any]]:
	client = get_supabase()
	res = client.table("products").select("*").order("id").limit(limit).execute()
	return res.data or []


def min_price() -> Optional[float]:
	client = get_supabase()
	res = client.rpc("products_min_price").execute()
	if res.data:
		# Expecting RPC to return a single value or object with key 'min'
		val = res.data[0] if isinstance(res.data, list) else res.data
		try:
			return float(val.get("min") if isinstance(val, dict) else val)
		except Exception:
			return None
	return None
