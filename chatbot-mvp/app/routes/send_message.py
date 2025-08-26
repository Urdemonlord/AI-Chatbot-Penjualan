from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from ..services.wa_service import send_wa_message_async, send_wa_template_async, list_wa_templates_async
from ..services.ig_service import send_ig_message_async
from ..models.chat import ChatMessage, log_message
from ..utils.logger import logger

router = APIRouter()

class SendMessagePayload(BaseModel):
	channel: str
	user_id: str
	text: str


@router.post("/send-message")
async def send_message(payload: SendMessagePayload):
	# Manual send untuk testing
	try:
		if payload.channel == "wa":
			await send_wa_message_async(payload.user_id, payload.text)
		elif payload.channel == "ig":
			await send_ig_message_async(payload.user_id, payload.text)
		else:
			return JSONResponse({"error": "unsupported channel"}, status_code=400)
		log_message(
			ChatMessage(channel=payload.channel, user_id=payload.user_id, text=payload.text, intent="manual_send")
		)
		return {"status": "sent"}
	except Exception as e:
		logger.exception("Gagal kirim pesan: %s", e)
		return JSONResponse({"error": str(e)}, status_code=500)


class SendTemplatePayload(BaseModel):
	user_id: str
	template: str
	language: str | None = None
	components: list | None = None


@router.post("/send-template")
async def send_template(payload: SendTemplatePayload):
	try:
		resp = await send_wa_template_async(
			user_id=payload.user_id,
			template_name=payload.template,
			language=payload.language,
			components=payload.components,
		)
		return {"status": "sent", "response": resp}
	except Exception as e:
		logger.exception("Gagal kirim template: %s", e)
		return JSONResponse({"error": str(e)}, status_code=500)


@router.get("/wa-templates")
async def wa_templates():
	try:
		return await list_wa_templates_async()
	except Exception as e:
		logger.exception("Gagal ambil template WA: %s", e)
		return JSONResponse({"error": str(e)}, status_code=500)
