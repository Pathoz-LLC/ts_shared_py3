class Singleton(type):
    _instances = {}  # set, not dict

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class ExampleUsage(metaclass=Singleton):
    def __init__(self) -> None:
        pass
