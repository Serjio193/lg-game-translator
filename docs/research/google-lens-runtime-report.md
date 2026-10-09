# Google Lens / GOCR Android runtime research

Generated automatically from the current Google App APK. Strings alone are never treated as proof of execution.

## Input

- APK SHA-256: 2e3fb6182625e93e60f827b63c57a5bf63e202e66f8990d03ded42c86a54d979
- liblens_ondevice_engine_base.so: 275680 bytes, SHA-256 1ada5226d1923762e21c843a2bbdc1e3e754e328fb7d6426ee4cf08d8cf6da93
- liblens_ondevice_engine_play_ml.so: 19906776 bytes, SHA-256 d9cfafb045a296708246727f3c0473895790bcd5ae61265713459bb5bd515203
- liblens_vision.so: 18912 bytes, SHA-256 c8af8d909ad7693be5ddab63dca6c5a5dd48a971d7f76ada5d9b08353e189cf6
- libtensorflowlite_jni_gms_client.so: 527872 bytes, SHA-256 92c48469ee752562264527259cc8982878153026fd74a54a704ee73fbbe800f9

## Delegate/backend evidence

| Candidate | Evidence level | Meaning |
|---|---|---|
| xnnpack | **POSSIBLE** | matching strings only; presence is not proof of use |
| nnapi | **STRONG** | disassembly context exists; GOCR ownership still needs confirmation |
| gpu | **STRONG** | disassembly context exists; GOCR ownership still needs confirmation |
| ahwb | **PROVEN** | dynamic reference plus disassembly call context |

## Detector TensorFlowModelRunnerConfig raw payload

- payload length: 268 bytes
- payload SHA-256: 42feff5414682f802c6c81aeb865565a3dd334408a228a18da9cc90c13e929db
- raw hex: 3a89020a342e2f676f63725f67726f75705f72706e5f746578745f646574656374696f6e5f6d6f64656c5f323032345f71342e74666c6974651804300142084964656e74697479420a4964656e746974795f31420a4964656e746974795f32420a4964656e746974795f33420a4964656e746974795f34420a4964656e746974795f35420a4964656e746974795f36420a4964656e746974795f37420a4964656e746974795f38420a4964656e746974795f39420b4964656e746974795f3130620e696e7075745f66656174757265736210696e7075745f66656174757265735f316210696e7075745f66656174757265735f326210696e7075745f66656174757265735f33800105880101

Raw protobuf fields:

    [{"field": 7, "wire": 2, "len": 265, "hex": "0a342e2f676f63725f67726f75705f72706e5f746578745f646574656374696f6e5f6d6f64656c5f323032345f71342e74666c6974651804300142084964656e74697479420a4964656e746974795f31420a4964656e746974795f32420a4964", "ascii": ".4./gocr_group_rpn_text_detection_model_2024_q4.tflite..0.B.IdentityB.Identity_1B.Identity_2B.Identity_3B.Identity_4B.Identity_5B.Identity_6B.Identity_7B.Identi", "start": 0}]

## Per-library evidence

### liblens_ondevice_engine_base.so

NEEDED: libandroid.so, libjnigraphics.so, libdl.so, liblog.so, libc.so, libm.so


Protobuf/config clues:

    0x46a6: third_party/absl/base/throw_delegate.cc

### liblens_ondevice_engine_play_ml.so

NEEDED: libandroid.so, libjnigraphics.so, libdl.so, libz.so, libm.so, libEGL.so, libGLESv2.so, liblog.so, libc.so

Relevant dynamic imports:

    239: 0000000000000000     0 NOTYPE  WEAK   DEFAULT  UND AHardwareBuffer_release
    240: 0000000000000000     0 NOTYPE  WEAK   DEFAULT  UND AHardwareBuffer_allocate
    241: 0000000000000000     0 NOTYPE  WEAK   DEFAULT  UND AHardwareBuffer_lock
    242: 0000000000000000     0 NOTYPE  WEAK   DEFAULT  UND AHardwareBuffer_unlock

**tflite_core strings (90 shown):**

    0x5b480 num_threads_ - exiting_threads_ < max_threads_
    0x6f6b6 interpreter_->ModifyGraphWithDelegate(delegate_.get()) == kTfLiteOk
    0x71487 thread_pool_.num_threads() == 1
    0x7bc2a ) with num_threads=0, 
    0x7e1b0 num_threads should be >=0 or just -1 to let TFLite runtime set the value.
    0x83950 Using default executor with num_threads: 
    0x8f15c num_threads should be >= 0 or just -1 to let TFLite runtime set the value.
    0xb4f8f falling back to num_threads=1.
    0xb8daa SharedPoolExecutor requires num_threads argument.
    0xbd532 builder(interpreter_out, settings_.interpreter_num_threads()) == kTfLiteOk
    0xd0632 ModifyGraphWithDelegate
    0xd13d0  configured previously with num_threads=
    0xd5730 num_threads is not specified in ThreadPoolExecutorOptions.
    0xd847f ModifyGraphWithDelegate model namespace: %s model id: %s accelerator name: %s
    0xda18a ; cannot re-configure with num_threads=
    0xe8e07 TF Lite FlatBufferModel is null. Please make sure to call one of the BuildModelFrom methods before calling InitInterpreter.
    0xf93f8 ctx->num_threads_strategy()
    0xfae6e Starting SharedPoolExecutor with num_threads=
    0x105247 `num_threads` must be greater than 0 or equal to -1.
    0x10b97c HL_NUM_THREADS
    0x122c17 , num_threads=
    0x1266c9 ExecutorConfig for the default executor and the graph-level num_threads field should not both be specified.
    0x12b8e6 num_threads >= 1
    0x132751 Null output pointer passed to InterpreterBuilder.
    0x132f35 InitializeTfliteInterpreterAndDelegate()
    0x13eea2 The num_threads field in ThreadPoolExecutorOptions should be positive but is 
    0x14b96e TF_RUN_HANDLER_NUM_THREADS_IN_SUB_THREAD_POOL
    0x15f14d N12acceleration7regular24TfLiteInterpreterWrapperE
    0x15f2fb NSt6__ndk110__function6__funcIZN9barhopper13deep_learning21BarcodeDetectorClient38InitializeTfliteInterpreterAndDelegateEvE3$_0NS_9allocatorIS5_EEFN4absl6StatusERKN12acceleration7regular28InterpreterCreationResourcesEPNS_10unique_ptrIN6tflite4impl11InterpreterENS_14default_deleteISI_EEEEEEE
    0x15f41f ZN9barhopper13deep_learning21BarcodeDetectorClient38InitializeTfliteInterpreterAndDelegateEvE3$_0
    0x16c092 NSt6__ndk110__function6__funcIZN10google_ocr23TfliteModelPooledRunner26InterpreterFactoryCallbackEN4absl4SpanIKNS_6vectorIiNS_9allocatorIiEEEEEEPN6tflite4impl15FlatBufferModelEE3$_0NS7_ISG_EEFNS_10unique_ptrINSD_11InterpreterENS_14default_deleteISJ_EEEEvEEE
    0x16c1fe NSt6__ndk110__function6__funcIZN6tflite4impl11Interpreter23ModifyGraphWithDelegateI14TfLiteDelegatePFvPS6_EEE12TfLiteStatusNS_10unique_ptrIT_T0_EEEUlS7_E_NS_9allocatorISF_EES8_EE
    0x16c2b1 ZN6tflite4impl11Interpreter23ModifyGraphWithDelegateI14TfLiteDelegatePFvPS3_EEE12TfLiteStatusNSt6__ndk110unique_ptrIT_T0_EEEUlS4_E_
    0x16c335 ZN10google_ocr23TfliteModelPooledRunner26InterpreterFactoryCallbackEN4absl4SpanIKNSt6__ndk16vectorIiNS3_9allocatorIiEEEEEEPN6tflite4impl15FlatBufferModelEE3$_0
    0x1a3508 NSt6__ndk110__function6__funcIN11data_lookup21SimpleLruCacheOptionsINS_12basic_stringIcNS_11char_traitsIcEENS_9allocatorIcEEEENS_10shared_ptrIN12acceleration7regular24TfLiteInterpreterWrapperEEEE10entry_sizeMUlRKS9_RKSE_E_ENS7_ISL_EEFmSI_SK_EEE
    0x1a35fd NSt6__ndk110__function6__baseIFmRKNS_12basic_stringIcNS_11char_traitsIcEENS_9allocatorIcEEEERKNS_10shared_ptrIN12acceleration7regular24TfLiteInterpreterWrapperEEEEEE
    0x1a36a3 N11data_lookup21SimpleLruCacheOptionsINSt6__ndk112basic_stringIcNS1_11char_traitsIcEENS1_9allocatorIcEEEENS1_10shared_ptrIN12acceleration7regular24TfLiteInterpreterWrapperEEEE10entry_sizeMUlRKS7_RKSC_E_E
    0x1a376f N11data_lookup14cache_internal14SimpleLruCacheINSt6__ndk112basic_stringIcNS2_11char_traitsIcEENS2_9allocatorIcEEEENS2_10shared_ptrIN12acceleration7regular24TfLiteInterpreterWrapperEEEN4absl13hash_internal4HashIS8_EENS2_8equal_toIS8_EELNS0_14ValueSemanticsE1EEE
    0x1a3874 N11data_lookup14cache_internal14SimpleLruCacheINSt6__ndk112basic_stringIcNS2_11char_traitsIcEENS2_9allocatorIcEEEENS2_10shared_ptrIN12acceleration7regular24TfLiteInterpreterWrapperEEEN4absl13hash_internal4HashIS8_EENS2_8equal_toIS8_EELNS0_14ValueSemanticsE0EEE
    0x1a3979 N11data_lookup14CacheInterfaceINSt6__ndk112basic_stringIcNS1_11char_traitsIcEENS1_9allocatorIcEEEENS1_10shared_ptrIN12acceleration7regular24TfLiteInterpreterWrapperEEELNS_14cache_internal14ValueSemanticsE1EEE
    0x1a3a4a N11data_lookup14CacheInterfaceINSt6__ndk112basic_stringIcNS1_11char_traitsIcEENS1_9allocatorIcEEEENS1_10shared_ptrIN12acceleration7regular24TfLiteInterpreterWrapperEEELNS_14cache_internal14ValueSemanticsE0EEE
    0x1a3b1b N11data_lookup14cache_internal26SimpleLruCacheWithEvictionINSt6__ndk112basic_stringIcNS2_11char_traitsIcEENS2_9allocatorIcEEEENS2_10shared_ptrIN12acceleration7regular24TfLiteInterpreterWrapperEEEN4absl13hash_internal4HashIS8_EENS2_8equal_toIS8_EEEE
    0x1a3c14 18SimpleLRUCacheBaseINSt6__ndk112basic_stringIcNS0_11char_traitsIcEENS0_9allocatorIcEEEENS0_10shared_ptrIN12acceleration7regular24TfLiteInterpreterWrapperEEEN4absl13flat_hash_mapIS6_P18SimpleLRUCacheElemIS6_SB_ENSC_13hash_internal4HashIS6_EENS0_8equal_toIS6_EENS4_INS0_4pairIKS6_SG_EEEEEESL_N4util5cache14UtilClockTimerEE
    0x1a3d56 NSt6__ndk120__shared_ptr_pointerIPNS_10shared_ptrIN12acceleration7regular24TfLiteInterpreterWrapperEEEZN11data_lookup14cache_internal14SimpleLruCacheINS_12basic_stringIcNS_11char_traitsIcEENS_9allocatorIcEEEES5_N4absl13hash_internal4HashISF_EENS_8equal_toISF_EELNS8_14ValueSemanticsE0EE6LookupERKSF_EUlS6_E_NSD_IS5_EEEE
    0x1a3e96 ZN11data_lookup14cache_internal14SimpleLruCacheINSt6__ndk112basic_stringIcNS2_11char_traitsIcEENS2_9allocatorIcEEEENS2_10shared_ptrIN12acceleration7regular24TfLiteInterpreterWrapperEEEN4absl13hash_internal4HashIS8_EENS2_8equal_toIS8_EELNS0_14ValueSemanticsE0EE6LookupERKS8_EUlPSD_E_
    0x1a3fb1 N11data_lookup14cache_internal15ThreadSafeCacheINSt6__ndk112basic_stringIcNS2_11char_traitsIcEENS2_9allocatorIcEEEENS2_10shared_ptrIN12acceleration7regular24TfLiteInterpreterWrapperEEELNS_15LockRequirementE2ELNS0_14ValueSemanticsE1ELNS0_18CacheLineAlignmentE0EEE
    0x1a40b8 N11data_lookup14cache_internal15ThreadSafeCacheINSt6__ndk112basic_stringIcNS2_11char_traitsIcEENS2_9allocatorIcEEEENS2_10shared_ptrIN12acceleration7regular24TfLiteInterpreterWrapperEEELNS_15LockRequirementE2ELNS0_14ValueSemanticsE0ELNS0_18CacheLineAlignmentE0EEE
    0x1a41bf NSt6__ndk120__shared_ptr_pointerIPKNS_10shared_ptrIN12acceleration7regular24TfLiteInterpreterWrapperEEEZN11data_lookup14cache_internal15ThreadSafeCacheINS_12basic_stringIcNS_11char_traitsIcEENS_9allocatorIcEEEES5_LNS8_15LockRequirementE2ELNS9_14ValueSemanticsE0ELNS9_18CacheLineAlignmentE0EE6LookupERKSG_EUlS7_E_NSE_IS5_EEEE
    0x1a4304 ZN11data_lookup14cache_internal15ThreadSafeCacheINSt6__ndk112basic_stringIcNS2_11char_traitsIcEENS2_9allocatorIcEEEENS2_10shared_ptrIN12acceleration7regular24TfLiteInterpreterWrapperEEELNS_15LockRequirementE2ELNS0_14ValueSemanticsE0ELNS0_18CacheLineAlignmentE0EE6LookupERKS8_EUlPKSD_E_
    0x1a4594 NSt6__ndk120__shared_ptr_pointerIPN12acceleration7regular24TfLiteInterpreterWrapperENS_14default_deleteIS3_EENS_9allocatorIS3_EEEE

