"""Use LiteRT where installed; webOS uses its existing TensorFlow Lite C API."""
import ctypes as C
import os
import numpy as np


def create_interpreter(model_path, num_threads):
    try:
        from ai_edge_litert.interpreter import Interpreter
    except ImportError:
        return CInterpreter(model_path, num_threads)
    return Interpreter(model_path=str(model_path), num_threads=num_threads)


class Quantization(C.Structure):
    _fields_ = [("scale", C.c_float), ("zero_point", C.c_int)]


class CInterpreter:
    def __init__(self, model_path, num_threads=2):
        self.lib = C.CDLL(os.environ.get("GOCR_TFLITE_C_LIBRARY", "/usr/lib/libtensorflow-lite.so"))
        declarations = {
            "TfLiteModelCreateFromFile": (C.c_void_p, [C.c_char_p]),
            "TfLiteModelDelete": (None, [C.c_void_p]),
            "TfLiteInterpreterOptionsCreate": (C.c_void_p, []),
            "TfLiteInterpreterOptionsSetNumThreads": (None, [C.c_void_p, C.c_int]),
            "TfLiteInterpreterOptionsDelete": (None, [C.c_void_p]),
            "TfLiteInterpreterCreate": (C.c_void_p, [C.c_void_p, C.c_void_p]),
            "TfLiteInterpreterDelete": (None, [C.c_void_p]),
            "TfLiteInterpreterGetInputTensorCount": (C.c_int, [C.c_void_p]),
            "TfLiteInterpreterGetOutputTensorCount": (C.c_int, [C.c_void_p]),
            "TfLiteInterpreterGetInputTensor": (C.c_void_p, [C.c_void_p, C.c_int]),
            "TfLiteInterpreterGetOutputTensor": (C.c_void_p, [C.c_void_p, C.c_int]),
            "TfLiteInterpreterResizeInputTensor": (C.c_int, [C.c_void_p, C.c_int, C.POINTER(C.c_int), C.c_int]),
            "TfLiteInterpreterAllocateTensors": (C.c_int, [C.c_void_p]),
            "TfLiteInterpreterInvoke": (C.c_int, [C.c_void_p]),
            "TfLiteTensorType": (C.c_int, [C.c_void_p]),
            "TfLiteTensorNumDims": (C.c_int, [C.c_void_p]),
            "TfLiteTensorDim": (C.c_int, [C.c_void_p, C.c_int]),
            "TfLiteTensorByteSize": (C.c_size_t, [C.c_void_p]),
            "TfLiteTensorName": (C.c_char_p, [C.c_void_p]),
            "TfLiteTensorQuantizationParams": (Quantization, [C.c_void_p]),
            "TfLiteTensorCopyFromBuffer": (C.c_int, [C.c_void_p, C.c_void_p, C.c_size_t]),
            "TfLiteTensorCopyToBuffer": (C.c_int, [C.c_void_p, C.c_void_p, C.c_size_t]),
        }
        for name, (result, arguments) in declarations.items():
            function = getattr(self.lib, name)
            function.restype, function.argtypes = result, arguments
        self.model = self.lib.TfLiteModelCreateFromFile(str(model_path).encode())
        self.context = None
        if not self.model:
            raise RuntimeError("TensorFlow Lite cannot open original Google model")
        options = self.lib.TfLiteInterpreterOptionsCreate()
        try:
            self.lib.TfLiteInterpreterOptionsSetNumThreads(options, num_threads)
            self.context = self.lib.TfLiteInterpreterCreate(self.model, options)
        finally:
            self.lib.TfLiteInterpreterOptionsDelete(options)
        if not self.context:
            self.close()
            raise RuntimeError("TensorFlow Lite cannot create original Google interpreter")
        self.input_count = self.lib.TfLiteInterpreterGetInputTensorCount(self.context)

    def _input(self, index):
        if not 0 <= index < self.input_count:
            raise ValueError("invalid input ordinal")
        return self.lib.TfLiteInterpreterGetInputTensor(self.context, index)

    def _details(self, tensor, index):
        dtype = {1: np.float32, 2: np.int32, 3: np.uint8, 9: np.int8,
                 10: np.float16}.get(self.lib.TfLiteTensorType(tensor))
        if dtype is None:
            raise RuntimeError("unsupported original model tensor type")
        shape = [self.lib.TfLiteTensorDim(tensor, i)
                 for i in range(self.lib.TfLiteTensorNumDims(tensor))]
        quantization = self.lib.TfLiteTensorQuantizationParams(tensor)
        return {"index": index, "name": self.lib.TfLiteTensorName(tensor).decode(),
                "dtype": dtype, "shape": np.asarray(shape, dtype=np.int32),
                "quantization": (quantization.scale, quantization.zero_point)}

    def get_input_details(self):
        return [self._details(self._input(i), i) for i in range(self.input_count)]

    def get_output_details(self):
        count = self.lib.TfLiteInterpreterGetOutputTensorCount(self.context)
        return [self._details(self.lib.TfLiteInterpreterGetOutputTensor(self.context, i),
                              self.input_count+i) for i in range(count)]

    def resize_tensor_input(self, index, shape, strict=False):
        self._input(index)
        dimensions = (C.c_int*len(shape))(*shape)
        if self.lib.TfLiteInterpreterResizeInputTensor(self.context, index, dimensions, len(shape)):
            raise RuntimeError("Google tensor resize failed")

    def allocate_tensors(self):
        if self.lib.TfLiteInterpreterAllocateTensors(self.context):
            raise RuntimeError("Google tensor allocation failed")

    def set_tensor(self, index, values):
        tensor = self._input(index)
        array = np.ascontiguousarray(values)
        details = self._details(tensor, index)
        if (array.dtype != details["dtype"] or list(array.shape) != list(details["shape"])
                or array.nbytes != self.lib.TfLiteTensorByteSize(tensor)):
            raise ValueError("original Google input contract mismatch")
        if self.lib.TfLiteTensorCopyFromBuffer(tensor, array.ctypes.data, array.nbytes):
            raise RuntimeError("Google input copy failed")

    def invoke(self):
        if self.lib.TfLiteInterpreterInvoke(self.context):
            raise RuntimeError("Google inference failed")

    def get_tensor(self, index):
        ordinal = index-self.input_count
        if not 0 <= ordinal < self.lib.TfLiteInterpreterGetOutputTensorCount(self.context):
            raise ValueError("invalid output ordinal")
        tensor = self.lib.TfLiteInterpreterGetOutputTensor(self.context, ordinal)
        details = self._details(tensor, index)
        array = np.empty(details["shape"], dtype=details["dtype"])
        if array.nbytes != self.lib.TfLiteTensorByteSize(tensor):
            raise ValueError("original Google output contract mismatch")
        if self.lib.TfLiteTensorCopyToBuffer(tensor, array.ctypes.data, array.nbytes):
            raise RuntimeError("Google output copy failed")
        return array

    def close(self):
        if getattr(self, "context", None):
            self.lib.TfLiteInterpreterDelete(self.context)
            self.context = None
        if getattr(self, "model", None):
            self.lib.TfLiteModelDelete(self.model)
            self.model = None

    def __del__(self):
        self.close()
