# Amazon Ads API Setup: Step-by-Step Guide
## Getting Everything Claude Needs to Manage Your Campaigns

---

## STEP 1: Create an Amazon Advertising API Application

You're in the Amazon Developer portal (developer.amazon.com) — good. Now we need to create an app specifically for the Advertising API.

### 1a. Go to "My Apps" (top-left nav in developer.amazon.com)
- Click **"My Apps"**
- Click **"Add New App"** (or "Create a New Security Profile" if prompted)

### 1b. If you don't see advertising-related options:
You may need to register separately at the **Amazon Advertising API portal**:
1. Go to: **advertising.amazon.com**
2. Log in with your seller credentials
3. Look for **"Amazon Ads API"** or **"Partner Network"** in the menu
4. Navigate to developer/API settings

### 1c. Create a Login with Amazon (LWA) Security Profile
The Advertising API uses **Login with Amazon (LWA)** for OAuth 2.0:
1. In the Developer portal, go to **"My Apps"** or **"Login with Amazon"** console
2. Click **"Create a New Security Profile"**
3. Fill in:
   - **Security Profile Name**: "My Amazon Ads Manager" (or whatever you want)
   - **Security Profile Description**: "AI-powered campaign management"
   - **Consent Privacy Notice URL**: Can use a placeholder for personal use
4. Click **Save**
5. You'll get:
   - ✅ **Client ID** (looks like: `amzn1.application-oa2-client.xxxxxxxxxx`)
   - ✅ **Client Secret** (a long string — KEEP THIS SECRET)

**Screenshot what you see after this step (blur any secrets) so I can help if you get stuck.**

---

## STEP 2: Link Your LWA App to Amazon Advertising API

### 2a. Go to the Amazon Advertising API Console
1. Visit: **advertising.amazon.com**
2. Click your account menu → look for **API access** or **Developer tools**
3. Or try: Navigate to **Campaign Manager** → **Measurement & Reporting** → **Amazon Advertising API**

### 2b. Register your LWA Security Profile for the Ads API
1. You should see a section to **connect** or **register** your LWA application
2. Select the Security Profile you created in Step 1
3. Set the **API authorization** scope (you want full Sponsored Products access)
4. Since you're already verified/accepted (as you mentioned), this should be straightforward

---

## STEP 3: Complete the OAuth 2.0 Flow to Get a Refresh Token

This is the trickiest step. The refresh token lets Claude authenticate without you logging in each time.

### Option A: Use Amazon's Authorization URL (Manual)

1. Open this URL in your browser (replace YOUR_CLIENT_ID):
```
https://www.amazon.com/ap/oa?client_id=YOUR_CLIENT_ID&scope=advertising::campaign_management&response_type=code&redirect_uri=https://localhost/callback
```

2. Log in and **authorize** the application
3. You'll be redirected to something like:
```
https://localhost/callback?code=AUTHORIZATION_CODE&scope=advertising::campaign_management
```
4. Copy the `code` value (the AUTHORIZATION_CODE)
5. Then exchange it for tokens using curl (replace placeholders):

```bash
curl -X POST "https://api.amazon.com/auth/o2/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=authorization_code" \
  -d "code=YOUR_AUTHORIZATION_CODE" \
  -d "client_id=YOUR_CLIENT_ID" \
  -d "client_secret=YOUR_CLIENT_SECRET" \
  -d "redirect_uri=https://localhost/callback"
```

