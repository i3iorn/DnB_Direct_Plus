import getpass
import logging
from pathlib import Path
from typing import List

from src.exceptions import CSVExportError, FlattenerError, XLSXExportError
from src.decorators import timeit
from src.transformer.aligner import ArrayAligner
from src.transformer.csv_exporter import CSVExporter
from src.transformer.xlsx_exporter import XLSXExporter
from src.transformer.flattener import Flattener


class Transformer:
    """
    Processes a list of dictionaries. The list of dictionaries can be flattened and aligned. The flattened and aligned
    list of dictionaries can be exported to a CSV file.

    :param data: List of dictionaries to process.
    """
    def __init__(self, data: List[dict]):
        if not isinstance(data, list) or not all(isinstance(d, dict) for d in data):
            raise ValueError("data must be a list of dictionaries.")
        self.log = logging.getLogger(__name__)
        self.data = data

    @timeit
    def process_data(self, flattener_options: dict = None) -> List[dict]:
        """
        Flattens and aligns arrays in a list of dictionaries. If flattener_options is provided, the flattener will be
        initialized with the provided options. Otherwise, the flattener will be initialized with the default options.

        :param flattener_options:  Options to initialize the flattener with.
        :return:  List of dictionaries with flattened and aligned arrays.
        """
        try:
            flattener = Flattener(**flattener_options) if flattener_options else Flattener()
        except FlattenerError as e:
            raise RuntimeError(f"Error initializing Flattener: {e}")
        array_aligner = ArrayAligner()

        flattened_data = [flattener.flatten(d) for d in self.data]
        aligned_data = array_aligner.align_arrays(flattened_data)

        return aligned_data

    @timeit
    def export_to_csv(self, file_path: str, include_headers: bool = True, delimiter: str = ',',
                      flattener_options: dict = None, overwrite: bool = False, keys_to_write: List[str] = None,
                      do_not_flatten: bool = False
                      ) -> None:
        """
        Exports a list of dictionaries to a CSV file. If include_headers is True, the first row of the CSV file will
        contain the keys of the dictionaries. If include_headers is False, the first row of the CSV file will contain
        the values of the first dictionary.

        :param keys_to_write: List of keys to write to the CSV file. If None, all keys will be written.
        :param do_not_flatten: If True, the data will not be flattened before exporting.
        :param overwrite:  If True, the file will be overwritten if it already exists.
        :param file_path:  Path to the CSV file to write to.
        :param include_headers:  If True, the first row of the CSV file will contain the keys of the dictionaries.
        :param delimiter:  Delimiter to use between values in the CSV file.
        :param flattener_options:  Options to initialize the flattener with.
        :return:  None
        """
        if not file_path:
            raise ValueError("file_path must be provided.")

        if not Path(file_path).is_absolute():
            parent = r'C:\users\{username}\Downloads'.format(username=getpass.getuser())
            file_path = Path(parent) / file_path

        try:
            flattened_data = self.process_data(flattener_options) if not do_not_flatten else self.data
            CSVExporter.run(flattened_data, file_path, include_headers, delimiter, overwrite=overwrite, keys_to_write=keys_to_write)
        except CSVExportError as e:
            raise RuntimeError(f"Error exporting to CSV") from e
        except FlattenerError as e:
            raise RuntimeError(f"Error during flattening") from e

    def export_to_excel(self, file_path: str, include_headers: bool = True, delimiter: str = ',',
                        flattener_options: dict = None, overwrite: bool = False, keys_to_write: List[str] = None,
                        do_not_flatten: bool = False
                        ) -> None:
        """
        Exports a list of dictionaries to an Excel file. If include_headers is True, the first row of the Excel file
        will contain the keys of the dictionaries. If include_headers is False, the first row of the Excel file will
        contain the values of the first dictionary.

        :param keys_to_write: List of keys to write to the Excel file. If None, all keys will be written.
        :param do_not_flatten: If True, the data will not be flattened before exporting.
        :param overwrite:  If True, the file will be overwritten if it already exists.
        :param file_path:  Path to the Excel file to write to.
        :param include_headers:  If True, the first row of the Excel file will contain the keys of the dictionaries.
        :param delimiter:  Delimiter to use between values in the Excel file.
        :param flattener_options:  Options to initialize the flattener with.
        :return:  None
        """
        if not file_path:
            raise ValueError("file_path must be provided.")

        if not Path(file_path).is_absolute():
            parent = r'C:\users\{username}\Downloads'.format(username=getpass.getuser())
            file_path = Path(parent) / file_path

        try:
            flattened_data = self.process_data(flattener_options) if not do_not_flatten else self.data
            XLSXExporter.run(flattened_data, file_path, include_headers, overwrite=overwrite, keys_to_write=keys_to_write)
        except XLSXExportError as e:
            raise RuntimeError(f"Error exporting to CSV") from e
        except FlattenerError as e:
            raise RuntimeError(f"Error during flattening") from e