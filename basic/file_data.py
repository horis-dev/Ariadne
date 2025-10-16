import msgspec
import base64
from basic.fuzzword import FuzzWord
from basic.position import FilePosition

class FileData(msgspec.Struct, tag="file_data", frozen=True):
    file_path: str = ""
    file_name: str = ""
    file_content: bytes = b''  # TODO: file_content may change

    def to_fuzzword(self) -> list[FuzzWord]:
        name_fuzzword = FuzzWord(
            value=self.file_name,
            position=FilePosition(
                file_path=self.file_path,
                is_content=False
            )
        )
        if self.file_content == b'':
            return [name_fuzzword]
        content_fuzzword = FuzzWord(
            value=base64.b64encode(self.file_content).decode(),
            position=FilePosition(
                file_path=self.file_path,
                is_content=True
            )
        )
        return [name_fuzzword, content_fuzzword]
        # return [content_fuzzword]
