# Command Line Interface (CLI)
> **Rich-Powered Interactive Terminal**

Built using `Typer` and `Rich`, this directory provides the administrator interface for AegisDesk.

## Commands
- `aegisdesk ask "query"`: Streams reasoning to the terminal.
- `aegisdesk ingest <file>`: Chunks and loads PDFs/txts into ChromaDB.
- `aegisdesk teach-router "query" category domain`: Manually inserts a historical ticket into the SQLite database for dynamic Few-Shot semantic routing.
- `aegisdesk init`: Scaffolds the `~/.aegisdesk` directory structure.
