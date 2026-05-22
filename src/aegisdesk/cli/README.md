# Rich Typer CLI (`src/aegisdesk/cli/`)

> **Verified for AegisDesk v0.1.0 (Phase 16)**

**The Headless Operator Interface**

A fully self-contained administration binary, dynamically rendering streaming outputs, spin-locks, and ASCII diagnostics using Textualize's `Rich` library.
- Safely handles native Windows `cp1252` terminal streams by reconfiguring stdout to `utf-8`.\n