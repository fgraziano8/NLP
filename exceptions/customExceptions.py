class LanguageNotSupportedError(Exception):
    def __init__(self, message):
        self.message = message


class LanguageGenericError(Exception):
    def __init__(self, message):
        self.message = message


class UnspecifiedExtensionError(Exception):
    def __init__(self, message):
        self.message = message


class ExtensionNotSupportedError(Exception):
    def __init__(self, message):
        self.message = message


class UnspecifiedQuestionAnsweringError(Exception):
    def __init__(self, message):
        self.message = message