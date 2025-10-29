# 🚀 Deployment Guide - philipwright.me

## Quick Deploy to Cloudflare Pages

### Option 1: Web Dashboard (Easiest - 5 minutes)

1. **Go to Cloudflare Dashboard**
   ```
   https://dash.cloudflare.com
   ```

2. **Create Pages Project**
   - Click **"Pages"** in left sidebar
   - Click **"Create a project"**
   - Click **"Connect to Git"**
   - Select **GitHub**
   - Authorize Cloudflare if needed

3. **Select Repository**
   - Choose: `pdubbbbbs/claude-code-server`
   - Click **"Begin setup"**

4. **Configure Build**
   ```
   Project name: claude-code-server
   Production branch: main
   Framework preset: None
   Build command: (leave blank)
   Build output directory: docs
   Root directory: / (or leave blank)
   ```

5. **Deploy**
   - Click **"Save and Deploy"**
   - Wait ~2 minutes for deployment
   - Note your URL: `https://claude-code-server.pages.dev`

6. **Add Custom Domain**
   - After deployment: **Settings → Custom domains**
   - Click **"Add a custom domain"**
   - Enter: `claude.philipwright.me` (or your preferred subdomain)
   - Click **"Continue"** - Cloudflare auto-configures DNS
   - Wait ~5 minutes for SSL certificate

### Option 2: Command Line (via Wrangler)

**Prerequisites:**
- Cloudflare API Token: https://dash.cloudflare.com/profile/api-tokens
  - Template: "Edit Cloudflare Pages"
  - Or custom with: `Account → Cloudflare Pages → Edit`

**Steps:**

```bash
# 1. Set API token
export CLOUDFLARE_API_TOKEN="your_token_here"

# 2. Deploy
cd /home/me52/claude-code-server
~/.local/bin/wrangler pages deploy docs --project-name=claude-code-server

# 3. Add custom domain (via dashboard or API)
# Go to: https://dash.cloudflare.com → Pages → Settings → Custom domains
```

### Option 3: GitHub Actions (Automated on Push)

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Cloudflare Pages

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Deploy to Cloudflare Pages
        uses: cloudflare/pages-action@v1
        with:
          apiToken: ${{ secrets.CLOUDFLARE_API_TOKEN }}
          accountId: ${{ secrets.CLOUDFLARE_ACCOUNT_ID }}
          projectName: claude-code-server
          directory: docs
          gitHubToken: ${{ secrets.GITHUB_TOKEN }}
```

Add secrets in GitHub:
- `CLOUDFLARE_API_TOKEN`
- `CLOUDFLARE_ACCOUNT_ID` (from Cloudflare dashboard URL)

---

## ✅ Verification

After deployment, test:

```bash
curl https://claude.philipwright.me
curl https://claude-code-server.pages.dev
```

Both should return the documentation page.

---

## 🌐 DNS Configuration

Cloudflare automatically creates:
```
Type: CNAME
Name: claude
Target: claude-code-server.pages.dev
Proxy: Enabled (orange cloud)
```

---

## 🎯 Recommended Subdomains

- `claude.philipwright.me` - Documentation
- `api.philipwright.me` - Future API server
- `git.philipwright.me` - Future Gitea instance

---

## 📝 Notes

- Documentation auto-deploys on GitHub push (if using Option 3)
- Free SSL certificate included
- Cloudflare CDN for fast global access
- No server management required
- Static site hosting (perfect for docs)

---

## 🚀 Next Steps

1. Deploy docs → **Option 1 (easiest)**
2. Set up custom domain → `claude.philipwright.me`
3. Test: Visit https://claude.philipwright.me
4. Share the link!

For Gitea or running the actual FastAPI server, you'll need a VPS or Cloudflare Workers (paid).
