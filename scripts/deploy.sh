#!/bin/bash
# Deploy to Railway

echo "🚀 StormCloud → Railway"
echo ""

if ! command -v railway &> /dev/null; then
    echo "❌ Install Railway CLI:"
    echo "   npm i -g @railway/cli"
    exit 1
fi

echo "🔐 Logging in..."
railway login

echo "📦 Initializing project..."
railway init

echo "🗄️  Adding PostgreSQL..."
railway add --plugin postgresql

echo "🗄️  Adding Redis..."
railway add --plugin redis

echo "⚙️  Set these in Railway dashboard:"
echo "   - OPENROUTER_API_KEY"
echo "   - STRIPE_SECRET_KEY"
echo "   - JWT_SECRET"
echo ""

echo "🚀 Deploying..."
railway up

echo ""
echo "✅ Deployed!"
echo ""
echo "Get your URL:"
echo "   railway domain"
