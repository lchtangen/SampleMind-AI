// Phase 8 — VST3/AU Plugin
// IPCSocket implementation.
// Uses POSIX socket() / connect() directly (no JUCE abstraction) for
// Unix domain socket (AF_UNIX, SOCK_STREAM). Length prefix is 4-byte
// big-endian uint32 matching Python struct.pack(">I", len).
// TODO: implement in Phase 8 — VST3/AU Plugin

#include "IPCSocket.h"
