// plugin/Source/PythonSidecar.h — manages the Python sidecar subprocess lifecycle.
//
// On start(): locates the Python executable, spawns
//   `python -m samplemind.sidecar.server --socket <path>`
//   then polls for the Unix socket to appear (up to 3 s).
//
// On stop(): sends SIGTERM to the child process.
//
// sendRequest() must NOT be called from the audio thread — it blocks on I/O.

#pragma once
#include <juce_core/juce_core.h>
#include <string>
#include "IPCSocket.h"

class PythonSidecar {
public:
    PythonSidecar();
    ~PythonSidecar();

    /** Launch the sidecar subprocess.  Returns true if the socket appeared within 3 s. */
    bool start();

    /** Terminate the sidecar process (called in PluginProcessor destructor). */
    void stop();

    /** Returns true if the child process is still alive. */
    bool isRunning() const;

    /**
     * Send a JSON request string and return the JSON response string.
     *
     * Blocking — opens a new IPCSocket connection per call, sends, reads, disconnects.
     * Do NOT call from the audio thread.
     *
     * Returns a JSON error object on failure:
     *   {"status":"error","message":"..."}
     */
    std::string sendRequest(const std::string& jsonRequest);

    /** Returns the Unix socket path used by this sidecar instance. */
    juce::String getSocketPath() const { return socketPath.getFullPathName(); }

private:
    juce::ChildProcess process;   // JUCE cross-platform subprocess wrapper
    juce::File socketPath;        // ~/tmp/samplemind.sock
    bool running = false;

    /** Search common locations for a Python 3 executable. */
    juce::File findPythonExecutable() const;

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR(PythonSidecar)
};
