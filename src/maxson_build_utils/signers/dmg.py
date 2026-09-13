# src/maxson_build_utils/signers/dmg.py
import base64
import os
import subprocess
import tempfile
"""
Alternatively, use YML runner recipe, greg.
"""
def sign_dmg(dmg_path: str, p12_base64: str, p12_password: str):
    """
    Signs a DMG cross-platform using the `rcodesign` binary.
    Decodes the base64 string on the fly without cluttering the workspace.
    """
    if not os.path.exists(dmg_path):
        raise FileNotFoundError(f"Target DMG not found at: {dmg_path}")

    # Decode the base64 payload into raw p12 bytes
    try:
        p12_data = base64.b64decode(p12_base64)
    except Exception as e:
        raise ValueError("Failed to decode base64 certificate string.") from e

    # Create a secure temporary file for rcodesign to read
    # delete=False ensures it persists until we explicitly wipe it post-subprocess
    with tempfile.NamedTemporaryFile(delete=False, suffix=".p12") as temp_p12:
        try:
            temp_p12.write(p12_data)
            temp_p12.close()  # Close handle so subprocess can read it cleanly

            # Invoke indygreg's rcodesign tool
            result = subprocess.run(
                [
                    "rcodesign", "sign",
                    "--p12-file", temp_p12.name,
                    "--p12-password", p12_password,
                    dmg_path
                ],
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                raise RuntimeError(f"rcodesign failed: {result.stderr}")
                
            print(f"Successfully signed DMG at: {dmg_path}")

        finally:
            # Securely erase the raw cert file from the runner disk immediately
            if os.path.exists(temp_p12.name):
                os.unlink(temp_p12.name)
