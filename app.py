import gradio as gr
import pandas as pd
import numpy as np
from pathlib import Path
import io
from pydub import AudioSegment
import tempfile
import os
from typing import Dict, List, Tuple, Optional
import glob

def get_available_files(data_dir: str = ".") -> List[Tuple[str, str]]:
    """Get list of available parquet files with their sizes"""
    data_path = Path(data_dir) / "long_audio"
    parquet_files = sorted(glob.glob(str(data_path / "*.parquet")))
    
    file_info = []
    for file_path in parquet_files:
        file_name = Path(file_path).name
        file_size = os.path.getsize(file_path)
        size_mb = file_size / (1024 * 1024)
        file_info.append((f"{file_name} ({size_mb:.1f} MB)", file_name))
    
    return file_info

class AudioEditorApp:
    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir)
        self.df = None
        self.original_df = None
        self.current_index = 0
        self.modified_indices = set()
        self.loaded = False
        self.original_data = {}  # Maps row_id -> {'audio': bytes, 'text': str}
        self.next_row_id = 0
        
    def load_data(self, selected_files: List[str] = None):
        """Load selected parquet files from the long_audio directory"""
        import pyarrow.parquet as pq
        
        if selected_files is None or len(selected_files) == 0:
            parquet_files = sorted(glob.glob(str(self.data_dir / "long_audio" / "*.parquet")))
        else:
            parquet_files = [str(self.data_dir / "long_audio" / f) for f in selected_files]
        
        if not parquet_files:
            raise ValueError(f"No parquet files found in {self.data_dir / 'long_audio'}")
        
        print(f"Loading {len(parquet_files)} parquet files...")
        dfs = []
        for file in parquet_files:
            print(f"Loading {Path(file).name}...")
            
            parquet_file = pq.ParquetFile(file)
            total_rows = parquet_file.metadata.num_rows
            print(f"  Total rows: {total_rows}")
            
            batches = []
            batch_size = 1000  # Process 1000 rows at a time
            for i, batch in enumerate(parquet_file.iter_batches(batch_size=batch_size)):
                df_batch = batch.to_pandas()
                batches.append(df_batch)
                if (i + 1) % 10 == 0:  # Progress update every 10 batches
                    print(f"  Loaded {(i + 1) * batch_size} / {total_rows} rows...")
            
            df_temp = pd.concat(batches, ignore_index=True)
            df_temp['source_file'] = Path(file).name
            dfs.append(df_temp)
            print(f"  ✓ Completed loading {Path(file).name}")
        
        self.df = pd.concat(dfs, ignore_index=True)
        self.original_df = self.df.copy()
        self.loaded = True
        self.current_index = 0
        self.modified_indices = set()
        
        # Initialize row IDs and store original data
        self.df['row_id'] = range(len(self.df))
        self.next_row_id = len(self.df)
        
        # Store original audio and text for each row
        for idx, row in self.df.iterrows():
            row_id = row['row_id']
            self.original_data[row_id] = {
                'audio': row['audio']['bytes'],
                'text': row['text']
            }
        
        print(f"Loaded {len(self.df)} samples total")
        
    def bytes_to_audio_segment(self, audio_bytes: bytes) -> AudioSegment:
        """Convert audio bytes to AudioSegment"""
        return AudioSegment.from_file(io.BytesIO(audio_bytes), format="wav")
    
    def audio_segment_to_bytes(self, audio_segment: AudioSegment) -> bytes:
        """Convert AudioSegment to bytes"""
        buffer = io.BytesIO()
        audio_segment.export(buffer, format="wav")
        return buffer.getvalue()
    
    def is_loaded(self) -> bool:
        """Check if data has been loaded"""
        return self.loaded and self.df is not None
    
    def get_audio_file(self, index: int) -> str:
        """Get audio as temporary file path for Gradio"""
        if not self.is_loaded() or index < 0 or index >= len(self.df):
            return None
        
        audio_bytes = self.df.iloc[index]['audio']['bytes']
        
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
        temp_file.write(audio_bytes)
        temp_file.close()
        
        return temp_file.name
    
    def get_sample_info(self, index: int) -> Dict:
        """Get all information for a sample"""
        if not self.is_loaded() or index < 0 or index >= len(self.df):
            return None
        
        row = self.df.iloc[index]
        audio_bytes = row['audio']['bytes']
        audio_segment = self.bytes_to_audio_segment(audio_bytes)
        duration = len(audio_segment) / 1000.0  # Convert to seconds
        
        return {
            'index': index,
            'total': len(self.df),
            'region': row['region'],
            'province_code': row['province_code'],
            'province_name': row['province_name'],
            'filename': row['filename'],
            'text': row['text'],
            'speakerID': row['speakerID'],
            'gender': 'Nam' if row['gender'] == 1 else 'Nữ',
            'audio_duration': duration,
            'source_file': row['source_file'],
            'modified': index in self.modified_indices
        }
    
    def update_text(self, index: int, new_text: str):
        """Update the text transcript for a sample"""
        if index >= 0 and index < len(self.df):
            self.df.at[index, 'text'] = new_text
            self.modified_indices.add(index)
    
    def trim_audio(self, index: int, start_ms: float, end_ms: float):
        """Trim audio to specified range and create new entry for the remaining part"""
        if index < 0 or index >= len(self.df):
            return
        
        audio_bytes = self.df.iloc[index]['audio']['bytes']
        audio_segment = self.bytes_to_audio_segment(audio_bytes)
        
        # Split audio into two parts
        kept_part = audio_segment[start_ms:end_ms]
        remaining_part = audio_segment[end_ms:]
        
        # Convert to bytes
        kept_bytes = self.audio_segment_to_bytes(kept_part)
        remaining_bytes = self.audio_segment_to_bytes(remaining_part)
        
        # Update the current row with the kept part
        self.df.at[index, 'audio'] = {'bytes': kept_bytes}
        self.modified_indices.add(index)
        
        # Only create a new row if there's remaining audio
        if len(remaining_part) > 0:
            # Create a new row for the remaining part by copying the current row
            new_row = self.df.iloc[index].copy()
            new_row['audio'] = {'bytes': remaining_bytes}
            
            # Generate new filename with numeric suffix
            original_filename = new_row['filename']
            # Find the next available number for this filename
            base_filename = original_filename
            counter = 1
            # Check if filename already has a number suffix
            if '{' in original_filename and '}' in original_filename:
                # Extract base filename and current number
                parts = original_filename.rsplit('{', 1)
                base_filename = parts[0]
                try:
                    current_num = int(parts[1].rstrip('}'))
                    counter = current_num + 1
                except ValueError:
                    pass
            
            # Find the highest existing number for this base filename
            for _, row in self.df.iterrows():
                fname = row['filename']
                if fname.startswith(base_filename + '{'):
                    try:
                        num_part = fname.split('{')[1].rstrip('}')
                        num = int(num_part)
                        counter = max(counter, num + 1)
                    except (IndexError, ValueError):
                        pass
            
            new_row['filename'] = f"{base_filename}{{{counter}}}"
            
            # Assign a new unique row_id for the split segment
            new_row_id = self.next_row_id
            self.next_row_id += 1
            new_row['row_id'] = new_row_id
            
            # Store original data for the new row (same as parent)
            parent_row_id = self.df.iloc[index]['row_id']
            self.original_data[new_row_id] = self.original_data[parent_row_id].copy()
            
            # Insert the new row right after the current index
            # Split dataframe and concatenate
            df_before = self.df.iloc[:index + 1]
            df_after = self.df.iloc[index + 1:]
            self.df = pd.concat([df_before, pd.DataFrame([new_row]), df_after], ignore_index=True)
            
            # Update modified indices - shift all indices after the insertion point
            new_modified_indices = set()
            for idx in self.modified_indices:
                if idx <= index:
                    new_modified_indices.add(idx)
                else:
                    new_modified_indices.add(idx + 1)
            new_modified_indices.add(index + 1)  # Mark the new row as modified
            self.modified_indices = new_modified_indices

    
    def reset_audio(self, index: int):
        """Reset audio to original"""
        if index < 0 or index >= len(self.df):
            return
        
        # Get the row_id to find original data
        row_id = self.df.iloc[index]['row_id']
        if row_id in self.original_data:
            original_audio_bytes = self.original_data[row_id]['audio']
            self.df.at[index, 'audio'] = {'bytes': original_audio_bytes}
            
            # Check if text was also modified
            original_text = self.original_data[row_id]['text']
            if self.df.at[index, 'text'] == original_text:
                self.modified_indices.discard(index)
    
    def reset_text(self, index: int):
        """Reset text to original"""
        if index < 0 or index >= len(self.df):
            return
        
        # Get the row_id to find original data
        row_id = self.df.iloc[index]['row_id']
        if row_id in self.original_data:
            original_text = self.original_data[row_id]['text']
            self.df.at[index, 'text'] = original_text
            
            # Check if audio was also modified
            original_audio_bytes = self.original_data[row_id]['audio']
            current_audio_bytes = self.df.iloc[index]['audio']['bytes']
            if original_audio_bytes == current_audio_bytes:
                self.modified_indices.discard(index)
    
    def delete_audio(self, index: int) -> int:
        """Delete an audio entry from the dataset
        Returns the new current index after deletion"""
        if index < 0 or index >= len(self.df):
            return index
        
        self.df = self.df.drop(self.df.index[index]).reset_index(drop=True)
        
        new_modified_indices = set()
        for idx in self.modified_indices:
            if idx < index:
                new_modified_indices.add(idx)
            elif idx > index:
                new_modified_indices.add(idx - 1)
        self.modified_indices = new_modified_indices
        

        if len(self.df) > 0:
            self.modified_indices.add(max(0, index - 1))
        
        new_index = min(index, len(self.df) - 1) if len(self.df) > 0 else 0
        return new_index
    
    def save_modifications(self) -> str:
        """Save all modifications to new parquet files"""
        if len(self.modified_indices) == 0:
            return "Không có thay đổi nào để lưu."
        
        # Group by source file
        source_files = self.df['source_file'].unique()
        saved_files = []
        
        output_dir = self.data_dir / "long_audio_edited"
        output_dir.mkdir(exist_ok=True)
        
        for source_file in source_files:
            # Get rows from this source file
            mask = self.df['source_file'] == source_file
            df_subset = self.df[mask].copy()
            
            # Drop the source_file and row_id columns before saving
            df_subset = df_subset.drop(columns=['source_file', 'row_id'])
            
            # Save to new file
            output_path = output_dir / source_file.replace('.parquet', '_edited.parquet')
            df_subset.to_parquet(output_path, index=False)
            saved_files.append(output_path.name)
        
        message = f"✅ Đã lưu {len(self.modified_indices)} mẫu đã chỉnh sửa vào {len(saved_files)} file:\n"
        message += "\n".join(f"  - {f}" for f in saved_files[:10])
        if len(saved_files) > 10:
            message += f"\n  ... và {len(saved_files) - 10} file khác"
        message += f"\n\nThư mục: {output_dir}"
        
        return message

