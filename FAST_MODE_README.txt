
Use this fast-boot version to reduce cold-start time.

- Toggle SAFE mode in the sidebar, or set env var INK_SAFE=1
- Matplotlib is lazily imported via _mpl()

Example:
    plt, PdfPages = _mpl()
    # use plt / PdfPages normally
