import importlib
import pkgutil

TASK_REGISTRY = {}


def register_task(cls):
    """
    注册 task
    """
    TASK_REGISTRY[cls.name] = cls
    return cls


def get_task(name):
    """
    获取 task 实例
    """
    if name not in TASK_REGISTRY:
        raise ValueError(f"Unknown task {name}")
    return TASK_REGISTRY[name]()


def auto_import_tasks():
    """
    自动扫描 tasks 目录加载 plugin
    """
    package_name = "evalforge.tasks"
    package = importlib.import_module(package_name)

    for _, module_name, _ in pkgutil.iter_modules(package.__path__):
        if module_name.endswith("_task"):
            importlib.import_module(f"{package_name}.{module_name}")