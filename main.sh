#!/bin/sh
set -e
cd "$(dirname "$0")"
python3 src/main.py
cd public
python3 -m http.server 8888
