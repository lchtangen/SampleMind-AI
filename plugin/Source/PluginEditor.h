// plugin/Source/PluginEditor.h — SampleMind plugin UI.
//
// Layout (500 × 440 px):
//   ┌────────────────────────────────────────────┐
//   │  SampleMind  [search field……………] [Search] │  ← header row (44 px)
//   ├────────────────────────────────────────────┤
//   │  results list  (filename · BPM · energy)   │  ← fills remaining height
//   └────────────────────────────────────────────┘
//
// Interaction:
//   - Return key in search field  → calls performSearch()
//   - "Search" button click       → calls performSearch()
//   - Double-click result row     → copies full path to system clipboard

#pragma once
#include <juce_audio_processors/juce_audio_processors.h>
#include <juce_gui_basics/juce_gui_basics.h>
#include "PluginProcessor.h"

// ── ResultsModel — provides data to the ListBox ───────────────────────────────

struct SampleRow {
    juce::String filename;
    juce::String path;
    juce::String bpm;
    juce::String energy;
};

class ResultsModel : public juce::ListBoxModel {
public:
    juce::Array<SampleRow> rows;

    int getNumRows() override { return rows.size(); }

    void paintListBoxItem(int rowNumber, juce::Graphics& g,
                          int width, int height,
                          bool rowIsSelected) override;

    void listBoxItemDoubleClicked(int row, const juce::MouseEvent&) override;
};

// ── PluginEditor ──────────────────────────────────────────────────────────────

class SampleMindEditor : public juce::AudioProcessorEditor,
                         public juce::TextEditor::Listener {
public:
    explicit SampleMindEditor(SampleMindProcessor&);
    ~SampleMindEditor() override;

    void paint(juce::Graphics&) override;
    void resized() override;

    // juce::TextEditor::Listener
    void textEditorReturnKeyPressed(juce::TextEditor&) override;

private:
    SampleMindProcessor& processor;

    juce::TextEditor  searchField;
    juce::TextButton  searchButton  { "Search" };
    juce::ListBox     resultsList;
    ResultsModel      resultsModel;
    juce::Label       statusLabel;

    void performSearch();

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR(SampleMindEditor)
};
