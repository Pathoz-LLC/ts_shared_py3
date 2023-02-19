from typing import Any


class Singleton(type):
    def __init__(self, name, bases, dic):
        self.__single_instance = None
        super().__init__(name, bases, dic)

    def __call__(cls, *args, **kwargs):
        if cls.__single_instance:
            return cls.__single_instance
        # if args or kwargs:
        #     cls = super().__call__(*args, **kwargs)
        single_obj = cls.__new__(cls)
        setattr(single_obj, "init_completed", False)
        single_obj.__init__(*args, **kwargs)
        setattr(single_obj, "init_completed", True)
        cls.__single_instance = single_obj
        return single_obj


# class Singleton(type):
#     _instances: map[str, Any] = {}

#     def __call__(cls, *args: Any, **kwargs: Any) -> Any:
#         #
#         if args or kwargs:
#             # assert (False, "skipping Singleton logic")
#             cls = super().__call__(*args, **kwargs)

#         class_type = str(type(cls))
#         inst = getattr(Singleton._instances, class_type, None)
#         alreadyExists = isinstance(inst, cls)
#         if alreadyExists:
#             return inst

#         inst = cls.__new__(cls)
#         cls.__init__(inst)
#         Singleton._instances[class_type] = inst
#         return inst

# def __new__(cls, name, bases, dct):
#     if not isinstance(cls._instance, cls):
#         cls._instance = super().__new__(cls, name, bases, dct)
#         setattr(cls._instance, "init_completed", False)
#     return cls._instance


# class ExampleUsage(metaclass=Singleton):
#     def __init__(self) -> None:
#         pass