6. The response will contain:
   - ✅ **access_token** (expires in 1 hour — we don't store this)
   - ✅ **refresh_token** (long-lived — THIS IS WHAT WE NEED)

### Option B: I Can Help You Run the OAuth Flow
If you share your Client ID (NOT the client secret in chat — we'll use env vars), I can help you script this locally so credentials stay on your machine.

---

## STEP 4: Get Your Advertising Profile ID(s)

Once you have an access token, we can retrieve your profile IDs:

```bash
curl -X GET "https://advertising-api.amazon.com/v2/profiles" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Amazon-Advertising-API-ClientId: YOUR_CLIENT_ID"
```

This returns your profile(s) — usually one per marketplace (US, CA, etc.).
Each profile has:
- ✅ **profileId** (a number like `1234567890`)
- **countryCode** (US, CA, UK, etc.)
- **accountInfo** (seller vs. vendor, marketplace)

---

## STEP 5: Store Credentials Securely

**DO NOT paste credentials into chat or commit them to GitHub.**

Instead, create a `.env` file locally:

```bash
# Create .env file (this will be gitignored)
touch .env
```

```env
# .env (NEVER commit this file)
AMAZON_ADS_CLIENT_ID=amzn1.application-oa2-client.xxxxxxxxxx
AMAZON_ADS_CLIENT_SECRET=your-client-secret-here
AMAZON_ADS_REFRESH_TOKEN=your-refresh-token-here
AMAZON_ADS_PROFILE_ID=1234567890
AMAZON_ADS_REGION=NA
```

I'll configure Claude Code to read from this file via MCP server configuration.

---

## STEP 6: Other Data I Need (Non-API)

These don't require API setup — just manual downloads from Seller Central:

### From Seller Central (sellercentral.amazon.com):

**A. Sponsored Products Bulk Download**
1. Go to: **Campaign Manager** → **Sponsored Products**
2. Click **"Bulk Operations"** (top of page or sidebar)
3. Click **"Create spreadsheet for download"**
4. Select: Last 60 days, All campaigns
5. Download the .xlsx file

**B. Search Term Report**
1. Go to: **Campaign Manager** → **Measurement & Reporting** → **Sponsored Products Reports**
2. Report type: **Search Term**
3. Date range: **Last 60 days**
4. Download

**C. Business Report (for TACoS)**
1. Go to: **Reports** → **Business Reports**
2. Select: **Detail Page Sales and Traffic by Child Item** (by ASIN)
3. Date range: **Last 30 days**
4. Download

**D. Brand Analytics (if Brand Registered)**
1. Go to: **Brands** → **Brand Analytics**
2. Select: **Search Query Performance**
3. Download the most recent available period

**E. FBA Inventory Report**
1. Go to: **Inventory** → **FBA Inventory**
2. Download current inventory

### From You (Business Info):

For each product you're advertising, I need:
- **ASIN**
- **Product cost** (landed cost per unit, including FBA fees)
- **Selling price**
- **Target ACoS** (or I can calculate break-even from margins)
- **Monthly ad budget** (total)
- **Current stage**: Launch / Growth / Optimization / Maintenance

### Your Preferences:
- **Autonomy level**: How much should Claude do without asking?
  - Level 1: Recommend only, you approve everything
  - Level 2: Auto-execute routine (bids, negations), approve strategic
  - Level 3: Auto-execute everything within guardrails, daily summary
  - Level 4: Fully autonomous, weekly review
- **Risk tolerance**: Conservative / Moderate / Aggressive
- **Top 3-5 competitor ASINs** (products you compete against)

---

## Summary Checklist

```
API Credentials:
[ ] Client ID (from LWA Security Profile)
[ ] Client Secret (from LWA Security Profile)
[ ] Refresh Token (from OAuth 2.0 flow)
[ ] Profile ID(s) (from Profiles API call)

Campaign Data (Manual Downloads):
[ ] Sponsored Products Bulk Download (.xlsx)
[ ] Search Term Report (60 days)
[ ] Business Report (30 days)
[ ] Brand Analytics - Search Query Performance (if available)
[ ] FBA Inventory Report

Business Information:
[ ] ASIN(s) being advertised
[ ] Product cost per unit
[ ] Selling price(s)
[ ] Target ACoS per product
[ ] Monthly ad budget
[ ] Product lifecycle stage(s)

Preferences:
[ ] Autonomy level (1-4)
[ ] Risk tolerance
[ ] Competitor ASINs
[ ] Any actions Claude should NEVER take without asking
```

---

## Where You Are Right Now

✅ Amazon Developer account — verified and accepted
✅ In the developer portal (developer.amazon.com)
🔲 Need to create LWA Security Profile (for Client ID + Secret)
🔲 Need to complete OAuth flow (for Refresh Token)
🔲 Need to get Profile ID(s)
🔲 Need to download campaign data from Seller Central
🔲 Need to provide product/business info

**Next action: Go to "My Apps" or "Login with Amazon" in the developer portal and create a Security Profile. Screenshot what you see and I'll guide you through it.**
