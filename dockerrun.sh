#!/bin/bash

docker run --rm -u "$(id -u):$(id -g)" --cap-add PERFMON \
  --security-opt seccomp=unconfined -v "$PWD:/host" -w /host \
  "$USER/598ape" "$@"
