#!/usr/bin/env python3

import argparse
import csv
import datetime
import re
import shutil
import subprocess
from pathlib import Path


root = Path(__file__).resolve().parent
runs = 5

ops = {
    "diabetes": ["./genetic_benchmark", "diabetes"],
    "cancer": ["./genetic_benchmark", "cancer"],
    "housing": ["./genetic_benchmark", "housing"],
}


def docker(worktree, command, capture=False):
    result = subprocess.run(
        [str(root / "dockerrun.sh")] + command,
        cwd=worktree, check=True, text=True,
        stdout=subprocess.PIPE if capture else None
    )
    return result.stdout


def show_table(names, rows):
    table = [["commit"] + names]
    for commit, values in rows:
        table.append([commit] + ["%.6f" % values[name] for name in names])

    widths = []
    for column in range(len(table[0])):
        widths.append(max(len(row[column]) for row in table))

    for number, row in enumerate(table):
        print(" | ".join(row[n].ljust(widths[n]) for n in range(len(row))))
        if number == 0:
            print("-+-".join("-" * width for width in widths))


parser = argparse.ArgumentParser()
parser.add_argument("--commits", nargs="*")
parser.add_argument("--ops", nargs="*", choices=ops)
parser.add_argument("--csv", action="store_true")
args = parser.parse_args()

dirty = not args.commits
commits = args.commits or ["HEAD"]
names = args.ops or list(ops)

stamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
run_dir = root / "runs" / stamp
worktree = run_dir / "worktree"
run_dir.mkdir(parents=True)

first = subprocess.check_output(
    ["git", "rev-parse", commits[0]], cwd=root, text=True
).strip()
subprocess.run(
    ["git", "worktree", "add", "--detach", str(worktree), first],
    cwd=root, check=True
)

if dirty:
    patch = subprocess.check_output(["git", "diff", "HEAD", "--binary"], cwd=root)
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

rows = []
timer = re.compile(r"Time\(.*\) = ([0-9.]+) sec")

for commit in commits:
    commit_id = subprocess.check_output(
        ["git", "rev-parse", commit], cwd=root, text=True
    ).strip()
    if not dirty:
        subprocess.run(
            ["git", "checkout", "--detach", "--force", commit_id],
            cwd=worktree, check=True
        )

    docker(worktree, ["make", "clean"])
    docker(worktree, ["make", "-j4"])

    values = {}
    label = "working tree" if dirty else commit
    print("\n" + label + " (" + commit_id[:12] + ")")
    for name in names:
        times = []
        for number in range(runs):
            output = docker(worktree, ops[name], True)
            seconds = float(timer.search(output).group(1))
            times.append(seconds)
            print("  %-12s %2d/%d  %.6f" %
                  (name, number + 1, runs, seconds))
        values[name] = min(times)

    rows.append((label + " (" + commit_id[:12] + ")", values))

print()
show_table(names, rows)

if args.csv:
    csv_file = run_dir / "results.csv"
    with csv_file.open("w", newline="") as output:
        writer = csv.writer(output)
        writer.writerow(["commit"] + names)
        for commit, values in rows:
            writer.writerow([commit] + [values[name] for name in names])
    print("\n" + str(csv_file))
