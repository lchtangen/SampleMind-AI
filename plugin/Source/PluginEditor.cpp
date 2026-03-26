// plugin/Source/PluginEditor.cpp — SampleMind plugin UI implementation.
//
// Layout (500 × 440):
//   Header row (44 px): title label | search field | "Search" button
//   Remaining height:   ListBox with filename / BPM / energy columns
//   Status bar (20 px): short feedback message at the bottom

#include "PluginEditor.h"
#include "PluginProcessor.h"

// ── Theme colours ──────────────────────────────────────────────────────────────
static const juce::Colour kBackground   { 0xff1a1a1a };
static const juce::Colour kSurface      { 0xff242424 };
static const juce::Colour kAccent       { 0xff7c3aed };
static const juce::Colour kTextPrimary  { 0xffffffff };
static const juce::Colour kTextMuted    { 0xffaaaaaa };
static const juce::Colour kSelected     { 0xff3d2b6b };

// ── ResultsModel ──────────────────────────────────────────────────────────────

void ResultsModel::paintListBoxItem(int rowNumber, juce::Graphics& g,
                                    int width, int height, bool rowIsSelected)
{
    if (rowNumber >= rows.size())
        return;

    const auto& row = rows.getReference(rowNumber);

    // Row background
    g.fillAll(rowIsSelected ? kSelected : (rowNumber % 2 == 0 ? kBackground : kSurface));

    // Filename (left)
    g.setColour(kTextPrimary);
    g.setFont(juce::Font(13.0f));
    g.drawText(row.filename, 8, 0, width - 120, height,
               juce::Justification::centredLeft, true);

    // BPM + energy (right, muted)
    juce::String meta;
    if (row.bpm.isNotEmpty())
        meta = row.bpm + " bpm";
    if (row.energy.isNotEmpty())
        meta += (meta.isEmpty() ? "" : " · ") + row.energy;

    g.setColour(kTextMuted);
    g.setFont(juce::Font(11.0f));
    g.drawText(meta, width - 118, 0, 110, height,
               juce::Justification::centredRight, true);
}

void ResultsModel::listBoxItemDoubleClicked(int row, const juce::MouseEvent&)
{
    if (row < 0 || row >= rows.size())
        return;
    juce::SystemClipboard::copyTextToClipboard(rows.getReference(row).path);
}

// ── SampleMindEditor ──────────────────────────────────────────────────────────

SampleMindEditor::SampleMindEditor(SampleMindProcessor& p)
    : juce::AudioProcessorEditor(&p), processor(p)
{
    setSize(500, 440);

    // Search field
    searchField.setTextToShowWhenEmpty("Search samples…", kTextMuted);
    searchField.setColour(juce::TextEditor::backgroundColourId, kSurface);
    searchField.setColour(juce::TextEditor::textColourId, kTextPrimary);
    searchField.setColour(juce::TextEditor::outlineColourId, kAccent.withAlpha(0.4f));
    searchField.addListener(this);
    addAndMakeVisible(searchField);

    // Search button
    searchButton.setColour(juce::TextButton::buttonColourId, kAccent);
    searchButton.setColour(juce::TextButton::textColourOffId, kTextPrimary);
    searchButton.onClick = [this] { performSearch(); };
    addAndMakeVisible(searchButton);

    // Results list
    resultsList.setModel(&resultsModel);
    resultsList.setColour(juce::ListBox::backgroundColourId, kBackground);
    resultsList.setColour(juce::ListBox::outlineColourId, juce::Colours::transparentBlack);
    resultsList.setRowHeight(26);
    addAndMakeVisible(resultsList);

    // Status label
    statusLabel.setFont(juce::Font(11.0f));
    statusLabel.setColour(juce::Label::textColourId, kTextMuted);
    statusLabel.setJustificationType(juce::Justification::centredLeft);
    addAndMakeVisible(statusLabel);
}

SampleMindEditor::~SampleMindEditor() = default;

// ── paint() ───────────────────────────────────────────────────────────────────

void SampleMindEditor::paint(juce::Graphics& g)
{
    g.fillAll(kBackground);

    // Header strip
    g.setColour(kSurface);
    g.fillRect(0, 0, getWidth(), 44);

    // Title
    g.setColour(kAccent);
    g.setFont(juce::Font(15.0f, juce::Font::bold));
    g.drawText("SampleMind", 10, 0, 100, 44, juce::Justification::centredLeft);
}

// ── resized() ─────────────────────────────────────────────────────────────────

void SampleMindEditor::resized()
{
    const int w         = getWidth();
    const int h         = getHeight();
    const int hdrH      = 44;
    const int statusH   = 20;
    const int btnW      = 64;
    const int margin    = 8;

    searchField.setBounds(112, margin, w - 112 - btnW - margin * 2, hdrH - margin * 2);
    searchButton.setBounds(w - btnW - margin, margin, btnW, hdrH - margin * 2);
    resultsList.setBounds(0, hdrH, w, h - hdrH - statusH);
    statusLabel.setBounds(8, h - statusH, w - 16, statusH);
}

// ── textEditorReturnKeyPressed() ──────────────────────────────────────────────

void SampleMindEditor::textEditorReturnKeyPressed(juce::TextEditor&)
{
    performSearch();
}

// ── performSearch() ───────────────────────────────────────────────────────────

void SampleMindEditor::performSearch()
{
    auto query = searchField.getText().trim();
    statusLabel.setText("Searching…", juce::dontSendNotification);

    // Build JSON request
    juce::String requestJson = R"({"action":"search","query":")" + query + R"("})";

    // Issue request on a background thread to avoid blocking the message thread.
    juce::Thread::launch([this, requestJson]() {
        auto responseStr = processor.getSidecar().sendRequest(requestJson.toStdString());

        // Parse with JUCE's built-in JSON
        juce::var parsed;
        if (juce::JSON::parse(juce::String(responseStr), parsed).wasOk()) {
            auto* samplesArray = parsed["samples"].getArray();

            juce::Array<SampleRow> newRows;
            if (samplesArray != nullptr) {
                for (const auto& item : *samplesArray) {
                    SampleRow row;
                    row.filename = item["filename"].toString();
                    row.path     = item["path"].toString();
                    row.bpm      = item["bpm"].isVoid() ? ""
                                   : juce::String(static_cast<double>(item["bpm"]), 1);
                    row.energy   = item["energy"].toString();
                    newRows.add(row);
                }
            }

            // Update UI on the message thread
            juce::MessageManager::callAsync([this, newRows]() mutable {
                resultsModel.rows = std::move(newRows);
                resultsList.updateContent();
                statusLabel.setText(
                    juce::String(resultsModel.rows.size()) + " result(s)",
                    juce::dontSendNotification);
            });
        } else {
            juce::MessageManager::callAsync([this]() {
                statusLabel.setText("Search failed — is the sidecar running?",
                                    juce::dontSendNotification);
            });
        }
    });
}