# Global app instance
app = None

def init_app():
    global app
    if app is None:
        app = AudioEditorApp("data")
    return app

def load_files_handler(selected_files):
    """Handle loading selected files"""
    global app
    
    if not selected_files or len(selected_files) == 0:
        return "❌ Vui lòng chọn ít nhất một file để load", gr.update(visible=False), "", "", None, None, 0, 10000, 0
    
    try:
        app = AudioEditorApp("data")
        app.load_data(selected_files)
        
        # Load first sample
        first_sample = load_sample(0)
        
        message = f"✅ Đã load thành công {len(selected_files)} file với {len(app.df)} mẫu"
        return (message, gr.update(visible=True)) + first_sample
    except Exception as e:
        import traceback
        error_msg = f"❌ Lỗi khi load file: {str(e)}\n{traceback.format_exc()}"
        return error_msg, gr.update(visible=False), "", "", None, None, 0, 10000, 0

def load_sample(index: int):
    """Load and display a sample"""
    app = init_app()
    info = app.get_sample_info(index)
    
    if info is None:
        return None, "", "", None, 0, info['audio_duration'] * 1000
    
    audio_path = app.get_audio_file(index)
    
    # Create metadata display
    metadata = f"""**Mẫu {info['index'] + 1}/{info['total']}** {'🔴 Đã chỉnh sửa' if info['modified'] else ''}

**Vùng miền:** {info['region']}
**Tỉnh:** {info['province_name']} ({info['province_code']})
**Speaker ID:** {info['speakerID']}
**Giới tính:** {info['gender']}
**File gốc:** {info['filename']}
**Thời lượng audio:** {info['audio_duration']:.2f}s
**Source:** {info['source_file']}"""
    
    return (
        metadata,
        info['text'],
        audio_path,
        audio_path,
        0,
        info['audio_duration'] * 1000,
        index
    )

