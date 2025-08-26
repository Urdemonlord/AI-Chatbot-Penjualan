from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from ..utils.db import get_supabase


class FaqItem(BaseModel):
	id: Optional[int] = None
	intent: str
	question: str
	answer: str
	tags: Optional[List[str]] = None


def get_faq_by_intent(intent: str) -> Optional[Dict[str, Any]]:
	client = get_supabase()
	res = client.table("faqs").select("*").eq("intent", intent).limit(1).execute()
	return res.data[0] if res.data else None
