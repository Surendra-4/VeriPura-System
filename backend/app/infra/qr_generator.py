import base64
import io
from pathlib import Path
from typing import Optional

import qrcode
from PIL import Image

from app.config import get_settings
from app.logger import logger


class QRGeneratorError(Exception):
    """Raised when QR generation fails"""

    pass


class QRGenerator:
    """
    Generate QR codes for batch traceability.

    QR codes encode the verification URL, allowing instant lookup
    of validation records by scanning physical labels.
    """

    def __init__(self):
        self.settings = get_settings()
        self.qr_dir = self.settings.upload_dir.parent / "qr_codes"
        self.qr_dir.mkdir(parents=True, exist_ok=True)

    def _get_verification_url(self, batch_id: str) -> str:
        """
        Construct verification URL for batch ID.

        In production, replace localhost with actual domain.
        """
        # TODO: Replace with actual domain from environment variable
        base_url = self.settings.qr_base_url  # Will be configured in deployment
        return f"{base_url}/api/v1/verify/{batch_id}"

    def _get_qr_path(self, batch_id: str) -> Path:
        """
        Get storage path for QR code image.
        Uses same sharding strategy as document storage.
        """
        # Shard by first 4 chars of batch ID (after BATCH- prefix)
        # BATCH-20260207-A3F5E8 → 20/26/BATCH-20260207-A3F5E8.png
        parts = batch_id.split("-")
        if len(parts) >= 3:
            prefix1 = parts[1][:2]  # First 2 digits of date
            prefix2 = parts[1][2:4]  # Next 2 digits of date
        else:
            prefix1 = "00"
            prefix2 = "00"

        qr_path = self.qr_dir / prefix1 / prefix2 / f"{batch_id}.png"
        qr_path.parent.mkdir(parents=True, exist_ok=True)
        return qr_path

    def generate(
        self,
        batch_id: str,
        size: int = 300,
        error_correction: int = qrcode.constants.ERROR_CORRECT_H,
    ) -> Path:
        """
        Generate QR code for batch ID.

        Args:
            batch_id: Batch identifier to encode
            size: Image size in pixels (square)
            error_correction: Error correction level (L, M, Q, H)
                - L: 7% error correction
                - M: 15% error correction
                - Q: 25% error correction
                - H: 30% error correction (recommended for physical labels)

        Returns:
            Path to generated QR code image

        Raises:
            QRGeneratorError: If generation fails
        """
        try:
            qr_path = self._get_qr_path(batch_id)

            # Check if QR already exists (avoid regeneration)
            if qr_path.exists():
                logger.debug(f"QR code already exists: {batch_id}")
                return qr_path

            # Create verification URL
            verification_url = self._get_verification_url(batch_id)

            # Generate QR code
            qr = qrcode.QRCode(
                version=None,  # Auto-size based on data
                error_correction=error_correction,
                box_size=10,  # Size of each "box" in pixels
                border=4,  # Minimum required border (4 boxes)
            )

            qr.add_data(verification_url)
            qr.make(fit=True)

            # Create image
            img = qr.make_image(fill_color="black", back_color="white")

            # Resize to desired dimensions
            img = img.resize((size, size), Image.Resampling.LANCZOS)

            # Save to disk
            img.save(qr_path, format="PNG")

            logger.info(f"QR code generated: {batch_id} → {qr_path}")
            return qr_path

        except Exception as e:
            logger.error(f"QR generation failed for {batch_id}: {str(e)}")
            raise QRGeneratorError(f"Failed to generate QR code: {str(e)}") from e

    def get_qr_as_base64(self, batch_id: str) -> str:
        """
        Get QR code as base64-encoded string (for embedding in API responses).

        Args:
            batch_id: Batch identifier

        Returns:
            Base64-encoded PNG data (without data URI prefix)

        Raises:
            FileNotFoundError: If QR code doesn't exist
        """
        qr_path = self._get_qr_path(batch_id)

        if not qr_path.exists():
            raise FileNotFoundError(f"QR code not found for batch: {batch_id}")

        with open(qr_path, "rb") as f:
            img_data = f.read()

        return base64.b64encode(img_data).decode("utf-8")

    def get_qr_path(self, batch_id: str) -> Optional[Path]:
        """
        Get path to existing QR code.

        Returns:
            Path if exists, None otherwise
        """
        qr_path = self._get_qr_path(batch_id)
        return qr_path if qr_path.exists() else None

    def generate_with_logo(
        self, batch_id: str, logo_path: Optional[Path] = None, size: int = 300
    ) -> Path:
        """
        Generate QR code with embedded logo (optional, for branding).

        Args:
            batch_id: Batch identifier
            logo_path: Path to logo image (will be centered in QR)
            size: Final image size

        Returns:
            Path to generated QR code

        Note: Logo should be small (~20% of QR size) to maintain scannability.
        """
        # Generate base QR code
        qr_path = self.generate(batch_id, size=size)

        if logo_path is None or not logo_path.exists():
            return qr_path  # No logo, return standard QR

        try:
            # Open QR and logo
            qr_img = Image.open(qr_path).convert("RGBA")
            logo_img = Image.open(logo_path).convert("RGBA")

            # Calculate logo size (20% of QR size)
            logo_size = int(size * 0.2)
            logo_img = logo_img.resize((logo_size, logo_size), Image.Resampling.LANCZOS)

            # Calculate center position
            pos = ((size - logo_size) // 2, (size - logo_size) // 2)

            # Paste logo (with alpha transparency)
            qr_img.paste(logo_img, pos, logo_img)

            # Save
            qr_img.save(qr_path, format="PNG")

            logger.info(f"QR code with logo generated: {batch_id}")
            return qr_path

        except Exception as e:
            logger.warning(f"Failed to add logo to QR: {str(e)}")
            return qr_path  # Return QR without logo on error
