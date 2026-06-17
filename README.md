# Email Validator Pro API

Validates emails in real-time: syntax, DNS, MX records, disposable detection.

---

## Run locally

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

Then open: http://localhost:8000/docs

### Test it:
```bash
# Single email
curl "http://localhost:8000/validate?email=test@gmail.com"

# Bulk
curl -X POST "http://localhost:8000/validate/bulk" \
  -H "Content-Type: application/json" \
  -d '{"emails": ["good@gmail.com", "fake@mailinator.com", "bad@notreal12345.xyz"]}'
```

---

## Deploy to Railway (free, 5 minutes)

1. Push this folder to a GitHub repo
2. Go to https://railway.app → New Project → Deploy from GitHub
3. Select the repo → Railway auto-detects Dockerfile
4. Done. You get a public URL like `https://email-validator-pro.up.railway.app`

---

## Deploy to Render (alternative, also free)

1. Push to GitHub
2. Go to https://render.com → New Web Service
3. Connect repo → Runtime: Docker → Free plan
4. Done. URL: `https://email-validator-pro.onrender.com`

---

## List on RapidAPI / Zyla API Hub

### RapidAPI steps:
1. https://rapidapi.com/provider → Sign up as Provider
2. "Add New API" → enter your Railway/Render URL as the base URL
3. Add your endpoints: GET /validate and POST /validate/bulk
4. Set pricing plans (see below)
5. Submit for review → usually approved in 24-48 hours

### Zyla API Hub (https://zylalabs.com):
- Similar process, stricter quality check, but better visibility
- Requires 99.8% uptime (Railway/Render handles this)

---

## Pricing strategy (Freemium model)

| Plan | Price | Limit |
|------|-------|-------|
| Free | $0 | 100 calls/month |
| Basic | $9/month | 5,000 calls/month |
| Pro | $29/month | 50,000 calls/month |
| Ultra | $79/month | 500,000 calls/month |

**Why this works:** Free plan gets you subscribers fast. Even 5% converting to Basic = money while you sleep.

---

## Expand the API (grow revenue)

Once you have users, add these endpoints:
- `GET /validate/phone` — phone number validation (big demand)
- `GET /validate/address` — address validation
- `GET /typo-check` — "did you mean gmail.com?"

Each new endpoint = reason to upgrade to higher plan.

---

## Expected revenue timeline

- Month 1-2: 0-50 free users → $0-50
- Month 3-4: 200+ users → $100-300/month
- Month 6+: snowball → $500-2000/month

The key: **don't touch it after deployment**. RapidAPI handles billing, users, and payments.
