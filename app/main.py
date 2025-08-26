from fastapi import FastAPI

app = FastAPI()

# Import routes
from .routes import webhook, send_message, admin

app.include_router(webhook.router)
app.include_router(send_message.router)
app.include_router(admin.router)

@app.get("/")
def root():
    return {"message": "AI Chatbot Penjualan MVP is running."}
