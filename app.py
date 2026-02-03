import gradio as gr
import pandas as pd
import numpy as np
import soundfile as sf
import io
import glob
import os
import pyarrow.parquet as pq

DATA_DIR = r"data\long_audio"
LIMIT = 30
OUTPUT_FILE = "edited_output.parquet"

# ==============================
# AUDIO UTILS
# ==============================
def read_audio(audio_bytes):
    data, sr = sf.read(io.BytesIO(audio_bytes), dtype="float32")

    if data.ndim > 1:
        data = data.mean(axis=1)

    return sr, data


def write_audio(sr, audio_np):
    buffer = io.BytesIO()
    sf.write(buffer, audio_np, sr, format="WAV")
    return buffer.getvalue()


def get_duration(audio_bytes):
    info = sf.info(io.BytesIO(audio_bytes))
    return info.frames / info.samplerate


# ==============================
# LOAD DATASET
# ==============================
print("Loading parquet...")

files = glob.glob(os.path.join(DATA_DIR, "*.parquet"))

dfs = []
for f in files:
    print(f"Reading {f}...")
    try:
        # Read the parquet file with combine_chunks to avoid chunked arrays
        parquet_file = pq.ParquetFile(f)
        table = parquet_file.read()
        
        # Combine chunks for nested columns
        table = table.combine_chunks()
        
        # Convert to pandas
        df_temp = table.to_pandas()
        dfs.append(df_temp)
        print(f"  ✓ Successfully loaded {len(df_temp)} rows")
    except Exception as e:
        print(f"  ✗ Error: {e}")
        raise

df = pd.concat(dfs, ignore_index=True)
print(f"\nTotal rows: {len(df)}")

print("Scanning long audio...")
pending_indices = []

for i, item in enumerate(df["audio"]):
    dur = get_duration(item["bytes"])
    if dur > LIMIT:
        pending_indices.append(i)

print("Need editing:", len(pending_indices))

pointer = 0


# ==============================
# LOAD SAMPLE
# ==============================
def load_sample():
    global pointer

    if pointer >= len(pending_indices):
        return None, "", "✅ Done all samples"

    idx = pending_indices[pointer]
    row = df.iloc[idx]

    sr, audio = read_audio(row["audio"]["bytes"])
    duration = len(audio) / sr

    transcript = row.get("transcript", "")

    status = f"Sample {pointer+1}/{len(pending_indices)} | {duration:.2f}s"

    return (sr, audio), transcript, status


# ==============================
# SAVE EDIT
# ==============================
def save_and_next(audio_data, transcript, start, end):
    global pointer

    if audio_data is None:
        return load_sample()

    idx = pending_indices[pointer]

    sr, audio = audio_data

    start_i = int(start * sr)
    end_i = int(end * sr)

    cut_audio = audio[start_i:end_i]
    new_bytes = write_audio(sr, cut_audio)

    df.at[idx, "audio"] = {
        "bytes": new_bytes,
        "path": df.iloc[idx]["audio"].get("path", "")
    }

    df.at[idx, "transcript"] = transcript

    pointer += 1

    return load_sample()


# ==============================
# EXPORT
# ==============================
def export_parquet():
    print("Exporting to parquet...")
    df.to_parquet(OUTPUT_FILE, compression="snappy", engine="pyarrow")
    print(f"Saved to {OUTPUT_FILE}")
    return f"✅ Saved to {OUTPUT_FILE}"


# ==============================
# UI
# ==============================
with gr.Blocks() as app:
    gr.Markdown("# 🎧 Audio Dataset Editor")

    status = gr.Textbox(label="Status")

    audio = gr.Audio(type="numpy", label="Audio")

    transcript = gr.Textbox(label="Transcript", lines=3)

    with gr.Row():
        start = gr.Number(label="Start time (sec)", value=0)
        end = gr.Number(label="End time (sec)", value=30)

    with gr.Row():
        next_btn = gr.Button("OK → Next", variant="primary")
        export_btn = gr.Button("Export Parquet", variant="secondary")

    next_btn.click(
        save_and_next,
        inputs=[audio, transcript, start, end],
        outputs=[audio, transcript, status],
    )

    export_btn.click(export_parquet, outputs=status)

    app.load(load_sample, outputs=[audio, transcript, status])

app.launch()