**xnnpack strings (101 shown):**

    0x54f74 unsupported quantization type %d for %s tensor %d in XNNPACK delegate
    0x55258 failed to create XNNPACK runtime
    0x5c8c2 unsupported quantized dimension %d for INT32 tensor %d in XNNPACK delegate
    0x5c935 failed to create XNNPACK Value for tensor %d
    0x5ea62 TfliteModelPooledXNNPackCached::AllocateModelTensors
    0x6ca24 XNNPACK runtime is null.
    0x6f661 for TFLite, XNNPack and Nnapi
    0x7442e unsupported datatype (%s) of tensor %d in XNNPACK delegate
    0x74469 third_party/tensorflow/lite/delegates/xnnpack/xnnpack_delegate.cc
    0x7ed47 Failed to modify graph with XNNPack delegate.
    0x81415 for TFLite, XNNPack
    0x86660 unsupported scale value (%f) in channel %d for %s tensor %d in XNNPACK delegate
    0x866b0 unsupported zero-point value (%d) for %s tensor %d in XNNPACK delegate
    0x868bf failed to create FP32 XNNPACK Value for tensor %d
    0x868f1 XNNPack delegate failed to get resize output tensor
    0x8e005 unsupported number (%d) of scale quantization parameters for UINT8 tensor %d in XNNPACK delegate
    0x8e066 mismatching number of scale (%d) and zero point (%d) quantization parameters for %s tensor %d in XNNPACK delegate
    0x8e36b XNNPack weight cache loaded from '%s'.
    0x8e3b2 XNNPack weight cache: a null cache key was provided.
    0x8e3e7 third_party/tensorflow/lite/delegates/xnnpack/file_util.cc
    0x95fc0 XNNPack
    0x961e3 XNNPack weight cache: written to '%s'.
    0x9e95f failed to create XNNPACK subgraph
    0xa65ed unsupported quantization type %d for INT32 tensor %d in XNNPACK delegate
    0xa66de XNNPack delegate failed to reshape external value
    0xae054 mismatching number of quantization parameters %d and outer dimension %d for INT32 tensor %d in XNNPACK delegate
    0xaed1f acceleration.XNNPackSettings
    0xb648c XNNPack weight cache could not be locked in memory.
    0xb64d5 missing zero point quantization parameters for %s tensor %d in XNNPACK delegate
    0xbe675 unsupported quantization type %d for UINT8 tensor %d in XNNPACK delegate
    0xbe6be mismatching number of quantization parameters %d and outer dimension %d for INT8 tensor %d in XNNPACK delegate
    0xbe8bd failed to setup XNNPACK runtime
    0xc141b third_party/mediapipe/calculators/tensor/inference_calculator_xnnpack.cc
    0xcf83c missing quantization parameters for affine quantized tensor %d in XNNPACK delegate
    0xcf88f unsupported tensor type %d for tensorwise quantization of tensor %d in XNNPACK delegate
    0xcfb70 XNNPack weight cache: no fingerprint identifier was set when appending a buffer to the cache file.
    0xd2c03 Xnnpack
    0xd85be XNNPack weight cache was manually overridden but not loaded and no file path or file descriptor was provided.
    0xd8660 unsupported zero-point value (%d) in channel %d of %s tensor %d in XNNPACK delegate
    0xd8834 TfLiteXNNPackDelegate
    0xd884a failed to get XNNPACK profile information.
    0xdbb30 input_side_packet_delegate.has_xnnpack() || input_side_packet_delegate.delegate_case() == drishti::InferenceCalculatorOptions::Delegate::DELEGATE_NOT_SET
    0xe0cfe Variable ops support is enabled by default, TfLiteXNNPackDelegateOptions::handle_variable_ops is deprecated and will be removed in the future.
    0xe0f77 XNNPack delegate failed to start cache build step.
    0xe1021 XNNPack in-memory weight cache
    0xe34e3 TfliteModelPooledXNNPackCached::InsertInterpreter
    0xf8ae9 Subgraph reshaping is enabled by default, TFLITE_XNNPACK_DELEGATE_FLAG_ENABLE_SUBGRAPH_RESHAPING is deprecated and will be removed in the future.
    0xf8bea third_party/tensorflow/lite/delegates/xnnpack/weight_cache.cc
    0xfaac5 InterpreterFactoryCallbackXNNPack
    0xfdf92 drishti.InferenceCalculatorOptions.Delegate.Xnnpack

**nnapi strings (242 shown):**

    0x51ffb NnapiTextClassifier::Process started 
    0x54dc6 Nnapi
    0x54e59 ANeuralNetworksModel_setOperandValue
    0x54e7e ANeuralNetworksModel_identifyInputsAndOutputs
    0x54eac ANeuralNetworksCompilation_free
    0x54ecc ANeuralNetworksMemoryDesc_addOutputRole
    0x54ef4 ANeuralNetworksExecution_enableInputAndOutputPadding
    0x5b0ab NnapiLstmClient::RunSessionWithTargets batch size is 
    0x5b5b3 ANeuralNetworks_getDeviceCount returned error
    0x5c76a configuring NNAPI caching
    0x5c78f Execution info: getSessionId=%d getErrorCode=%d getNnApiVersion=%ld getModelArchHash=%x getDeviceIds=%s getInputDataClass=%d getOutputDataClass=%d isCachingEnabled=%s isControlFlowUsed=%s getExecutionMode=%d getRuntimeExecutionTimeNanos=%lu getDriverExecutionTimeNanos=%lu getHardwareExecutionTimeNanos=%lu
    0x623eb ./ocr/photo/classifiers/nnapi_text_classifier.h
    0x6241b NnapiTextClassifier::InitClient
    0x63387 nnapi_client_->NumSparseOutputs() == tflite_client_->NumSparseOutputs()
    0x6343d ANeuralNetworksModel_finish Model time: 
    0x64be0 creating NNAPI model for given devices
    0x64c2d SL_ANeuralNetworksDiagnosticExecutionInfo_getDeviceIds
    0x6b24d ocr/photo/recognition/nnapi_lstm_recognizer.cc
    0x6b2b9 ANeuralNetworksCompilation_finish memory1 
    0x6b2fa NnapiLstmClient::LoadNnapiModelInfo
    0x6c6be NNAPI:
    0x6c6dc creating NNAPI model
    0x6c706 ANEURALNETWORKS_UNMAPPABLE
    0x6c743 ANeuralNetworksModel_addOperand
    0x6c763 ANeuralNetworksCompilation_setTimeout
    0x6c789 ANeuralNetworksMemoryDesc_free
    0x6c7a8 SL_ANeuralNetworksDiagnosticCompilationInfo_getDeviceIds
    0x6f661 for TFLite, XNNPack and Nnapi
    0x71bdb nnapi_client_inited in text classifier
    0x741fc completing NNAPI compilation
    0x7422e nnapi error: unable to open both library %s (%s) and library %s (%s)
    0x74274 ANeuralNetworksCompilation_create
    0x74296 ANeuralNetworksExecution_setInput
    0x742b8 ANeuralNetworksExecution_setOutput
    0x742db ANeuralNetworksExecution_setOutputFromMemory
    0x74308 ANeuralNetworksEvent_free
    0x74322 ANeuralNetworksExecution_getOutputOperandRank
    0x74350 SL_ANeuralNetworksDiagnosticExecutionInfo_getRuntimeExecutionTimeNanos
    0x7a6e9 Failed to initialized script id NNAPI model, 
    0x7b7f4 ocr/photo/segmentation/nnapi_lstm_client.cc
    0x7b83c NnapiLstmClient::Initialize ANeuralNetworksCompilation_finish
    0x7b87a ANeuralNetworksCompilation_finish compilation 
    0x7b8ca NnapiLstmClient::BuildFusedModel ANeuralNetworksModel_finish
    0x7d63c ANeuralNetworksExecution_getDuration
    0x7d661 SL_ANeuralNetworksDiagnosticCompilationInfo_getModelArchHash
    0x7d69e SL_ANeuralNetworksDiagnosticExecutionInfo_getOutputDataClass
    0x83ef2 drishti.InferenceCalculatorOptions.Delegate.Nnapi
    0x853cd NnapiLstmClient::BuildFusedModel
    0x86572 ANEURALNETWORKS_INCOMPLETE
    0x8658d ANeuralNetworksModel_setOperandSymmPerChannelQuantParams

