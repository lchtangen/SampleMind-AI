#pragma once
// Phase 8 — VST3/AU Plugin
// PythonSidecar: manages the lifecycle of the samplemind sidecar process.
// On start(), checks if ~/tmp/samplemind.sock exists; if not, spawns
// `samplemind sidecar` as a subprocess. On stop(), sends SIGTERM.
// TODO: implement in Phase 8 — VST3/AU Plugin
