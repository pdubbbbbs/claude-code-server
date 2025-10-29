#!/bin/bash
# Automated Cloudflare Pages Deployment Script

set -e

echo "🚀 Claude Code Server - Cloudflare Pages Deployment"
echo "=================================================="
echo ""

# Check if wrangler is installed
if ! command -v wrangler &> /dev/null; then
    echo "📦 Installing Wrangler CLI..."
    npm install -g wrangler --prefix ~/.local
    export PATH="$HOME/.local/bin:$PATH"
fi

# Add to PATH if not already there
export PATH="$HOME/.local/bin:$PATH"

echo "✅ Wrangler version: $(wrangler --version)"
echo ""

# Check if logged in
echo "🔑 Checking Cloudflare authentication..."
if ! wrangler whoami &> /dev/null; then
    echo ""
    echo "⚠️  Not logged in to Cloudflare"
    echo ""
    echo "Please choose authentication method:"
    echo "1. OAuth (opens browser)"
    echo "2. API Token (paste token)"
    echo ""
    read -p "Choice (1 or 2): " auth_choice
    
    if [ "$auth_choice" = "1" ]; then
        echo ""
        echo "Opening browser for OAuth login..."
        wrangler login
    else
        echo ""
        echo "Get your API token from: https://dash.cloudflare.com/profile/api-tokens"
        echo "Required permissions: Account > Cloudflare Pages > Edit"
        echo ""
        read -sp "Paste your Cloudflare API Token: " CF_API_TOKEN
        echo ""
        export CLOUDFLARE_API_TOKEN="$CF_API_TOKEN"
    fi
fi

echo ""
echo "✅ Authenticated with Cloudflare"
echo ""

# Get project name
read -p "📝 Project name (default: claude-code-server): " PROJECT_NAME
PROJECT_NAME=${PROJECT_NAME:-claude-code-server}

# Get custom domain
read -p "🌐 Custom domain (e.g., claude.philipwright.me) [optional]: " CUSTOM_DOMAIN

echo ""
echo "🚀 Deploying to Cloudflare Pages..."
echo "   Project: $PROJECT_NAME"
echo "   Directory: docs/"
[ -n "$CUSTOM_DOMAIN" ] && echo "   Domain: $CUSTOM_DOMAIN"
echo ""

# Deploy
cd "$(dirname "$0")"
wrangler pages deploy docs --project-name="$PROJECT_NAME" --branch=main

echo ""
echo "✅ Deployment complete!"
echo ""
echo "🔗 Your site is live at:"
wrangler pages project list | grep "$PROJECT_NAME"

if [ -n "$CUSTOM_DOMAIN" ]; then
    echo ""
    echo "📌 To add custom domain:"
    echo "   1. Go to: https://dash.cloudflare.com"
    echo "   2. Pages → $PROJECT_NAME → Settings → Custom domains"
    echo "   3. Add: $CUSTOM_DOMAIN"
    echo "   4. DNS will be auto-configured"
fi

echo ""
echo "🎉 Done! Your documentation is now live!"
