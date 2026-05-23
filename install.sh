#!/bin/bash
set -e
echo "✿ Installing Misho Notes..."
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
echo ""
echo "✅ Done! Run with:"
echo "  source venv/bin/activate"
echo "  MISHO_PASSWORD=your_password python app.py"