**gpu strings (179 shown):**

    0x3b4e eglGetProcAddress
    0x3b60 eglQueryString
    0x3d61 eglGetCurrentContext
    0x3dc2 eglGetDisplay
    0x3ffd eglCreatePbufferSurface
    0x4015 eglGetError
    0x4021 eglInitialize
    0x402f eglChooseConfig
    0x403f eglCreateContext
    0x4050 eglMakeCurrent
    0x405f eglDestroySurface
    0x4071 eglDestroyContext
    0x4083 eglGetCurrentDisplay
    0x4098 eglGetCurrentSurface
    0x40c0 eglReleaseThread
    0x40e8 eglTerminate
    0x4413 eglBindAPI
    0x475e _ZN4base33HasDuplicateGlobalSymbolsInternalEv
    0x4aae libEGL.so
    0x51a42 third_party/mediapipe/gpu/gl_context_egl.cc
    0x51a6e Creating a context with OpenGL ES 3 failed: 
    0x57b11 TfLiteGpuDelegate Prepare: %s
    0x57b98 MlDriftOpenCl
    0x5b520 No EGL error, but eglChooseConfig failed.
    0x60502 #pragma OPENCL EXTENSION cl_intel_subgroups : enable
    0x61c6f eglQueryDevicesEXT
    0x61c82 eglGetPlatformDisplayEXT
    0x67ac4 TfLiteGpuDelegate CopyToBufferHandle: %s
    0x68e56 OpenCL error: 
    0x68f59 libOpenCL-car.so
    0x68f6a OpenCL is not supported.
    0x68fc1 clEnqueueAcquireEGLObjectsKHR
    0x69823 Tensor::GetOpenGlBufferWriteView is not executed on the same GL context where GL buffer was created. Note that Tensor has limited synchronization support when sharing OpenGl objects between multiple OpenGL contexts.
    0x69b01 : external context uses a different version of OpenGL
    0x6b719 No EGL error, but eglCreateContext failed.
    0x6f6fa TFLiteRunner and ML_DRIFT_OPENCL are incompatible.
    0x6fc9e Missing OpenGL SSBO
    0x6fd02 *egl_create_sync_khr in third_party/tensorflow/lite/delegates/gpu/cl/egl_sync.cc:61
    0x714d8 surface_ != EGL_NO_SURFACE
    0x714f3 Failed to create and initialize a valid EGL display! 
    0x7879b #pragma OPENCL EXTENSION cl_qcom_subgroup_uniform_load: enable
    0x79490 No supported OpenCL platform.
    0x7a15d eglChooseConfig() returned no matching EGL configuration for 
    0x8156c Falling back to OpenGL: 
    0x815d2 ) is not supported by TFLite GPU Delegate.
    0x81ba5 eglCreateSyncKHR
    0x81bb6 eglDestroySyncKHR
    0x82a90 clEnqueueAcquireGLObjects
    0x83595 No GL extension functions found to bind AHardwareBuffer and OpenGL buffer
    0x835df eglGetNativeClientBufferANDROID

**ahwb strings (25 shown):**

    0x3dd9 AHardwareBuffer_release
    0x3df1 AHardwareBuffer_allocate
    0x3e0a AHardwareBuffer_lock
    0x3e1f AHardwareBuffer_unlock
    0x51725 third_party/mediapipe/framework/formats/ahwb_gpu_releaser.cc
    0x83595 No GL extension functions found to bind AHardwareBuffer and OpenGL buffer
    0x933df ahwb->Unlock() is OK
    0xadf80 ANeuralNetworksMemory_createFromAHardwareBuffer
    0xb2eb8 AHWB GPU releaser requires OpenGL support.
    0xc34af third_party/mediapipe/framework/formats/tensor_ahwb.cc
    0xc34e6 ahwb_usages_.size() > 0
    0xd5413 Failed to release AHardwareBuffer: 
    0xf574c Maximum number of pooled buffers reached (set to keep at most %d buffers of the same type and size). MP buffer allocation patterns can be observed with Perfetto by inspecting the PerfettoScopedMemoryObjectCounters-based GpuBuffer and AhwbBuffer counters. Then consider adjusting the MultiPoolOptions.keep_count
    0x11e2d4 third_party/mediapipe/framework/formats/tensor_ahwb_usage.cc
    0x136a35 AHardwareBuffer_allocate failed: 
    0x136a57 Failed to force-complete AHWB usage.
    0x15694f Lock of AHWB failed
    0x1c272f use_ahwb
    0x1c273f useAhwb
    0x1d9ad4 NSt6__ndk110__function6__funcIZN9mediapipe6Tensor16ReleaseAhwbStuffEvE3$_0NS_9allocatorIS4_EEFN4absl6StatusEvEEE
    0x1d9b45 NSt6__ndk110__function6__funcIZN9mediapipe8internalL17MakeAttachmentPtrINS2_15AhwbGpuReleaserEJEEENS_9enable_ifIXntsr3std8is_arrayIT_EE5valueENS_10unique_ptrIS7_NS_8functionIFvPvEEEEEE4typeEDpOT0_EUlSA_E_NS_9allocatorISJ_EESB_EE
    0x1d9c50 ZN9mediapipe8internalL17MakeAttachmentPtrINS_15AhwbGpuReleaserEJEEENSt6__ndk19enable_ifIXntsr3std8is_arrayIT_EE5valueENS3_10unique_ptrIS5_NS3_8functionIFvPvEEEEEE4typeEDpOT0_EUlS8_E_
    0x1d9d07 ZN9mediapipe6Tensor16ReleaseAhwbStuffEvE3$_0
    0x1d9d34 NSt6__ndk110__function6__funcIZN9mediapipe9GlContext3RunIZNKS2_6Tensor16MapAhwbToCpuReadEvE3$_0vEEvT_EUlvE_NS_9allocatorIS8_EEFN4absl6StatusEvEEE
    0x1d9dc6 ZN9mediapipe9GlContext3RunIZNKS_6Tensor16MapAhwbToCpuReadEvE3$_0vEEvT_EUlvE_

**gms strings (8 shown):**

    0x4a35 liblens_ondevice_engine_play_ml.so
    0xa7327 lens/ondevice/engine/play_ml_pack_split_handler.cc
    0xe1f02 lens/ondevice/engine/play_ml_pack_split_jni.cc
    0x192ca5 NmMgMsM]K
    0x2a3d12 //java/com/google/android/libraries/lens/ondevice/jni:liblens_ondevice_engine_play_ml.so
    0x2a4132 blaze-out/arm64-v8a-opt-ST-182ce64ae7be/bin/java/com/google/android/libraries/lens/ondevice/jni/liblens_ondevice_engine_play_ml.so
    0x114dc29 QGms
    0x114df55 QGms

**group_rpn strings (25 shown):**

    0x4f2ea google_ocr.GroupRpnTextDetectionMutatorRuntimeOptions
    0x5735e google_ocr.GocrDetectorLevel1GroupingConfig
    0x6a27c Invalid TensorFlowModelRunnerConfig.
    0x7690e ocr/google_ocr/detection/group_rpn_detector_utils.cc
    0x7fe05 GroupRpnTextDetectionMutator: Perform line detection
    0x988e4 ocr/google_ocr/detection/group_rpn_detector_v2.cc
    0xa0ed1 Unknown options for GocrGroupRpnTextDetectionMutator:
    0xa8381 GocrGroupRpnTextDetectionMutator
    0xb7b19 TensorFlowModelRunnerConfig=
    0xb881c google_ocr.GroupRpnTextDetectionMutatorConfig
    0xb884a ProcessPackedImagePyramid
    0xd21fc google_ocr.GocrDetectorMergeLevel1Config
    0xe1a83 google_ocr.TensorFlowModelRunnerConfig
    0xe346f sub_config must be GroupRPNTextDetectionMutatorConfig:
    0xe34a7 ocr/google_ocr/detection/group_rpn_detector_tensor_utils.cc
    0xeb4cd google_ocr.GocrDetectorModelConfig
    0xfaa40 ocr/google_ocr/engine/page_layout_mutators/gocr_group_rpn_text_detection_mutator.cc
    0xfab7f google_ocr.GocrDetectorLevel1NMS
    0x12bb2e ocr/google_ocr/detection/group_rpn_detector_inference_utils.cc
    0x12bc69 google_ocr.GocrDetectorNMS
    0x13423e ./ocr/google_ocr/detection/group_rpn_detector_utils.h
    0x134274 GocrGroupRpnTextDetectionMutator::MutateSub
    0x13c01a ./ocr/google_ocr/detection/group_rpn_detector_hac.h
    0x143dec GroupRpnTextDetectionMutator: Done all work.
    0x1a2064 N10google_ocr12_GLOBAL__N_132GocrGroupRpnTextDetectionMutatorE

