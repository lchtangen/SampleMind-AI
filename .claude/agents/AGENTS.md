# Agent Index

This directory contains routing agents used to specialize implementation by phase and domain.

## Phase Agents

- fase-02-audio-testing
- fase-03-database
- fase-04-cli
- fase-05-web
- fase-06-desktop
- fase-07-fl-studio
- fase-08-vst-plugin
- fase-09-sample-packs
- fase-10-production

## Cross-Cutting Agents

- audio-analyzer
- doc-writer
- fl-studio-agent
- tauri-builder
- test-runner

## Routing Rule

If a task explicitly references a phase number, route to the matching phase agent.
Otherwise route to the most specific cross-cutting domain agent.
