# bwUniCluster 3.0 (KIT HPC) access

I have access to bwUniCluster 3.0, a university HPC cluster run by KIT for
Baden-Wuerttemberg universities: a Slurm cluster with H100/A100/MI300 GPU
nodes, CPU nodes, a highmem partition, and a Lustre file system. Used for
large-scale benchmark runs for this paper (e.g. LUBM past the 265-university
/ 97,289-fact scale currently in `paper/`). Official docs:
https://wiki.bwhpc.de/e/BwUniCluster3.0

## Reaching it

- From this Windows PC: `ssh uc3 "<command>"`. The alias `uc3` is in
  `~/.ssh/config` (user `ma_lsandouk`, login node 1, IPv4 only). `scp` works
  the same way (`scp file uc3:path`); rsync is not available in Git Bash here.
- For multi-line remote work: `ssh -o BatchMode=yes uc3 'bash -s' <<'REMOTE' ... REMOTE`.
  Filter the login banner and the post-quantum-warning lines from output.
- First action every session: `ssh -o BatchMode=yes -o ConnectTimeout=15 uc3 hostname`.
  - "Connection refused" -> VPN is off. I need to reconnect Cisco Secure
    Client to vpn.uni-mannheim.de. Ask me, don't try to fix it yourself.
  - "Permission denied (publickey,keyboard-interactive)" -> my 8-hour SSH
    key window closed. Ask me to run `ssh uc3` once (TOTP + service
    password — never ask me for these, never type them yourself).
  - "pam_ses_open.sh ... Access denied" is intermittent; just retry.

## How the cluster works

- Login nodes are shared/overloaded — use only for editing, git, small pip
  installs, and `sbatch`. All real compute, downloads, and container builds
  go into batch jobs.
- Submit: `sbatch script.sh`. Watch: `squeue -u $USER`. Inspect:
  `scontrol show job <id>`. History: `sacct -u $USER -S now-24hours -X`.
  Cancel: `scancel <id>`. Free nodes: `sinfo_t_idle` (plain `sinfo -N` is
  denied). Pending with reason "Priority" is normal — don't resubmit in
  loops; submit once and watch in the background.

## Partitions (bwUniCluster 3.0, verified 2026-09-18)

- `cpu_il`: 264 nodes, up to 128 CPUs / 256GB RAM per node, max 3 days.
- `cpu`: 80 nodes, up to 192 CPUs / 384GB RAM per node, max 3 days.
- `highmem`: 5 nodes, up to 192 CPUs / ~2.3TB RAM per node, max 3 days.
  Use for very large in-memory benchmark runs.
- `dev_cpu`, `dev_cpu_il`: single-node, short walltime — smoke tests.
- GPU partitions (`gpu_h100`, `gpu_a100_il`, `gpu_mi300`, ...) exist but this
  project's benchmark workload is CPU/RAM-bound, not GPU.
- No `java` module is available by default (`module spider java` finds
  nothing) — needed only if/when running the Jena/Virtuoso/GraphDB external
  reference points on-cluster; get a JDK via conda/miniforge or a tarball
  if that's ever needed.

## Storage

- `$HOME` = `/home/ma/ma_ma/ma_lsandouk` (`/pfs/data6/...`), 250GB quota,
  backed up. Code and logs only.
- Workspaces hold data/results: `ws_allocate <name> <days>`,
  `ws_find <name>` for the path, `ws_extend <name> <days>` (up to 3x),
  `ws_list` to see all. A workspace named `llm` already exists — that
  belongs to a different project, don't touch it. This project should use
  its own workspace (e.g. `sfdb`).
- `$TMPDIR` inside a job is node-local NVMe, wiped at job end.

## Software

- `module load devel/miniforge` for Python 3.12 (system python3 is old).
  `uv` is this repo's normal tool but may not be present on the cluster —
  check, and fall back to `python -m venv` + `pip install -e .` if not.
- Enroot and Apptainer are installed (no Docker) for any container needs.

## How to work

- Proceed without asking permission for reversible steps (submitting a
  cancellable job, building an env, running a smoke test). Stop only for
  things that need me in person: VPN, OTP login, bwIDM portal.
- This repo's benchmark numbers feed directly into `paper/`, which has a
  history of numbers being wrong until adversarial review caught them (see
  `paper/sections/discussion.tex`'s bug inventory and recent git log). Treat
  any new large-scale run with the same rigor as the existing
  `scripts/lubm_benchmark.py`: cross-engine verification on every query
  class, a reproducibility manifest, and don't silently overwrite the
  existing `results/lubm_benchmark.json` (which backs numbers already in
  the paper) — write new large-scale results to their own file.
- Report outcomes plainly, with actual error text on failure. Verify before
  claiming something works.
