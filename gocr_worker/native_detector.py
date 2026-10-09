"""Native detector boundary; Python only config parsing and result serialization."""
import ctypes as C
import os
import time
from pathlib import Path

from .assets import DETECTOR_CONFIG, DETECTOR_MODEL, locate
from .detector_config import parse_detector_binarypb
from .detector import GoogleGroupRpnDetector
from .native_postprocess import Config as PostConfig, Line, Proposal, Stats as PostStats
from .execution_profile import execution_profile, google_runner_contract


class Config(C.Structure):
    _fields_=[("limits",C.c_int32*4),("sources",C.c_int32*11),("strides",C.c_int32*11),
              ("anchors",C.c_double*11),("confidence_threshold",C.c_double),
              ("anchor_x",C.c_double),("anchor_y",C.c_double),("postprocess",PostConfig)]


def config_from_assets(assets):
    launch=parse_detector_binarypb(locate(assets,DETECTOR_CONFIG))
    if launch.profile_max_dim!=1280 or len(launch.anchor_widths)<6:
        raise ValueError("native detector requires unchanged Google 1280 profile")
    cfg=Config()
    cfg.limits[:]=[launch.profile_max_dim,1280,640,160]
    cfg.sources[:]=[0,0,1,1,2,3,0,0,1,1,2]
    cfg.strides[:]=[8,32,8,32,32,32,8,32,8,32,32]
    cfg.anchors[:]=[launch.anchor_widths[i] for i in (0,1,2,3,4,5,0,1,2,3,4)]
    cfg.confidence_threshold=launch.confidence_threshold
    cfg.anchor_x,cfg.anchor_y=launch.anchor_x_center,launch.anchor_y_center
    cfg.postprocess=PostConfig(launch.max_height_ratio,launch.search_radius_factor,
        launch.maximum_angle_difference,launch.max_centers_relative_distance,
        launch.optimal_centers_relative_distance,launch.min_overlap,launch.min_overlap_optimal,
        launch.duplicate_horizontal_overlap,GoogleGroupRpnDetector.REFERENCE_DUPLICATE_IOU,
        GoogleGroupRpnDetector.REFERENCE_GROUP_ACROSS_FACTOR)
    return cfg


class Stats(C.Structure):
    _fields_=[(n,C.c_double) for n in ("prepare_ms","invoke_ms","decode_ms","postprocess_ms","total_ms")]+[
        ("grouping",PostStats),("raw_pieces",C.c_int32),("raw_groups",C.c_int32)]


