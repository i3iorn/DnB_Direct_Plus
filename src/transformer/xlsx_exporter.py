from pathlib import Path
from typing import List

from openpyxl.workbook import Workbook


class XLSXExporter:
    """
    An Exporter object for XLSX files. This class is a wrapper around openpyxl. It provides a convenient interface for
    exporting data into XLSX files.
    """
    @staticmethod
    def _check_and_create_directory(file_path: Path, create_parent: bool) -> None:
        """
        Checks if the parent directory of the file exists. If create_parent is True, the parent directory will be
        created if it does not exist.
        :param file_path:
        :param create_parent:
        :return:
        """
        if not file_path.parent.exists():
            if not create_parent:
                raise FileNotFoundError(f"Directory {file_path.parent} does not exist.")
            else:
                file_path.parent.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _check_and_create_file(file_path: Path, overwrite: bool, override_suffix: bool) -> None:
        """
        Checks if the file exists and if it is a XLSX file. If overwrite is False, a FileExistsError will be raised if
        the file already exists. If override_suffix is False, a ValueError will be raised if the file extension is not
        '.xlsx'.
        :param file_path:
        :param overwrite:
        :param override_suffix:
        :return:
        """
        if file_path.exists():
            if not overwrite:
                raise FileExistsError(f"File {file_path} already exists.")
        elif not override_suffix and file_path.suffix != '.xlsx':
            raise ValueError(f"File {file_path} is not a XLSX file.")

    @staticmethod
    def run(data: List[dict], file_path: str, include_headers: bool = True, overwrite: bool = False,
            create_parent: bool = False, override_suffix: bool = True, keys_to_write: List[str] = None) -> None:
        """
        Exports a list of dictionaries to an XLSX file. If include_headers is True, the first row of the XLSX file will
        contain the keys of the dictionaries. If include_headers is False, the first row of the XLSX file will contain
        the values of the first dictionary.

        :param keys_to_write: List of keys to write to the XLSX file. If None, all keys will be written.
        :param overwrite:  If True, the file will be overwritten if it already exists.
        :param file_path:  Path to the XLSX file to write to.
        :param include_headers:  If True, the first row of the XLSX file will contain the keys of the dictionaries.
        :param create_parent:  If True, the parent directory of the file will be created if it does not exist.
        :param override_suffix:  If True, the file extension of the file will be ignored.
        :return:  None
        """
        if not isinstance(data, list) or not all(isinstance(d, dict) for d in data):
            raise TypeError("Data must be a list of dictionaries.")

        if not data:
            raise ValueError("Data is empty.")

        if keys_to_write is not None:
            data = [{k: v for k, v in d.items() if k in keys_to_write} for d in data]

        file_path = Path(file_path)

        XLSXExporter._check_and_create_directory(file_path, create_parent)
        XLSXExporter._check_and_create_file(file_path, overwrite, override_suffix)

        workbook = Workbook()
        worksheet = workbook.active

        if include_headers:
            worksheet.append(list(data[0].keys()))

        for row in data:
            worksheet.append(list(row.values()))

        workbook.save(file_path)
        raise NotImplementedError('None values are outputted as TRUE/FALSE in Excel.')
