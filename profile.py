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
parser.add_argument(
    "--events", nargs="+", choices=("cycles", "instructions"),
    default=("cycles", "instructions")
)
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

docker(worktree, ["make", "clean"])
docker(worktree, ["make", "-j4"])

outputs = []
for event in args.events:
    profile_dir = worktree / "profile" / event
    profile_dir.mkdir(parents=True)
    relative_dir = f"profile/{event}"
    perf = [
        "perf", "record", "-e", f"{event}:u", "-F", str(args.freq),
        "--call-graph", "dwarf", "-o", f"{relative_dir}/perf.data", "--"
    ]
    docker(worktree, perf + ops[args.op])
    docker(worktree, [
        "bash", "-c",
        f"perf script -i {relative_dir}/perf.data > {relative_dir}/perf.txt"
    ])
    docker(worktree, [
        "bash", "-c",
        f"FlameGraph/stackcollapse-perf.pl {relative_dir}/perf.txt "
        f"> {relative_dir}/perf.folded"
    ])
    docker(worktree, [
        "bash", "-c",
        f"FlameGraph/flamegraph.pl --countname samples "
        f"{relative_dir}/perf.folded > {relative_dir}/flamegraph.svg"
    ])
    docker(worktree, [
        "bash", "-c",
        f"perf report --stdio -i {relative_dir}/perf.data "
        f"> {relative_dir}/report.txt"
    ])
    outputs.append(profile_dir / "flamegraph.svg")

print("\n" + "\n".join(str(output) for output in outputs))
