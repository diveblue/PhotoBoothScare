# qr_generator.py
"""
Generates a QR code image for a given URL.
"""

import qrcode


def generate_qr(url, out_path="qr_code.png", size=6):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=size,
        border=2,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(out_path)
    return out_path
