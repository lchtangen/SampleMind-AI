# plugin/CMakeLists.txt — JUCE 8 build configuration for SampleMind VST3/AU plugin.
#
# Prerequisites:
#   git clone https://github.com/juce-framework/JUCE plugin/JUCE
#
# Build (macOS):
#   cmake --preset macos-debug
#   cmake --build build/macos-debug
#
# Build (Linux):
#   cmake --preset linux-debug
#   cmake --build build/linux-debug

cmake_minimum_required(VERSION 3.22)
project(SampleMindPlugin VERSION 0.1.0)

# ── Load JUCE ──────────────────────────────────────────────────────────────────
# Clone JUCE 8 to plugin/JUCE/:
#   git clone https://github.com/juce-framework/JUCE JUCE
add_subdirectory(JUCE)

# ── Plugin configuration ───────────────────────────────────────────────────────
juce_add_plugin(SampleMind
    # Metadata shown in the DAW plugin scanner
    COMPANY_NAME                "SampleMind"
    PLUGIN_MANUFACTURER_CODE    "SmAI"     # 4-char unique vendor code
    PLUGIN_CODE                 "SmPl"     # 4-char unique plugin code
    FORMATS                     VST3 AU    # AU is macOS-only; ignored on other platforms

    # SampleMind is a pure UI browser — no audio processing
    IS_SYNTH                    FALSE
    NEEDS_MIDI_INPUT            FALSE
    NEEDS_MIDI_OUTPUT           FALSE
    IS_MIDI_EFFECT              FALSE

    PRODUCT_NAME                "SampleMind"
    BUNDLE_ID                   "com.samplemind.plugin"

    # macOS hardened runtime + entitlement for Python sidecar execution
    HARDENED_RUNTIME_ENABLED    TRUE
    HARDENED_RUNTIME_OPTIONS
        "com.apple.security.cs.allow-unsigned-executable-memory"
)

# ── Source files ───────────────────────────────────────────────────────────────
target_sources(SampleMind PRIVATE
    Source/PluginProcessor.cpp
    Source/PluginProcessor.h
    Source/PluginEditor.cpp
    Source/PluginEditor.h
    Source/PythonSidecar.cpp
    Source/PythonSidecar.h
    Source/IPCSocket.cpp
    Source/IPCSocket.h
)

# ── Compile definitions ────────────────────────────────────────────────────────
target_compile_definitions(SampleMind PUBLIC
    JUCE_WEB_BROWSER=0          # No embedded browser
    JUCE_USE_CURL=0             # No libcurl dependency
    JUCE_VST3_CAN_REPLACE_VST2=0
)

# ── C++ standard ───────────────────────────────────────────────────────────────
target_compile_features(SampleMind PRIVATE cxx_std_17)

# ── Linked libraries ───────────────────────────────────────────────────────────
target_link_libraries(SampleMind PRIVATE
    juce::juce_audio_utils
    juce::juce_gui_basics
    juce::juce_audio_processors
    juce_recommended_config_flags
    juce_recommended_lto_flags
    juce_recommended_warning_flags
)
