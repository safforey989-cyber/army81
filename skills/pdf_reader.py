"""Army81 Skill — PDF Reader"""
import os
import logging

logger = logging.getLogger("army81.skill.pdf_reader")


def read_pdf(file_path: str, max_pages: int = 10) -> str:
    """يقرأ ملف PDF ويستخرج النص"""
    if not os.path.exists(file_path):
        return f"الملف غير موجود: {file_path}"

    try:
        import PyPDF2
        text_parts = []
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            pages = min(len(reader.pages), max_pages)
            for i in range(pages):
                page_text = reader.pages[i].extract_text()
                if page_text:
                    text_parts.append(f"--- صفحة {i+1} ---\n{page_text}")
        return "\n\n".join(text_parts) if text_parts else "لم يُستخرج نص من الـ PDF"
    except ImportError:
        return "مكتبة PyPDF2 غير مثبتة. شغّل: pip install PyPDF2"
    except Exception as e:
        return f"خطأ في قراءة PDF: {e}"


def pdf_info(file_path: str) -> str:
    """معلومات عن ملف PDF"""
    try:
        import PyPDF2
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            info = reader.metadata
            return (
                f"الصفحات: {len(reader.pages)}\n"
                f"العنوان: {info.get('/Title', 'غير محدد')}\n"
                f"المؤلف: {info.get('/Author', 'غير محدد')}"
            )
    except Exception as e:
        return f"خطأ: {e}"
