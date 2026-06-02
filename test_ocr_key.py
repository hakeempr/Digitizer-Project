"""
Run this from your project root to test your OCR.space API key.

Usage (Windows):
    cd D:\digitizer
    venv\Scripts\activate
    python test_ocr_key.py
"""

import os
import sys
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("OCR_SPACE_API_KEY", "").strip()

print()
print("=" * 60)
print(f"OCR.space API Key Test")
print(f"Key: {API_KEY[:4]}...{API_KEY[-4:] if len(API_KEY) > 8 else API_KEY}")
print("=" * 60)

if not API_KEY:
    print("ERROR: OCR_SPACE_API_KEY is empty in your .env file")
    sys.exit(1)

# ── Test with the correct file-upload endpoint ────────────────
# OCR.space requires file upload via multipart POST to parse/image
# The imageurl endpoint needs a different path

print("\nSending test request to OCR.space...")

import io
# Create a tiny 1x1 white PNG in memory (valid image, no file needed)
# PNG header + IHDR + IDAT + IEND
tiny_png = bytes([
    0x89,0x50,0x4E,0x47,0x0D,0x0A,0x1A,0x0A,  # PNG signature
    0x00,0x00,0x00,0x0D,0x49,0x48,0x44,0x52,  # IHDR length + type
    0x00,0x00,0x00,0x01,0x00,0x00,0x00,0x01,  # 1x1 pixels
    0x08,0x02,0x00,0x00,0x00,0x90,0x77,0x53,0xDE,  # 8-bit RGB + CRC
    0x00,0x00,0x00,0x0C,0x49,0x44,0x41,0x54,  # IDAT length + type
    0x08,0xD7,0x63,0xF8,0xFF,0xFF,0x3F,0x00,  # compressed white pixel
    0x05,0xFE,0x02,0xFE,0xDC,0xCC,0x59,0xE7,  # CRC
    0x00,0x00,0x00,0x00,0x49,0x45,0x4E,0x44,  # IEND
    0xAE,0x42,0x60,0x82                        # IEND CRC
])

try:
    resp = requests.post(
        "https://api.ocr.space/parse/image",   # correct endpoint
        data={
            "apikey":    API_KEY,
            "language":  "eng",
            "OCREngine": "1",                  # use engine 1 for this test (fastest)
            "isHandwriting": "false",
        },
        files={"file": ("test.png", io.BytesIO(tiny_png), "image/png")},
        timeout=30,
    )

    print(f"HTTP Status : {resp.status_code}")
    print(f"Response    : {resp.text[:400]}")
    print()

    if resp.status_code == 403:
        print("RESULT: API key is INVALID or EXPIRED")
        print()
        print("Fix:")
        print("  1. Go to https://ocr.space/ocrapi/freekey")
        print("  2. Enter your email and click 'Get API Key'")
        print("  3. Check your email inbox for the key")
        print("  4. Paste it in your .env file as OCR_SPACE_API_KEY=Kyourkey")
        sys.exit(1)

    if resp.status_code == 200:
        data = resp.json()
        exit_code  = data.get("OCRExitCode")
        is_errored = data.get("IsErroredOnProcessing")
        error_msg  = data.get("ErrorMessage", "")

        print(f"OCRExitCode        : {exit_code}")
        print(f"IsErroredOnProcess : {is_errored}")
        print(f"ErrorMessage       : {error_msg}")

        if exit_code in (1, 2) and not is_errored:
            print()
            print("RESULT: API key is VALID and working!")
            print("The image was processed successfully.")
            print("You can now upload handwritten notes in the app.")
        elif "InvalidApiKey" in str(error_msg) or "Unauthorized" in str(error_msg):
            print()
            print("RESULT: API key REJECTED by OCR.space")
            print("Go to https://ocr.space/ocrapi/freekey to get a new key")
        else:
            print()
            print("RESULT: Connected to OCR.space — key appears valid.")
            print("(Empty image gives no text, which is expected)")

except requests.exceptions.ConnectionError:
    print("ERROR: Cannot connect to api.ocr.space")
    print("Check your internet connection")
    sys.exit(1)
except requests.exceptions.Timeout:
    print("ERROR: Request timed out")
    sys.exit(1)
except Exception as e:
    print(f"ERROR: {e}")
    sys.exit(1)

print()
print("=" * 60)
