"""One-command reproduction: uv sync -> pytest -> benchmark -> verify."""
import subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STEPS = [
    ("uv sync --group dev", "Install dependencies"),
    ("uv run pytest --tb=short -q", "Run 347 tests"),
    ("uv run sfdb benchmark --size tiny --runs 3 --warm-up 1", "Run benchmark suite (quick smoke check)"),
    ("uv run sfdb verify", "Verify integrity"),
    ("uv run sfdb doctor", "System health"),
]

print("=" * 60)
print("SFDB - Complete Reproduction")
print("=" * 60)

for cmd, desc in STEPS:
    print(f"\n[{desc}]")
    print(f"  $ {cmd}")
    t0 = time.time()
    result = subprocess.run(cmd, shell=True, cwd=ROOT,
                          capture_output=True, text=True, timeout=600)
    elapsed = time.time() - t0
    if result.returncode == 0:
        print(f"  [OK] completed in {elapsed:.1f}s")
    else:
        err_lines = [l for l in result.stderr.strip().split("\n") if l.strip()][-3:]
        for line in err_lines:
            print(f"  [FAIL] {line}")
        print(f"  [FAIL] exit code {result.returncode}")
        sys.exit(1)

print("\n" + "=" * 60)
print("All steps passed.")
print("=" * 60)
