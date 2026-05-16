import importlib
import pkgutil


METRIC_REGISTRY = {}


def register_metric(name):
    def decorator(func):
        METRIC_REGISTRY[name] = func
        return func
    return decorator


def get_metric(name):
    if name not in METRIC_REGISTRY:
        raise ValueError(f"Unknown metric: {name}")
    return METRIC_REGISTRY[name]


def auto_import_metrics():

    package_name = "evalforge.metrics"
    package = importlib.import_module(package_name)

    for _, module_name, _ in pkgutil.iter_modules(package.__path__):

        if module_name.endswith("_distance") or module_name.endswith("_judge"):
            importlib.import_module(f"{package_name}.{module_name}")


auto_import_metrics()