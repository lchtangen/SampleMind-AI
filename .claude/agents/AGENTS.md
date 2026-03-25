# Agent Index

This directory contains routing agents used to specialize implementation by phase and domain.

## Phase Agents

- phase-02-audio-testing
- phase-03-database
- phase-04-cli
- phase-05-web
- phase-06-desktop
- phase-07-fl-studio
- phase-08-vst-plugin
- phase-09-sample-packs
- phase-10-production

## Cross-Cutting Agents

- audio-analyzer
- doc-writer
- fl-studio-agent
- tauri-builder
- test-runner

## Routing Rule

If a task explicitly references a phase number, route to the matching phase agent.
Otherwise route to the most specific cross-cutting domain agent.