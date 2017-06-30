class _BaseException(Exception):
    def __init__(self, message, *args) -> None:
        super().__init__(*args)
        self.message = message


class IntegrationTestException(_BaseException):
    pass


class NfvValidationException(IntegrationTestException):
    pass


class SdnValidationException(IntegrationTestException):
    pass
