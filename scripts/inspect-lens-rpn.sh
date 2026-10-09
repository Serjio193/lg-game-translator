#!/usr/bin/env bash
set -euo pipefail
OUT=lens-rpn-report
mkdir -p "$OUT"
UA="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/140 Safari/537.36"
curl -fL -A "$UA" "https://d.apkpure.net/b/APK/com.google.android.googlequicksearchbox?version=latest" -o "$OUT/google.apk"
MODEL_PATH="assets/lens_ondevice_text_stack_multiscript_omni/third_party/lens/line_detector/v688492737/gocr_group_rpn_text_detection_model_2024_q4.tflite"
CFG_PATH="assets/lens_ondevice_text_stack_multiscript_omni/third_party/lens/line_detector/v688492737/gocr_group_rpn_text_detection_config_2024_q4.binarypb"
unzip -p "$OUT/google.apk" "$MODEL_PATH" > "$OUT/detector.tflite"
unzip -p "$OUT/google.apk" "$CFG_PATH" > "$OUT/detector-config.binarypb"
sha256sum "$OUT/detector.tflite" "$OUT/detector-config.binarypb" > "$OUT/sha256.txt"
stat -c '%n %s bytes' "$OUT/detector.tflite" "$OUT/detector-config.binarypb" > "$OUT/sizes.txt"
strings -a "$OUT/detector-config.binarypb" > "$OUT/config-strings.txt"

python3 -m pip install --quiet tflite flatbuffers
python3 - <<'PY' > "$OUT/model-structure.txt"
import tflite
from collections import Counter
p='lens-rpn-report/detector.tflite'
buf=open(p,'rb').read()
m=tflite.Model.GetRootAsModel(buf,0)
print('version',m.Version())
print('subgraphs',m.SubgraphsLength())
print('operator_codes',m.OperatorCodesLength())
codes=[]
for i in range(m.OperatorCodesLength()):
    oc=m.OperatorCodes(i)
    try: name=tflite.BuiltinOperator.BuiltinOperator().Name(oc.BuiltinCode())
    except Exception: name=str(oc.BuiltinCode())
    codes.append((i,name,oc.BuiltinCode(),oc.CustomCode().decode() if oc.CustomCode() else ''))
print('OPERATOR_CODES')
for x in codes: print(x)
for si in range(m.SubgraphsLength()):
    sg=m.Subgraphs(si)
    print('\nSUBGRAPH',si,'name=',sg.Name().decode() if sg.Name() else '')
    print('INPUTS')
    for j in range(sg.InputsLength()):
        idx=sg.Inputs(j); t=sg.Tensors(idx)
        print(j,'tensor',idx,'name=',t.Name().decode() if t.Name() else '', 'shape=',[t.Shape(k) for k in range(t.ShapeLength())],'type=',t.Type())
    print('OUTPUTS')
    for j in range(sg.OutputsLength()):
        idx=sg.Outputs(j); t=sg.Tensors(idx)
        print(j,'tensor',idx,'name=',t.Name().decode() if t.Name() else '', 'shape=',[t.Shape(k) for k in range(t.ShapeLength())],'type=',t.Type())
    cnt=Counter()
    for oi in range(sg.OperatorsLength()):
        op=sg.Operators(oi); code_idx=op.OpcodeIndex(); cnt[codes[code_idx][1]]+=1
    print('OPERATORS_TOTAL',sg.OperatorsLength())
    print('OPERATOR_COUNTS')
    for k,v in cnt.most_common(): print(k,v)
    print('TENSORS',sg.TensorsLength())
    print('TENSOR_NAMES_SHAPES')
    for ti in range(sg.TensorsLength()):
        t=sg.Tensors(ti); n=t.Name().decode(errors='replace') if t.Name() else ''
        if any(q in n.lower() for q in ('input','identity','feature','rpn','anchor','box','score','class','conv')):
            print(ti,n,[t.Shape(k) for k in range(t.ShapeLength())],t.Type())
PY

rm "$OUT/google.apk"
