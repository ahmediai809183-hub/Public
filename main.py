from fastapi import FastAPI, HTTPException, Security, status
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

# 🔑 المفتاح المؤقت بتاعك للتجربة (تقدر تغيره لأي كلمة تحبها)
MY_SECRET_API_KEY = "PRO_VALIDATOR_MASTER_2026"

# 🛑 عدد المحاولات المجانية (هنخليها 0 لو عايز الفخ يقفل فوراً على أي حد معندوش مفتاح)
FREE_LIMIT = 0 
# هنا تقدر تستخدم متغير بسيط يعد الطلبات لو عايز، بس طالما الفخ شغال للـ Production:
# السيستم هيرفض أي طلب ما فيهوش الـ Key الماستر بتاعك فوق.

@app.get("/validate")
async def validate_email(email: str, api_key: str = Security(api_key_header)):
    # 1. التحقق من وجود الـ API Key الصحيح
    if not api_key or api_key != MY_SECRET_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="[Email Validator Pro] Free limit reached. To unlock high-volume production validation, get your API Key instantly."
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
