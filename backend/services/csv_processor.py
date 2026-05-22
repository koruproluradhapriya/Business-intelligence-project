from services.data_intelligence_service import SUPPORTED_EXTENSIONS, process_dataset, read_dataset


def process_file(file_path: str, upload_type: str = "auto") -> dict:
    return process_dataset(file_path, upload_type)


def load_latest_dataframe(file_path: str):
    return read_dataset(file_path)
