"""Intel Xe-LP assets from donor 20A2314a, qualified for target 20G1443."""

from ..base import BaseHardware, HardwareVariant, HardwareVariantGraphicsSubclass
from ...base import PatchType


class IntelXeLP(BaseHardware):
    # Implemented WhateverXe backends; catalogued but unsupported families are excluded.
    DEVICE_IDS = {0x9A40, 0x9A49, 0x9A78, 0x46D0, 0x46D1, 0x46D2, 0x46D3, 0x46D4}

    def name(self) -> str:
        return f"{self.hardware_variant()}: Intel Xe-LP"

    def present(self) -> bool:
        return any(
            gpu.vendor_id == 0x8086 and gpu.device_id in self.DEVICE_IDS
            and gpu.class_code not in (None, 0, 0xFFFFFFFF)
            for gpu in self._computer.gpus
        )

    def native_os(self) -> bool:
        # These private driver interfaces are qualified only for this exact build.
        return self._xnu_major != 20 or self._os_build != "20G1443"

    def hardware_variant(self) -> HardwareVariant:
        return HardwareVariant.GRAPHICS

    def hardware_variant_graphics_subclass(self) -> HardwareVariantGraphicsSubclass:
        return HardwareVariantGraphicsSubclass.METAL_31001_GRAPHICS

    def requires_primary_kernel_cache(self) -> bool:
        return True

    def patches(self) -> dict:
        if self.native_os():
            return {}
        return {
            "Intel Xe-LP": {
                PatchType.OVERWRITE_SYSTEM_VOLUME: {
                    "/System/Library/Extensions": {
                        name: "11.0 20A2314a" for name in (
                            "AppleIntelTGLCompat.kext",
                            "AppleIntelTGLGraphics.kext",
                            "AppleIntelTGLGraphicsFramebuffer.kext",
                            "AppleIntelTGLGraphicsGLDriver.bundle",
                            "AppleIntelTGLGraphicsMTLDriver.bundle",
                            "AppleIntelTGLGraphicsVADriver.bundle",
                        )
                    }
                }
            }
        }
