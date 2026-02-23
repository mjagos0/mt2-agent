#!/bin/bash

# Run from WSL - installs and runs mt2-agent on Windows side with admin PowerShell

SKIP_INSTALL=false

# Check for --no-install flag
for arg in "$@"; do
  if [ "$arg" = "--no-install" ]; then
    SKIP_INSTALL=true
    break
  fi
done

# Remove --no-install from args passed to mt2-agent
ARGS=()
for arg in "$@"; do
  if [ "$arg" != "--no-install" ]; then
    ARGS+=("$arg")
  fi
done

PROJECT_DIR=$(wslpath -w "$(pwd)")
ARGS_STR="${ARGS[*]}"

if [ "$SKIP_INSTALL" = true ]; then
  INSTALL_CMD=""
else
  INSTALL_CMD="pip install -e .;"
fi

powershell.exe -Command "Start-Process powershell -Verb RunAs -ArgumentList '-NoExit -Command cd \"$PROJECT_DIR\"; ${INSTALL_CMD} mt2-agent $ARGS_STR'"