"""AegisDesk CLI entrypoint."""

import typing

# --- MONKEY PATCH FOR PYTHON 3.12+ BUG ---
# Pydantic v1 is broken on Python 3.12 because the internal signature of _evaluate changed.
_orig_evaluate = typing.ForwardRef._evaluate
def _evaluate_patch(self, globalns, localns, *args, **kwargs):
    if "recursive_guard" not in kwargs and args:
        kwargs["recursive_guard"] = args[0]
        args = args[1:]
    try:
        return _orig_evaluate(self, globalns, localns, *args, **kwargs)
    except TypeError:
        return _orig_evaluate(self, globalns, localns, type_params=None, *args, **kwargs)
typing.ForwardRef._evaluate = _evaluate_patch

# Transformers import hangs on Windows Python 3.12 due to packages_distributions()
import importlib.metadata
_orig_pd = getattr(importlib.metadata, "packages_distributions", None)
if _orig_pd:
    def _fast_pd():
        return {"transformers": ["transformers"]}
    importlib.metadata.packages_distributions = _fast_pd
# -----------------------------------------

import os
import sys
import asyncio
import io
from pathlib import Path
import os
os.environ["TRANSFORMERS_VERBOSITY"] = "error"

import typer
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass
from dotenv import load_dotenv
import warnings

# Suppress LangChain and Google GenAI deprecation warnings for a clean CLI experience
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", message=".*LangChainDeprecationWarning.*")

# --- MIGRATION BRIDGE ---
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
sys.path.insert(0, project_root)

from src.aegisdesk.core.ingestion import process_file_to_chroma
from src.aegisdesk.core.pipeline import execute_rag_pipeline
# ------------------------

app = typer.Typer(
    help="AegisDesk: Enterprise IT Helpdesk Assistant CLI",
    add_completion=False,
)
console = Console()

@app.command()
def init():
    """Initialize the local workspace, directories, and config."""
    console.print("[bold green]Initializing AegisDesk workspace...[/bold green]")
    
    directories = ["data", "logs"]
    for dir_name in directories:
        d = Path(dir_name)
        if not d.exists():
            d.mkdir(parents=True, exist_ok=True)
            console.print(f"📁 Created '{dir_name}' directory.")
        else:
            console.print(f"✅ '{dir_name}' directory already exists.")
            
    env_path = Path(".env")
    if not env_path.exists():
        example_path = Path(".env.example")
        if example_path.exists():
            console.print("⚠️ [yellow].env file missing. Please copy .env.example to .env[/yellow]")
        else:
            console.print("❌ [bold red].env and .env.example are missing![/bold red]")
    else:
        console.print("✅ .env file exists.")
        
    console.print("✨ Workspace initialized successfully.")

@app.command()
def ingest(file_path: str = typer.Argument(..., help="Path to the .txt or .pdf to ingest")):
    """Ingest a knowledge base document into ChromaDB."""
    load_dotenv()
    path = Path(file_path)
    if not path.exists():
        console.print(f"❌ [bold red]File not found:[/bold red] {file_path}")
        raise typer.Exit(1)
        
    console.print(f"🚀 [bold blue]Ingesting document into ChromaDB:[/bold blue] {path.name}")
    
    with console.status("[cyan]Chunking and Embedding...[/cyan]", spinner="dots"):
        success = process_file_to_chroma(str(path), path.name)
    
    if success:
        console.print(f"✅ [bold green]Successfully ingested {path.name}![/bold green]")
    else:
        console.print(f"❌ [bold red]Failed to ingest {path.name}. Ensure it is a .txt or .pdf file.[/bold red]")
        raise typer.Exit(1)

