from __future__ import annotations

from importlib import import_module
from typing import Callable

from trading_dashboard.use_cases import CreditCanaryModule, CrossAssetRegimeModule

ModuleFactory = Callable[[], object]


MODULE_REGISTRY: dict[str, ModuleFactory] = {
    "credit_canary": CreditCanaryModule,
    "cross_asset_regime": CrossAssetRegimeModule,
}


def _load_dotted_module(spec: str) -> object:
    """Load module class from dotted path: package.module:ClassName"""
    if ":" not in spec:
        raise ValueError(f"Invalid dotted module '{spec}'. Use package.module:ClassName")
    mod_name, cls_name = spec.split(":", 1)
    mod = import_module(mod_name)
    cls = getattr(mod, cls_name)
    return cls()


def build_modules(names: tuple[str, ...], dynamic_specs: tuple[str, ...] = ()) -> list[object]:
    modules: list[object] = []
    for name in names:
        factory = MODULE_REGISTRY.get(name)
        if factory is None:
            available = ", ".join(sorted(MODULE_REGISTRY))
            raise ValueError(f"Unknown module '{name}'. Available modules: {available}")
        modules.append(factory())
    for spec in dynamic_specs:
        modules.append(_load_dotted_module(spec))
    return modules
