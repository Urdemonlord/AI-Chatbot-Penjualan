import httpx
from ..config import IG_PAGE_TOKEN, IG_USER_ID, META_API_VERSION


async def send_ig_message_async(user_id: str, text: str):
	if not IG_PAGE_TOKEN or not IG_USER_ID:
		raise RuntimeError("IG_PAGE_TOKEN atau IG_USER_ID belum diset.")
	# Instagram messaging uses the same Graph API
	url = f"https://graph.facebook.com/{META_API_VERSION}/{IG_USER_ID}/messages"
	headers = {"Authorization": f"Bearer {IG_PAGE_TOKEN}", "Content-Type": "application/json"}
	payload = {
		"recipient": {"id": user_id},
		"message": {"text": text},
	}
	async with httpx.AsyncClient(timeout=20) as client:
		resp = await client.post(url, headers=headers, json=payload)
		resp.raise_for_status()
		return resp.json()


def send_ig_message(user_id: str, text: str):
	import anyio
	return anyio.run(send_ig_message_async, user_id, text)
