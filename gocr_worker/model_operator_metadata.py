"""Untimed TFLite schema-v3 metadata reader; no inference or model mutation.

Field numbers follow TensorFlow v2.17 compiler/mlir/lite/schema/schema.fbs.
Only the Model/SubGraph/Operator tables needed by the profiler are decoded.
"""
import struct


class _Table:
    def __init__(self, data, position):
        self.data = data
        self.position = position

    def field(self, number):
        vtable = self.position - struct.unpack_from("<i", self.data, self.position)[0]
        length = struct.unpack_from("<H", self.data, vtable)[0]
        entry = 4 + number * 2
        offset = struct.unpack_from("<H", self.data, vtable + entry)[0] if entry < length else 0
        return self.position + offset if offset else None

    def vector(self, number, tables=False):
        field = self.field(number)
        if field is None:
            return []
        start = field + struct.unpack_from("<I", self.data, field)[0]
        count = struct.unpack_from("<I", self.data, start)[0]
        result = []
        for i in range(count):
            item = start + 4 + i * 4
            value = struct.unpack_from("<i", self.data, item)[0]
            result.append(_Table(self.data, item + value) if tables else value)
        return result


def operator_metadata(model_path):
    data = model_path.read_bytes()
    if data[4:8] != b"TFL3":
        raise ValueError("expected original TFLite schema-v3 model")
    root = _Table(data, struct.unpack_from("<I", data)[0])
    result = {}
    for subgraph_index, graph in enumerate(root.vector(2, tables=True)):
        tensors = graph.vector(0, tables=True)
        for node_index, operator in enumerate(graph.vector(3, tables=True)):
            inputs, outputs = operator.vector(1), operator.vector(2)
            result[(subgraph_index, node_index)] = {
                "input_tensor_indices": inputs, "output_tensor_indices": outputs,
                "declared_input_shapes": [tensors[i].vector(0) if i >= 0 else None for i in inputs],
                "declared_output_shapes": [tensors[i].vector(0) for i in outputs],
            }
    return result
