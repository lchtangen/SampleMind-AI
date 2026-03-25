cmake_minimum_required(VERSION 3.22)
project(SampleMind VERSION 0.1.0)

# Phase 8 — VST3/AU Plugin
# JUCE 8 CMake build configuration.
# Builds SampleMind as VST3 (Windows/macOS/Linux) and AU (macOS only).
# The PluginProcessor hosts a Python sidecar process (PythonSidecar.cpp)
# that connects to the samplemind Unix socket server.
# TODO: implement in Phase 8 — VST3/AU Plugin

# set(JUCE_DIR "/path/to/JUCE" CACHE PATH "JUCE library root")
# add_subdirectory(${JUCE_DIR} JUCE)
# juce_add_plugin(SampleMind ...)
