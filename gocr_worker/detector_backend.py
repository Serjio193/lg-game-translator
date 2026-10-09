"""Select the proven native detector; retain Python for debug/unavailable hosts."""
import os
import warnings
from .execution_profile import execution_profile


class FrameDetector:
    """Use native for selected TV frames, preserve generic image API behavior."""
    def __init__(self,native,assets,threads):
        self.native,self.assets,self.threads=native,assets,threads
        self.reference=None

    def detect(self,image):
        if image.mode=="RGB" and image.size==(1280,720):
            return self.native.detect(image)
        if self.reference is None:
            from .detector_runtime import GoogleConfiguredGroupRpnDetector
            self.reference=GoogleConfiguredGroupRpnDetector(self.assets,self.threads)
        return self.reference.detect(image)

    def close(self):
        self.native.close()
        if self.reference is not None:
            close=getattr(self.reference.interpreter,"close",None)
            if close is not None:
                close()
            self.reference=None


def create_detector(assets,threads=2):
    profile=execution_profile()
    mode=os.environ.get("GOCR_DETECTOR","native")
    if mode not in ("native","python"):
        raise ValueError("GOCR_DETECTOR must be native or python")
    if profile!="strict" and mode!="native":
        raise ValueError("experimental profile requires the native detector")
    if mode=="native":
        try:
            from .native_detector import NativeDetector
            return FrameDetector(NativeDetector(assets,threads),assets,threads)
        except (OSError,RuntimeError) as exc:
            if profile!="strict":
                raise RuntimeError("experimental profile unavailable; no implicit fallback") from exc
            warnings.warn(f"native detector unavailable; using Python reference: {exc}",RuntimeWarning)
    from .detector_runtime import GoogleConfiguredGroupRpnDetector
    return GoogleConfiguredGroupRpnDetector(assets,threads)
