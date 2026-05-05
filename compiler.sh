#!/bin/bash
set -euo pipefail
exec poetry run main "$@"
