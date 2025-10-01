#!/bin/bash

echo "🚀 Starting Document Knowledge Base..."
echo

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ .env file not found!"
    echo "Please copy .env.example to .env and add your OpenAI API key"
    echo
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install requirements if needed
if [ ! -f "venv/bin/streamlit" ]; then
    echo "📦 Installing requirements..."
    pip install -r requirements.txt
fi

# Run the application
echo "🚀 Starting Streamlit application..."
echo
echo "Open your browser and go to: http://localhost:8501"
echo "Press Ctrl+C to stop the application"
echo

streamlit run src/app.py