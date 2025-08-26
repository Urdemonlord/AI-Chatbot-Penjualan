from fastapi import APIRouter, Request, Query
from fastapi.responses import PlainTextResponse
from ..services.intent_parser import parse_intent
from ..services.wa_service import send_wa_message_async
from ..services.ig_service import send_ig_message_async
from ..models.chat import ChatMessage, log_message, schedule_followup
from ..models.faq import get_faq_by_intent
from ..models.product import list_products, min_price
from ..config import VERIFY_TOKEN, ALLOW_ANY_VERIFY_TOKEN
from ..utils.logger import logger
from ..services.qa_service import answer_product_query

router = APIRouter()

@router.get("/webhook")
def verify_webhook(
	request: Request,
	mode: str = Query("", alias="hub.mode"),
	hub_verify_token: str = Query("", alias="hub.verify_token"),
	challenge: str = Query("", alias="hub.challenge"),
	verify_token_param: str = Query("", alias="verify_token"),
	token_param: str = Query("", alias="token"),
):
	"""
	Meta Webhook verification (Echo).
	"""
	def _clean(s: str) -> str:
		return (s or "").strip().strip('"').strip("'")

	provided = _clean(
		hub_verify_token
		or verify_token_param
		or token_param
		or request.query_params.get("hub.verify_token", "")
		or request.query_params.get("verify_token", "")
		or request.query_params.get("token", "")
	)
	expected = _clean(VERIFY_TOKEN)
	mode_val = (mode or request.query_params.get("hub.mode") or request.query_params.get("mode") or "").strip()
	challenge_val = (challenge or request.query_params.get("hub.challenge") or request.query_params.get("challenge") or "").strip()

	if (mode_val in ("", "subscribe")) and (ALLOW_ANY_VERIFY_TOKEN or provided == expected):
		return PlainTextResponse(challenge_val or "Verified", status_code=200)

	logger.info(
		"Webhook verify failed: mode=%s, provided_len=%s, expected_len=%s allow_any=%s",
		mode_val,
		len(provided),
		len(expected),
		ALLOW_ANY_VERIFY_TOKEN,
	)
	return PlainTextResponse("Invalid token", status_code=401)

def _extract_wa_events(body: dict):
    """
    Pulangkan list event WhatsApp dalam bentuk seragam:
    [{"from": "62xxxx", "text": "isi pesan", "type": "text", "wamid": "..."}]
    """
    events = []
    if body.get("object") != "whatsapp_business_account":
        return events
    for entry in body.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            for msg in value.get("messages", []) or []:
                mtype = msg.get("type")
                text = msg.get("text", {}).get("body") if mtype == "text" else None
                events.append({
                    "from": msg.get("from"),
                    "text": text or "",
                    "type": mtype,
                    "wamid": msg.get("id")
                })
    return events

@router.post("/webhook")
async def handle_webhook(request: Request):
    # 1) Baca JSON; jika gagal, tetap balas 200 agar Meta tidak retry terus
    try:
        data = await request.json()
    except Exception as ex:
        logger.exception("Gagal parse JSON webhook: %s", ex)
        return PlainTextResponse("bad_request", status_code=200)

    # 2) Coba format WhatsApp dulu
    wa_events = _extract_wa_events(data)
    if wa_events:
        for ev in wa_events:
            user_id = ev["from"]
            text = ev["text"]
            intent = parse_intent(text)

            try:
                log_message(ChatMessage(channel="wa", user_id=user_id, text=text, intent=intent))
            except Exception as e:
                logger.exception("Gagal log chat: %s", e)

            # Balasan sederhana berbasis intent (contoh)
            if intent == "greeting":
                reply_text = "Halo! Saya asisten belanja. Saya bisa bantu carikan produk, harga, dan stok. Ketik 'katalog' untuk lihat cepat, atau tanya langsung misalnya 'ada kaos hitam?'."
            elif intent.startswith("faq_"):
                faq = get_faq_by_intent(intent)
                reply_text = faq.get("answer") if faq else "Berikut info yang saya punya."
            elif intent == "katalog":
                products = list_products(limit=5)
                if products:
                    lines = [f"{p.get('name')} - Rp{int(p.get('price', 0)):,}" for p in products]
                    reply_text = "Katalog singkat:\n" + "\n".join(lines)
                else:
                    reply_text = "Katalog kosong untuk saat ini."
            elif intent == "order":
                mn = min_price()
                reply_text = f"Siap bantu order. Harga mulai Rp{int(mn):,}." if mn else "Siap bantu order. Produk apa yang kamu cari?"
            else:
                # fallback ke pencarian produk sederhana berbasis teks bebas
                reply_text = answer_product_query(text)

            try:
                # Kirim via WhatsApp Cloud API (async)
                await send_wa_message_async(user_id, reply_text)
            except Exception as e:
                logger.exception("Gagal kirim pesan WA: %s", e)

            # Follow-up (opsional)
            if intent not in {"faq_harga", "faq_stok"}:
                try:
                    schedule_followup(channel="wa", user_id=user_id, text="Halo, masih berminat?", delay_minutes=60*24)
                except Exception as e:
                    logger.exception("Gagal schedule followup: %s", e)

        return PlainTextResponse("OK", status_code=200)

    # 3) Fallback: format internal generik {channel, user_id, text}
    channel = data.get("channel")
    user_id = data.get("user_id")
    text = data.get("text", "")
    if channel and user_id:
        intent = parse_intent(text)
        try:
            log_message(ChatMessage(channel=channel, user_id=user_id, text=text, intent=intent))
        except Exception as e:
            logger.exception("Gagal log chat: %s", e)

        if intent == "greeting":
            reply_text = "Halo! Saya asisten belanja. Saya bisa bantu carikan produk, harga, dan stok. Ketik 'katalog' untuk lihat cepat, atau tanya langsung misalnya 'ada kaos hitam?'."
        else:
            # fallback ke pencarian produk sederhana berbasis teks bebas
            reply_text = answer_product_query(text)
        # … (bisa pakai logika yang sama seperti di atas)
        try:
            if channel == "wa":
                await send_wa_message_async(user_id, reply_text)
            elif channel == "ig":
                await send_ig_message_async(user_id, reply_text)
        except Exception as e:
            logger.exception("Gagal kirim pesan: %s", e)

        return PlainTextResponse("OK", status_code=200)

    logger.warning("Payload tidak dikenal: %s", data)
    return PlainTextResponse("ignored", status_code=200)
