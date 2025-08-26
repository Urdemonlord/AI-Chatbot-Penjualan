# AI Chatbot Penjualan MVP

Chatbot sederhana untuk auto-reply FAQ, kirim katalog produk, dan follow-up pelanggan di IG/WA.

## Fitur
- Auto-reply FAQ
- Kirim katalog produk
- Follow-up otomatis

## Stack
- FastAPI
- Supabase
- WhatsApp Cloud API
- Instagram Messaging API

## Menjalankan

```bash
uvicorn app.main:app --reload
```

## Environment

Tambahkan file `.env` dengan variabel berikut:

```
WA_PHONE_ID=
WA_TOKEN=
META_API_VERSION=v18.0
IG_USER_ID=
IG_PAGE_TOKEN=
VERIFY_TOKEN=
SUPABASE_URL=
SUPABASE_KEY=
WA_WABA_ID=
WA_FOLLOWUP_TEMPLATE=
WA_FOLLOWUP_LANG=en_US
```

## Skema Tabel Supabase (minimal)

- chat_messages
  - id (bigint, identity) PK
  - channel (text)
  - user_id (text)
  - text (text)
  - intent (text)
  - created_at (timestamptz) default now()
  - followup_at (timestamptz) nullable
  - status (text)

- faqs
  - id (bigint, identity) PK
  - intent (text)
  - question (text)
  - answer (text)
  - tags (text[])

- products
  - id (bigint, identity) PK
  - name (text)
  - price (numeric)
  - stock (int4)
  - variants (text[])

## Endpoint Uji

- GET `/webhook?hub.mode=subscribe&hub.verify_token=...&hub.challenge=12345`
- POST `/webhook` body minimal:

```json
{ "channel": "wa", "user_id": "<phone|ig_user>", "text": "katalog" }
```

- Kirim pesan teks WA:

```bash
curl -X POST http://localhost:8000/send-message \
  -H "Content-Type: application/json" \
  -d '{"channel":"wa","user_id":"62XXXXXXXXXX","text":"Halo"}'
```

- Kirim template WA (ganti `template` dan `language` sesuai daftar di `/wa-templates`):

```bash
curl -X POST http://localhost:8000/send-template \
  -H "Content-Type: application/json" \
  -d '{"user_id":"62XXXXXXXXXX","template":"follow_up_24h","language":"en_US","components":[]}'
```

- List template WA (butuh `WA_WABA_ID`):

```bash
curl http://localhost:8000/wa-templates
```

## Scheduler Follow-up

Panggil fungsi `run_followup_scheduler` secara periodik (cron / worker) untuk mengirim pesan yang due.
