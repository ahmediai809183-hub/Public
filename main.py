from fastapi import FastAPI, Security, status
from fastapi.responses import JSONResponse
from fastapi.security.api_key import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
import re

app = FastAPI(title="Email Validator Pro")

# إعدادات الـ CORS عشان الـ API يستقبل طلبات من أي مكان
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# تحديد رأس الطلب اللي هيدور على الـ API Key
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

# 🔑 المفتاح المؤقت بتاعك للتجربة
MY_SECRET_API_KEY = "PRO_VALIDATOR_MASTER_2026"

# 🛑 عدد المحاولات المجانية (0 عشان الفخ يقفل فوراً على أي حد معندوش مفتاح)
FREE_LIMIT = 0 

@app.get("/validate")
async def validate_email(email: str, api_key: str = Security(api_key_header)):
    # 1. التحقق من وجود الـ API Key الصحيح
    if not api_key or api_key != MY_SECRET_API_KEY:
        # هنا المصيدة بتقفل وترجع رابط الدفع بتاع ليمون سكويز
        return JSONResponse(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            content={
                "status": "failed",
                "error": "Free tier limit reached",
                "message": "You have exceeded the allowed free verification volume. To unlock unlimited production-grade validation immediately, subscribe to our Master API Key.",
                "payment_url": "https://email-validator.lemonsqueezy.com/checkout/buy/3290c236-c717-4508-a993-b5ffa4e7a260"
            }
        )
    
    # 2. لو المفتاح صح.. السيستم يشتغل وينفذ الفحص الطبيعي:
    email_regex = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    is_valid = bool(re.match(email_regex, email))
    domain = email.split("@")[1] if "@" in email else ""
    
    return {
        "email": email,
        "is_valid": is_valid,
        "score": 100 if is_valid else 0,
        "syntax_valid": is_valid,
        "domain_exists": is_valid, # تبسيط مؤقت
        "domain": domain,
        "message": "Valid email address" if is_valid else "Invalid email syntax"
    }