@app.command()
def ask(
    query: str = typer.Argument(..., help="The IT question to ask"),
    user: str = typer.Option("default_user", "--user", "-u", help="User ID for graph memory"),
    session: str = typer.Option("default_session", "--session", "-s", help="Session ID for chat history"),
    image: str = typer.Option(None, "--image", "-i", help="Path to a screenshot or image to analyze")
):
    """Ask a question and run the RAG + Memory pipeline."""
    load_dotenv()
    
    console.print(f"[bold cyan]User ({user}):[/bold cyan] {query}")
    if image:
        console.print(f"[bold cyan]Attachment:[/bold cyan] {image}")
    console.print("[bold magenta]AegisDesk:[/bold magenta] ", end="")
    
    async def run_pipeline():
        user_approval = None
        while True:
            needs_approval = False
            async def stream_output(approval_flag):
                nonlocal needs_approval
                nonlocal user_approval
                try:
                    with console.status("[bold cyan]Analyzing intent...[/bold cyan]", spinner="dots") as status:
                        async for chunk in execute_rag_pipeline(query, user, session, image, approval_flag):
                            if isinstance(chunk, dict):
                                if chunk["type"] == "status":
                                    status.update(f"[bold cyan]Thinking... ({chunk['msg']})[/bold cyan]")
                                elif chunk["type"] == "interrupt":
                                    status.stop()
                                    console.print("\n")
                                    console.print(Panel(
                                        f"[bold red]System Intercepted Tool Execution[/bold red]\n\n"
                                        f"AegisDesk requires permission to proceed.\n"
                                        f"[yellow]{chunk['msg']}[/yellow]",
                                        title="⚠️ SECURITY INTERRUPT",
                                        border_style="red"
                                    ))
                                    user_approval = typer.confirm("Authorize this action?")
                                    needs_approval = True
                                    return
                                elif chunk["type"] == "content":
                                    status.stop()
                                    console.print(chunk["msg"])
                            else:
                                status.stop()
                                console.print(chunk, end="")
                except Exception as e:
                    console.print(f"\n❌ [bold red]Pipeline Error:[/bold red] {e}")
            
            await stream_output(user_approval)
            if not needs_approval:
                break
        console.print("\n")

    asyncio.run(run_pipeline())

@app.command()
def chat(
    user: str = typer.Option("default_user", "--user", "-u", help="User ID for graph memory"),
    session: str = typer.Option("default_session", "--session", "-s", help="Session ID for chat history")
):
    """Start an interactive, persistent AegisDesk session."""
    load_dotenv()
    
    # CRITICAL FIX: Validate API keys before entering the REPL loop
    if not os.getenv("GROQ_API_KEY"):
        console.print("[bold red]❌ Critical Error:[/bold red] GROQ_API_KEY is missing from .env!")
        raise typer.Exit(1)
        
    console.print(Panel(
        f"[bold cyan]AegisDesk Interactive Session[/bold cyan]\n"
        f"User: [green]{user}[/green] | Session: [green]{session}[/green]\n"
        f"[dim]Type 'exit' or 'quit' to end.[/dim]",
        border_style="cyan"
    ))
    
    while True:
        try:
            query = console.input("[bold cyan]❯[/bold cyan] ")
            if query.lower() in ("exit", "quit", "q"):
                console.print("[dim]Session ended.[/dim]")
                break
            if not query.strip():
                continue
            
            # Intercept nested CLI commands so we don't confuse the semantic router
            if query.strip().startswith("aegisdesk "):
                import subprocess
                subprocess.run(query.strip(), shell=True)
                continue
                
            async def run_pipeline():
                from app.memory.extractor import extract_memory_background
                memory_task = asyncio.create_task(extract_memory_background(user, query))
                
                user_approval = None
                while True:
                    needs_approval = False
                    async def stream_output(approval_flag):
                        nonlocal needs_approval
                        nonlocal user_approval
                        try:
                            with console.status("[bold cyan]Analyzing intent...[/bold cyan]", spinner="dots") as status:
                                async for chunk in execute_rag_pipeline(query, user, session, None, approval_flag):
                                    if isinstance(chunk, dict):
                                        if chunk["type"] == "status":
                                            status.update(f"[bold cyan]Thinking... ({chunk['msg']})[/bold cyan]")
                                        elif chunk["type"] == "interrupt":
                                            status.stop()
                                            from rich.panel import Panel
                                            console.print("\n")
                                            console.print(Panel(
                                                f"[bold red]Tier 3 Security Guardrail Activated[/bold red]\n\n"
                                                f"[yellow]{chunk['msg']}[/yellow]",
                                                title="⚠️ SELECTIVE INTERRUPT",
                                                border_style="red"
                                            ))
                                            user_approval = typer.confirm("Authorize this dangerous action?")
                                            needs_approval = True
                                            return
                                        elif chunk["type"] == "content":
                                            status.stop()
                                            console.print(chunk["msg"])
                                    else:
                                        status.stop()
                                        console.print(chunk, end="")
                        except Exception as e:
                            console.print(f"\n❌ [bold red]Pipeline Error:[/bold red] {e}")
                    
                    await stream_output(user_approval)
                    if not needs_approval:
                        break
                
                # Await the background task so we don't close the event loop prematurely
                try:
                    await memory_task
                except Exception as e:
                    pass
                console.print("\n")
            
            asyncio.run(run_pipeline())
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Session ended.[/dim]")
            break

