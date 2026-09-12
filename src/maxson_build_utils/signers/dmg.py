# src/maxson_build_utils/signers/dmg.py
import subprocess
import os

def sign_dmg(dmg_path: str, p12_base64: str, p12_password: str):
    """
    Signs a DMG cross-platform using the `rcodesign` binary.
    Does not require Xcode, macOS, or a local Keychain.
    """
    # 1. Decode your reusable P12 certificate to a temp file
    # 2. Call out to rcodesign:
    #    rcodesign sign --p12-file cert.p12 --p12-password secret paths/to/assets
    subprocess.run(["rcodesign", "sign", "--p12-file", p12_base64, "--p12-password", p12_password, dmg_path])

