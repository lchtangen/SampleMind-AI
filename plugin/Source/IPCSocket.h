// plugin/Source/IPCSocket.h — POSIX Unix domain socket client.
//
// Protocol (matches src/samplemind/sidecar/protocol.py v2):
//   send:    4-byte big-endian uint32 length  +  UTF-8 JSON payload
//   receive: 4-byte big-endian uint32 length  +  UTF-8 JSON payload
//
// Each sendRequest() call opens a new connection, exchanges one message, then
// disconnects.  This keeps the plugin side stateless and avoids stale sockets
// when the sidecar process is restarted.

#pragma once
#include <string>

class IPCSocket {
public:
    IPCSocket();
    ~IPCSocket();

    /** Open a connection to the given Unix socket path. Returns true on success. */
    bool connect(const std::string& socketPath);

    /** Close the socket if open. Safe to call multiple times. */
    void disconnect();

    /** Write a length-prefixed message.  Returns false on error. */
    bool send(const std::string& message);

    /**
     * Read a length-prefixed message.
     * Blocks until all bytes arrive.  Returns "" on error.
     */
    std::string receive();

    bool isConnected() const;

private:
    int fd = -1;   // POSIX file descriptor; -1 when closed
};