def navigate(direction: int, current_index: int):
    """Navigate to previous or next sample"""
    app = init_app()
    new_index = max(0, min(current_index + direction, len(app.df) - 1))
    return load_sample(new_index)

def update_text_handler(text: str, index: int):
    """Handle text update"""
    app = init_app()
    app.update_text(index, text)
    return f"✅ Đã cập nhật text cho mẫu {index + 1}"

def trim_audio_handler(start_ms: float, end_ms: float, index: int):
    """Handle audio trimming"""
    app = init_app()
    
    if start_ms >= end_ms:
        return "❌ Thời gian bắt đầu phải nhỏ hơn thời gian kết thúc", None, index
    
    app.trim_audio(index, start_ms, end_ms)
    
    # Reload the sample to show updated audio
    results = load_sample(index)
    message = f"✅ Đã cắt audio từ {start_ms/1000:.2f}s đến {end_ms/1000:.2f}s\n"
    message += f"Phần giữ lại được lưu tại mẫu {index + 1}\n"
    message += f"Phần còn lại được lưu tại mẫu {index + 2}"
    return message, results[2], index

def reset_audio_handler(index: int):
    """Reset audio to original"""
    app = init_app()
    app.reset_audio(index)
    results = load_sample(index)
    return f"✅ Đã khôi phục audio gốc", results[2], index

