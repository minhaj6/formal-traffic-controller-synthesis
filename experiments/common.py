"""Shared helper for the experiment scripts: run a tool pipeline with limits."""
import os
import signal
import subprocess
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(ROOT, "tools")


def run(pipeline, seconds=300, memory_gb=6, stdin=None):
    """Run a shell pipeline from the tools directory under a time and memory limit.

    Returns (status, stdout, elapsed seconds); status is "ok", "timeout" or
    "fail" (non-zero exit, which includes running out of memory).  On a
    timeout every process the pipeline started is killed.
    """
    command = f"ulimit -v {int(memory_gb * 2**20)}; set -o pipefail; {pipeline}"
    start = time.time()
    process = subprocess.Popen(["bash", "-c", command], cwd=TOOLS, text=True,
                               stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                               stderr=subprocess.DEVNULL, start_new_session=True)
    try:
        out, _ = process.communicate(stdin, timeout=seconds)
        status = "ok" if process.returncode == 0 else "fail"
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGKILL)
        out, _ = process.communicate()
        status = "timeout"
    return status, out, time.time() - start
