import csv
from pathlib import Path
from typing import List

from src.exceptions import CSVExporterError


class CSVExporter:
    @staticmethod
    def _check_and_create_directory(file_path: Path, create_parent: bool) -> None:
        if not file_path.parent.exists():
            if not create_parent:
                raise FileNotFoundError(f"Directory {file_path.parent} does not exist.")
            else:
                file_path.parent.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _check_and_create_file(file_path: Path, overwrite: bool, override_suffix: bool) -> None:
        if file_path.exists():
            if not overwrite:
                raise FileExistsError(f"File {file_path} already exists.")
        elif not override_suffix and file_path.suffix != '.csv':
            raise ValueError(f"File {file_path} is not a CSV file.")

    @staticmethod
    def run(flattened_data: List[dict], file_path: str, include_headers: bool = True,
            delimiter: str = ',', lineterminator: str = '\n', overwrite: bool = False,
            create_parent: bool = False, override_suffix: bool = False, keys_to_write: List[str] = None) -> None:
        if not isinstance(flattened_data, list) or not all(isinstance(d, dict) for d in flattened_data):
            raise TypeError("Data must be a list of dictionaries.")

        if not flattened_data:
            raise ValueError("Data is empty.")

        if keys_to_write is not None:
            flattened_data = [{k: v for k, v in d.items() if k in keys_to_write} for d in flattened_data]

        keys = flattened_data[0].keys()
        file_path = Path(file_path)

        CSVExporter._check_and_create_directory(file_path, create_parent)
        CSVExporter._check_and_create_file(file_path, overwrite, override_suffix)

        try:
            with open(file_path, "w", encoding="UTF8", newline='') as csv_file:
                csv_writer = csv.DictWriter(csv_file, fieldnames=keys, delimiter=delimiter, lineterminator=lineterminator)

                if include_headers:
                    csv_writer.writeheader()

                for row in flattened_data:
                    csv_writer.writerow(row)
        except (PermissionError, IOError, OSError) as e:
            raise CSVExporterError(f"Error while writing to {file_path}: {e}") from e
