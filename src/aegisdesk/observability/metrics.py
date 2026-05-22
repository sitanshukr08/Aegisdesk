"""
Observability module for recording performance metrics.
"""
import time
import json
from pathlib import Path
from typing import Dict, Any

class MetricsRecorder:
    def __init__(self, log_dir: str = "logs"):
        self.log_file = Path(log_dir) / "performance_metrics.jsonl"
        self.log_file.parent.mkdir(exist_ok=True)
        self.current_metrics: Dict[str, Any] = {}
        
    def start_timer(self, metric_name: str):
        self.current_metrics[f"{metric_name}_start"] = time.perf_counter()
        
    def stop_timer(self, metric_name: str):
        start_time = self.current_metrics.pop(f"{metric_name}_start", None)
        if start_time is not None:
            elapsed = time.perf_counter() - start_time
            self.current_metrics[metric_name] = round(elapsed, 4)  # seconds
            
    def record_custom(self, key: str, value: Any):
        self.current_metrics[key] = value

    def flush(self, query: str):
        """Writes the recorded metrics to the JSONL file."""
        self.current_metrics["timestamp"] = time.time()
        self.current_metrics["query"] = query
        
        with open(self.log_file, "a") as f:
            f.write(json.dumps(self.current_metrics) + "\n")
            
        self.current_metrics.clear()

# Global singleton to be used across the core pipeline
recorder = MetricsRecorder()