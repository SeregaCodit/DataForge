from pathlib import Path

from tools.annotation_converter.reader.base import BaseReader
import xmltodict

class XMLReader(BaseReader):

    def read(self, file_path: Path) -> dict:
        data = xmltodict.parse(file_path.read_text())
        return data