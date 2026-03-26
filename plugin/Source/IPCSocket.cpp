// plugin/Source/IPCSocket.cpp — POSIX Unix domain socket client.
//
// Protocol (matches src/samplemind/sidecar/protocol.py v2):
//   send:    4-byte big-endian uint32 length  +  UTF-8 JSON payload
//   receive: 4-byte big-endian uint32 length  +  UTF-8 JSON payload
//
// Uses raw POSIX syscalls (socket/connect/read/write/close) — no JUCE
// abstraction — so the IPC layer compiles and runs without any JUCE modules.

#include "IPCSocket.h"

#include <sys/socket.h>
#include <sys/un.h>
#include <unistd.h>
#include <arpa/inet.h>
#include <cstring>
#include <cerrno>

// ── Constructor / Destructor ───────────────────────────────────────────────────

IPCSocket::IPCSocket() = default;

IPCSocket::~IPCSocket()
{
    disconnect();
}

// ── connect() ─────────────────────────────────────────────────────────────────

bool IPCSocket::connect(const std::string& socketPath)
{
    fd = ::socket(AF_UNIX, SOCK_STREAM, 0);
    if (fd < 0)
        return false;

    sockaddr_un addr{};
    addr.sun_family = AF_UNIX;
    std::strncpy(addr.sun_path, socketPath.c_str(), sizeof(addr.sun_path) - 1);

    if (::connect(fd, reinterpret_cast<sockaddr*>(&addr), sizeof(addr)) != 0) {
        ::close(fd);
        fd = -1;
        return false;
    }

    return true;
}

// ── disconnect() ──────────────────────────────────────────────────────────────

void IPCSocket::disconnect()
{
    if (fd >= 0) {
        ::close(fd);
        fd = -1;
    }
}

bool IPCSocket::isConnected() const
{
    return fd >= 0;
}

// ── send() ────────────────────────────────────────────────────────────────────

bool IPCSocket::send(const std::string& message)
{
    if (fd < 0)
        return false;

    // Write 4-byte big-endian length prefix.
    auto payloadLen = static_cast<uint32_t>(message.size());
    uint32_t lenBE = htonl(payloadLen);
    if (::write(fd, &lenBE, sizeof(lenBE)) != sizeof(lenBE))
        return false;

    // Write payload in one call (safe for messages < PIPE_BUF on Linux/macOS).
    ssize_t written = ::write(fd, message.data(), payloadLen);
    return written == static_cast<ssize_t>(payloadLen);
}

// ── receive() ─────────────────────────────────────────────────────────────────

std::string IPCSocket::receive()
{
    if (fd < 0)
        return {};

    // Read 4-byte big-endian length prefix.
    uint32_t lenBE = 0;
    if (::read(fd, &lenBE, sizeof(lenBE)) != sizeof(lenBE))
        return {};

    uint32_t payloadLen = ntohl(lenBE);
    if (payloadLen == 0)
        return {};

    // Guard against pathological lengths (> 64 MiB).
    constexpr uint32_t kMaxPayload = 64u * 1024u * 1024u;
    if (payloadLen > kMaxPayload)
        return {};

    std::string buf(payloadLen, '\0');
    ssize_t total = 0;

    // Loop until all bytes arrive (TCP-style reassembly over the Unix socket).
    while (total < static_cast<ssize_t>(payloadLen)) {
        ssize_t n = ::read(fd, buf.data() + total,
                           static_cast<size_t>(payloadLen) - static_cast<size_t>(total));
        if (n <= 0)
            return {};  // connection closed or error
        total += n;
    }

    return buf;
}
