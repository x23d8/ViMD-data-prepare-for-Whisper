from huggingface_hub import snapshot_download
dataset_dir = 'D:\SPL\Code\PhanBietVungMien\DAT301m\data' # chọn vị trí muốn lưu (tối thiểu 60gb) do hf không cho tải từng folder - file lẻ thì được
snapshot_download(
    repo_id="nguyendv02/ViMD_Dataset",
    repo_type="dataset",  # quan trọng 
    local_dir=dataset_dir,
    resume_download=True
)