@app.command()
def doctor():
    """Check system health, API keys, dependencies, and database connections."""
    console.print("[bold yellow]Running system checks...[/bold yellow]")
    
    data_dir = Path("data")
    if not data_dir.exists():
        console.print("❌ [bold red]Data directory missing.[/bold red] Run 'aegisdesk init'.")
        raise typer.Exit(1)
    else:
        console.print("✅ [green]Data directory exists.[/green]")
        
    env_path = Path(".env")
    if not env_path.exists():
        console.print("❌ [bold red].env file missing![/bold red] Please copy .env.example to .env")
        raise typer.Exit(1)
        
    load_dotenv()
    critical_keys = ["GROQ_API_KEY", "GEMINI_API_KEY", "TAVILY_API_KEY"]
    missing = [k for k in critical_keys if not os.getenv(k)]
    
    if missing:
        console.print(f"❌ [bold red]Missing API Keys in .env:[/bold red] {', '.join(missing)}")
    else:
        console.print("✅ [green]Critical API Keys found.[/green]")
        
    try:
        import chromadb
        client = chromadb.PersistentClient(path="./data")
        console.print("✅ [green]ChromaDB loaded successfully.[/green]")
    except ImportError:
        console.print("❌ [bold red]ChromaDB is not installed![/bold red] Run 'pip install chromadb'")
    except Exception as e:
        console.print(f"❌ [bold red]ChromaDB failed to initialize:[/bold red] {e}")
        
    console.print("✅ [bold green]System check complete![/bold green]")

@app.command(name="memory-list")
def memory_list(limit: int = typer.Option(50, help="Number of facts to list")):
    """Visualize the Semantic Graph Memory."""
    from app.memory.graph_store import graph_db
    
    console.print(f"\n[bold magenta]--- Semantic Graph Memory (Top {limit}) ---[/bold magenta]")
    
    with graph_db._connect() as conn:
        rows = conn.execute(
            "SELECT entity1, relation, entity2, status FROM memory_facts ORDER BY updated_at DESC LIMIT ?", 
            (limit,)
        ).fetchall()
        
    if not rows:
        console.print("[dim]No memory facts found.[/dim]")
        return
        
    for r in rows:
        status_color = "green" if r["status"] == "ACTIVE" else "red"
        strike = "[strike]" if r["status"] != "ACTIVE" else ""
        strike_end = "[/strike]" if r["status"] != "ACTIVE" else ""
        
        console.print(
            f"{strike}[{status_color}]{r['entity1']}[/{status_color}] "
            f"--[bold yellow]{r['relation']}[/bold yellow]--> "
            f"[{status_color}]{r['entity2']}[/{status_color}]{strike_end} "
            f"[dim]({r['status']})[/dim]"
        )


@app.command(name="tickets-list")
def tickets_list():
    """List all escalated IT support tickets."""
    ticket_file = Path("data/tickets.jsonl")
    if not ticket_file.exists():
        console.print("[dim]No support tickets have been created yet.[/dim]")
        return
        
    console.print("\n[bold cyan]--- IT Support Tickets ---[/bold cyan]")
    with open(ticket_file, "r") as f:
        for line in f:
            if not line.strip(): continue
            t = json.loads(line.strip())
            console.print(f"🎫 [bold]{t['ticket_id']}[/bold] | Status: [yellow]{t['status']}[/yellow] | Issue: [dim]{t['issue_description']}[/dim]")

@app.command()
def teach_router(query: str, category: str, domain: str):
    """Teach the semantic router a new phrase or historical ticket.
    
    Example: aegisdesk teach-router "Deploy to AWS" it_support cloud_integrations
    """
    from app.memory.graph_store import graph_db
    try:
        graph_db.add_routing_example(query, category, domain)
        console.print(f"[bold green]Successfully taught router:[/bold green] '{query}' -> {category}/{domain}")
        # Clear the singleton so it reloads from DB next time
        from app.rag import pipeline
        pipeline._ROUTER_MODEL = None
    except Exception as e:
        console.print(f"[bold red]Failed to teach router:[/bold red] {e}")

@app.command()
def author():
    """Show the author/creator of AegisDesk."""
    console.print("[bold cyan]AegisDesk[/bold cyan] was created by [bold magenta]sitanshukr08[/bold magenta].")


if __name__ == "__main__":
    app()