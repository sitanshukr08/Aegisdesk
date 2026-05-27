import re
import subprocess

from langchain_core.tools import tool

from aegisdesk.observability.logger import get_logger

logger = get_logger("aegisdesk.tools")

def sanitize_input(value: str) -> str:
    """Strictly prevents shell metacharacter injection and destructive commands."""
    # Tier 1: Metacharacter Blocking
    if re.search(r'[&|;<>`$\n\r\(\){}"\']', value):
        raise ValueError(f"Security Alert: Blocked illegal shell characters in input: {value}")
        
    # Tier 1: Destructive Command Denylist
    destructive_patterns = r'\b(del|rmdir|rm|remove-item|format|diskpart|drop|truncate|clear-content|rd)\b'
    if re.search(destructive_patterns, value, re.IGNORECASE):
        logger.warning(f"[SECURITY] Intercepted destructive command attempt: {value}")
        raise ValueError("Security Alert: Execution of destructive command patterns is strictly prohibited by MNC Policy.")
        
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

@tool
def check_ethernet_status() -> str:
    """Use this to check the status of ethernet and network adapters."""
    return run_cmd(["powershell", "-Command", "Get-NetAdapter | Select-Object Name, Status, LinkSpeed | Format-Table -AutoSize"])

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

# Tier 2: Protected System Processes
CRITICAL_SYSTEM_PROCESSES = {
    "explorer.exe", "svchost.exe", "lsass.exe", "csrss.exe", 
    "smss.exe", "wininit.exe", "services.exe", "winlogon.exe", 
    "taskmgr.exe", "spoolsv.exe", "conhost.exe"
}

@tool
def kill_process(process_name: str) -> str:
    """Use this to forcefully close a frozen or misbehaving application by its exact name (e.g. 'excel.exe')."""
    try:
        safe_name = sanitize_input(process_name)
        
        # Tier 2 Check
        if safe_name.lower() in CRITICAL_SYSTEM_PROCESSES:
            logger.warning(f"[SECURITY] Agent attempted to kill critical system process: {safe_name}")
            return f"Permission Denied by MNC Policy: '{safe_name}' is a critical system process and cannot be terminated."
            
        return run_cmd(["taskkill", "/F", "/IM", safe_name])
    except Exception as e:
        return str(e)

@tool
def start_process(executable_name: str) -> str:
    """Use this to start or restart an application by its executable name (e.g. 'spotify.exe' or 'notepad.exe')."""
    try:
        safe_name = sanitize_input(executable_name)
        # Using powershell Start-Process safely without string interpolation
        return run_cmd(["powershell", "-NoProfile", "-Command", "Start-Process", safe_name, "-ErrorAction", "Stop"])
    except Exception as e:
        return str(e)

# --- MASTER TOOLSET ---
SAFE_TOOLS = [
    ping_network,
    get_ip_config,
    check_wifi_status,
    check_ethernet_status,
    get_system_info,
    list_running_processes
]

DANGEROUS_TOOLS = [
    flush_dns_cache,
    kill_process,
    start_process
]

# Export this list so the LLM can bind all tools at once.
IT_SUPPORT_TOOLS = SAFE_TOOLS + DANGEROUS_TOOLS

