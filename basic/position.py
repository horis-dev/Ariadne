import msgspec  

class ApiPosition(msgspec.Struct, tag="api_position", tag_field="_type", frozen=True):  
    whose: bytes  
    name: str  
    is_required: bool = True  

class TablePosition(msgspec.Struct, tag="table_position", tag_field="_type", frozen=True):  
    table_name: str  
    col_name: str  

class ResponsePosition(msgspec.Struct, tag="response_position", tag_field="_type", frozen=True):  
    type: str 
    where: str  
    from_api: bytes  

class FilePosition(msgspec.Struct, tag="file_position", tag_field="_type", frozen=True):  
    is_content: bool # 0 name / 1 content
    file_path: str
