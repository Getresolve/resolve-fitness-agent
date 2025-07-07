#!/bin/bash

echo "🚀 Deploying Resolve Fitness Lead Agent..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed"
    exit 1
fi

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo "⬇️ Installing dependencies..."
pip install -r requirements.txt

# Set up cron job for daily runs
echo "⏰ Setting up daily automation..."
(crontab -l 2>/dev/null; echo "0 9 * * * cd $(pwd) && ./venv/bin/python main.py") | crontab -

echo "✅ Deployment complete!"
echo "📊 The agent will run daily at 9 AM JST"
echo "🏃‍♂️ To run manually: python main.py"
echo "📁 Check leads.json for your lead database"
