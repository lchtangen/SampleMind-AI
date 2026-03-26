// plugin/Source/PluginProcessor.h — SampleMind JUCE AudioProcessor
//
// SampleMind is a pure UI browser/controller plugin — it does not modify the
// audio signal.  processBlock() is a deliberate pass-through.
//
// On construction:  creates a PythonSidecar and calls start()
// On destruction:   calls sidecar->stop() to cleanly terminate the subprocess

#pragma once
#include <juce_audio_processors/juce_audio_processors.h>
#include "PythonSidecar.h"

class SampleMindProcessor : public juce::AudioProcessor {
public:
    SampleMindProcessor();
    ~SampleMindProcessor() override;

    // ── Audio processing (pass-through — SampleMind is a browser, not a DSP) ──
    void prepareToPlay(double /*sampleRate*/, int /*samplesPerBlock*/) override {}
    void releaseResources() override {}
    void processBlock(juce::AudioBuffer<float>&, juce::MidiBuffer&) override {}

    // ── Plugin metadata ────────────────────────────────────────────────────────
    const juce::String getName() const override { return "SampleMind"; }
    bool acceptsMidi()  const override { return false; }
    bool producesMidi() const override { return false; }
    bool isMidiEffect() const override { return false; }
    double getTailLengthSeconds() const override { return 0.0; }

    // ── Program / preset handling (unused — no DSP state to save) ─────────────
    int getNumPrograms() override { return 1; }
    int getCurrentProgram() override { return 0; }
    void setCurrentProgram(int) override {}
    const juce::String getProgramName(int) override { return "Default"; }
    void changeProgramName(int, const juce::String&) override {}
    void getStateInformation(juce::MemoryBlock&) override {}
    void setStateInformation(const void*, int) override {}

    // ── Editor ─────────────────────────────────────────────────────────────────
    juce::AudioProcessorEditor* createEditor() override;
    bool hasEditor() const override { return true; }

    // ── Sidecar access (called by PluginEditor to issue search requests) ───────
    PythonSidecar& getSidecar() { return *sidecar; }

private:
    std::unique_ptr<PythonSidecar> sidecar;

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR(SampleMindProcessor)
};
