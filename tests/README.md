# Verification Suite
> **Enterprise Validation & Benchmarks**

## 1. Benchmarking (`benchmark.py`)
A rigorous 50-query stress test evaluating the Zero-Token Semantic Router. Validates sub-5ms latency and >75% strict direct-match accuracy.

## 2. Exploit Testing (`test_exploits.py`)
Red-Team simulated attacks against the RCE tools (e.g. attempting to inject `&& rm -rf /`) and SSRF tools (e.g. attempting to scrape `http://169.254.169.254`).

## 3. End-to-End (`test_e2e.py`)
Validates the full pipeline execution from CLI input to tool response.
