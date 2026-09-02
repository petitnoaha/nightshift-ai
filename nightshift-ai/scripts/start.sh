#!/usr/bin/env bash
set -euo pipefail
sudo systemctl start nightshift
sleep 2
sudo systemctl status nightshift --no-pager
