import fitz   # PyMuPDF


class PDFParseError(Exception):
    """Raised when a PDF cannot be opened or read."""


def extract_pages_from_pdf(file_path: str):
    """
    Extract text page-by-page from a PDF.

    Pages with no extractable text (images, scans) are skipped, but the
    page numbers of the remaining pages stay correct, so citations keep
    pointing at the right page of the original document.

    Returns:
        [
            {"page_number": 1, "text": "..."},
            ...
        ]
    """

    try:
        document = fitz.open(file_path)

    except Exception as error:
        raise PDFParseError(f"Could not open the PDF: {error}") from error

    if document.is_encrypted and not document.authenticate(""):
        document.close()
        raise PDFParseError(
            "This PDF is password protected and cannot be read."
        )

    pages = []

    try:

        for page_number, page in enumerate(document, start=1):

            text = page.get_text("text").strip()

            if text:
                pages.append({
                    "page_number": page_number,
                    "text": text,
                })

    except Exception as error:
        raise PDFParseError(
            f"Failed while reading the PDF: {error}"
        ) from error

    finally:
        document.close()

    return pages
