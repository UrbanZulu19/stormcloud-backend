#!/bin/bash
# Quick local development setup

echo "🔧 StormCloud Local Setup"
echo ""

if [ ! -f .env ]; then
    cp .env.example .env
    echo "📝 Created .env - EDIT IT AND ADD YOUR KEYS!"
    echo ""
fi

# Backend
if [ -f backend/requirements.txt ]; then
    echo "📦 Installing Python dependencies..."
    cd backend
    pip install -r requirements.txt
    cd ..
    echo "✅ Backend ready"
else
    echo "⚠️  No backend/requirements.txt found"
fi

# Frontend
if [ -f frontend/package.json ]; then
    echo "📦 Installing Node dependencies..."
    cd frontend
    npm install
    cd ..
    echo "✅ Frontend ready"
else
    echo "⚠️  No frontend/package.json found"
fi

# Docker services
if command -v docker-compose &> /dev/null; then
    echo "🐳 Starting database and redis..."
    docker-compose up -d db redis
    echo "✅ Services running"
else
    echo "⚠️  Docker not found"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "Start dev servers:"
echo "   cd backend && uvicorn main:app --reload"
echo "   cd frontend && npm start"
