class Singleton(type):
    _instance = None

    def __new__(cls, name, bases, dct):
        if not isinstance(cls._instance, cls):
            cls._instance = super().__new__(cls, name, bases, dct)
            cls._instance.__setattr__("init_completed", False)
        return cls._instance


class ExampleUsage(metaclass=Singleton):
    def __init__(self) -> None:
        pass
