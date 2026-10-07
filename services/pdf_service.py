import os
from typing import List, Optional
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import Paragraph
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from utils.logging import get_logger

logger = get_logger("linkforge.pdf_service")


class PdfService:
    """Converts images into multi-page PDF documents."""

    @classmethod
    def images_to_pdf(
        cls,
        image_paths: List[str],
        output_pdf_path: str,
        title: Optional[str] = None,
        caption: Optional[str] = None,
        include_caption: bool = False
    ) -> bool:
        """Convert a list of image file paths into a single PDF document.
        
        Optionally prepends a clean title & caption cover page if include_caption is True.
        Each image becomes one page in the PDF, preserving orientation and aspect ratio.
        """
        if not image_paths:
            logger.warning("No image paths provided for PDF generation.")
            return False

        try:
            os.makedirs(os.path.dirname(output_pdf_path), exist_ok=True)
            c = canvas.Canvas(output_pdf_path)

            # Optional Cover Page if caption requested
            if include_caption and (title or caption):
                c.setPageSize(A4)
                page_w, page_h = A4
                margin = 54  # 0.75 inch margin
                avail_w = page_w - (margin * 2)

                styles = getSampleStyleSheet()
                title_style = ParagraphStyle(
                    "CoverTitle",
                    parent=styles["Heading1"],
                    fontName="Helvetica-Bold",
                    fontSize=22,
                    leading=28,
                    textColor=colors.HexColor("#0f172a"),
                    spaceAfter=15
                )
                body_style = ParagraphStyle(
                    "CoverBody",
                    parent=styles["Normal"],
                    fontName="Helvetica",
                    fontSize=11,
                    leading=17,
                    textColor=colors.HexColor("#334155")
                )

                cursor_y = page_h - margin

                if title:
                    safe_title = title.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                    p_title = Paragraph(safe_title, title_style)
                    tw, th = p_title.wrapOn(c, avail_w, cursor_y)
                    cursor_y -= th
                    p_title.drawOn(c, margin, cursor_y)
                    cursor_y -= 15

                    # Divider line
                    c.setStrokeColor(colors.HexColor("#cbd5e1"))
                    c.setLineWidth(1)
                    c.line(margin, cursor_y, page_w - margin, cursor_y)
                    cursor_y -= 20

                if caption:
                    safe_cap = caption.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br/>")
                    p_cap = Paragraph(safe_cap, body_style)
                    cw, ch = p_cap.wrapOn(c, avail_w, cursor_y - margin)
                    cursor_y -= ch
                    p_cap.drawOn(c, margin, cursor_y)

                c.showPage()

            for img_path in image_paths:
                if not os.path.exists(img_path):
                    continue

                try:
                    with Image.open(img_path) as img:
                        # Convert modes incompatible with PDF (e.g. RGBA, CMYK, P) to RGB
                        if img.mode in ("RGBA", "LA", "P"):
                            bg = Image.new("RGB", img.size, (255, 255, 255))
                            if img.mode == "P":
                                img = img.convert("RGBA")
                            bg.paste(img, mask=img.split()[-1] if "A" in img.mode else None)
                            temp_rgb_path = f"{img_path}_converted.jpg"
                            bg.save(temp_rgb_path, "JPEG", quality=95)
                            draw_path = temp_rgb_path
                        else:
                            draw_path = img_path

                        img_width, img_height = img.size

                        # Set page size to match the image dimensions for clean presentation
                        c.setPageSize((img_width, img_height))
                        c.drawImage(draw_path, 0, 0, width=img_width, height=img_height)
                        c.showPage()

                        # Clean up temporary converted image if created
                        if draw_path != img_path and os.path.exists(draw_path):
                            try:
                                os.remove(draw_path)
                            except OSError:
                                pass

                except Exception as img_err:
                    logger.warning(f"Error processing image {img_path} for PDF: {img_err}")
                    continue

            c.save()
            return os.path.exists(output_pdf_path) and os.path.getsize(output_pdf_path) > 0

        except Exception as e:
            logger.error(f"Failed to generate PDF at {output_pdf_path}: {e}", exc_info=True)
            return False
