import os
from typing import List, Optional
import docx
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from utils.logging import get_logger

logger = get_logger("linkforge.docx_service")


class DocxService:
    """Converts images into formatted Microsoft Word (.docx) documents."""

    @classmethod
    def images_to_docx(
        cls,
        image_paths: List[str],
        output_docx_path: str,
        title: Optional[str] = None,
        caption: Optional[str] = None,
        include_caption: bool = True
    ) -> bool:
        """Convert a list of image file paths into a formatted Word (.docx) document.
        
        Optionally prepends document title and post caption / description.
        """
        if not image_paths:
            logger.warning("No image paths provided for DOCX generation.")
            return False

        try:
            os.makedirs(os.path.dirname(output_docx_path), exist_ok=True)
            doc = docx.Document()

            # Set 0.5 inch margins for clean page-filling images
            for section in doc.sections:
                section.top_margin = Inches(0.5)
                section.bottom_margin = Inches(0.5)
                section.left_margin = Inches(0.5)
                section.right_margin = Inches(0.5)

            # Prepend Title & Caption if requested
            if include_caption and (title or caption):
                if title:
                    h = doc.add_heading(title, level=1)
                    h.alignment = WD_ALIGN_PARAGRAPH.CENTER
                if caption:
                    p = doc.add_paragraph()
                    run = p.add_run(caption)
                    run.font.size = Pt(11)
                    run.font.italic = True
                    p.paragraph_format.space_after = Pt(18)
                doc.add_page_break()

            # Insert document pages/slides
            valid_images_added = 0
            for idx, img_path in enumerate(image_paths):
                if not os.path.exists(img_path):
                    continue
                try:
                    p = doc.add_paragraph()
                    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    p.paragraph_format.space_before = Pt(0)
                    p.paragraph_format.space_after = Pt(0)
                    run = p.add_run()
                    # Fit to width (7.2 inches fits nicely inside 0.5-inch margins on 8.5-inch wide letter/A4)
                    run.add_picture(img_path, width=Inches(7.2))
                    valid_images_added += 1

                    if idx < len(image_paths) - 1:
                        doc.add_page_break()
                except Exception as img_err:
                    logger.warning(f"Error inserting image {img_path} into docx: {img_err}")
                    continue

            if valid_images_added == 0:
                logger.warning("No valid images were added to DOCX.")
                return False

            doc.save(output_docx_path)
            return os.path.exists(output_docx_path) and os.path.getsize(output_docx_path) > 0

        except Exception as e:
            logger.error(f"Failed to generate DOCX at {output_docx_path}: {e}", exc_info=True)
            return False
