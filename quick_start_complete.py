#!/usr/bin/env python3
"""
QUICK START - COMPLETE INTEGRATION
Run this to fix everything and start the demo-ready system
Save as: quick_start_complete.py
Run: python quick_start_complete.py
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def main():
    """Complete quick start with all fixes"""
    
    print("""
🏥 MEDICARE AI SCHEDULING - COMPLETE INTEGRATION QUICK START
==========================================================

This will:
✅ Fix all critical issues identified in tests
✅ Update database schema
✅ Create visual feedback system  
✅ Launch enhanced UI with live monitoring
✅ Enable all integrations with demo feedback

Starting in 3 seconds...
""")
    
    time.sleep(3)
    
    print("🔧 Step 1: Applying all critical fixes...")
    try:
        result = subprocess.run([sys.executable, "fix_complete_integration.py"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ All fixes applied successfully")
        else:
            print(f"⚠️ Some fixes had issues: {result.stderr}")
    except Exception as e:
        print(f"❌ Fix script failed: {e}")
        print("Continuing with manual fixes...")
    
    print("\n🚀 Step 2: Starting enhanced application...")
    
    try:
        # Try the fixed main entry point
        if Path("main_fixed.py").exists():
            print("Using enhanced main entry point...")
            subprocess.run([sys.executable, "main_fixed.py"])
        else:
            print("Using original streamlit app...")
            subprocess.run([sys.executable, "-m", "streamlit", "run", "ui/streamlit_app.py", 
                          "--server.port", "8501"])
    except KeyboardInterrupt:
        print("\n👋 Application stopped. Thank you!")
    except Exception as e:
        print(f"❌ Application failed: {e}")
        print("\n🔧 Troubleshooting:")
        print("1. Check if all dependencies are installed: pip install -r requirements.txt")
        print("2. Verify .env file has GOOGLE_API_KEY")
        print("3. Try: python -m streamlit run ui/streamlit_app.py")

if __name__ == "__main__":
    main()