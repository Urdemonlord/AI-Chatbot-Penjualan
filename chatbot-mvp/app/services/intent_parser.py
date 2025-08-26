import re

FAQ_PATTERNS = {
    "greeting": r"\b(hai|halo|hello|hi|pagi|siang|sore|malam)\b",
    "faq_harga": r"(harga|berapa|diskon)",
    "faq_stok": r"(stok|ready|tersedia)",
    "katalog": r"(katalog|produk|lihat)",
    "varian": r"(warna|ukuran|size)",
    "order": r"(beli|order|pesan)"
}

def parse_intent(text: str) -> str:
    for intent, pattern in FAQ_PATTERNS.items():
        if re.search(pattern, text, re.IGNORECASE):
            return intent
    return "unknown"
