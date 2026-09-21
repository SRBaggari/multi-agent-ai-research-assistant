def create_chunks(pages, chunk_size=1200, overlap=200):
    """
    Split page text into overlapping chunks, keeping the page number.

    Input:
        [{"page_number": 1, "text": "..."}, ...]

    Output:
        [{"text": "...", "page_number": 1}, ...]

    The overlap keeps sentences that fall on a chunk boundary readable
    in at least one of the two chunks.
    """

    chunk_size = max(100, int(chunk_size))

    # An overlap as large as the chunk would never advance the cursor.
    overlap = max(0, min(int(overlap), chunk_size - 1))

    step = chunk_size - overlap

    chunks = []

    for page in pages:

        text = page.get("text", "")

        page_number = page.get("page_number", 0)

        if not text:
            continue

        start = 0

        while start < len(text):

            chunk_text = text[start:start + chunk_size].strip()

            if chunk_text:
                chunks.append({
                    "text": chunk_text,
                    "page_number": page_number,
                })

            start += step

    return chunks
