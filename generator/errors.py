"""Generator failures. Unsupported specifications are errors, not guesses."""


class GeneratorError(Exception):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(f"{code}: {message}")
