from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from ..utils.db import get_supabase


class ChatMessage(BaseModel):
	id: Optional[str] = None
	channel: str  # "wa" | "ig"
	user_id: str
	text: str
	intent: str = "unknown"
	created_at: datetime = datetime.now(timezone.utc)
	followup_at: Optional[datetime] = None
	status: str = "received"  # received | replied | followup_pending | followup_sent


def log_message(message: ChatMessage) -> Dict[str, Any]:
    client = get_supabase()
    payload = message.model_dump(exclude_none=True)
    # Biarkan DB mengisi created_at default
    payload.pop("created_at", None)
    # Normalisasi datetime ke ISO jika ada
    if isinstance(payload.get("followup_at"), datetime):
        payload["followup_at"] = payload["followup_at"].isoformat()
    result = client.table("chat_messages").insert(payload).execute()
    return result.data[0] if result.data else {}


def schedule_followup(
	*,
	channel: str,
	user_id: str,
	text: str,
	intent: str = "followup",
	delay_minutes: int = 60,
) -> Dict[str, Any]:
	client = get_supabase()
	followup_time = datetime.now(timezone.utc) + timedelta(minutes=delay_minutes)
	row = {
		"channel": channel,
		"user_id": user_id,
		"text": text,
		"intent": intent,
		"created_at": datetime.now(timezone.utc).isoformat(),
		"followup_at": followup_time.isoformat(),
		"status": "followup_pending",
	}
	result = client.table("chat_messages").insert(row).execute()
	return result.data[0] if result.data else {}


def get_due_followups(limit: int = 50) -> List[Dict[str, Any]]:
	client = get_supabase()
	now_iso = datetime.now(timezone.utc).isoformat()
	result = (
		client.table("chat_messages")
		.select("*")
		.eq("status", "followup_pending")
		.lte("followup_at", now_iso)
		.limit(limit)
		.execute()
	)
	return result.data or []


def mark_followup_sent(row_id: Any) -> None:
	client = get_supabase()
	client.table("chat_messages").update({"status": "followup_sent"}).eq("id", row_id).execute()
