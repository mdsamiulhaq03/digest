class AppError(Exception):
    status_code = 500

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class NotFoundError(AppError):
    status_code = 404


class DocumentNotFoundError(NotFoundError):
    def __init__(self, document_id: str) -> None:
        super().__init__(f"Document {document_id} not found")
        self.document_id = document_id
