# 598APE-HW2

This repository contains our optimized C++ symbolic regression system for CS
598 APE Homework 2.

## 1. Build

The artifact requires Docker, Git, and Python 3. Build the Docker image and
benchmark program from the repository root:

```bash
./dockerbuild.sh
./dockerrun.sh make clean
./dockerrun.sh make -j4
```

The three benchmark workloads can then be run with:

```bash
./dockerrun.sh ./genetic_benchmark diabetes
./dockerrun.sh ./genetic_benchmark cancer
./dockerrun.sh ./genetic_benchmark housing
```

Each command prints the generated programs, their fitness and test metric, and
the end-to-end runtime.

## 2. Benchmark

`benchmark.py` builds and benchmarks the specified commits in an isolated Git
worktree. It runs each workload five times, reports the minimum runtime, and
optionally writes the results to CSV. For example:

```bash
./benchmark.py --commits dd08bc7 c110cab c1e541a \
  --ops diabetes housing --csv
```

The available workloads are `diabetes`, `cancer`, and `housing`. Omitting
`--commits` benchmarks the current working tree, while omitting `--ops` runs all
three workloads.

## 3. Evaluation

The following commands reproduce the results presented in the report.

### Overall Performance

The main figure compares the baseline, O1 compiler configuration, O2
interpreter work reduction, O3 OpenMP parallelization, O4 SIMD vectorization,
O5 sorting and loss improvements, and O6 evaluation-fitness fusion:

```bash
./benchmark.py \
  --commits 45e31dd 066e9a4 63d2a77 dd08bc7 c1e541a ef4c0c0 202724b \
  --ops diabetes cancer housing --csv
```

The baseline workloads are substantially slower than the optimized versions;
running all five baseline trials takes approximately 30 minutes on the course
VM.

### Vectorization Breakdown

The vectorization table compares O3, blocked node-first evaluation with SIMD
for simple arithmetic, and the addition of `libmvec` for vector math:

```bash
./benchmark.py \
  --commits dd08bc7 c110cab c1e541a \
  --ops diabetes cancer housing --csv
```

The Intel oneAPI row is stored on the `compiler-ablation` branch. Build its
Docker image and benchmark its compiler commit with:

```bash
git worktree add runs/compiler-ablation compiler-ablation
runs/compiler-ablation/dockerbuild.sh
./benchmark.py --commits e59c1a6 \
  --ops diabetes cancer housing --csv
```

### OpenMP Scheduling

The scheduling experiment is stored on the `schedule-ablation` branch. The two
commits differ only in the OpenMP schedule and evaluate static and dynamic
scheduling, in that order:

```bash
./benchmark.py \
  --commits f2d41db f1f197b \
  --ops diabetes cancer housing --csv
```

