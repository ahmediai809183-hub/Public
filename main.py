"""
Email Validation API
===================
Validates email addresses: syntax, domain, MX records, disposable detection.
Ready to deploy on Railway/Render and list on RapidAPI / Zyla API Hub.
"""

import re
import dns.resolver
from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import time

app = FastAPI(
    title="Email Validator Pro",
    description="Fast, accurate email validation. Checks syntax, DNS, MX records, and disposable emails.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Known disposable email domains (expand this list) ──────────────────────────
DISPOSABLE_DOMAINS = {
    "mailinator.com", "tempmail.com", "guerrillamail.com", "10minutemail.com",
    "throwaway.email", "yopmail.com", "fakeinbox.com", "trashmail.com",
    "dispostable.com", "maildrop.cc", "getairmail.com", "sharklasers.com",
    "guerrillamailblock.com", "grr.la", "guerrillamail.info", "spam4.me",
    "discard.email", "spamgourmet.com", "mailnull.com", "tempr.email",
    "spamhereplease.com", "spamthisplease.com", "anonaddy.com"
}

# ── Free providers (useful metadata for clients) ───────────────────────────────
FREE_PROVIDERS = {
    "gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "icloud.com",
    "aol.com", "protonmail.com", "mail.com", "zoho.com", "live.com"
}

# ── Response Models ────────────────────────────────────────────────────────────
class ValidationResult(BaseModel):
    email: str
    is_valid: bool
    score: int  # 0-100 confidence score
    syntax_valid: bool
    domain_exists: bool
    has_mx_records: bool
    is_disposable: bool
    is_free_provider: bool
    domain: str
    suggestion: Optional[str]  # e.g. "did you mean gmail.com?"
    message: str

class BulkRequest(BaseModel):
    emails: list[str]

class BulkResult(BaseModel):
    total: int
    valid: int
    invalid: int
    results: list[ValidationResult]

# ── Core Validation Logic ──────────────────────────────────────────────────────
EMAIL_REGEX = re.compile(
    r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$'
)

COMMON_DOMAIN_TYPOS = {
    "gmial.com": "gmail.com",
    "gmaill.com": "gmail.com",
    "gamil.com": "gmail.com",
    "hotmial.com": "hotmail.com",
    "yahooo.com": "yahoo.com",
    "outlok.com": "outlook.com",
}

def validate_email(email: str) -> ValidationResult:
    email = email.strip().lower()
    
    # 1. Syntax check
    syntax_valid = bool(EMAIL_REGEX.match(email))
    if not syntax_valid:
        return ValidationResult(
            email=email, is_valid=False, score=0,
            syntax_valid=False, domain_exists=False,
            has_mx_records=False, is_disposable=False,
            is_free_provider=False, domain="",
            suggestion=None, message="Invalid email syntax"
        )

    local, domain = email.rsplit("@", 1)

    # 2. Check for typos
    suggestion = COMMON_DOMAIN_TYPOS.get(domain)

    # 3. Disposable check
    is_disposable = domain in DISPOSABLE_DOMAINS

    # 4. Free provider check
    is_free_provider = domain in FREE_PROVIDERS

    # 5. DNS: does domain exist? (A or AAAA record)
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

    # 6. MX records check (most important — proves domain accepts email)
    if domain_exists:
        try:
            dns.resolver.resolve(domain, 'MX')
            has_mx = True
        except Exception:
            pass

    # 7. Score calculation
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
        email=email, is_valid=is_valid, score=score,
        syntax_valid=syntax_valid, domain_exists=domain_exists,
        has_mx_records=has_mx, is_disposable=is_disposable,
        is_free_provider=is_free_provider, domain=domain,
        suggestion=suggestion, message=msg
    )

# ── API Key middleware (simple demo — replace with DB check for production) ────
VALID_KEYS = {"demo-key-free", "pro-key-paid-example"}

def check_api_key(x_rapidapi_key: Optional[str] = Header(None)):
    """RapidAPI injects X-RapidAPI-Key automatically for paying users."""
    if x_rapidapi_key and x_rapidapi_key in VALID_KEYS:
        return x_rapidapi_key
    # In production on RapidAPI, this check isn't needed — they handle it
    return None

# ── Endpoints ──────────────────────────────────────────────────────────────────

@app.get("/", tags=["Info"])
def root():
    return {
        "name": "Email Validator Pro",
        "version": "1.0.0",
        "endpoints": {
            "validate single": "/validate?email=test@example.com",
            "validate bulk":   "/validate/bulk  [POST]",
            "health":          "/health"
        },
        "docs": "/docs"
    }

@app.get("/health", tags=["Info"])
def health():
    return {"status": "ok", "timestamp": time.time()}

@app.get("/validate", response_model=ValidationResult, tags=["Validation"])
def validate_single(
    email: str = Query(..., description="Email address to validate", example="user@gmail.com")
):
    """
    Validate a single email address.
    
    Returns syntax check, DNS lookup, MX record verification,
    disposable email detection, and a 0-100 confidence score.
    """
    return validate_email(email)

@app.post("/validate/bulk", response_model=BulkResult, tags=["Validation"])
def validate_bulk(payload: BulkRequest):
    """
    Validate up to 100 emails in one request.
    
    Returns validation results for each email plus summary stats.
    Ideal for list cleaning and signup form verification.
    """
    if len(payload.emails) > 100:
        raise HTTPException(
            status_code=400,
            detail="Maximum 100 emails per request. Upgrade plan for higher limits."
        )

    results = [validate_email(e) for e in payload.emails]
    valid_count = sum(1 for r in results if r.is_valid)

    return BulkResult(
        total=len(results),
        valid=valid_count,
        invalid=len(results) - valid_count,
        results=results
    )
