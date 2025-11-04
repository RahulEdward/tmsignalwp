# Database Status Report

**Date:** November 4, 2025  
**Database:** SQLite (Local: `sqlite:///db/algo.db`)

---

## 📊 Current Database State

### 1. Users Table
```
Username: erahul41
User ID: LLVR1277
Broker APIKey: z6DaAedv
Approved: True
```

### 2. ApiKeys Table (App API Keys)
```
User ID: LLVR1277
App API Key: IkxMVlIxMjc3Ig.aQoFOA.8QqhykjIcxlNLQ1536-grRcHl-E
```

### 3. AuthTokens Table (JWT Tokens)
```
Username: erahul41
User ID: LLVR1277
Access Token: eyJhbGciOiJIUzUxMiJ9.eyJ1c2VybmFtZSI6IkxMVlIxMjc3I... (JWT)
Feed Token: eyJhbGciOiJIUzUxMiJ9.eyJ1c2VybmFtZSI6IkxMVlIxMjc3I... (JWT)
Refresh Token: None ❌
Expires At: None ❌
Is Active: True ✅
```

### 4. Auth Table (Legacy)
```
Name: erahul41
Auth Token: (empty)
Is Revoked: True ❌
```

---

## ⚠️ Issues Found

### 1. No Refresh Token
- **Issue:** `refresh_token` is `None` in AuthTokens table
- **Impact:** Cannot refresh expired JWT tokens
- **Solution:** Store refresh token during login

### 2. No Token Expiry
- **Issue:** `expires_at` is `None`
- **Impact:** Tokens never expire (security risk)
- **Solution:** Set expiry time during login (typically 24 hours)

### 3. Auth Table Token Revoked
- **Issue:** Legacy auth token is revoked
- **Impact:** Old auth system won't work
- **Status:** This is OK if using new AuthTokens table

### 4. Railway Database Mismatch
- **Issue:** Local SQLite database ≠ Railway PostgreSQL database
- **Impact:** API key validation fails on Railway
- **Solution:** Railway needs to use PostgreSQL with same data

---

## 🔧 Fixes Needed

### Fix 1: Update Login to Store Refresh Token
**File:** `blueprints/auth.py`

Current code stores tokens but doesn't capture refresh_token from AngelOne API.

**AngelOne API Response:**
```json
{
  "status": true,
  "data": {
    "jwtToken": "eyJ...",
    "refreshToken": "eyJ...",  // ← This is not being stored
    "feedToken": "eyJ..."
  }
}
```

### Fix 2: Set Token Expiry
Add expiry time when storing tokens (typically 24 hours or based on broker session).

### Fix 3: Railway Database
Railway is using PostgreSQL, not SQLite. Need to:
1. Check Railway environment variables
2. Ensure PostgreSQL has the same user and API key data
3. Or sync local SQLite data to Railway PostgreSQL

---

## 🧪 Test Results

### Local Test (SQLite)
```
✅ App API Key: IkxMVlIxMjc3Ig.aQoFOA.8QqhykjIcxlNLQ1536-grRcHl-E
✅ User ID: LLVR1277
✅ JWT Token: Available
❌ Refresh Token: Missing
❌ Token Expiry: Not set
```

### Railway Test (PostgreSQL)
```
❌ API Key Validation: Failed (403 Invalid API key)
❌ Reason: Railway database doesn't have the API key
```

---

## 📝 Recommended Actions

1. **Immediate:** Check Railway PostgreSQL database
   - Login to Railway dashboard
   - Check if user `LLVR1277` exists
   - Check if API key exists in `api_keys` table

2. **Short-term:** Fix refresh token storage
   - Update `blueprints/auth.py` login function
   - Store `refreshToken` from AngelOne API response

3. **Short-term:** Set token expiry
   - Calculate expiry based on broker session (3:30 AM IST)
   - Store in `expires_at` field

4. **Long-term:** Database sync
   - Create migration script to sync SQLite → PostgreSQL
   - Or use same database for local and Railway

---

## 🔗 API Key Types

### 1. Broker API Key (AngelOne)
- **Purpose:** Authenticate with AngelOne broker
- **Storage:** `users.apikey` column
- **Value:** `z6DaAedv`
- **Used in:** Order placement API calls to AngelOne

### 2. App API Key (TM-Algo)
- **Purpose:** Authenticate webhook requests to TM-Algo
- **Storage:** `api_keys.api_key` column
- **Value:** `IkxMVlIxMjc3Ig.aQoFOA.8QqhykjIcxlNLQ1536-grRcHl-E`
- **Used in:** TradingView webhook authentication

### 3. JWT Token (Session)
- **Purpose:** User session authentication
- **Storage:** `auth_tokens.access_token` column
- **Value:** `eyJhbGciOiJIUzUxMiJ9...`
- **Used in:** Web dashboard authentication

---

## 🎯 Current Problem

**Railway webhook fails because:**
1. Railway uses PostgreSQL (not SQLite)
2. PostgreSQL database doesn't have the API key
3. Local SQLite has the key but Railway can't access it

**Solution:**
- Add user and API key to Railway PostgreSQL database
- Or use Railway's database URL in local `.env` for testing
