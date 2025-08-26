import httpx
from ..config import (
	WA_TOKEN,
	WA_PHONE_ID,
	META_API_VERSION,
	WA_FOLLOWUP_TEMPLATE,
	WA_FOLLOWUP_LANG,
	WA_WABA_ID,
)
from ..utils.logger import logger


async def send_wa_message_async(user_id: str, text: str):
	if not WA_TOKEN or not WA_PHONE_ID:
		raise RuntimeError("WA_TOKEN atau WA_PHONE_ID belum diset.")
	url = f"https://graph.facebook.com/{META_API_VERSION}/{WA_PHONE_ID}/messages"
	headers = {"Authorization": f"Bearer {WA_TOKEN}", "Content-Type": "application/json"}
	payload = {
		"messaging_product": "whatsapp",
		"to": user_id,
		"type": "text",
		"text": {"body": text},
	}
	async with httpx.AsyncClient(timeout=20) as client:
		resp = await client.post(url, headers=headers, json=payload)
		if resp.status_code >= 400:
			try:
				err = resp.json()
			except Exception:
				err = {"error": resp.text}
			logger.error("WA API error %s: %s", resp.status_code, err)
			raise RuntimeError(f"WA API error {resp.status_code}: {err}")
		return resp.json()


def send_wa_message(user_id: str, text: str):
	"""Sync wrapper untuk kemudahan pemanggilan dari route sync."""
	import anyio
	return anyio.run(send_wa_message_async, user_id, text)


async def send_wa_template_async(
	user_id: str,
	template_name: str,
	language: str = None,
	components: list | None = None,
):
	"""Kirim template message (HSM) untuk di luar 24 jam window."""
	if not WA_TOKEN or not WA_PHONE_ID:
		raise RuntimeError("WA_TOKEN atau WA_PHONE_ID belum diset.")
	url = f"https://graph.facebook.com/{META_API_VERSION}/{WA_PHONE_ID}/messages"
	headers = {"Authorization": f"Bearer {WA_TOKEN}", "Content-Type": "application/json"}
	payload = {
		"messaging_product": "whatsapp",
		"to": user_id,
		"type": "template",
		"template": {
			"name": template_name,
			"language": {"code": (language or WA_FOLLOWUP_LANG or "en_US")},
		}
	}
	if components:
		payload["template"]["components"] = components
	async with httpx.AsyncClient(timeout=20) as client:
		resp = await client.post(url, headers=headers, json=payload)
		if resp.status_code >= 400:
			try:
				err = resp.json()
			except Exception:
				err = {"error": resp.text}
			logger.error("WA Template API error %s: %s", resp.status_code, err)
			raise RuntimeError(f"WA Template API error {resp.status_code}: {err}")
		return resp.json()


async def list_wa_templates_async() -> dict:
	"""Ambil daftar template dari WABA untuk membantu debug nama dan bahasa."""
	if not WA_TOKEN or not WA_WABA_ID:
		raise RuntimeError("WA_TOKEN atau WA_WABA_ID belum diset.")
	url = f"https://graph.facebook.com/{META_API_VERSION}/{WA_WABA_ID}/message_templates"
	headers = {"Authorization": f"Bearer {WA_TOKEN}"}
	params = {"limit": 50}
	async with httpx.AsyncClient(timeout=20) as client:
		resp = await client.get(url, headers=headers, params=params)
		if resp.status_code >= 400:
			try:
				err = resp.json()
			except Exception:
				err = {"error": resp.text}
			logger.error("WA List Templates API error %s: %s", resp.status_code, err)
			raise RuntimeError(f"WA List Templates API error {resp.status_code}: {err}")
		return resp.json()
