#!/usr/bin/env python3
"""
Test RTSP ONVIF token fetching locally
"""

import sys
import os

sys.path.insert(0, "src")


def test_onvif_token():
    """Test ONVIF token fetching"""
    try:
        from photobooth.managers.rtsp_camera_manager import get_rtsp_url_onvif

        # Test with your camera
        camera_ip = "192.168.86.38"
        username = "admin"
        password = "dive2000"

        print(f"Testing ONVIF token fetch from {camera_ip}...")
        print(f"Using credentials: {username}/*****")

        rtsp_url = get_rtsp_url_onvif(camera_ip, username, password)

        if rtsp_url:
            print(f"✅ SUCCESS! Got RTSP URL with token:")
            print(f"   {rtsp_url}")
            return rtsp_url
        else:
            print("❌ Failed to get RTSP URL via ONVIF")
            return None

    except ImportError as e:
        print(f"❌ Missing ONVIF package: {e}")
        print("Install with: pip install onvif_zeep")
        return None
    except Exception as e:
        print(f"❌ ONVIF error: {e}")
        return None


if __name__ == "__main__":
    print("RTSP ONVIF Token Test")
    print("=" * 30)

    url = test_onvif_token()

    if url:
        print("\n✅ ONVIF token fetching works!")
        print("The PhotoBooth should now connect to the secondary camera properly.")
    else:
        print("\n❌ ONVIF token fetching failed.")
        print("The camera might not support ONVIF or credentials are incorrect.")
