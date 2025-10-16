class TableSubstractError(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)

class Api2HTTPRequestError(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)