class NativeDetector:
    def __init__(self,assets,threads=2,library=None,runtime=None,xnnpack=None):
        library=library or os.environ.get("GOCR_DETECTOR_LIBRARY") or str(
            Path(__file__).resolve().parents[1]/"native/gocr_detector_native/libgocr_detector_native.so")
        runtime=runtime or os.environ.get("GOCR_DETECTOR_TFLITE_LIBRARY") or os.environ.get(
            "GOCR_TFLITE_C_LIBRARY","/usr/lib/libtensorflow-lite.so")
        # Explicit low-level argument remains available to research probes.
        # Worker selection uses GOCR_PROFILE; legacy delegate env cannot alter STRICT.
        xnnpack=int(execution_profile()!="strict") if xnnpack is None else int(xnnpack)
        self.xnnpack=bool(xnnpack)
        if execution_profile()=="google_runner_experimental":
            required=google_runner_contract(assets)["interpreter_num_threads"]
            if threads!=required or not self.xnnpack:
                raise ValueError("Google experimental detector requires original four-thread XNNPACK contract")
        self.lib=C.CDLL(str(Path(library).resolve()))
        self.context=None
        self.lib.gocr_detector_abi.restype=C.c_int
        if self.lib.gocr_detector_abi()!=1:
            raise RuntimeError("unsupported native detector ABI")
        signatures={
            "create":(C.c_void_p,[C.c_char_p,C.c_char_p,C.c_int,C.c_int,C.POINTER(Config),C.c_char_p,C.c_size_t]),
            "destroy":(None,[C.c_void_p]),"error":(C.c_char_p,[C.c_void_p]),
            "version":(C.c_char_p,[C.c_void_p]),
            "prepare":(C.c_int,[C.c_void_p,C.c_void_p,C.c_size_t]),
            "invoke":(C.c_int,[C.c_void_p]),
            "finish":(C.c_int,[C.c_void_p,C.POINTER(Line),C.c_int,C.POINTER(Stats)]),
            "detect":(C.c_int,[C.c_void_p,C.c_void_p,C.c_size_t,C.POINTER(Line),C.c_int,C.POINTER(Stats)]),
            "copy_input":(C.c_size_t,[C.c_void_p,C.c_int,C.c_void_p,C.c_size_t]),
            "copy_output":(C.c_size_t,[C.c_void_p,C.c_int,C.c_void_p,C.c_size_t]),
            "copy_proposals":(C.c_int,[C.c_void_p,C.POINTER(Proposal),C.c_int])}
        for name,(result,args) in signatures.items():
            f=getattr(self.lib,"gocr_detector_"+name)
            f.restype,f.argtypes=result,args
        cfg=config_from_assets(assets)
        error=C.create_string_buffer(512)
        self.context=self.lib.gocr_detector_create(str(locate(assets,DETECTOR_MODEL)).encode(),
            runtime.encode(),threads,xnnpack,C.byref(cfg),error,len(error))
        if not self.context:
            raise RuntimeError(error.value.decode())
        self.output=(Line*4096)()
        self.stats=Stats()

    def detect(self,image):
        if image.mode!="RGB" or image.size!=(1280,720):
            raise ValueError("native detector requires selected RGB1280x720")
        start=time.perf_counter()
        pixels=image.tobytes()
        count=self.lib.gocr_detector_detect(self.context,pixels,len(pixels),self.output,
                                             len(self.output),C.byref(self.stats))
        if count<0:
            raise RuntimeError(self.lib.gocr_detector_error(self.context).decode())
        lines=[]
        for b in self.output[:count]:
            q=[[b.quad[k*2],b.quad[k*2+1]] for k in range(4)]
            xs,ys=[p[0] for p in q],[p[1] for p in q]
            lines.append({"quad":q,"bbox":[min(xs),min(ys),max(xs),max(ys)],
                          "angle":b.angle,"score":b.score,"pieces":b.piece_count})
        result=[]
        for i,b in enumerate(sorted(lines,key=lambda x:(x["bbox"][1],x["bbox"][0]))):
            x1,y1,x2,y2=b["bbox"]
            if x2<=0 or y2<=0 or x1>=1280 or y1>=720:
                continue
            b["line_id"]=str(i)
            b["bbox"]=[max(0.,x1),max(0.,y1),min(1280.,x2),min(720.,y2)]
            result.append(b)
        s,g=self.stats,self.stats.grouping
        return {"lines":result,"invoke_ms":s.invoke_ms,"total_ms":(time.perf_counter()-start)*1000,
            "postprocess":"google_config_cleanroom_v1","backend":"native","detector_execution":"native",
            "raw_piece_count":s.raw_pieces,"raw_group_count":s.raw_groups,
            "stages_ms":{"pyramid_prepare_allocate":s.prepare_ms,"tflite_invoke":s.invoke_ms,
                "decode_heads":s.decode_ms,"native_total_postprocess":s.postprocess_ms,
                "piece_dedupe":g.dedupe_ms,"pairwise_connections":g.pairwise_ms,
                "component_fit":g.fit_ms,"group_refine_dedupe":g.refine_ms},
            "counts":{"pieces_after_dedupe":g.deduped_count,"pair_tests":g.pair_tests,
                      "components":g.component_count}}

    def tensor_bytes(self,kind,index):
        f=getattr(self.lib,"gocr_detector_copy_"+kind)
        size=f(self.context,index,None,0)
        if not size:
            raise RuntimeError("native tensor not available")
        data=C.create_string_buffer(size)
        if f(self.context,index,data,size)!=size:
            raise RuntimeError("native tensor export failed")
        return data.raw

    def close(self):
        if getattr(self,"context",None):
            self.lib.gocr_detector_destroy(self.context)
            self.context=None

    def __del__(self):
        self.close()