**recognizer strings (168 shown):**

    0x4dddc Unable to get base recognizer for language model: 
    0x4de19 google_ocr.MultiPassLineRecognitionMutatorRuntimeOptions.custom_line_recognizers
    0x4f0c9 CtcDecoderConfidenceScorer_AvgLogits
    0x4f136 ./ocr/google_ocr/recognition/gocr_line_recognizer.h
    0x4f189 CTCDecoderOutput labels and TextLineResult atoms do not match
    0x56163 LanguageBasedLineRecognizerConfigSelector
    0x5655f CTCDecoder::Decode End (
    0x57016 Recognizer was not initialized properly.
    0x5b06a ./ocr/photo/recognition/tflite_lstm_recognizer.h
    0x5dcb1 For recognizer_name=%s, prior has the wrong number of channels. Expected %d, but got %d.
    0x5e893 GocrLineRecognizer: Start
    0x634ff MobileLstmRecognizer::DecodingLine
    0x6b24d ocr/photo/recognition/nnapi_lstm_recognizer.cc
    0x6c523 ocr.photo.MognetLstmRecognizerSettings
    0x6db03 BarcodeRecognizer_Recognize
    0x6e11f CTCDecoder::Decode (
    0x72d65 TfliteLstmRecognizer::Process
    0x75901 photos/vision/barhopper/deep_learning/mobile/barcode_recognizer.cc
    0x75ae7 ocr/google_ocr/recognition/language_based_line_recognizer_config_selector.cc
    0x75b4b google_ocr.GocrLineRecognizerConfig
    0x766e4 This recognizer does not support multiple language models.
    0x7671f google_ocr.LineRecognizerRuntimeOptions
    0x7eb38 Unable to find a recognizer creator - add to configuration: 
    0x7fc44 GocrTextLineRecognizer
    0x7fceb google_ocr.CTCDecoderConfidenceScorerConfig
    0x85415 ocr/photo/recognition/mobile_lstm_recognizer.cc
    0x85476 MobileLstmRecognizer::RecognizeLinesWithContext
    0x87aa9 Lazy initialization for recognizer: 
    0x88754 recognizers_.size() == 2
    0x8876d google_ocr.LineRecognizerConfig
    0x8fa76 google_ocr.MultiPassLineRecognitionMutatorRuntimeOptions.line_recognizer_options
    0x8fac7 google_ocr.LineRecognizerConfigSelectorConfig
    0x908e1 google_ocr.GocrCTCDecoderRecognizerRuntimeOptions
    0x90913 google_ocr.GocrLineRecognizerConfig.lang_id_model_file
    0x94d52 MobileLstmRecognizer::DecodeBestPath
    0x9750d Unable to add language model to recognizer: 
    0x98721 google_ocr.GocrLineRecognizerConfig.lang_id_name
    0x98752 google_ocr.GocrCTCDecoderRecognizerConfig.content_type_names
    0x9d07f TfliteLstmRecognizer
    0x9fa2c Preloading recognizers in parallel.
    0x9fa50 Finished preloading a recognizer for "
    0x9fabf google_ocr.MultiPassLineRecognitionMutatorConfig.LineRecognizerConfig
    0x9fe39 GocrCTCDecoderRecognizer::InitSub
    0x9fe76 GocrCTCDecoderRecognizer::GenerateLineWordsMaybeSetColors
    0xa0d1d GocrMathFormulaRecognizer
    0xa0da7 google_ocr.GocrCTCDecoderRecognizerConfig.prior_path
    0xa0ddc google_ocr.CTCDecoderConfidenceFeatureExtractorConfig
    0xa747d Custom language model base recognizer is not CTC: 
    0xa74b0 google_ocr.LineRecognizerConfigSelectorConfig.default_key
    0xa81f7 No recognizer name.

Relevant disassembly contexts:

      a07804:	54000161 	b.ne	a07830 <Java_com_google_android_libraries_lens_ondevice_nativeapi_LodeSplitRegistry_initializePlayMlPackSplitHandler@@VERS_1.0+0x5ab3d0>  // b.any
      a07808:	94000158 	bl	a07d68 <Java_com_google_android_libraries_lens_ondevice_nativeapi_LodeSplitRegistry_initializePlayMlPackSplitHandler@@VERS_1.0+0x5ab908>
      a0780c:	941f5646 	bl	11dd124 <Java_com_google_android_libraries_lens_ondevice_nativeapi_LodeSplitRegistry_initializePlayMlPackSplitHandler@@VERS_1.0+0xd80cc4>
      a07810:	34000340 	cbz	w0, a07878 <Java_com_google_android_libraries_lens_ondevice_nativeapi_LodeSplitRegistry_initializePlayMlPackSplitHandler@@VERS_1.0+0x5ab418>
      a07814:	f9401260 	ldr	x0, [x19, #32]
      a07818:	941f6d4e 	bl	11e2d50 <AHardwareBuffer_release@plt>
      a0781c:	f900127f 	str	xzr, [x19, #32]
      a07820:	a900fe7f 	stp	xzr, xzr, [x19, #8]
      a07824:	f900027f 	str	xzr, [x19]
      a07828:	b9001a7f 	str	wzr, [x19, #24]
      a0782c:	1400000f 	b	a07868 <Java_com_google_android_libraries_lens_ondevice_nativeapi_LodeSplitRegistry_initializePlayMlPackSplitHandler@@VERS_1.0+0x5ab408>
      a07830:	528019a8 	mov	w8, #0xcd                  	// #205
    ---
      a07914:	910003e0 	mov	x0, sp
      a07918:	910163e1 	add	x1, sp, #0x58
      a0791c:	a901ffff 	stp	xzr, xzr, [sp, #24]
      a07920:	3d8003e0 	str	q0, [sp]
      a07924:	f9000be8 	str	x8, [sp, #16]
      a07928:	941f6d0e 	bl	11e2d60 <AHardwareBuffer_allocate@plt>
      a0792c:	b9004fe0 	str	w0, [sp, #76]
      a07930:	35000680 	cbnz	w0, a07a00 <Java_com_google_android_libraries_lens_ondevice_nativeapi_LodeSplitRegistry_initializePlayMlPackSplitHandler@@VERS_1.0+0x5ab5a0>
      a07934:	f9402fe8 	ldr	x8, [sp, #88]
      a07938:	b4000648 	cbz	x8, a07a00 <Java_com_google_android_libraries_lens_ondevice_nativeapi_LodeSplitRegistry_initializePlayMlPackSplitHandler@@VERS_1.0+0x5ab5a0>
      a0793c:	52800029 	mov	w9, #0x1                   	// #1
      a07940:	a903a3e9 	stp	x9, x8, [sp, #56]
    ---
      a07aa0:	f26002df 	tst	x22, #0x100000000
      a07aa4:	9100a3e4 	add	x4, sp, #0x28
      a07aa8:	5a9f12c2 	csinv	w2, w22, wzr, ne	// ne = any
      a07aac:	aa1503e1 	mov	x1, x21
      a07ab0:	aa1f03e3 	mov	x3, xzr
      a07ab4:	941f6caf 	bl	11e2d70 <AHardwareBuffer_lock@plt>
      a07ab8:	b90007e0 	str	w0, [sp, #4]
      a07abc:	350004c0 	cbnz	w0, a07b54 <Java_com_google_android_libraries_lens_ondevice_nativeapi_LodeSplitRegistry_initializePlayMlPackSplitHandler@@VERS_1.0+0x5ab6f4>
      a07ac0:	f94017e9 	ldr	x9, [sp, #40]
      a07ac4:	52800028 	mov	w8, #0x1                   	// #1
      a07ac8:	3900a288 	strb	w8, [x20, #40]
      a07acc:	a9002668 	stp	x8, x9, [x19]
    ---
      a07bc4:	94000069 	bl	a07d68 <Java_com_google_android_libraries_lens_ondevice_nativeapi_LodeSplitRegistry_initializePlayMlPackSplitHandler@@VERS_1.0+0x5ab908>
      a07bc8:	941f5557 	bl	11dd124 <Java_com_google_android_libraries_lens_ondevice_nativeapi_LodeSplitRegistry_initializePlayMlPackSplitHandler@@VERS_1.0+0xd80cc4>
      a07bcc:	340001c0 	cbz	w0, a07c04 <Java_com_google_android_libraries_lens_ondevice_nativeapi_LodeSplitRegistry_initializePlayMlPackSplitHandler@@VERS_1.0+0x5ab7a4>
      a07bd0:	f9401260 	ldr	x0, [x19, #32]
      a07bd4:	aa1403e1 	mov	x1, x20
      a07bd8:	941f6c6a 	bl	11e2d80 <AHardwareBuffer_unlock@plt>
      a07bdc:	b9002fe0 	str	w0, [sp, #44]
      a07be0:	35000400 	cbnz	w0, a07c60 <Java_com_google_android_libraries_lens_ondevice_nativeapi_LodeSplitRegistry_initializePlayMlPackSplitHandler@@VERS_1.0+0x5ab800>
      a07be4:	3900a27f 	strb	wzr, [x19, #40]
      a07be8:	52800033 	mov	w19, #0x1                   	// #1
      a07bec:	aa1303e0 	mov	x0, x19
      a07bf0:	a9434ff4 	ldp	x20, x19, [sp, #48]
    ---
     11e2d40:	f0000770 	adrp	x16, 12d1000 <pthread_rwlock_rdlock@plt+0xed650>
     11e2d44:	f9405e11 	ldr	x17, [x16, #184]
     11e2d48:	9102e210 	add	x16, x16, #0xb8
     11e2d4c:	d61f0220 	br	x17
    
    00000000011e2d50 <AHardwareBuffer_release@plt>:
     11e2d50:	f0000770 	adrp	x16, 12d1000 <pthread_rwlock_rdlock@plt+0xed650>
     11e2d54:	f9406211 	ldr	x17, [x16, #192]
     11e2d58:	91030210 	add	x16, x16, #0xc0
     11e2d5c:	d61f0220 	br	x17
    
    00000000011e2d60 <AHardwareBuffer_allocate@plt>:
    ---
     11e2d50:	f0000770 	adrp	x16, 12d1000 <pthread_rwlock_rdlock@plt+0xed650>
     11e2d54:	f9406211 	ldr	x17, [x16, #192]
     11e2d58:	91030210 	add	x16, x16, #0xc0
     11e2d5c:	d61f0220 	br	x17
    
    00000000011e2d60 <AHardwareBuffer_allocate@plt>:
     11e2d60:	f0000770 	adrp	x16, 12d1000 <pthread_rwlock_rdlock@plt+0xed650>
     11e2d64:	f9406611 	ldr	x17, [x16, #200]
     11e2d68:	91032210 	add	x16, x16, #0xc8
     11e2d6c:	d61f0220 	br	x17
    
    00000000011e2d70 <AHardwareBuffer_lock@plt>:
    ---
     11e2d60:	f0000770 	adrp	x16, 12d1000 <pthread_rwlock_rdlock@plt+0xed650>
     11e2d64:	f9406611 	ldr	x17, [x16, #200]
     11e2d68:	91032210 	add	x16, x16, #0xc8
     11e2d6c:	d61f0220 	br	x17
    
    00000000011e2d70 <AHardwareBuffer_lock@plt>:
     11e2d70:	f0000770 	adrp	x16, 12d1000 <pthread_rwlock_rdlock@plt+0xed650>
     11e2d74:	f9406a11 	ldr	x17, [x16, #208]
     11e2d78:	91034210 	add	x16, x16, #0xd0
     11e2d7c:	d61f0220 	br	x17
    
    00000000011e2d80 <AHardwareBuffer_unlock@plt>:
    ---
     11e2d70:	f0000770 	adrp	x16, 12d1000 <pthread_rwlock_rdlock@plt+0xed650>
     11e2d74:	f9406a11 	ldr	x17, [x16, #208]
     11e2d78:	91034210 	add	x16, x16, #0xd0
     11e2d7c:	d61f0220 	br	x17
    
    00000000011e2d80 <AHardwareBuffer_unlock@plt>:
     11e2d80:	f0000770 	adrp	x16, 12d1000 <pthread_rwlock_rdlock@plt+0xed650>
     11e2d84:	f9406e11 	ldr	x17, [x16, #216]
     11e2d88:	91036210 	add	x16, x16, #0xd8
     11e2d8c:	d61f0220 	br	x17
    
    00000000011e2d90 <glGetProgramInfoLog@plt>:
    ---

Protobuf/config clues:

    0x4fb4c: Created TensorFlow Lite delegate for GPU.
    0x4fb76: ./third_party/tensorflow/lite/delegates/gpu/gl/gl_buffer.h
    0x4fbb1: glBindBuffer in ./third_party/tensorflow/lite/delegates/gpu/gl/gl_buffer.h:224
    0x4fc00: glDeleteBuffers in ./third_party/tensorflow/lite/delegates/gpu/gl/gl_buffer.h:195
    0x4fe69: third_party/tensorflow/lite/delegates/gpu/gl/runtime.cc
    0x508f9: third_party/tensorflow/lite/delegates/gpu/common/selectors/simple_selectors.cc
    0x50cc4: third_party/tensorflow/lite/delegates/gpu/common/tasks/special/conv_pointwise.cc
    0x54e04: NN API Delegate: Can't get an equivalent TF Lite type for provided NN API type: %d.
    0x54f74: unsupported quantization type %d for %s tensor %d in XNNPACK delegate
    0x57b11: TfLiteGpuDelegate Prepare: %s
    0x58aab: third_party/tensorflow/lite/delegates/gpu/common/task/qcom_thin_filter_desc.cc
    0x596d9: glProgramUniform2i in third_party/tensorflow/lite/delegates/gpu/gl/gl_program.cc:66
    0x59d2c: drishti.InferenceCalculatorOptions.Delegate.TfLite
    0x5b54a: third_party/tensorflow/lite/delegates/gpu/gl/request_gpu_info.cc
    0x5c8c2: unsupported quantized dimension %d for INT32 tensor %d in XNNPACK delegate
    0x5d163: Null delegate.
    0x5d1a3: delegate->CopyFromBufferHandle != nullptr
    0x5fa17: third_party/tensorflow/lite/delegates/gpu/gl/compiler/preprocessor.cc
    0x5fa9f: third_party/tensorflow/lite/delegates/gpu/gl/kernels/add.cc
    0x60ee1: third_party/tensorflow/lite/delegates/gpu/common/memory_management.cc
    0x60f27: third_party/tensorflow/lite/delegates/gpu/cl/kernels/converter.cc
    0x60fde: third_party/tensorflow/lite/delegates/gpu/cl/qcom_thin_filter.cc
    0x64bc0: delegate_plugin_
    0x65baf: acceleration.CoreMLDelegateSettings
    0x67ac4: TfLiteGpuDelegate CopyToBufferHandle: %s
    0x67d39: ./third_party/tensorflow/lite/delegates/gpu/gl/runtime/shared_buffer.h
    0x67d80: third_party/tensorflow/lite/delegates/gpu/gl/kernels/converter.cc
    0x68fdf: third_party/tensorflow/lite/delegates/gpu/common/task/gpu_operation.cc
    0x69135: glDeleteBuffers in third_party/tensorflow/lite/delegates/gpu/gl/gl_buffer.cc:78
    0x69185: glUnmapBuffer in third_party/tensorflow/lite/delegates/gpu/gl/gl_buffer.cc:160
    0x6990c: glDeleteTextures in third_party/tensorflow/lite/delegates/gpu/gl/gl_texture.cc:60
    0x6a27c: Invalid TensorFlowModelRunnerConfig.
    0x6d279: Failed to apply the default TensorFlow Lite delegate indexed at %zu.
    0x6d348: delegate_context_switch_count_ >= 1
    0x6d4b5: acceleration.HexagonDelegateSettings
    0x6f30d: CreateOneStageMobileRaid: Unknown MediaPipe delegate
    0x6f613: Initialize: Unknown MediaPipe delegate
    0x6f6b6: interpreter_->ModifyGraphWithDelegate(delegate_.get()) == kTfLiteOk
    0x6fcb2: glUnmapBuffer in third_party/tensorflow/lite/delegates/gpu/cl/gl_interop.cc:291
    0x6fd02: *egl_create_sync_khr in third_party/tensorflow/lite/delegates/gpu/cl/egl_sync.cc:61
    0x6fdd0: third_party/tensorflow/lite/delegates/gpu/common/gpu_model.cc
    0x70b9f: third_party/tensorflow/lite/delegates/gpu/cl/program_cache.cc
    0x712b5: glTexParameteri in third_party/tensorflow/lite/delegates/gpu/gl/gl_texture.cc:105
    0x7442e: unsupported datatype (%s) of tensor %d in XNNPACK delegate
    0x74469: third_party/tensorflow/lite/delegates/xnnpack/xnnpack_delegate.cc
    0x7531e: acceleration.StableDelegateLoaderSettings
    0x7690e: ocr/google_ocr/detection/group_rpn_detector_utils.cc
    0x777a3: ./third_party/tensorflow/lite/delegates/gpu/api.h
    0x777ec: third_party/tensorflow/lite/delegates/gpu/gl/compiler/rename.cc
    0x77873: glBufferData in ./third_party/tensorflow/lite/delegates/gpu/gl/gl_buffer.h:269
    0x778fb: third_party/tensorflow/lite/delegates/gpu/gl/kernels/depthwise_conv.cc
    0x793c1: third_party/tensorflow/lite/delegates/gpu/cl/buffer.cc
    0x7941c: third_party/tensorflow/lite/delegates/gpu/cl/cl_kernel.cc
    0x79456: third_party/tensorflow/lite/delegates/gpu/cl/cl_device.cc
    0x79f09: glTexParameteri in third_party/tensorflow/lite/delegates/gpu/gl/gl_texture.cc:108
    0x7a512: drishti.InferenceCalculatorOptions.Delegate.LiteRt.Cpu
    0x7d5a3: NN API Delegate: unsupported tensor types conversion: from type code %d to type code %d.
    0x7d617: Could not resize new delegate tensor
    0x7ed47: Failed to modify graph with XNNPack delegate.
    0x814b7: input_side_packet_delegate.has_gpu() || input_side_packet_delegate.delegate_case() == drishti::InferenceCalculatorOptions::Delegate::DELEGATE_NOT_SET
    0x815d2: ) is not supported by TFLite GPU Delegate.
    0x819b9: third_party/tensorflow/lite/delegates/gpu/gl/kernels/reshape.cc
    0x835ff: glProgramUniform2f in third_party/tensorflow/lite/delegates/gpu/gl/gl_program.cc:101
    0x83654: third_party/tensorflow/lite/delegates/gpu/gl/gl_shader.cc
    0x8368e: glBindTexture in third_party/tensorflow/lite/delegates/gpu/gl/gl_texture.cc:84
    0x836dd: glTexParameteri in third_party/tensorflow/lite/delegates/gpu/gl/gl_texture.cc:97
    0x83762: Specified Delegate type does not match the provided delegate options.
    0x83ef2: drishti.InferenceCalculatorOptions.Delegate.Nnapi
    0x8557e: CustomizeDelegate failed
    0x85811: third_party/tensorflow/lite/delegates/gpu/gl/gl_errors.cc
    0x86660: unsupported scale value (%f) in channel %d for %s tensor %d in XNNPACK delegate
    0x866b0: unsupported zero-point value (%d) for %s tensor %d in XNNPACK delegate
    0x868f1: XNNPack delegate failed to get resize output tensor
    0x89045: Initialize: Unsupported MediaPipe delegate.
    0x89420: third_party/tensorflow/lite/delegates/gpu/cl/api.cc
    0x89454: *egl_client_wait_sync_khr in third_party/tensorflow/lite/delegates/gpu/cl/egl_sync.cc:121
    0x89974: third_party/tensorflow/lite/delegates/gpu/common/selectors/google/default_selector.cc
    0x8a2bb: third_party/tensorflow/lite/delegates/gpu/common/task/arguments.cc
    0x8af33: glTexStorage2D in third_party/tensorflow/lite/delegates/gpu/gl/gl_texture.cc:145
    0x8affd: third_party/tensorflow/lite/delegates/gpu/common/model.cc

### liblens_vision.so

NEEDED: libgoogle3.so, libdl.so, libc.so, libm.so


### libtensorflowlite_jni_gms_client.so

NEEDED: libdl.so, libm.so, libGLESv3.so, libEGL.so, liblog.so, libc.so


**tflite_core strings (36 shown):**

    0x2b76 GmsTfLiteInterpreterGetInputTensor
    0x2bf9 GmsTfLiteInterpreterAllocateTensors
    0x2e8e GmsTfLiteInterpreterGetOutputTensor
    0x30db GmsTfLiteInterpreterInvoke
    0x41b8 GmsTfLiteInterpreterCreate
    0x41d3 GmsTfLiteInterpreterDelete
    0x41ee GmsTfLiteInterpreterGetInputTensorCount
    0x4216 GmsTfLiteInterpreterInputTensorIndices
    0x423d GmsTfLiteInterpreterGetOutputTensorCount
    0x4266 GmsTfLiteInterpreterOutputTensorIndices
    0x428e GmsTfLiteInterpreterGetTensor
    0x42e7 GmsTfLiteInterpreterGetSignatureRunner
    0x430e GmsTfLiteInterpreterGetSignatureCount
    0x4334 GmsTfLiteInterpreterGetSignatureKey
    0x4377 GmsTfLiteInterpreterOptionsCreate
    0x4399 GmsTfLiteInterpreterOptionsDelete
    0x43bb GmsTfLiteInterpreterOptionsSetNumThreads
    0x43e4 GmsTfLiteInterpreterOptionsEnableCancellation
    0x4412 GmsTfLiteInterpreterOptionsSetErrorReporter
    0x443e GmsTfLiteInterpreterOptionsAddDelegate
    0x4c01 GmsTfLiteInterpreterOptionsAddOperator
    0x4c28 GmsTfLiteInterpreterResizeInputTensor
    0x4e97 GmsTfLiteInterpreterCancel
    0x7fb7 TfLiteInterpreterOutputTensorIndices
    0x8260 ERROR: This app is using TFLite in Google Play services, and uses a non-default OpResolver, but doesn't have the TF Lite Extensions API enabled. If your code MUST use custom TF Lite ops, then add a dependency on "//third_party/tensorflow/lite/c:c_api_opaque" to enable the TF Lite Extensions API, and convert any custom op implementations that are not using TfLiteOperator to use TfLiteOperator. Otherwise (and preferably!), use only the default OpResolver, by either calling the single-argument cons
    0x91c9 num_threads should be >= 0 or just -1 to let TFLite runtime set the value.
    0x9df3 TfLiteInterpreterInputTensorIndices
    0x9e17 TfLiteInterpreterGetTensor
    0xb09c TfLiteInterpreterGetSignatureCount
    0xb744 TfLiteInterpreterOptionsEnableCancellation
    0xbd6b TfLiteInterpreterOptionsAddDelegate not supported: TFLite-in-GMSCore module's stable ABI version < 1.1.0, and app had no dependency on //java/com/google/android/gmscore/integ/client/tflite/native:experimental_abi 
    0xbe41 TfLiteInterpreterGetSignatureRunner
    0xc4a5 TfLiteInterpreterGetSignatureKey
    0xc8a8 Null output pointer passed to InterpreterBuilder.
    0xcafd TfLiteInterpreterOptionsAddOperator
    0xd660 TfLiteInterpreterCancel

**xnnpack strings (4 shown):**

    0x4eb2 GmsTfLiteXnnpackDelegatePluginCApi
    0x8f2e TfLiteXnnpackDelegateCreate
    0xb76f TfLiteXnnpackDelegateDestroy
    0xc91e TfLiteXnnpackDelegateErrno

**nnapi strings (11 shown):**

    0x2953 Java_com_google_android_gms_tflite_nnapi_NnApiDelegateImpl_createDelegate
    0x29ab Java_com_google_android_gms_tflite_nnapi_NnApiDelegateImpl_getNnapiErrno
    0x29f4 Java_com_google_android_gms_tflite_nnapi_NnApiDelegateImpl_deleteDelegate
    0x4188 GmsTfLiteNnapiDelegatePluginCApi
    0x7e43 TfLiteNnapiDelegateCreate
    0x924e logNnApiCompilationEvent
    0x9267 getFlagNnapiSlEnableTelemetry
    0xa11f ) is too old to use the NNAPI Support Library
    0xa5f0 TfLiteNnapiDelegateDestroy
    0xc88f TfLiteNnapiDelegateErrno
    0xcb27 logNnApiExecutionCounters

**gpu strings (8 shown):**

    0x4957 Java_com_google_android_gms_tflite_gpu_GpuDelegate_createDelegate
    0x4999 Java_com_google_android_gms_tflite_gpu_GpuDelegate_deleteDelegate
    0x49db Java_com_google_android_gms_tflite_gpu_GpuDelegateNative_nativeDoNothing
    0x4ade GmsTfLiteGpuDelegatePluginCApi
    0x5432 libEGL.so
    0x7b48 TfLiteGpuDelegateDestroy
    0xb714 TfLiteGpuDelegateErrno
    0xcd23 TfLiteGpuDelegateCreate

**gms strings (257 shown):**

    0x2953 Java_com_google_android_gms_tflite_nnapi_NnApiDelegateImpl_createDelegate
    0x29ab Java_com_google_android_gms_tflite_nnapi_NnApiDelegateImpl_getNnapiErrno
    0x29f4 Java_com_google_android_gms_tflite_nnapi_NnApiDelegateImpl_deleteDelegate
    0x2a4c Java_com_google_android_gms_tflite_InterpreterFactoryImpl_nativeRuntimeVersion
    0x2a9b GmsTfLiteVersion
    0x2aac Java_com_google_android_gms_tflite_InterpreterFactoryImpl_nativeSchemaVersion
    0x2afa GmsTfLiteSchemaVersion
    0x2b2c Java_com_google_android_gms_tflite_NativeInterpreterWrapper_getInputNames
    0x2b76 GmsTfLiteInterpreterGetInputTensor
    0x2b99 GmsTfLiteTensorName
    0x2bad Java_com_google_android_gms_tflite_NativeInterpreterWrapper_allocateTensors
    0x2bf9 GmsTfLiteInterpreterAllocateTensors
    0x2c1d Java_com_google_android_gms_tflite_NativeInterpreterWrapper_hasUnresolvedFlexOp
    0x2c6d Java_com_google_android_gms_tflite_NativeInterpreterWrapper_getSignatureKeys
    0x2cba Java_com_google_android_gms_tflite_NativeInterpreterWrapper_getInputTensorIndex
    0x2d0a Java_com_google_android_gms_tflite_NativeInterpreterWrapper_getOutputTensorIndex
    0x2d5b Java_com_google_android_gms_tflite_NativeInterpreterWrapper_getExecutionPlanLength
    0x2dae Java_com_google_android_gms_tflite_NativeInterpreterWrapper_getInputCount
    0x2df8 Java_com_google_android_gms_tflite_NativeInterpreterWrapper_getOutputCount
    0x2e43 Java_com_google_android_gms_tflite_NativeInterpreterWrapper_getOutputNames
    0x2e8e GmsTfLiteInterpreterGetOutputTensor
    0x2eb2 Java_com_google_android_gms_tflite_NativeInterpreterWrapper_allowFp16PrecisionForFp32
    0x2f08 Java_com_google_android_gms_tflite_NativeInterpreterWrapper_allowBufferHandleOutput
    0x2f5c Java_com_google_android_gms_tflite_NativeInterpreterWrapper_createErrorReporter
    0x2fac Java_com_google_android_gms_tflite_NativeInterpreterWrapper_createModel
    0x2ff4 Java_com_google_android_gms_tflite_NativeInterpreterWrapper_createModelWithBuffer
    0x3046 Java_com_google_android_gms_tflite_NativeInterpreterWrapper_createInterpreter
    0x309b Java_com_google_android_gms_tflite_NativeInterpreterWrapper_run
    0x30db GmsTfLiteInterpreterInvoke
    0x30f6 Java_com_google_android_gms_tflite_NativeInterpreterWrapper_resizeInput
    0x313e Java_com_google_android_gms_tflite_NativeInterpreterWrapper_createCancellationFlag
    0x3191 Java_com_google_android_gms_tflite_NativeInterpreterWrapper_deleteCancellationFlag
    0x31e4 Java_com_google_android_gms_tflite_NativeInterpreterWrapper_setCancelled
    0x322d Java_com_google_android_gms_tflite_NativeInterpreterWrapper_delete
    0x3270 Java_com_google_android_gms_tflite_NativeSignatureRunnerWrapper_nativeGetSignatureRunner
    0x32c9 Java_com_google_android_gms_tflite_NativeSignatureRunnerWrapper_nativeGetSubgraphIndex
    0x3320 Java_com_google_android_gms_tflite_NativeSignatureRunnerWrapper_nativeInputNames
    0x3371 Java_com_google_android_gms_tflite_NativeSignatureRunnerWrapper_nativeOutputNames
    0x33c3 Java_com_google_android_gms_tflite_NativeSignatureRunnerWrapper_nativeGetInputIndex
    0x3417 Java_com_google_android_gms_tflite_NativeSignatureRunnerWrapper_nativeGetOutputIndex
    0x346c Java_com_google_android_gms_tflite_NativeSignatureRunnerWrapper_nativeResizeInput
    0x34be GmsTfLiteSignatureRunnerGetInputTensor
    0x34e5 GmsTfLiteSignatureRunnerResizeInputTensor
    0x350f Java_com_google_android_gms_tflite_NativeSignatureRunnerWrapper_nativeAllocateTensors
    0x3565 GmsTfLiteSignatureRunnerAllocateTensors
    0x358d Java_com_google_android_gms_tflite_NativeSignatureRunnerWrapper_nativeInvoke
    0x35da GmsTfLiteSignatureRunnerInvoke
    0x35f9 Java_com_google_android_gms_tflite_TensorImpl_create
    0x362e Java_com_google_android_gms_tflite_TensorImpl_createSignatureInputTensor
    0x3677 Java_com_google_android_gms_tflite_TensorImpl_createSignatureOutputTensor

Relevant disassembly contexts:

    /tmp/google-runtime/out/libs/libtensorflowlite_jni_gms_client.so:     file format elf64-littleaarch64
    
    
    Disassembly of section .text:
    
    0000000000029920 <Java_com_google_android_gms_tflite_nnapi_NnApiDelegateImpl_createDelegate@@VERS_1.0-0x60>:
       29920:	d503245f 	bti	c
       29924:	d503201f 	nop
       29928:	102936c0 	adr	x0, 7c000 <pthread_rwlock_rdlock@plt+0x3af0>
       2992c:	14013895 	b	77b80 <__cxa_finalize@plt>
       29930:	d503245f 	bti	c
       29934:	d65f03c0 	ret
    ---
       29930:	d503245f 	bti	c
       29934:	d65f03c0 	ret
       29938:	d503245f 	bti	c
       2993c:	1401248f 	b	72b78 <GmsTfLiteInternalForwardingBuiltinOpResolverFindCustomOp@@VERS_1.0+0x2f45c>
       29940:	d503245f 	bti	c
       29944:	b4000060 	cbz	x0, 29950 <Java_com_google_android_gms_tflite_nnapi_NnApiDelegateImpl_createDelegate@@VERS_1.0-0x30>
       29948:	aa0003f0 	mov	x16, x0
       2994c:	d61f0200 	br	x16
       29950:	d65f03c0 	ret
       29954:	d503245f 	bti	c
       29958:	aa0003e1 	mov	x1, x0
       2995c:	d503201f 	nop
    ---
       2994c:	d61f0200 	br	x16
       29950:	d65f03c0 	ret
       29954:	d503245f 	bti	c
       29958:	aa0003e1 	mov	x1, x0
       2995c:	d503201f 	nop
       29960:	10ffff00 	adr	x0, 29940 <Java_com_google_android_gms_tflite_nnapi_NnApiDelegateImpl_createDelegate@@VERS_1.0-0x40>
       29964:	d503201f 	nop
       29968:	102934c2 	adr	x2, 7c000 <pthread_rwlock_rdlock@plt+0x3af0>
       2996c:	14013889 	b	77b90 <__cxa_atexit@plt>
       29970:	d503245f 	bti	c
       29974:	d503201f 	nop
       29978:	10293443 	adr	x3, 7c000 <pthread_rwlock_rdlock@plt+0x3af0>
    ---
       29970:	d503245f 	bti	c
       29974:	d503201f 	nop
       29978:	10293443 	adr	x3, 7c000 <pthread_rwlock_rdlock@plt+0x3af0>
       2997c:	14013889 	b	77ba0 <__register_atfork@plt>
    
    0000000000029980 <Java_com_google_android_gms_tflite_nnapi_NnApiDelegateImpl_createDelegate@@VERS_1.0>:
       29980:	d503233f 	paciasp
       29984:	d10383ff 	sub	sp, sp, #0xe0
       29988:	a9087bfd 	stp	x29, x30, [sp, #128]
       2998c:	a9096ffc 	stp	x28, x27, [sp, #144]
       29990:	a90a67fa 	stp	x26, x25, [sp, #160]
       29994:	a90b5ff8 	stp	x24, x23, [sp, #176]
    ---
       2999c:	a90d4ff4 	stp	x20, x19, [sp, #208]
       299a0:	52808008 	mov	w8, #0x400                 	// #1024
       299a4:	2a0703f4 	mov	w20, w7
       299a8:	2a0603f3 	mov	w19, w6
       299ac:	f9000be8 	str	x8, [sp, #16]
       299b0:	d0fffee8 	adrp	x8, 7000 <Java_com_google_android_gms_tflite_nnapi_NnApiDelegateImpl_createDelegate@@VERS_1.0-0x22980>
       299b4:	aa0503f5 	mov	x21, x5
       299b8:	3dc1f900 	ldr	q0, [x8, #2016]
       299bc:	12b00008 	mov	w8, #0x7fffffff            	// #2147483647
       299c0:	aa0403f6 	mov	x22, x4
       299c4:	b9001be8 	str	w8, [sp, #24]
       299c8:	52800028 	mov	w8, #0x1                   	// #1
    ---
       299f8:	a9047fff 	stp	xzr, xzr, [sp, #64]
       299fc:	f9001fff 	str	xzr, [sp, #56]
       29a00:	f804e3ff 	stur	xzr, [sp, #78]
       29a04:	7900e3e8 	strh	w8, [sp, #112]
       29a08:	f9003fff 	str	xzr, [sp, #120]
       29a0c:	b4000743 	cbz	x3, 29af4 <Java_com_google_android_gms_tflite_nnapi_NnApiDelegateImpl_createDelegate@@VERS_1.0+0x174>
       29a10:	f9400328 	ldr	x8, [x25]
       29a14:	aa1903e0 	mov	x0, x25
       29a18:	aa1703e1 	mov	x1, x23
       29a1c:	aa1f03e2 	mov	x2, xzr
       29a20:	f942a508 	ldr	x8, [x8, #1352]
       29a24:	d63f0100 	blr	x8
    ---
       29a20:	f942a508 	ldr	x8, [x8, #1352]
       29a24:	d63f0100 	blr	x8
       29a28:	aa0003fa 	mov	x26, x0
       29a2c:	910003e0 	mov	x0, sp
       29a30:	aa1a03e1 	mov	x1, x26
       29a34:	9400009f 	bl	29cb0 <Java_com_google_android_gms_tflite_nnapi_NnApiDelegateImpl_createDelegate@@VERS_1.0+0x330>
       29a38:	f9400328 	ldr	x8, [x25]
       29a3c:	2a0003fb 	mov	w27, w0
       29a40:	aa1903e0 	mov	x0, x25
       29a44:	aa1703e1 	mov	x1, x23
       29a48:	aa1a03e2 	mov	x2, x26
       29a4c:	f942a908 	ldr	x8, [x8, #1360]
    ---
       29a44:	aa1703e1 	mov	x1, x23
       29a48:	aa1a03e2 	mov	x2, x26
       29a4c:	f942a908 	ldr	x8, [x8, #1360]
       29a50:	d63f0100 	blr	x8
       29a54:	2a1b03fa 	mov	w26, w27
       29a58:	b4000536 	cbz	x22, 29afc <Java_com_google_android_gms_tflite_nnapi_NnApiDelegateImpl_createDelegate@@VERS_1.0+0x17c>
       29a5c:	f9400328 	ldr	x8, [x25]
       29a60:	aa1903e0 	mov	x0, x25
       29a64:	aa1603e1 	mov	x1, x22
       29a68:	aa1f03e2 	mov	x2, xzr
       29a6c:	f942a508 	ldr	x8, [x8, #1352]
       29a70:	d63f0100 	blr	x8
    ---
       29a6c:	f942a508 	ldr	x8, [x8, #1352]
       29a70:	d63f0100 	blr	x8
       29a74:	aa0003fb 	mov	x27, x0
       29a78:	910003e0 	mov	x0, sp
       29a7c:	aa1b03e1 	mov	x1, x27
       29a80:	9400008c 	bl	29cb0 <Java_com_google_android_gms_tflite_nnapi_NnApiDelegateImpl_createDelegate@@VERS_1.0+0x330>
       29a84:	f9400328 	ldr	x8, [x25]
       29a88:	2a0003fc 	mov	w28, w0
       29a8c:	aa1903e0 	mov	x0, x25
       29a90:	aa1603e1 	mov	x1, x22
       29a94:	aa1b03e2 	mov	x2, x27
       29a98:	f942a908 	ldr	x8, [x8, #1360]
    ---
       29a90:	aa1603e1 	mov	x1, x22
       29a94:	aa1b03e2 	mov	x2, x27
       29a98:	f942a908 	ldr	x8, [x8, #1360]
       29a9c:	d63f0100 	blr	x8
       29aa0:	2a1c03fb 	mov	w27, w28
       29aa4:	b4000315 	cbz	x21, 29b04 <Java_com_google_android_gms_tflite_nnapi_NnApiDelegateImpl_createDelegate@@VERS_1.0+0x184>
       29aa8:	f9400328 	ldr	x8, [x25]
       29aac:	aa1903e0 	mov	x0, x25
       29ab0:	aa1503e1 	mov	x1, x21
       29ab4:	aa1f03e2 	mov	x2, xzr
       29ab8:	f942a508 	ldr	x8, [x8, #1352]
       29abc:	d63f0100 	blr	x8
    ---
       29ab8:	f942a508 	ldr	x8, [x8, #1352]
       29abc:	d63f0100 	blr	x8
       29ac0:	aa0003fc 	mov	x28, x0
       29ac4:	910003e0 	mov	x0, sp
       29ac8:	aa1c03e1 	mov	x1, x28
       29acc:	94000079 	bl	29cb0 <Java_com_google_android_gms_tflite_nnapi_NnApiDelegateImpl_createDelegate@@VERS_1.0+0x330>
       29ad0:	f9400328 	ldr	x8, [x25]
       29ad4:	2a0003fd 	mov	w29, w0
       29ad8:	aa1903e0 	mov	x0, x25
       29adc:	aa1503e1 	mov	x1, x21
       29ae0:	aa1c03e2 	mov	x2, x28
       29ae4:	f942a908 	ldr	x8, [x8, #1360]
    ---
       29adc:	aa1503e1 	mov	x1, x21
       29ae0:	aa1c03e2 	mov	x2, x28
       29ae4:	f942a908 	ldr	x8, [x8, #1360]
       29ae8:	d63f0100 	blr	x8
       29aec:	2a1d03fc 	mov	w28, w29
       29af0:	14000006 	b	29b08 <Java_com_google_android_gms_tflite_nnapi_NnApiDelegateImpl_createDelegate@@VERS_1.0+0x188>
       29af4:	aa1f03fa 	mov	x26, xzr
       29af8:	b5fffb36 	cbnz	x22, 29a5c <Java_com_google_android_gms_tflite_nnapi_NnApiDelegateImpl_createDelegate@@VERS_1.0+0xdc>
       29afc:	aa1f03fb 	mov	x27, xzr
       29b00:	b5fffd55 	cbnz	x21, 29aa8 <Java_com_google_android_gms_tflite_nnapi_NnApiDelegateImpl_createDelegate@@VERS_1.0+0x128>
       29b04:	aa1f03fc 	mov	x28, xzr
       29b08:	52800028 	mov	w8, #0x1                   	// #1
    ---
       29ae4:	f942a908 	ldr	x8, [x8, #1360]
       29ae8:	d63f0100 	blr	x8
       29aec:	2a1d03fc 	mov	w28, w29
       29af0:	14000006 	b	29b08 <Java_com_google_android_gms_tflite_nnapi_NnApiDelegateImpl_createDelegate@@VERS_1.0+0x188>
       29af4:	aa1f03fa 	mov	x26, xzr
       29af8:	b5fffb36 	cbnz	x22, 29a5c <Java_com_google_android_gms_tflite_nnapi_NnApiDelegateImpl_createDelegate@@VERS_1.0+0xdc>
       29afc:	aa1f03fb 	mov	x27, xzr
       29b00:	b5fffd55 	cbnz	x21, 29aa8 <Java_com_google_android_gms_tflite_nnapi_NnApiDelegateImpl_createDelegate@@VERS_1.0+0x128>
       29b04:	aa1f03fc 	mov	x28, xzr
       29b08:	52800028 	mov	w8, #0x1                   	// #1
       29b0c:	b94033f9 	ldr	w25, [sp, #48]
       29b10:	910003e0 	mov	x0, sp
    ---
       29aec:	2a1d03fc 	mov	w28, w29
       29af0:	14000006 	b	29b08 <Java_com_google_android_gms_tflite_nnapi_NnApiDelegateImpl_createDelegate@@VERS_1.0+0x188>
       29af4:	aa1f03fa 	mov	x26, xzr
       29af8:	b5fffb36 	cbnz	x22, 29a5c <Java_com_google_android_gms_tflite_nnapi_NnApiDelegateImpl_createDelegate@@VERS_1.0+0xdc>
       29afc:	aa1f03fb 	mov	x27, xzr
       29b00:	b5fffd55 	cbnz	x21, 29aa8 <Java_com_google_android_gms_tflite_nnapi_NnApiDelegateImpl_createDelegate@@VERS_1.0+0x128>
       29b04:	aa1f03fc 	mov	x28, xzr
       29b08:	52800028 	mov	w8, #0x1                   	// #1
       29b0c:	b94033f9 	ldr	w25, [sp, #48]
       29b10:	910003e0 	mov	x0, sp
       29b14:	52800141 	mov	w1, #0xa                   	// #10
       29b18:	2a1803e2 	mov	w2, w24
    ---
       29b10:	910003e0 	mov	x0, sp
       29b14:	52800141 	mov	w1, #0xa                   	// #10
       29b18:	2a1803e2 	mov	w2, w24
       29b1c:	2a1f03e3 	mov	w3, wzr
       29b20:	390183e8 	strb	w8, [sp, #96]
       29b24:	9400009f 	bl	29da0 <Java_com_google_android_gms_tflite_nnapi_NnApiDelegateImpl_deleteDelegate@@VERS_1.0+0xc>
       29b28:	b40000b7 	cbz	x23, 29b3c <Java_com_google_android_gms_tflite_nnapi_NnApiDelegateImpl_createDelegate@@VERS_1.0+0x1bc>
       29b2c:	910003e0 	mov	x0, sp
       29b30:	52800081 	mov	w1, #0x4                   	// #4
       29b34:	aa1a03e2 	mov	x2, x26
       29b38:	94000154 	bl	2a088 <Java_com_google_android_gms_tflite_nnapi_NnApiDelegateImpl_deleteDelegate@@VERS_1.0+0x2f4>
       29b3c:	b40000b6 	cbz	x22, 29b50 <Java_com_google_android_gms_tflite_nnapi_NnApiDelegateImpl_createDelegate@@VERS_1.0+0x1d0>
    ---
       29b14:	52800141 	mov	w1, #0xa                   	// #10
       29b18:	2a1803e2 	mov	w2, w24
       29b1c:	2a1f03e3 	mov	w3, wzr
       29b20:	390183e8 	strb	w8, [sp, #96]
       29b24:	9400009f 	bl	29da0 <Java_com_google_android_gms_tflite_nnapi_NnApiDelegateImpl_deleteDelegate@@VERS_1.0+0xc>
       29b28:	b40000b7 	cbz	x23, 29b3c <Java_com_google_android_gms_tflite_nnapi_NnApiDelegateImpl_createDelegate@@VERS_1.0+0x1bc>
       29b2c:	910003e0 	mov	x0, sp
       29b30:	52800081 	mov	w1, #0x4                   	// #4
       29b34:	aa1a03e2 	mov	x2, x26
       29b38:	94000154 	bl	2a088 <Java_com_google_android_gms_tflite_nnapi_NnApiDelegateImpl_deleteDelegate@@VERS_1.0+0x2f4>
       29b3c:	b40000b6 	cbz	x22, 29b50 <Java_com_google_android_gms_tflite_nnapi_NnApiDelegateImpl_createDelegate@@VERS_1.0+0x1d0>
       29b40:	910003e0 	mov	x0, sp
    ---
       29b24:	9400009f 	bl	29da0 <Java_com_google_android_gms_tflite_nnapi_NnApiDelegateImpl_deleteDelegate@@VERS_1.0+0xc>
       29b28:	b40000b7 	cbz	x23, 29b3c <Java_com_google_android_gms_tflite_nnapi_NnApiDelegateImpl_createDelegate@@VERS_1.0+0x1bc>
       29b2c:	910003e0 	mov	x0, sp
       29b30:	52800081 	mov	w1, #0x4                   	// #4
       29b34:	aa1a03e2 	mov	x2, x26
       29b38:	94000154 	bl	2a088 <Java_com_google_android_gms_tflite_nnapi_NnApiDelegateImpl_deleteDelegate@@VERS_1.0+0x2f4>
       29b3c:	b40000b6 	cbz	x22, 29b50 <Java_com_google_android_gms_tflite_nnapi_NnApiDelegateImpl_createDelegate@@VERS_1.0+0x1d0>
       29b40:	910003e0 	mov	x0, sp
       29b44:	528000c1 	mov	w1, #0x6                   	// #6
       29b48:	aa1b03e2 	mov	x2, x27
       29b4c:	9400014f 	bl	2a088 <Java_com_google_android_gms_tflite_nnapi_NnApiDelegateImpl_deleteDelegate@@VERS_1.0+0x2f4>
       29b50:	b40000b5 	cbz	x21, 29b64 <Java_com_google_android_gms_tflite_nnapi_NnApiDelegateImpl_createDelegate@@VERS_1.0+0x1e4>
    ---
       29b28:	b40000b7 	cbz	x23, 29b3c <Java_com_google_android_gms_tflite_nnapi_NnApiDelegateImpl_createDelegate@@VERS_1.0+0x1bc>
       29b2c:	910003e0 	mov	x0, sp
       29b30:	52800081 	mov	w1, #0x4                   	// #4
       29b34:	aa1a03e2 	mov	x2, x26
       29b38:	94000154 	bl	2a088 <Java_com_google_android_gms_tflite_nnapi_NnApiDelegateImpl_deleteDelegate@@VERS_1.0+0x2f4>
       29b3c:	b40000b6 	cbz	x22, 29b50 <Java_com_google_android_gms_tflite_nnapi_NnApiDelegateImpl_createDelegate@@VERS_1.0+0x1d0>
       29b40:	910003e0 	mov	x0, sp
       29b44:	528000c1 	mov	w1, #0x6                   	// #6
       29b48:	aa1b03e2 	mov	x2, x27
       29b4c:	9400014f 	bl	2a088 <Java_com_google_android_gms_tflite_nnapi_NnApiDelegateImpl_deleteDelegate@@VERS_1.0+0x2f4>
       29b50:	b40000b5 	cbz	x21, 29b64 <Java_com_google_android_gms_tflite_nnapi_NnApiDelegateImpl_createDelegate@@VERS_1.0+0x1e4>
       29b54:	910003e0 	mov	x0, sp
    ---
       29b38:	94000154 	bl	2a088 <Java_com_google_android_gms_tflite_nnapi_NnApiDelegateImpl_deleteDelegate@@VERS_1.0+0x2f4>
       29b3c:	b40000b6 	cbz	x22, 29b50 <Java_com_google_android_gms_tflite_nnapi_NnApiDelegateImpl_createDelegate@@VERS_1.0+0x1d0>
       29b40:	910003e0 	mov	x0, sp
       29b44:	528000c1 	mov	w1, #0x6                   	// #6
       29b48:	aa1b03e2 	mov	x2, x27
       29b4c:	9400014f 	bl	2a088 <Java_com_google_android_gms_tflite_nnapi_NnApiDelegateImpl_deleteDelegate@@VERS_1.0+0x2f4>
       29b50:	b40000b5 	cbz	x21, 29b64 <Java_com_google_android_gms_tflite_nnapi_NnApiDelegateImpl_createDelegate@@VERS_1.0+0x1e4>
       29b54:	910003e0 	mov	x0, sp
       29b58:	52800101 	mov	w1, #0x8                   	// #8
       29b5c:	aa1c03e2 	mov	x2, x28
       29b60:	9400014a 	bl	2a088 <Java_com_google_android_gms_tflite_nnapi_NnApiDelegateImpl_deleteDelegate@@VERS_1.0+0x2f4>
       29b64:	3943a3f5 	ldrb	w21, [sp, #232]
    ---
       29b3c:	b40000b6 	cbz	x22, 29b50 <Java_com_google_android_gms_tflite_nnapi_NnApiDelegateImpl_createDelegate@@VERS_1.0+0x1d0>
       29b40:	910003e0 	mov	x0, sp
       29b44:	528000c1 	mov	w1, #0x6                   	// #6
       29b48:	aa1b03e2 	mov	x2, x27
       29b4c:	9400014f 	bl	2a088 <Java_com_google_android_gms_tflite_nnapi_NnApiDelegateImpl_deleteDelegate@@VERS_1.0+0x2f4>
       29b50:	b40000b5 	cbz	x21, 29b64 <Java_com_google_android_gms_tflite_nnapi_NnApiDelegateImpl_createDelegate@@VERS_1.0+0x1e4>
       29b54:	910003e0 	mov	x0, sp
       29b58:	52800101 	mov	w1, #0x8                   	// #8
       29b5c:	aa1c03e2 	mov	x2, x28
       29b60:	9400014a 	bl	2a088 <Java_com_google_android_gms_tflite_nnapi_NnApiDelegateImpl_deleteDelegate@@VERS_1.0+0x2f4>
       29b64:	3943a3f5 	ldrb	w21, [sp, #232]
       29b68:	72001e9f 	tst	w20, #0xff
    ---

Protobuf/config clues:

    0x2953: Java_com_google_android_gms_tflite_nnapi_NnApiDelegateImpl_createDelegate
    0x29ab: Java_com_google_android_gms_tflite_nnapi_NnApiDelegateImpl_getNnapiErrno
    0x29f4: Java_com_google_android_gms_tflite_nnapi_NnApiDelegateImpl_deleteDelegate
    0x3945: Java_com_google_android_gms_tflite_TensorImpl_hasDelegateBufferHandle
    0x3b39: GmsTfLiteOpaqueContextReplaceNodeSubsetsWithDelegateKernels
    0x412d: GmsTfLiteOpaqueDelegateCreate
    0x414b: GmsTfLiteOpaqueDelegateDelete
    0x4169: GmsTfLiteOpaqueDelegateGetData
    0x4188: GmsTfLiteNnapiDelegatePluginCApi
    0x443e: GmsTfLiteInterpreterOptionsAddDelegate
    0x4465: GmsTfLiteInternalInterpreterOptionsSetEnableDelegateFallback
    0x4957: Java_com_google_android_gms_tflite_gpu_GpuDelegate_createDelegate
    0x4999: Java_com_google_android_gms_tflite_gpu_GpuDelegate_deleteDelegate
    0x49db: Java_com_google_android_gms_tflite_gpu_GpuDelegateNative_nativeDoNothing
    0x4ade: GmsTfLiteGpuDelegatePluginCApi
    0x4eb2: GmsTfLiteXnnpackDelegatePluginCApi
    0x785f: Internal error: null object in Delegate handle list
    0x7a9b: TfLiteOpaqueDelegateOptionsCreate
    0x7b48: TfLiteGpuDelegateDestroy
    0x7d2e: Internal error: Failed to apply delegate.
    0x7e43: TfLiteNnapiDelegateCreate
    0x878a: TfLiteOpaqueDelegateOptionsSetCopyToBufferHandle
    0x8f2e: TfLiteXnnpackDelegateCreate
    0x9acb: TfLiteOpaqueDelegateDelete
    0x9bef: Restored original execution plan after delegate application failure.
    0x9f4e: TfLiteOpaqueDelegateOptionsSetFreeBufferHandle
    0xa59e: Internal error: Error applying delegate: %s
    0xa5f0: TfLiteNnapiDelegateDestroy
    0xab2a: Internal error: Failed to apply delegate: %s
    0xab90: TfLiteOpaqueDelegateOptionsDelete
    0xabb2: TfLiteOpaqueDelegateOptionsSetCopyFromBufferHandle
    0xb059: TfLiteOpaqueDelegateOptionsSetFlags
    0xb216: TfLiteOpaqueDelegateGetData
    0xb714: TfLiteGpuDelegateErrno
    0xb76f: TfLiteXnnpackDelegateDestroy
    0xbbad: Restored original execution plan after delegate application failure.
    0xbbf2: Restored original execution plan after delegate application failure.
    0xbcf2: TfLiteOpaqueDelegateCreate
    0xbd6b: TfLiteInterpreterOptionsAddDelegate not supported: TFLite-in-GMSCore module's stable ABI version < 1.1.0, and app had no dependency on //java/com/google/android/gmscore/integ/client/tflite/native:experimental_abi 
    0xc614: TfLiteOpaqueContextReplaceNodeSubsetsWithDelegateKernels
    0xc688: TfLiteOpaqueDelegateOptionsSetData
    0xc88f: TfLiteNnapiDelegateErrno
    0xc91e: TfLiteXnnpackDelegateErrno
    0xcd23: TfLiteGpuDelegateCreate
    0xd74a: third_party/absl/base/throw_delegate.cc
    0xd81d: N6tflite3jni27OpResolverLazyDelegateProxyE
    0xd85e: NSt6__ndk110__function6__funcIPFNS_10unique_ptrI14TfLiteDelegatePFvPS3_EEEP13TfLiteContextENS_9allocatorISB_EESA_EE
    0xd8d2: NSt6__ndk110__function6__baseIFNS_10unique_ptrI14TfLiteDelegatePFvPS3_EEEP13TfLiteContextEEE
    0xd92f: PFNSt6__ndk110unique_ptrI14TfLiteDelegatePFvPS1_EEEP13TfLiteContextE
    0xd974: FNSt6__ndk110unique_ptrI14TfLiteDelegatePFvPS1_EEEP13TfLiteContextE
    0xd9b8: NSt6__ndk110__function6__funcIPFNS_10unique_ptrI26TfLiteOpaqueDelegateStructPFvPS3_EEEiENS_9allocatorIS9_EES8_EE
    0xda29: NSt6__ndk110__function6__baseIFNS_10unique_ptrI26TfLiteOpaqueDelegateStructPFvPS3_EEEiEEE
    0xda83: PFNSt6__ndk110unique_ptrI26TfLiteOpaqueDelegateStructPFvPS1_EEEiE
    0xdac5: FNSt6__ndk110unique_ptrI26TfLiteOpaqueDelegateStructPFvPS1_EEEiE
    0xdb79: N7gmscore6tflite3ops7builtin40BuiltinOpResolverWithoutDefaultDelegatesE
    0xdcb5: NSt6__ndk110__function6__funcIPFvP26TfLiteOpaqueDelegateStructENS_9allocatorIS5_EES4_EE
    0xdd0d: NSt6__ndk110__function6__baseIFvP26TfLiteOpaqueDelegateStructEEE
    0xdd4e: PFvP26TfLiteOpaqueDelegateStructE
    0xdd70: FvP26TfLiteOpaqueDelegateStructE
    0xdfba: NSt6__ndk110__function6__funcIZN7gmscore6tflite3ops7builtin17BuiltinOpResolverC1EvE3$_0NS_9allocatorIS7_EEFNS_10unique_ptrI26TfLiteOpaqueDelegateStructPFvPSB_EEEiEEE

## Next confirmation step

Trace the GroupRPN model-runner constructor to the actual interpreter/delegate creation site. Detector and recognizer must be traced separately.
Raw readelf/strings/disassembly evidence is uploaded as the workflow artifact and is not committed in full.