def reset_text_handler(index: int):
    """Reset text to original"""
    app = init_app()
    app.reset_text(index)
    results = load_sample(index)
    return f"✅ Đã khôi phục text gốc", results[1], index

def delete_audio_handler(index: int):
    """Handle audio deletion"""
    app = init_app()
    
    if len(app.df) <= 1:
        return "❌ Không thể xóa mẫu cuối cùng", None, None, None, None, 0, 10000, index
    
    # Delete the audio
    new_index = app.delete_audio(index)
    
    # Load the new current sample
    results = load_sample(new_index)
    
    message = f"✅ Đã xóa mẫu {index + 1}. Tổng số mẫu còn lại: {len(app.df)}"
    return (message,) + results

def save_handler():
    """Handle save operation"""
    app = init_app()
    return app.save_modifications()

# Create Gradio interface
with gr.Blocks(title="Audio & Transcript Editor", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🎙️ Audio & Transcript Editor")
    gr.Markdown("Chỉnh sửa audio và text transcript từ file parquet")
    
    # File Selection Section
    with gr.Row():
        with gr.Column():
            gr.Markdown("### 📁 Chọn File để Load")
            
            # Get available files
            available_files = get_available_files("data")
            file_choices = [display_name for display_name, _ in available_files]
            file_values = [file_name for _, file_name in available_files]
            
            file_selector = gr.Dropdown(
                choices=file_choices,
                value=None,
                multiselect=True,
                label="Chọn file parquet (có thể chọn nhiều file)",
                info=f"Có {len(available_files)} file trong thư mục long_audio"
            )
            
            with gr.Row():
                load_btn = gr.Button("📥 Load File Đã Chọn", variant="primary", size="lg")
            
            load_status = gr.Textbox(
                label="Trạng thái",
                value="Chưa load file nào. Vui lòng chọn file và nhấn 'Load File Đã Chọn'",
                interactive=False,
                lines=2
            )
    
    # Hidden state to track current index
    current_index_state = gr.State(value=0)
    
    # Main editing interface (hidden until files are loaded)
    with gr.Column(visible=False) as editing_interface:
        with gr.Row():
            # Left column - Text editing
            with gr.Column(scale=1):
                gr.Markdown("### 📝 Text Transcript")
                metadata_display = gr.Markdown()
                text_editor = gr.TextArea(
                    label="Transcript",
                    placeholder="Nhập hoặc chỉnh sửa transcript...",
                    lines=10
                )
                
                with gr.Row():
                    reset_text_btn = gr.Button("↺ Khôi phục Text", variant="secondary", size="sm")
                    update_text_btn = gr.Button("💾 Lưu Text", variant="primary", size="sm")
                
                text_status = gr.Textbox(label="Trạng thái", interactive=False, show_label=False)
            
            # Right column - Audio editing
            with gr.Column(scale=1):
                gr.Markdown("### 🎵 Audio Player & Trimmer")
                
                audio_player = gr.Audio(
                    label="Audio hiện tại",
                    type="filepath",
                    interactive=False
                )
                
                original_audio = gr.Audio(
                    label="Audio gốc (để tham khảo)",
                    type="filepath",
                    interactive=False,
                    visible=True
                )
                
                gr.Markdown("**Cắt Audio (milliseconds)**")
                with gr.Row():
                    start_time = gr.Slider(
                        minimum=0,
                        maximum=30000,
                        value=0,
                        step=10,
                        label="Thời gian bắt đầu (ms)"
                    )
                    end_time = gr.Slider(
                        minimum=0,
                        maximum=40000,
                        value=40000,
                        step=10,
                        label="Thời gian kết thúc (ms)"
                    )
                
                with gr.Row():
                    reset_audio_btn = gr.Button("↺ Khôi phục Audio", variant="secondary", size="sm")
                    delete_btn = gr.Button("🗑️ Xóa Audio", variant="stop", size="sm")
                    trim_btn = gr.Button("✂️ Cắt Audio", variant="primary", size="sm")
                
                audio_status = gr.Textbox(label="Trạng thái", interactive=False, show_label=False)
        
        # Navigation and Save
        with gr.Row():
            prev_btn = gr.Button("⬅️ Mẫu trước", size="lg")
            next_btn = gr.Button("Mẫu sau ➡️", size="lg")
            save_btn = gr.Button("💾 LƯU TẤT CẢ THAY ĐỔI", variant="primary", size="lg")
        
        save_status = gr.Textbox(label="Kết quả lưu", interactive=False, lines=5)
    
    # Event handlers
    
    # Map display names back to file names for loading
    def map_selected_files(selected_display_names):
        if not selected_display_names:
            return []
        file_map = {display: fname for display, fname in available_files}
        return [file_map[display] for display in selected_display_names if display in file_map]
    
    # Load button handler
    def load_and_show(selected_display_names):
        selected_files = map_selected_files(selected_display_names)
        return load_files_handler(selected_files)
    
    load_btn.click(
        fn=load_and_show,
        inputs=[file_selector],
        outputs=[load_status, editing_interface, metadata_display, text_editor, audio_player, original_audio, start_time, end_time, current_index_state]
    )
    
    prev_btn.click(
        fn=lambda idx: navigate(-1, idx),
        inputs=[current_index_state],
        outputs=[metadata_display, text_editor, audio_player, original_audio, start_time, end_time, current_index_state]
    )
    
    next_btn.click(
        fn=lambda idx: navigate(1, idx),
        inputs=[current_index_state],
        outputs=[metadata_display, text_editor, audio_player, original_audio, start_time, end_time, current_index_state]
    )
    
    update_text_btn.click(
        fn=update_text_handler,
        inputs=[text_editor, current_index_state],
        outputs=[text_status]
    )
    
    reset_text_btn.click(
        fn=reset_text_handler,
        inputs=[current_index_state],
        outputs=[text_status, text_editor]
    )
    
    trim_btn.click(
        fn=trim_audio_handler,
        inputs=[start_time, end_time, current_index_state],
        outputs=[audio_status, audio_player, current_index_state]
    )
    
    reset_audio_btn.click(
        fn=reset_audio_handler,
        inputs=[current_index_state],
        outputs=[audio_status, audio_player, current_index_state]
    )
    
    delete_btn.click(
        fn=delete_audio_handler,
        inputs=[current_index_state],
        outputs=[audio_status, metadata_display, text_editor, audio_player, original_audio, start_time, end_time, current_index_state]
    )
    
    save_btn.click(
        fn=save_handler,
        outputs=[save_status]
    )

if __name__ == "__main__":
    demo.launch(share=False, server_name="localhost", server_port=7860)
