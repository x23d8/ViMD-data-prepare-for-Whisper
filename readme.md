# Introduction


This is a tool for data processing in the DAT301m with the dataset:nguyendv02/ViMD_Dataset
# Audio & Transcript Editor

A Gradio application for editing audio and text transcripts stored in a Parquet file.

## Features

### 📝 Text Editing

* View and edit transcripts
* Display metadata (region, province, speaker ID, gender)
* Restore original text
* Save text changes

### 🎵 Audio Editing

* Play both the current and original audio
* Trim audio using time ranges (milliseconds)
* Restore original audio
* Save audio changes

### 🔄 Navigation

* Move between samples
* Display the current sample index
* Mark edited samples

### 💾 Saving

* Save all changes to a new Parquet file
* Preserve the original file structure
* Automatically create a `data_edited` directory for edited files

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python audio_editor_app.py
```

The application will open at:
[http://localhost:7860](http://localhost:7860)

## User Guide
0. **Data prepare**: 
   * In the "prepare.ipynb" contains download and data pre-processing method
   * After run all the notebook the data will clean all the audio which have >30s lenngth 
   * The cleaned data will contain in the data folder. The processed data in the long_audio. After edit the data will be stored at the long_audio_edited
   

1. **View samples**: The first sample loads automatically when the app starts.
2. **Navigation**: Use "⬅️ Previous Sample" and "Next Sample ➡️" to move between samples.
3. **Edit text**:

   * Modify the text directly in the editor.
   * Click "💾 Save Text" to save changes.
   * Click "↺ Restore Text" to revert to the original transcript.
4. **Trim audio**:

   * Play the audio to identify the segment you want.
   * Adjust the "Start Time" and "End Time" sliders.
   * Click "✂️ Trim Audio" to apply trimming.
   * Click "↺ Restore Audio" to revert to the original audio.
5. **Save all changes**: Click "💾 SAVE ALL CHANGES" when editing is complete.


## Data Structure

The app supports Parquet files with the following columns:

* `region`: Region
* `province_code`: Province code
* `province_name`: Province name
* `filename`: Original file name
* `text`: Transcript text
* `speakerID`: Speaker ID
* `gender`: Gender (1: Male, 0: Female)
* `audio`: Audio stored as WAV bytes

## Notes

* The original file is never modified.
* Edited files are saved in the `data_edited/` directory.
* Output files include the suffix `_edited.parquet`.
* Audio must be stored in WAV format within the Parquet file.

---

