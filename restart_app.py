#!/usr/bin/env python3
"""
Restart script untuk aplikasi video translation dengan fix ImageMagick
"""

import subprocess
import sys
import time

def main():
    print("=" * 60)
    print("RESTARTING VIDEO TRANSLATION APP")
    print("=" * 60)
    print()
    print("Fixes applied:")
    print("✓ Removed ImageMagick dependency")
    print("✓ Improved audio processing without FFmpeg")
    print("✓ Better translation API")
    print("✓ ZIP download with video + SRT + instructions")
    print()
    print("Starting application at http://localhost:5000")
    print("=" * 60)

    # Run the main application
    try:
        subprocess.run([sys.executable, "main.py"], check=True)
    except KeyboardInterrupt:
        print("\nApplication stopped by user")
    except Exception as e:
        print(f"Error running application: {e}")

if __name__ == "__main__":
    main()