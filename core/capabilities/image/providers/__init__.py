"""image providers 包。当前 provider：stub（无真实图像 API）。

接真实 provider 时：新增 providers/<vendor>.py 继承 BaseProvider，
在 ImageAdapter 里换绑即可，业务层不动。
"""
from capabilities.image.providers.stub import ImageStubProvider

__all__ = ["ImageStubProvider"]
