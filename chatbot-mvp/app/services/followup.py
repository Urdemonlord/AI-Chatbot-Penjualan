from typing import Callable
from ..models.chat import get_due_followups, mark_followup_sent
from .wa_service import send_wa_message, send_wa_template_async
from ..config import WA_FOLLOWUP_TEMPLATE, WA_FOLLOWUP_LANG
from .ig_service import send_ig_message


def _sender_for_channel(channel: str) -> Callable[[str, str], None]:
	return send_wa_message if channel == "wa" else send_ig_message


def run_followup_scheduler(max_to_process: int = 50) -> int:
	"""Memproses follow-up yang sudah due. Return jumlah pesan terkirim."""
	due = get_due_followups(limit=max_to_process)
	sent = 0
	for row in due:
		channel = row.get("channel")
		user_id = row.get("user_id")
		text = row.get("text")
		if channel == "wa" and WA_FOLLOWUP_TEMPLATE:
			try:
				# Coba kirim template jika tersedia (untuk jendela >24 jam)
				import anyio
				anyio.run(
					send_wa_template_async,
					user_id,
					WA_FOLLOWUP_TEMPLATE,
					WA_FOLLOWUP_LANG,
					None,
				)
			except Exception:
				# Fallback ke pesan teks biasa (akan gagal jika di luar 24 jam)
				sender = _sender_for_channel(channel)
				sender(user_id, text)
		else:
			sender = _sender_for_channel(channel)
			sender(user_id, text)
		mark_followup_sent(row.get("id"))
		sent += 1
	return sent
