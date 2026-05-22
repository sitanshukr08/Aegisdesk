import subprocess
import re
from langchain_core.tools import tool
from src.aegisdesk.observability.logger import get_logger

logger = get_logger("aegisdesk.tools")

def sanitize_input(value: str) -> str:
    """Strictly prevents shell metacharacter injection."""
    if re.search(r'[&|;<>`$]', value):
        raise ValueError(f"Security Alert: Blocked illegal shell characters in input: {value}")
    return value.strip()

def run_cmd(command: list[str]) -> str:
    """Helper to run raw OS commands safely."""
    try:
        logger.debug(f"Executing IT tool command: {' '.join(command)}")
        # CRITICAL FIX: shell=False prevents & and | injection on Windows.
        result = subprocess.run(
            command, 
            capture_output=True, 
            text=True, 
            timeout=15,
            shell=False 
        )
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            return f"Command failed with error: {result.stderr.strip()}"
    except subprocess.TimeoutExpired:
        return "Command timed out after 15 seconds."
    except Exception as e:
        return f"System error executing command: {str(e)}"

# --- NETWORK DIAGNOSTICS ---

@tool
def ping_network(host: str) -> str:
    """Use this to check if a website, server, or IP address is online and reachable."""
    try:
        safe_host = sanitize_input(host)
        return run_cmd(["ping", "-n", "4", safe_host])
    except Exception as e:
        return str(e)

@tool
def get_ip_config() -> str:
    """Use this to check the user's current IP address, subnet, and default gateway."""
    return run_cmd(["ipconfig", "/all"])

@tool
def check_wifi_status() -> str:
    """Use this to check if the WiFi is connected, signal strength, and current SSID."""
    return run_cmd(["netsh", "wlan", "show", "interfaces"])

@tool
def flush_dns_cache() -> str:
    """Use this to fix DNS resolution errors (e.g. website not found, but internet works)."""
    return run_cmd(["ipconfig", "/flushdns"])

# --- SYSTEM DIAGNOSTICS ---

@tool
def get_system_info() -> str:
    """Use this to get the Windows OS version, RAM, and boot time."""
    return run_cmd(["systeminfo"])

@tool
def list_running_processes(process_name: str = "") -> str:
    """Use this to check if a specific application (e.g. 'chrome.exe') is running."""
    cmd = ["tasklist"]
    if process_name:
        try:
            safe_name = sanitize_input(process_name)
            cmd.extend(["/FI", f"IMAGENAME eq {safe_name}"])
        except Exception as e:
            return str(e)
    return run_cmd(cmd)

@tool
def kill_process(process_name: str) -> str:
    """Use this to forcefully close a frozen or misbehaving application by its exact name (e.g. 'excel.exe')."""
    try:
        safe_name = sanitize_input(process_name)
        return run_cmd(["taskkill", "/F", "/IM", safe_name])
    except Exception as e:
        return str(e)

# --- MASTER TOOLSET ---
# Export this list so the LLM and LangGraph can bind it.
IT_SUPPORT_TOOLS = [
    ping_network,
    get_ip_config,
    check_wifi_status,
    flush_dns_cache,
    get_system_info,
    list_running_processes,
    kill_process
]
