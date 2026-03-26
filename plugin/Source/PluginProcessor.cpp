// plugin/Source/PluginProcessor.cpp — SampleMind AudioProcessor implementation.
//
// SampleMind is a pure browser/controller plugin.  It spawns a Python sidecar
// on load and communicates with it via a Unix domain socket.  The audio buffer
// is never modified — processBlock() is intentionally empty.

#include "PluginProcessor.h"
#include "PluginEditor.h"

// ── Constructor / Destructor ───────────────────────────────────────────────────

SampleMindProcessor::SampleMindProcessor()
    : juce::AudioProcessor(
          BusesProperties()
              .withInput ("Input",  juce::AudioChannelSet::stereo(), true)
              .withOutput("Output", juce::AudioChannelSet::stereo(), true))
{
    sidecar = std::make_unique<PythonSidecar>();

    // Start the sidecar on a background thread so plugin load doesn't stall the DAW.
    juce::Thread::launch([this]() {
        if (!sidecar->start()) {
            DBG("SampleMind: sidecar failed to start — check that `samplemind` is in PATH");
        }
    });
}

SampleMindProcessor::~SampleMindProcessor()
{
    sidecar->stop();
}

// ── Editor factory ─────────────────────────────────────────────────────────────

juce::AudioProcessorEditor* SampleMindProcessor::createEditor()
{
    return new SampleMindEditor(*this);
}

// ── JUCE plugin instance factory (required) ────────────────────────────────────

juce::AudioProcessor* JUCE_CALLTYPE createPluginFilter()
{
    return new SampleMindProcessor();
}
