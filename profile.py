#!/usr/bin/env python3

import argparse
import datetime
import shutil
import subprocess
from pathlib import Path


root = Path(__file__).resolve().parent

ops = {
    "diabetes": ["./genetic_benchmark", "diabetes"],
    "cancer": ["./genetic_benchmark", "cancer"],
    "housing": ["./genetic_benchmark", "housing"],
}


def docker(worktree, command):
    subprocess.run(
        [str(root / "dockerrun.sh")] + command,
        cwd=worktree, check=True
    )


parser = argparse.ArgumentParser()
parser.add_argument("--commit")
parser.add_argument("--op", choices=ops, default="diabetes")
parser.add_argument("--freq", type=int)
args = parser.parse_args()

stamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
run_dir = root / "runs" / stamp
worktree = run_dir / "worktree"
commit = args.commit or "HEAD"
run_dir.mkdir(parents=True)

subprocess.run(
    ["git", "worktree", "add", "--detach", str(worktree), commit],
    cwd=root, check=True
)

if not args.commit:
    patch = subprocess.check_output(
        ["git", "diff", "HEAD", "--binary"], cwd=root
    )
    if patch:
        subprocess.run(["git", "apply"], cwd=worktree, input=patch, check=True)
    untracked = subprocess.check_output(
        ["git", "ls-files", "--others", "--exclude-standard", "-z"],
        cwd=root
    ).decode().split("\0")
    for name in untracked[:-1]:
        target = worktree / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(root / name, target)

subprocess.run(
    ["git", "clone", "--depth", "1",
     "https://github.com/brendangregg/FlameGraph.git", "FlameGraph"],
    cwd=worktree, check=True
)

(worktree / "profile").mkdir()
docker(worktree, ["make", "clean"])
docker(worktree, ["make", "-j4"])
perf = ["perf", "record", "-e", "cpu-clock:u"]
if args.freq:
    perf += ["-F", str(args.freq)]
perf += ["--call-graph", "dwarf", "-o", "profile/perf.data", "--"]
docker(worktree, perf + ops[args.op])
docker(worktree, [
    "bash", "-c",
    "perf script -i profile/perf.data > profile/perf.txt"
])
docker(worktree, [
    "bash", "-c",
    "FlameGraph/stackcollapse-perf.pl profile/perf.txt "
    "> profile/perf.folded"
])
docker(worktree, [
    "bash", "-c",
    "FlameGraph/flamegraph.pl --countname samples profile/perf.folded "
    "> profile/flamegraph.svg"
])
docker(worktree, [
    "bash", "-c",
    "perf report --stdio -i profile/perf.data > profile/report.txt"
])

print("\n" + str(worktree / "profile" / "flamegraph.svg"))
