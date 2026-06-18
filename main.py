"""
Email Validation API - Honey Trap Edition
========================================
Validates email addresses with built-in independent API Key authentication 
and IP-based free tier limiting (The Honey Trap).
"""

import re
import dns.resolver
import sqlite3
from fastapi import FastAPI, Header, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import time

app = FastAPI(
    title="Email Validator Pro",
    description="Fast, accurate email validation with built-in independent API key management.",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── إعداد قاعدة البيانات تلقائياً وتوليد مفتاح تجريبي للمستقبل ────────────────
def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS api_keys (
            key TEXT PRIMARY KEY,
            credits INTEGER
        )
    """)
    # هنحط مفتاح تجريبي مدفوع عشان تجربه بنفسك وتتأكد إنه شغال
    cursor.execute("INSERT OR IGNORE INTO api_keys (key, credits) VALUES ('ahmed_secret_pro_key', 1000)")
    conn.commit()
    conn.close()

init_db()

# ذاكرة مؤقتة سريعة لحفظ عدد محاولات الـ IP للأشخاص اللذين لا يملكون مفتاحاً
FREE_TIER_CACHE = {}

# ── قوائم الدومينات ──────────────────────────────────────────────────────────
DISPOSABLE_DOMAINS = {
    "mailinator.com", "tempmail.com", "guerrillamail.com", "10minutemail.com",
    "throwaway.email", "yopmail.com", "fakeinbox.com", "trashmail.com",
    "dispostable.com", "maildrop.cc", "getairmail.com", "sharklasers.com",
    "guerrillamailblock.com", "grr.la", "guerrillamail.info", "spam4.me",
    "discard.email", "spamgourmet.com", "mailnull.com", "tempr.email",
    "spamhereplease.com", "spamthisplease.com", "anonaddy.com"
}

FREE_PROVIDERS = {
    "gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "icloud.com",
    "aol.com", "protonmail.com", "mail.com", "zoho.com", "live.com"
}

# ── نماذج البيانات (Response Models) ──────────────────────────────────────────
class ValidationResult(BaseModel):
    email: str
    is_valid: bool
    score: int
    syntax_valid: bool
    domain_exists: bool
    has_mx_records: bool
    is_disposable: bool
    is_free_provider: bool
    domain: str
    suggestion: Optional[str]
    message: str

class BulkRequest(BaseModel):
    emails: list[str]

class BulkResult(BaseModel):
    total: int
    valid: int
    invalid: int
    results: list[ValidationResult]

# ── خوارزمية الفحص الأساسية ──────────────────────────────────────────────────
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$')
COMMON_DOMAIN_TYPOS = {
    "gmial.com": "gmail.com", "gmaill.com": "gmail.com", "gamil.com": "gmail.com",
    "hotmial.com": "hotmail.com", "yahooo.com": "yahoo.com", "outlok.com": "outlook.com"
}

def validate_email(email: str) -> ValidationResult:
    email = email.strip().lower()
    syntax_valid = bool(EMAIL_REGEX.match(email))
    if not syntax_valid:
        return ValidationResult(
            email=email, is_valid=False, score=0, syntax_valid=False, domain_exists=False,
            has_mx_records=False, is_disposable=False, is_free_provider=False, domain="",
            suggestion=None, message="Invalid email syntax"
        )

    local, domain = email.rsplit("@", 1)
    suggestion = COMMON_DOMAIN_TYPOS.get(domain)
    is_disposable = domain in DISPOSABLE_DOMAINS
    is_free_provider = domain in FREE_PROVIDERS

    domain_exists = False
    has_mx = False
    try:
        dns.resolver.resolve(domain, 'A')
        domain_exists = True
    except Exception:
        try:
            dns.resolver.resolve(domain, 'AAAA')
            domain_exists = True
        except Exception:
            pass

    if domain_exists:
        try:
            dns.resolver.resolve(domain, 'MX')
            has_mx = True
        except Exception:
            pass

    score = 0
    if syntax_valid:   score += 25
    if domain_exists:  score += 25
    if has_mx:         score += 35
    if not is_disposable: score += 15

    is_valid = syntax_valid and domain_exists and has_mx and not is_disposable
    msg = "Valid email address" if is_valid else (
        "Disposable email detected" if is_disposable else
        "Domain has no MX records — cannot receive email" if domain_exists else
        "Domain does not exist"
    )

    return ValidationResult(
        email=email, is_valid=is_valid, score=score, syntax_valid=syntax_valid,
        domain_exists=domain_exists, has_mx_records=has_mx, is_disposable=is_disposable,
        is_free_provider=is_free_provider, domain=domain, suggestion=suggestion, message=msg
    )

# ── دالة التحقق الذكي من الهوية وفخ العسل ─────────────────────────────────────
def verify_authentication(request: Request, x_api_key: Optional[str] = Header(None)):
    # 1. إذا كان العميل يمتلك مفتاحاً
    if x_api_key:
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute("SELECT credits FROM api_keys WHERE key = ?", (x_api_key,))
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            raise HTTPException(status_code=401, detail="Invalid API Key. Get a valid key from your dashboard.")
        
        credits = row[0]
        if credits <= 0:
            conn.close()
            raise HTTPException(status_code=403, detail="Your API Key has 0 credits remaining. Please upgrade your plan.")
            
        # خفض رصيد العميل 1 في قاعدة البيانات
        cursor.execute("UPDATE api_keys SET credits = credits - 1 WHERE key = ?", (x_api_key,))
        conn.commit()
        conn.close()
        return "paid_user"

    # 2. فخ العسل: إذا لم يرسل مفتاحاً (مطور يجرب الأداة مجاناً)
    client_ip = request.client.host
    current_free_uses = FREE_TIER_CACHE.get(client_ip, 0)

    if current_free_uses >= 3:
        # رسالة الطُعم القاتلة التي ستجبره على الشراء
        raise HTTPException(
            status_code=429, 
            detail="[Email Validator Pro] Free limit reached. To unlock high-volume production validation, get your API Key instantly from: https://yourdomain.com"
        )
    
    # زيادة عداد المحاولات المجانية لهذا الـ IP
    FREE_TIER_CACHE[client_ip] = current_free_uses + 1
    return "free_tier"

# ── Endpoints ──────────────────────────────────────────────────────────────────

@app.get("/", tags=["Info"])
def root():
    return {
        "name": "Email Validator Pro",
        "version": "2.0.0",
        "status": "Running independently"
    }

@app.get("/validate", response_model=ValidationResult, tags=["Validation"])
def validate_single(
    request: Request,
    email: str = Query(..., description="Email address to validate"),
    x_api_key: Optional[str] = Header(None)
):
    # تشغيل نظام التحقق والفخ قبل الفحص
    verify_authentication(request, x_api_key)
    return validate_email(email)

@app.post("/validate/bulk", response_model=BulkResult, tags=["Validation"])
def validate_bulk(request: Request, payload: BulkRequest, x_api_key: Optional[str] = Header(None)):
    # الفحص الجماعي يتطلب دائماً حساباً مدفوعاً ومفتاحاً
    if not x_api_key:
        raise HTTPException(
            status_code=401, 
            detail="Bulk validation is a PRO feature. Please insert your API Key or subscribe at: https://yourdomain.com"
        )
        
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT credits FROM api_keys WHERE key = ?", (x_api_key,))
    row = cursor.fetchone()
    
    if not row or row[0] < len(payload.emails):
        conn.close()
        raise HTTPException(status_code=403, detail="Not enough credits for bulk validation. Please upgrade.")
        
    # خصم عدد الإيميلات بالكامل من رصيده
    cursor.execute("UPDATE api_keys SET credits = credits - ? WHERE key = ?", (len(payload.emails), x_api_key))
    conn.commit()
    conn.close()

    results = [validate_email(e) for e in payload.emails]
    valid_count = sum(1 for r in results if r.is_valid)

    return BulkResult(
        total=len(results),
        valid=valid_count,
        invalid=len(results) - valid_count,
        results=results
    )

    

   
    

    
   

  
    
          
