// plugin/Source/PythonSidecar.cpp — manages the Python sidecar subprocess.
//
// The sidecar is started with:
//   <python> -m samplemind.sidecar.server --socket <socketPath>
//
// The socket path defaults to ~/tmp/samplemind.sock.
// start() polls for the socket file to appear (max 3 s / 30 × 100 ms) before
// returning, so callers can immediately issue sendRequest() calls.

#include "PythonSidecar.h"

PythonSidecar::PythonSidecar()
{
    socketPath = juce::File::getSpecialLocation(juce::File::userHomeDirectory)
                     .getChildFile("tmp/samplemind.sock");
}

PythonSidecar::~PythonSidecar()
{
    stop();
}

// ── start() ───────────────────────────────────────────────────────────────────

bool PythonSidecar::start()
{
    if (running)
        return true;

    // If the socket file already exists another instance may be running — reuse it.
    if (socketPath.existsAsFile()) {
        running = true;
        return true;
    }

    // Ensure ~/tmp/ exists.
    socketPath.getParentDirectory().createDirectory();

    auto python = findPythonExecutable();

    juce::StringArray args;
    args.add(python.getFullPathName());
    args.add("-m");
    args.add("samplemind.sidecar.server");
    args.add("--socket");
    args.add(socketPath.getFullPathName());

    if (!process.start(args)) {
        DBG("SampleMind: failed to launch sidecar process");
        return false;
    }

    running = true;

    // Poll for socket to appear (up to 3 seconds).
    for (int i = 0; i < 30; ++i) {
        if (socketPath.existsAsFile())
            return true;
        juce::Thread::sleep(100);
    }

    DBG("SampleMind: sidecar socket did not appear within 3 s");
    return false;
}

// ── stop() ────────────────────────────────────────────────────────────────────

void PythonSidecar::stop()
{
    if (!running)
        return;
    process.kill();
    running = false;
    // Remove stale socket file so the next start() launches a fresh process.
    socketPath.deleteFile();
}

// ── isRunning() ───────────────────────────────────────────────────────────────

bool PythonSidecar::isRunning() const
{
    return running && process.isRunning();
}

// ── sendRequest() ─────────────────────────────────────────────────────────────

std::string PythonSidecar::sendRequest(const std::string& jsonRequest)
{
    IPCSocket sock;
    if (!sock.connect(socketPath.getFullPathName().toStdString()))
        return R"({"status":"error","message":"socket not connected"})";

    if (!sock.send(jsonRequest))
        return R"({"status":"error","message":"send failed"})";

    auto response = sock.receive();
    if (response.empty())
        return R"({"status":"error","message":"empty response"})";

    return response;
}

// ── findPythonExecutable() ────────────────────────────────────────────────────

juce::File PythonSidecar::findPythonExecutable() const
{
    // 1. Virtual environment next to the working directory (uv project layout).
    auto venvPython = juce::File::getCurrentWorkingDirectory()
                          .getChildFile(".venv/bin/python");
    if (venvPython.existsAsFile())
        return venvPython;

    // 2. Common SampleMind development path.
    auto devPython = juce::File::getSpecialLocation(juce::File::userHomeDirectory)
                         .getChildFile("dev/projects/SampleMind-AI/.venv/bin/python");
    if (devPython.existsAsFile())
        return devPython;

    // 3. Bare name — OS resolves via PATH.
    return juce::File("python3");
}
