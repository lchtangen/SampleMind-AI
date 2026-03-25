#!/usr/bin/env bash
# Phase 8 — AU Validation (macOS only)
# Runs Apple's auval tool to verify the SampleMind AU component passes
# the Audio Unit Validation Tool checks. Required before App Store / Notarization.
#
# Usage: ./scripts/validate-au.sh
# Requires: macOS with Xcode Command Line Tools installed
# Component: aufx type, SmPl subtype, SmAI manufacturer
# TODO: implement in Phase 8 — VST3/AU Plugin

set -euo pipefail

if [[ "$(uname)" != "Darwin" ]]; then
  echo "ERROR: AU validation is macOS only" >&2
  exit 1
fi

echo "ERROR: validate-au.sh not yet implemented (Phase 8)" >&2
exit 1
