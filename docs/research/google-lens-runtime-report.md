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

## Targeted runner neighborhoods

    ### TensorFlowModelRunnerConfig 0x6a27c Invalid TensorFlowModelRunnerConfig.
      -6074 0x68ac2  mask_b = 
      -6063 0x68acd   reducer.x = min(reducer.x, reducer.y);
      -6021 0x68af7 ) + (
      -6015 0x68afd       int p = base + i;
      -5990 0x68b16   int src_b = p / args.src_tensor.Height();
      -5945 0x68b43   int dst_bhwc4 = B;
      -5923 0x68b59 true_tensor
      -5911 0x68b65   args.else_tensor.SetBatchRef((args.else_tensor.Batch() == 1 ? 0 : B));
      -5837 0x68baf m_i.w
      -5831 0x68bb5     if (d * 4 + 3 < args.dst_tensor.Channels()) maximum = max(maximum, t.w);
      -5753 0x68c03     float4 src = args.src_tensor.Read<float>(X, Y, s);
      -5697 0x68c3b     sum += dot(mask_temp, exp(src));
      -5659 0x68c61     float4 src = args.src_tensor.Read<float>(X, Y, dst_s) - INIT_FLOAT4(maximum);
      -5576 0x68cb4  == 0
      -5570 0x68cba  = (xc
      -5563 0x68cc1     int yc = tile_y + args.padding_y + (
      -5522 0x68cea   int tile_y = (tile_id / args.tiles_x) * 4 + DST_Y;
      -5468 0x68d20   if (tile_x < args.dst_tensor.Width()) {
      -5425 0x68d4b     int coord_y = Y + 
      -5402 0x68d62   float2 sum;
      -5387 0x68d71   float mean_sq = sum.y * args.inv_ch_count;
      -5341 0x68d9f   {  // reduction
      -5322 0x68db2  input in a 
      -5309 0x68dbf       FLT4 w2 = args.weights0.Read<
      -5273 0x68de3   int y_offseted = Y * args.stride_y + args.padding_y;
      -5217 0x68e1b ->add
      -5211 0x68e21 $0 = max($1, $2);
      -5193 0x68e33 $0.x = $1.x > $2.x;
      -5172 0x68e48 second_tensor
      -5158 0x68e56 OpenCL error: 
      -5143 0x68e65   __attribute__((
      -5125 0x68e77 __constant sampler_t smp_zero = CLK_NORMALIZED_COORDS_FALSE | CLK_ADDRESS_NONE | CLK_FILTER_NEAREST;
      -5023 0x68edd SINGLE_TEXTURE_2D support only channels in range [1-4], but 
      -4962 0x68f1a ro.product.brand
      -4945 0x68f2b Out of resources
      -4928 0x68f3c Misaligned sub-buffer offset
      -4899 0x68f59 libOpenCL-car.so
      -4882 0x68f6a OpenCL is not supported.
      -4857 0x68f83 clCreateContextFromType
      -4833 0x68f9b clGetPipeInfo
      -4819 0x68fa9 clCreateKernel
      -4804 0x68fb8 clFinish
      -4795 0x68fc1 clEnqueueAcquireEGLObjectsKHR
      -4765 0x68fdf third_party/tensorflow/lite/delegates/gpu/common/task/gpu_operation.cc
      -4694 0x69026 _buffer[] = 
      -4681 0x69033 $0(image2d, (int2)($1, $2), $3)
      -4649 0x69053  can not be created. Max Image3D width for this GPU - 
      -4594 0x6908a (convert_
      -4584 0x69094 PassThrough
      -4572 0x690a0 The maximum of the output uint tensor range must be less than or equal to 255.
      -4492 0x690f0       #define INPUT_STARTS_AT_BOTTOM;
      -4454 0x69116     
      -4449 0x6911b output_shape.dims[0] >= 1
      -4423 0x69135 glDeleteBuffers in third_party/tensorflow/lite/delegates/gpu/gl/gl_buffer.cc:78
      -4343 0x69185 glUnmapBuffer in third_party/tensorflow/lite/delegates/gpu/gl/gl_buffer.cc:160
      -4264 0x691d4 input_tensor_width > 0 && input_tensor_height > 0
      -4214 0x69206 cc.output_size_in
      -4196 0x69218 ksize.width > 0 && ksize.height > 0
      -4160 0x6923c void cv::hal::cpu_baseline::(anonymous namespace)::RGB2HSV_b::operator()(const uchar *, uchar *, int) const
      -4052 0x692a8 virtual void cv::impl::(anonymous namespace)::CvtColorLoop_Invoker<cv::RGB2Luv_f>::operator()(const Range &) const [Cvt = cv::RGB2Luv_f]
      -3915 0x69331 int cv::cpu_baseline::FilterEngine__start(FilterEngine &, const Size &, const Size &, const Point &)
      -3814 0x69396 third_party/OpenCV/public/modules/imgproc/src/filter.dispatch.cpp
      -3748 0x693d8 virtual void cv::cpu_baseline::RowFilter<float, double, cv::cpu_baseline::RowNoVec>::operator()(const uchar *, uchar *, int, int) [ST = float, DT = double, VecOp = cv::cpu_baseline::RowNoVec]
      -3556 0x69498 virtual void cv::cpu_baseline::SymmColumnFilter<cv::cpu_baseline::FixedPtCastEx<int, unsigned char>, cv::cpu_baseline::SymmColumnVec_32s8u>::operator()(const uchar **, uchar *, int, int, int) [CastOp = cv::cpu_baseline::FixedPtCastEx<int, unsigned char>, VecOp = cv::cpu_baseline::SymmColumnVec_32s8u]
      -3254 0x695c6 virtual void cv::cpu_baseline::SymmColumnFilter<cv::cpu_baseline::Cast<float, unsigned char>, cv::cpu_baseline::SymmColumnVec_32f8u>::operator()(const uchar **, uchar *, int, int, int) [CastOp = cv::cpu_baseline::Cast<float, unsigned char>, VecOp = cv::cpu_baseline::SymmColumnVec_32f8u]
      -2966 0x696e6 virtual void cv::cpu_baseline::SymmColumnFilter<cv::cpu_baseline::Cast<float, short>, cv::cpu_baseline::SymmColumnVec_32f16s>::operator()(const uchar **, uchar *, int, int, int) [CastOp = cv::cpu_baseline::Cast<float, short>, VecOp = cv::cpu_baseline::SymmColumnVec_32f16s]
      -2692 0x697f8 calcHist
      -2683 0x69801 split x_offset uniform not found.
      -2649 0x69823 Tensor::GetOpenGlBufferWriteView is not executed on the same GL context where GL buffer was created. Note that Tensor has limited synchronization support when sharing OpenGl objects between multiple OpenGL contexts.
      -2433 0x698fb locked_ptr is OK
      -2416 0x6990c glDeleteTextures in third_party/tensorflow/lite/delegates/gpu/gl/gl_texture.cc:60
      -2334 0x6995e BaseOptions::GpuOptions::cached_kernel_path ('
      -2287 0x6998d Input form tensor could be only int32 or int64
      -2240 0x699bc Not supported row partitioning tensor type
      -2197 0x699e7 Incorrect dimensions size: %d
      -2167 0x69a05 Non-constant per-channel quantized tensor: 
      -2123 0x69a31 To_remove node has other inputs
      -2091 0x69a51 ceil
      -2086 0x69a56 gather
      -2079 0x69a5d mean
      -2074 0x69a62 tile
      -2069 0x69a67 data_type
      -2059 0x69a71 Expected ImageProperties for tensor 
      -2022 0x69a96 multi_callback_
      -2006 0x69aa6 0 <= output_stream_index
      -1981 0x69abf num_pending_tasks_ == 0
      -1957 0x69ad7 Wrote graph runtime info to 
      -1928 0x69af4 , ts bound: 
      -1915 0x69b01 : external context uses a different version of OpenGL
      -1861 0x69b37 invalid plane number
      -1840 0x69b4c CalculatorNode::OpenNode() for 
      -1808 0x69b6c third_party/mediapipe/framework/tool/fill_packet_set.cc
      -1752 0x69ba4 Missing input side packet: 
      -1724 0x69bc0 : Filled input set at ts: 
      -1697 0x69bdb Expected packet info is missing for: 
      -1659 0x69c01 timer_status is OK
      -1640 0x69c14 A call to Calculator::Close.
      -1611 0x69c31 CPU timing for initiating a GPU task.
      -1573 0x69c57 Unable to find StatusHandler "
      -1542 0x69c76 Output Side Packet "
      -1521 0x69c8b third_party/mediapipe/framework/tool/options_util.cc
      -1468 0x69cc0 Dict requires an even number of arguments, got: 
      -1419 0x69cf1 ProtoPath field missing, field-id: 
      -1383 0x69d15 Input stream 
      -1369 0x69d23  Size:
      -1362 0x69d2a In stream "
      -1350 0x69d36 Locking memory for file '
      -1324 0x69d50 pittpatt_drishti::asr_captions_segmenter_demo
      -1278 0x69d7e pittpatt_drishti::change_event_demo
      -1242 0x69da2 video_pipeline
      -1227 0x69db1 Setting "read_as_binary" to false is a no-op on Android.
      -1170 0x69dea drishti.CalculatorGraphConfig.Node.calculator
      -1124 0x69e18 drishti.CalculatorGraphConfig.Node.executor
      -1080 0x69e44 mediapipe.tasks.core.proto.FilePointerMeta
      -1037 0x69e6f Size mismatch or unsupported padding bytes between pixel data and input tensor.
       -957 0x69ebf kTfLiteInt8 input type is not implemented yet.
       -910 0x69eee Libyuv I420Rotate operation failed.
       -874 0x69f12 Libyuv NV12ToABGR operation failed.
       -838 0x69f36 Libyuv ARGBToJ400 operation failed.
       -802 0x69f5a third_party/tensorflow_lite_support/cc/task/vision/utils/frame_buffer_common_utils.cc
       -716 0x69fb0 opts_.cell_threshold <= ColorCounter::kSize
       -672 0x69fdc width >= 0
       -661 0x69fe7 proj0_w
       -653 0x69fef 0 == rnn_init_states_.count(name)
       -619 0x6a011 tensor.has_name()
       -601 0x6a023 LogisticActivation
       -582 0x6a036 gemmlowp error: %s
       -562 0x6a04a box_index < classifier_sparse_scores->size()
       -517 0x6a077 Segmenter and BeamSearch output
       -485 0x6a097     Skipped segment, too small or too big.
       -442 0x6a0c2 ./ocr/photo/features/aligned_features.h
       -402 0x6a0ea ./ocr/photo/features/ocr_shapes_hog_features.h
       -355 0x6a119 gradient_magnitudes.size() == pix->w * pix->h
       -309 0x6a147 normalized_bottom > normalized_top
       -274 0x6a16a grad_mag_array != nullptr
       -240 0x6a18c  s_in: 
       -232 0x6a194 Valid CC candidate ratio = 
       -204 0x6a1b0 ocr/photo/detection/region_proposal_text_detector.cc
       -151 0x6a1e5 Use variable tiling
       -131 0x6a1f9 Cropped box image patch has one dimension zero wxh: 
        -78 0x6a22e Split Cluster using piece-wise fitting
        -39 0x6a255  aver i: 
        -29 0x6a25f Boxes overlap with cluster: 
         +0 0x6a27c Invalid TensorFlowModelRunnerConfig.
        +37 0x6a2a1 aai-Latn-PG
        +57 0x6a2b5 abq-Latn
        +66 0x6a2be ach-Latn-UG
        +94 0x6a2da ahh-Latn-ID
       +106 0x6a2e6 ahm-Latn-CI
       +118 0x6a2f2 aip-Latn-ID
       +130 0x6a2fe aji-Latn-NC
       +142 0x6a30a ali-Latn-PG
       +158 0x6a31a amp-Latn-PG
       +170 0x6a326 ang-Latn-GB
       +182 0x6a332 anr-Deva-IN
       +194 0x6a33e aod-Latn-PG
       +210 0x6a34e apl-Latn-US
       +226 0x6a35e aqm-Latn-ID
       +242 0x6a36e atd-Latn-PH
       +254 0x6a37a atg-Latn-NG
       +281 0x6a395 bac-Latn-ID
       +297 0x6a3a5 bba-Latn-BJ
       +313 0x6a3b5 bcd-Latn-ID
       +325 0x6a3c1 bdc-Latn-CO
       +337 0x6a3cd be-Cyrl-BY
       +348 0x6a3d8 bei-Latn-ID
       +360 0x6a3e4 bes-Latn-TD
       +372 0x6a3f0 bey-Latn-PG
       +396 0x6a408 bhd-Deva-IN
       +408 0x6a414 bhf-Latn-PG
       +444 0x6a438 bmp-Latn-PG
       +456 0x6a444 bmu-Latn-PG
       +472 0x6a454 bo-Tibt-CN
       +491 0x6a467 bsc-Latn-SN
       +511 0x6a47b bto-Latn-PH
       +523 0x6a487 btx-Latn-ID
       +547 0x6a49f bxq-Latn-NG
       +563 0x6a4af bym-Latn-AU
       +575 0x6a4bb byr-Latn-PG
       +587 0x6a4c7 byw-Deva-NP
       +599 0x6a4d3 cdo-Hans-CN
       +611 0x6a4df chf-Latn-MX
       +631 0x6a4f3 cli-Latn-GH
       +647 0x6a503 cnt-Latn-MX
       +659 0x6a50f cpx-Latn-CN
       +675 0x6a51f csm-Latn-US
       +687 0x6a52b cy-Latn-GB
       +698 0x6a536 dam-Latn-NG
       +714 0x6a546 ddd-Latn-SS
       +762 0x6a576 dsq-Latn-ML
       +774 0x6a582 dtb-Latn-MY
       +786 0x6a58e duu-Latn-CN
       +798 0x6a59a dwk-Orya-IN
       +810 0x6a5a6 dyi-Latn-CI
       +838 0x6a5c2 ekl-Latn-BD
       +850 0x6a5ce eko-Latn-MZ
       +862 0x6a5da ema-Latn-NG
       +874 0x6a5e6 emz-Latn-CM
       +898 0x6a5fe fif-Latn-SA
       +918 0x6a612 gaj-Latn-PG
       +930 0x6a61e gbe-Latn-PG
       +942 0x6a62a gby-Latn-NG
       +954 0x6a636 gbz-Arab-IR
       +970 0x6a646 gcn-Latn-PG
       +982 0x6a652 gec-Latn-LR
       +994 0x6a65e gin-Cyrl-RU
      +1006 0x6a66a gkn-Latn-NG
      +1022 0x6a67a god-Latn-CI
      +1038 0x6a68a grt-Beng-IN
      +1050 0x6a696 gtu-Latn-AU
      +1066 0x6a6a6 gup-Latn-AU
      +1086 0x6a6ba gww-Latn-AU
      +1098 0x6a6c6 ha-Arab-CM
      +1109 0x6a6d1 hei-Latn-CA
      +1129 0x6a6e5 hio-Latn-BW
      +1149 0x6a6f9 hna-Latn-CM
      +1177 0x6a715 ibu-Latn-ID
      +1193 0x6a725 ig-Latn-NG
      +1204 0x6a730 ihw-Latn-AU
      +1216 0x6a73c ii-Yiii-CN
      +1235 0x6a74f iow-Latn-US
      +1255 0x6a763 itr-Latn-PG
      +1279 0x6a77b jat-Arab-AF
      +1291 0x6a787 jbm-Latn-NG
      +1303 0x6a793 jbt-Latn-BR
      +1315 0x6a79f jei-Latn-ID
      +1327 0x6a7ab jiu-Latn-CN
      +1339 0x6a7b7 jmw-Latn-PG
      +1359 0x6a7cb kav-Latn-BR
      +1371 0x6a7d7 kbe-Latn-AU
      +1383 0x6a7e3 kbv-Latn-ID
      +1399 0x6a7f3 kef-Latn-TG
      +1415 0x6a803 kfp-Deva-IN
      +1427 0x6a80f kiu-Latn-TR
      +1443 0x6a81f kkh-Lana-MM
      +1455 0x6a82b klh-Latn-PG
      +1483 0x6a847 krz-Latn-ID
      +1495 0x6a853 ksk-Latn-US
      +1511 0x6a863 kug-Latn-NG
      +1531 0x6a877 kuu-Latn-US
      +1543 0x6a883 kux-Latn-AU
      +1563 0x6a897 kvo-Latn-ID
      +1575 0x6a8a3 kvy-Kali-MM
      +1587 0x6a8af kwm-Latn-NA
      +1599 0x6a8bb kwo-Latn-PG
      +1615 0x6a8cb kxt-Latn-PG
      +1643 0x6a8e7 lcp-Thai-CN
      +1659 0x6a8f7 lew-Latn-ID
      +1671 0x6a903 lie-Latn-CD
      +1699 0x6a91f lnu-Latn-NG
      +1711 0x6a92b low-Latn-MY
      +1739 0x6a947 lrv-Latn-VU
      +1759 0x6a95b lwh-Latn-VN
      +1771 0x6a967 lxm-Latn-PG
      +1787 0x6a977 man-Nkoo
      +1804 0x6a988 mcq-Latn-PG
      +1824 0x6a99c mea-Latn-CM
      +1844 0x6a9b0 mez-Latn-US
      +1860 0x6a9c0 mfv-Latn-SN
      +1884 0x6a9d8 miq-Latn-NI
      +1900 0x6a9e8 mjr-Mlym-IN
      +1920 0x6a9fc mky-Latn-ID
      +1932 0x6aa08 mlj-Latn-TD
      +1944 0x6aa14 mlx-Latn-VU
      +1964 0x6aa28 mnp-Latn-CN
      +1980 0x6aa38 mpc-Latn-AU
      +1992 0x6aa44 mpl-Latn-PG
      +2008 0x6aa54 mql-Latn-BJ
      +2028 0x6aa68 msm-Latn-PH
      +2048 0x6aa7c muz-Ethi-ET
      +2068 0x6aa90 mvn-Latn-PG
      +2084 0x6aaa0 mxj-Latn-IN
      +2100 0x6aab0 mzb-Arab-DZ
      +2128 0x6aacc nbh-Latn-NG
      +2140 0x6aad8 ncz-Latn-US
      +2152 0x6aae4 ndb-Latn-CM
      +2175 0x6aafb ngc-Latn-CD
      +2187 0x6ab07 nht-Latn-MX
      +2199 0x6ab13 niu-Latn-NU
      +2231 0x6ab33 nrn-Runr-GB
      +2243 0x6ab3f nsv-Yiii-CN
      +2259 0x6ab4f nud-Latn-PG
      +2275 0x6ab5f nuv-Latn-BF
      +2295 0x6ab73 obo-Latn-PH
      +2311 0x6ab83 oks-Latn-NG
      +2327 0x6ab93 oma-Latn-US
      +2343 0x6aba3 orc-Latn-KE
      +2355 0x6abaf orz-Latn-ID
      +2371 0x6abbf pab-Latn-BR
      +2391 0x6abd3 phv-Arab-AF
      +2403 0x6abdf pi-Deva-IN
      +2414 0x6abea pi-LK
      +2420 0x6abf0 pic-Latn-GA
      +2432 0x6abfc pis-Latn-SB
      +2452 0x6ac10 pmh-Brah-IN
      +2476 0x6ac28 prh-Latn-PH
      +2488 0x6ac34 prt-Thai-TH
      +2528 0x6ac5c qxp-Latn-PE
      +2544 0x6ac6c ray-Latn-PF
      +2560 0x6ac7c rhp-Latn-PG
      +2572 0x6ac88 rit-Latn-AU
      +2584 0x6ac94 rkh-Latn-CK
      +2596 0x6aca0 rm-Latn-CH
      +2607 0x6acab rmp-Latn-PG
      +2619 0x6acb7 rnn-Latn-ID
      +2631 0x6acc3 rog-Latn-VN
      +2643 0x6accf rub-Latn-UG
      +2655 0x6acdb sbu-Tibt-IN
      +2667 0x6ace7 sdq-Latn-ID
      +2687 0x6acfb sky-Latn-SB
      +2699 0x6ad07 slp-Latn-ID
      +2715 0x6ad17 smg-Latn-PG
      +2727 0x6ad23 smj-Latn-SE
      +2739 0x6ad2f sog-Sogd-UZ
      +2751 0x6ad3b sol-Latn-PG
      +2771 0x6ad4f spv-Orya-IN
      +2783 0x6ad5b sqo-Arab-IR
      +2795 0x6ad67 sr-Latn-TR
      +2806 0x6ad72 srl-Latn-ID
      +2829 0x6ad89 sxu-Runr-DE
      +2841 0x6ad95 szc-Latn-MY
      +2853 0x6ada1 szw-Latn-ID
      +2869 0x6adb1 taf-Latn-BR
      +2881 0x6adbd tbf-Latn-PG
      +2893 0x6adc9 tbu-Latn-MX
      +2905 0x6add5 tch-Latn-TC
      +2921 0x6ade5 tcy-Knda-IN
      +2933 0x6adf1 tdt-Latn-TL
      +2945 0x6adfd tfr-Latn-PA
      +2957 0x6ae09 tgh-Latn-TT
      +2973 0x6ae19 tgs-Latn-VU
      +3009 0x6ae3d tkp-Latn-SB
      +3021 0x6ae49 tlg-Latn-ID
      +3037 0x6ae59 tlx-Latn-PG
      +3053 0x6ae69 tnb-Latn-CO
      +3069 0x6ae79 tpa-Latn-PG
      +3081 0x6ae85 tpf-Latn-ID
      +3093 0x6ae91 tpn-Latn-BR
      +3109 0x6aea1 trn-Latn-BO
      +3121 0x6aead trq-Latn-MX
      +3141 0x6aec1 tsp-Latn-BF
      +3153 0x6aecd tsu-Latn-TW
      +3165 0x6aed9 tug-Latn-TD
      +3181 0x6aee9 txa-Latn-MY
      +3197 0x6aef9 ubl-Latn-PH
      +3221 0x6af11 uln-Latn-PG
      +3233 0x6af1d und-AZ
      +3240 0x6af24 und-Arab-IR
      +3252 0x6af30 und-BH
      +3259 0x6af37 bsq-Bass-LR
      +3271 0x6af43 und-Brai
      +3280 0x6af4c und-CO
      +3287 0x6af53 es-Latn-CU
      +3298 0x6af5e und-Cyrl-MD
      +3310 0x6af6a und-Cyrl-MN
      +3322 0x6af76 und-ER
      +3329 0x6af7d und-Gong
      +3338 0x6af86 zh-Hant-TW
      +3349 0x6af91 und-Hant-CA
      +3361 0x6af9d und-JP
      +3368 0x6afa4 und-Kana
      +3377 0x6afad bho-Kthi-IN
      +3389 0x6afb9 und-LV
      +3396 0x6afc0 en-Latn-BT
      +3407 0x6afcb fr-Latn-KM
      +3418 0x6afd6 und-Latn-LB
      +3430 0x6afe2 xlc-Lyci-TR
      +3442 0x6afee fr-Latn-MU
      +3453 0x6aff9 und-Modi
      +3462 0x6b002 und-Mymr
      +3471 0x6b00b es-Latn-NI
      +3482 0x6b016 new-Newa-NP
      +3494 0x6b022 und-Sarb
      +3503 0x6b02b und-Takr
      +3512 0x6b034 und-Tale
      +3521 0x6b03d und-Tang
      +3530 0x6b046 und-Tfng
      +3539 0x6b04f und-Tibt-BT
      +3551 0x6b05b und-UG
      +3558 0x6b062 unn-Latn-AU
      +3570 0x6b06e ure-Latn-BO
      +3582 0x6b07a urk-Thai-TH
      +3606 0x6b092 var-Latn-MX
      +3618 0x6b09e vec-Latn-IT
      +3650 0x6b0be wiv-Latn-PG
      +3662 0x6b0ca wlg-Latn-AU
      +3674 0x6b0d6 wni-Arab-KM
      +3686 0x6b0e2 wnp-Latn-PG
      +3698 0x6b0ee woe-Latn-FM
      +3710 0x6b0fa wsv-Arab-AF
      +3722 0x6b106 wur-Latn-AU
      +3734 0x6b112 wuy-Latn-ID
      +3746 0x6b11e wyr-Latn-BR
      +3766 0x6b132 xkj-Arab-IR
      +3782 0x6b142 xpq-Latn-US
      +3802 0x6b156 xwk-Latn-AU
      +3830 0x6b172 ykh-Cyrl-MN
      +3842 0x6b17e ymg-Latn-CD
      +3854 0x6b18a yna-Plrd-CN
      +3882 0x6b1a6 yut-Latn-PG
      +3898 0x6b1b6 zaf-Latn-MX
      +3914 0x6b1c6 zh-PF
      +3920 0x6b1cc zia-Latn-PG
      +3936 0x6b1dc zpv-Latn-MX
      +3952 0x6b1ec Error creating batch of the rest of input tensor.
      +4002 0x6b21e settings->tf_lstm_settings().conv_model_name()
      +4049 0x6b24d ocr/photo/recognition/nnapi_lstm_recognizer.cc
      +4096 0x6b27c lstm_model_size > 0
      +4116 0x6b290 Failed to set compilation's preference: 
      +4157 0x6b2b9 ANeuralNetworksCompilation_finish memory1 
      +4200 0x6b2e4 Failed to set output.
      +4222 0x6b2fa NnapiLstmClient::LoadNnapiModelInfo
      +4258 0x6b31e tensorflow.ConfigProto.device_filters
      +4296 0x6b344 tensorflow.TensorConnection.to_tensor
      +4334 0x6b36a tensorflow.InterconnectLink.type
      +4367 0x6b38b tensorflow.OptimizedFunctionGraph.node_name_to_control_ret
      +4426 0x6b3c6 tensorflow.OpDef.ArgDef.type_attr
      +4460 0x6b3e8 tensorflow.NameAttrList
      +4484 0x6b400 jt != class_labels_.end()
      +4510 0x6b41a  up 
      +4515 0x6b41f node_index < lattice->node_size()
      +4549 0x6b441 ======= Top Candidates at 
      +4576 0x6b45c Invalid Argument: box.width() <= 2, 
      +4613 0x6b481 Large image failure h: %d, w: %d
      +4646 0x6b4a2 google_ocr.ImageCacheProperty
      +4676 0x6b4c0 output_row_size * num_rows == output_tensor->bytes
      +4727 0x6b4f3 batch_size > 0
      +4742 0x6b502 ocr/photo/segmentation/tensor_cache.cc
      +4781 0x6b529 Path "
      +4788 0x6b530  contains parent traversal.
      +4816 0x6b54c namespace-file
      +4831 0x6b55b /mockable/
      +4842 0x6b566 /bigstore/
      +4853 0x6b571 /placer/
      +4862 0x6b57a /x20/
      +4868 0x6b580 append_matches != nullptr
      +4894 0x6b59a PRead
      +4900 0x6b5a0 Getting MemBlock - position=
      +4929 0x6b5bd wrong type
      +4940 0x6b5c8 : finishing operation that was not started
      +4983 0x6b5f3 hidden
      +4990 0x6b5fa on a child?)
      +5003 0x6b607 -PDomainT
      +5013 0x6b611 active_slots_ == 0
      +5032 0x6b624 [^/.]
      +5038 0x6b62a [._]*(?:/|[^/._][._]*)*
      +5062 0x6b642 (Maybe thread tries to join itself?) 
      +5100 0x6b668 Watchdog 
      +5110 0x6b672 Stack dump of thread %d done.
      +5140 0x6b690 /home/build/nonconf/google3/ocr/photo/segmentation/testdata
      +5200 0x6b6cc ro.board.platform
      +5218 0x6b6de Surface-less context is not properly supported on powervr.
      +5277 0x6b719 No EGL error, but eglCreateContext failed.
      +5320 0x6b744 apple a18 pro
      +5338 0x6b756 t604
      +5359 0x6b76b mediump 
      +5667 0x6b89f biztext_euro
      +5680 0x6b8ac alias_obj
      +5690 0x6b8b6 ILLEGAL_SUBTAG
      +5705 0x6b8c5 gregorian
      +5715 0x6b8cf level4
      +5734 0x6b8e2 bali
      +5739 0x6b8e7 segment
      +5747 0x6b8ef aqams
      +5753 0x6b8f5 cnckg
      +5759 0x6b8fb africa/addis_ababa
      +5778 0x6b90e africa/asmera
      +5792 0x6b91c gncky
      +5798 0x6b922 africa/johannesburg
      +5818 0x6b936 america/aruba
      +5832 0x6b944 america/santarem
      +5849 0x6b955 cayxy
      +5855 0x6b95b aqcas
      +5861 0x6b961 asia/amman
      +5872 0x6b96c iqbgw
      +5878 0x6b972 asia/hong_kong
      +5893 0x6b981 rugdx
      +5899 0x6b987 cynic
      +5905 0x6b98d saruh
      +5911 0x6b993 irthr
      +5917 0x6b999 asia/thimphu
      +5930 0x6b9a6 asia/tomsk
      +5941 0x6b9b1 asia/urumqi
      +5953 0x6b9bd australia/brisbane
      +5972 0x6b9d0 australia/darwin
      +5989 0x6b9e1 utcw01
      +5996 0x6b9e8 utcw10
      +6003 0x6b9ef etc/gmt+3
      +6013 0x6b9f9 etc/uct
      +6021 0x6ba01 nlams
      +6027 0x6ba07 debsngn
      +6035 0x6ba0f europe/copenhagen
      +6053 0x6ba21 lulux
      +6059 0x6ba27 ruvog
      +6065 0x6ba2d indian/chagos
      +6079 0x6ba3b indian/mahe
      +6094 0x6ba4a nz-chat
      +6102 0x6ba52 mhmaj
      +6108 0x6ba58 pacific/wallis
      +6123 0x6ba67 turkey
      +6130 0x6ba6e us/arizona
    
    ### TensorFlowModelRunnerConfig 0xb7b19 TensorFlowModelRunnerConfig=
      -6133 0xb6324 num_bits < 32
      -6119 0xb6332 Invalid RE2: 
      -6102 0xb6343 [:space:]
      -6092 0xb634d unexpected )
      -6079 0xb635a Elymaic
      -6065 0xb6368 Tai_Viet
      -6056 0xb6371 Vithkuqi
      -6047 0xb637a Please fix the alias conflict.
      -6016 0xb6399 Compilation
      -6004 0xb63a5 making execution reusable
      -5978 0xb63bf Could not save delegated nodes
      -5947 0xb63de num_splits == input_tensor.dims->data[axis]
      -5903 0xb640a Could not flock %s: %s
      -5880 0xb6421 Found serialized data for model %s (%d B) at %s
      -5832 0xb6451 SL_ANeuralNetworksDiagnosticExecutionInfo_getExecutionMode
      -5773 0xb648c XNNPack weight cache could not be locked in memory.
      -5721 0xb64c0 CheckTensorFloatType
      -5700 0xb64d5 missing zero point quantization parameters for %s tensor %d in XNNPACK delegate
      -5620 0xb6525 end_tensor
      -5609 0xb6530 logit_cap
      -5599 0xb653a xnn_define_tensor_value(subgraph, xnn_datatype_fp32, 0, nullptr, nullptr, XNN_INVALID_VALUE_ID, 0, &scale_out_id)
      -5485 0xb65ac xnn_define_unary(subgraph, xnn_unary_clamp, &clamp_params, scale_orig_id, scale_out_id, 0)
      -5394 0xb6607 xnn_define_tensor_value(subgraph, xnn_datatype_fp32, 0, nullptr, nullptr, XNN_INVALID_VALUE_ID, 0, &cap_div_out_id)
      -5278 0xb667b linear_scale
      -5265 0xb6688 output->params.zero_point
      -5239 0xb66a2 Unsupported datatype for atan2 output: %s
      -5197 0xb66cc params->spectrogram->ComputeSquaredMagnitudeSpectrogram( input_for_channel, &spectrogram_output)
      -5100 0xb672d third_party/tensorflow/lite/kernels/basic_rnn.cc
      -5051 0xb675e accum_dim_rhs
      -5037 0xb676c recurrent_to_forget_weights->dims->size
      -4997 0xb6794 projection_weights->dims->data[0]
      -4963 0xb67b6 projection_bias->dims->size
      -4935 0xb67d2 fw_recurrent_to_output_weights->dims->data[0]
      -4889 0xb6800 bw_num_units
      -4876 0xb680d fw_aux_input_weights->dims->data[0] didn't equal fw_num_units
      -4814 0xb684b input_type
      -4803 0xb6856 filter->dims->data[1] > 0
      -4777 0xb6870 third_party/tensorflow/lite/kernels/conv3d.cc %s
      -4728 0xb68a1 filter_output_channels
      -4705 0xb68b8 NumElements(output_shape)
      -4679 0xb68d2 output_channels * block_size * block_size
      -4637 0xb68fc SizeOfDimension(bias, 0)
      -4612 0xb6915 NumDimensions(input_class_predictions)
      -4573 0xb693c output->quantization.type
      -4547 0xb6956 SizeOfDimension(input_resource_id_tensor, 0)
      -4502 0xb6983 default_value_tensor->type
      -4475 0xb699e SizeOfDimension(value, 0)
      -4449 0xb69b8 forget_layer_norm_coefficients != nullptr
      -4407 0xb69e2 cell_layer_norm_coefficients->dims->data[0]
      -4363 0xb6a0e input->dims->size > 1
      -4341 0xb6a24 weights->dims->data[0]
      -4318 0xb6a3b op_context.input1 != nullptr
      -4289 0xb6a58 third_party/tensorflow/lite/kernels/mirror_pad.cc MirrorPad output size overflowed.
      -4205 0xb6aac padding_matrix->num_dims == static_cast<size_t>(input_dims)
      -4145 0xb6ae8 Mismatch: %f is quantized to %d with (%f, %d). abs(%f - %f) = %f > %f (tolerance) range percentage %f.
      -4041 0xb6b50 std: %f, mean: %f, max_diff: %f (scale: %f, zero_point: %d).
      -3979 0xb6b8e third_party/tensorflow/lite/kernels/pad.cc Pad paddings size overflowed.
      -3906 0xb6bd7 op_context.paddings->data.raw != nullptr || paddings_total == 0
      -3842 0xb6c17 third_party/tensorflow/lite/kernels/pad.cc INT64 padding overflow. Only support value between INT32_MIN and INT32_MAX.
      -3723 0xb6c8e third_party/tensorflow/lite/kernels/pad.cc Pad output dimension overflowed.
      -3647 0xb6cda scatter_nd index out of bounds
      -3616 0xb6cf9 data.dims->data[0]
      -3597 0xb6d0c decomposition_subgraph->outputs().size()
      -3556 0xb6d35 NumElements(index_tensor)
      -3530 0xb6d4f kNumOutputTensors
      -3512 0xb6d61 third_party/tensorflow/lite/kernels/stablehlo_reduce_window.cc The element size cannot be contained in an int64_t value.
      -3391 0xb6dda data->num_inserted_window_dims <= output->dims->size
      -3338 0xb6e0f size->type == kTfLiteInt32 || size->type == kTfLiteInt64
      -3281 0xb6e48 The sum of size_splits must be less than the dimension of value.
      -3216 0xb6e89 op_context.strides->type
      -3191 0xb6ea2 output type %d is not supported, requires float|uint8|int32 types.
      -3124 0xb6ee5 Cannot multiply %lld and %lld. Output shape dimensions must be in range [0, INT32_MAX].
      -3036 0xb6f3d SizeOfDimension(output, 0)
      -3009 0xb6f58 Type '%s' for input is not supported by rfft2d.
      -2961 0xb6f88 Unknown RNG algorithm: %d
      -2935 0xb6fa2 Spreadtrum
      -2924 0xb6fad WonderMedia
      -2912 0xb6fb9 ro.mediatek.platform
      -2891 0xb6fce third_party/tensorflow/lite/kernels/assign_variable.cc
      -2836 0xb7005 Quantization parameters has non-null scale but null zero_point.
      -2772 0xb7045 third_party/tensorflow/lite/util.cc
      -2736 0xb7069 hashtable need to be initialized before using
      -2690 0xb7097 ATrace_endSection
      -2672 0xb70a9 Unhandled fully-connected weights format.
      -2630 0xb70d3 Could not get 'stablehlo.case' operation parameters.
      -2577 0xb7108 RESOURCE_EXHAUSTED
      -2558 0xb711b DATA_LOSS
      -2548 0xb7125 lens.prime.EduEntityDetectorConfig
      -2513 0xb7148 lens.prime.EduEntityDetectorConfig.config_path
      -2466 0xb7177 google_ocr.TfliteModelPooledRunnerConfig.output_name
      -2413 0xb71ac acceleration.FallbackSettings
      -2383 0xb71ca third_party/protobuf/message_lite.cc
      -2346 0xb71ef  message of type "
      -2327 0xb7202 U_MULTIPLE_POST_CONTEXTS
      -2302 0xb721b U_PATTERN_SYNTAX_ERROR
      -2279 0xb7232 U_IDNA_DOMAIN_NAME_TOO_LONG_ERROR
      -2245 0xb7254 ServingCorpusSpecTest
      -2223 0xb726a ' have executed
      -2207 0xb727a next_free_key < kPerThreadSlots
      -2175 0xb729a ): string form of default value '
      -2141 0xb72bc warning
      -2133 0xb72c4 third_party/absl/status/statusor.cc
      -2097 0xb72e8 Check n <= size() failed: 
      -2066 0xb7307 detected illegal recursion into Mutex code
      -2023 0xb7332 UnlockSlow is confused
      -2000 0xb7349 enqueue_after->skip == nullptr || MuEquivalentWaiter(enqueue_after, s)
      -1929 0xb7390 pthread_sigmask failed: %d
      -1902 0xb73ab   runs: 
      -1893 0xb73b4  heap allocations: 
      -1873 0xb73c8 PReLU (ND)
      -1862 0xb73d3 Batch Matrix Multiply (NC, QDU8, F32, QC8W)
      -1818 0xb73ff Constant Pad (ND, X32)
      -1795 0xb7416 Convolution (NHWC, PF16)
      -1770 0xb742f Fully Connected (NC, QDU8, F16, QC8W)
      -1732 0xb7455 xnn_fingerprint_id_convolution2d_nhwc_f16_f16_f16_vmulcaddc_fp32_static_weights
      -1652 0xb74a5 xnn_fingerprint_id_convolution2d_nhwc_pf16_pf16_pf16_fp32_static_weights
      -1575 0xb74f2 left-square-bracket
      -1555 0xb7506 right-square-bracket
      -1534 0xb751b sizeof... 
      -1523 0xb7526 const_cast
      -1512 0xb7531 operator~
      -1502 0xb753b operator>>=
      -1490 0xb7547 unsigned __int128
      -1466 0xb755f unwind_phase2
      -1452 0xb756d malformed uleb128 expression
      -1423 0xb758a unsupported restore location for float register
      -1368 0xb75c1 Could not initialize the SensitivityClassificationEngineManager
      -1304 0xb7601 windows-1252
      -1291 0xb760e Failed to build auto regressor model from file.
      -1243 0xb763e interpreter_.ResizeAndAllocateTensorsWithFallback( absl::StrFormat("%d:%d:%d", input_height_, input_width_, input_depth_), [this](Interpreter* interpreter) -> absl::Status { RET_CHECK_EQ(interpreter_->ResizeInputTensor( interpreter_->inputs()[0], {1, input_height_, input_width_, input_depth_}), kTfLiteOk); RET_CHECK_EQ(interpreter_->AllocateTensors(), kTfLiteOk); return absl::OkStatus(); })
       -849 0xb77c8 locations_size * num_classes_ == output_scores_sizes_[i] * code_size_
       -779 0xb780e qr_detection_failed_with_angle
       -741 0xb7834 BEGIN:VCARD
       -725 0xb7844 No image was found in the cache for the polygon:
       -675 0xb7876 Expected PageLayout stream as the single input.
       -627 0xb78a6 InitializePageLayoutMutatorContextCalculator
       -582 0xb78d3 , total size 
       -568 0xb78e1 points->size() == 2u * static_cast<size_t>(clean_points.size())
       -504 0xb7921 GocrScriptDirectionIdentificationMutator
       -463 0xb794a typeset
       -455 0xb7952 research/ocr/api/internal/layout_analyzer/cluster_lines_step.cc
       -391 0xb7992 google_ocr::box_util::BoundingPolygonToBoundingBox( previous_word.polygon(), &box1) .ok()
       -301 0xb79ec Right word: 
       -288 0xb79f9 Small symbol breadth detected; performing symbol-level overlap removal.
       -216 0xb7a41 Complete Overlap
       -199 0xb7a52 RemoveOverlapsWordPruningStep
       -169 0xb7a70  entities of type 
       -150 0xb7a83 research/ocr/api/internal/layout_analyzer/split_lines_semantic_entities_step.cc
        -70 0xb7ad3 %s deadline %d ms exceeded: %d ms elapsed
        -28 0xb7afd LE,C
        -17 0xb7b08 Lj,C
         +0 0xb7b19 TensorFlowModelRunnerConfig=
        +29 0xb7b36 !BoundingBoxIsPolygon(src_box) && !BoundingBoxIsPolygon(*dst_box)
        +95 0xb7b78 SplitLinesGcnStep::AnalyzeInternal
       +130 0xb7b9b Failed to get interpreter pool.
       +162 0xb7bbb Loading from embedded model bytes.
       +201 0xb7be2 ComposeFst: Output symbol table of 1st argument 
       +250 0xb7c13 filter.Properties(fst::kOLabelSorted, true)
       +294 0xb7c3f NGramFst: Storage size calculation failed or overflowed
       +350 0xb7c77 not string
       +368 0xb7c89 \1\3
       +411 0xb7cb4 Prior has the wrong number of dimensions. Expected 1, but got %d
       +476 0xb7cf5 ./research/ocr/util/box_utils.h
       +508 0xb7d15 ocr/google_ocr/recognition/ctc_beam_ops.cc
       +551 0xb7d40 Total allocated bytes: 
       +575 0xb7d58 c->in_use() && (c->bin_num == kInvalidBinNum)
       +621 0xb7d86  allocated for chunks. 
       +645 0xb7d9e  end 
       +651 0xb7da4 upper
       +657 0xb7daa , next: 
       +666 0xb7db3 Available devices 
       +685 0xb7dc6 has_valid_fill_op: 
       +705 0xb7dda . The edge src node is name='
       +735 0xb7df8 ' (op='
       +746 0xb7e03 XLA_GPU
       +754 0xb7e0b  has input shape size 
       +777 0xb7e22  :: 
       +782 0xb7e27 No function registered to copy from devices of type 
       +835 0xb7e5c TF_SYNC_ON_FINISH
       +853 0xb7e6e Must run 'setup' before performing partial runs!
       +902 0xb7e9f  has already been fed.
       +925 0xb7eb6  step 
       +932 0xb7ebd ./third_party/tensorflow/compiler/xla/tsl/platform/logging.h
       +993 0xb7efa ReadVariableOp
      +1008 0xb7f09 ', which was created by a previous call to Create or Extend in this session.
      +1085 0xb7f56 Failed to find expected ScopedAllocator attr on 
      +1134 0xb7f87 copying input to output for device=
      +1170 0xb7fab Create multi device placer for inlined function body.
      +1224 0xb7fe1  (ret: 
      +1232 0xb7fe9     [control output] add control edge from: 
      +1277 0xb8016 TF_OVERRIDE_GLOBAL_THREADPOOL
      +1307 0xb8034 third_party/tensorflow/core/common_runtime/lower_functional_ops.cc
      +1374 0xb8077 Lowering While op requires a graph to be available.
      +1426 0xb80ab _dst
      +1431 0xb80b0 _partition_
      +1443 0xb80bc Skipping function/graph optimization passes when instantiating component function 
      +1526 0xb810f before_partition_passes
      +1550 0xb8127 third_party/tensorflow/core/common_runtime/parallel_concat_optimizer.cc
      +1622 0xb816f ProcessFunctionLibraryRuntime::InstantiateMultiDevice
      +1676 0xb81a5 cpu_pool
      +1685 0xb81ae No nodes with composiste device found.
      +1724 0xb81d5 Unexpected kMaxNumSubdivs 
      +1751 0xb81f0 Failed to dispatch ThenExecute in RingReducer
      +1797 0xb821e  in_table_ 
      +1809 0xb822a " of type "
      +1821 0xb8236 before_simplify_ici_dummy_variables_pass
      +1865 0xb8262 /device:CPU:
      +1878 0xb826f while inferring type of node '
      +1910 0xb828f   got:
      +1918 0xb8297 while querying input 
      +1942 0xb82af ' disabled by 
      +1957 0xb82be No CPU devices are available in this process
      +2002 0xb82eb number attr not found: 
      +2026 0xb8303 SetRetval 
      +2037 0xb830e   return 
      +2050 0xb831b ' is not available. You might need to include it in inputs or include its source node in the body
      +2148 0xb837d ' has constraint on attr '
      +2175 0xb8398  input_args
      +2187 0xb83a4 ', expected list
      +2204 0xb83b5 Value for number_attr() 
      +2229 0xb83ce ' of 
      +2235 0xb83d4  not equal to default of 0
      +2262 0xb83ef ; allows_uninitialized_input=true
      +2296 0xb8411 ; is_distributed_communication=true
      +2332 0xb8435 TF_DISABLE_JIT_KERNELS
      +2355 0xb844c  called allocate_output at index 
      +2389 0xb846e TF_RUN_HANDLER_SUB_THREAD_POOL_END_REQUEST_PERCENTAGE
      +2443 0xb84a4 Wrong number of inputs passed: 
      +2475 0xb84c4 DT_STRING
      +2485 0xb84ce DT_QINT32
      +2495 0xb84d8 DT_VARIANT
      +2506 0xb84e3 DT_INT64_REF
      +2519 0xb84f0 DT_QINT32_REF
      +2533 0xb84fe static_cast<size_t>(n->id()) < time_.size() && time_[n->id()] >= Microseconds(0)
      +2614 0xb854f  type_string: 
      +2629 0xb855e Did not find expected node '
      +2658 0xb857b Found unexpected node '
      +2682 0xb8593 ' is not expected '
      +2702 0xb85a7  gpu_compatible=
      +2719 0xb85b8 1 == NumElements()
      +2738 0xb85cb null buf_ with non-zero shape size 
      +2774 0xb85ef  elements from 
      +2790 0xb85ff Too many dimensions in tensor
      +2820 0xb861d Asking for tensor of 
      +2842 0xb8633 double
      +2849 0xb863a int8
      +2854 0xb863f unit < kUnits.end()
      +2877 0xb8656 TEST_TMPDIR
      +2889 0xb8662 We are not able to find a directory for temporary files.
      +2947 0xb869c  wl: 
      +2953 0xb86a2 Empty word.
      +2965 0xb86ae research/ocr/api/internal/layout_analyzer/step_utils.cc
      +3021 0xb86e6 ocr/google_ocr/engine/page_layout_mutators/direction_identification_utils.cc
      +3098 0xb8733 Key was not found.
      +3117 0xb8746 google_ocr.CTCDecoderRuntimeOptions.language_model_name
      +3173 0xb877e aksara.api_internal.PageLayoutAnalyzerSpec.CreateRegionBlocksStep
      +3239 0xb87c0 Invalid end math delimiter
      +3267 0xb87dc from input:
      +3279 0xb87e8 Replace: 
      +3289 0xb87f2 research/ocr/util/align_text_to_pieces.cc
      +3331 0xb881c google_ocr.GroupRpnTextDetectionMutatorConfig
      +3377 0xb884a ProcessPackedImagePyramid
      +3403 0xb8864 Creating cached interpreter pool: 
      +3438 0xb8887  pool size: 
      +3451 0xb8894 Input image and EntityDetector are not compatible. EntityDetector.input_image_channel_type:  $0, number of channels in input: $1
      +3580 0xb8915 Fallback model does not support center-aligned input image
      +3639 0xb8950 Head output shapes do not match! tf_output_vec[$0].dim_size(0) = $1, tf_output_vec[$2].dim_size(0) = $3
      +3743 0xb89b8 Head output shapes do not match! tf_output_vec[$0].dim_size(1) = $1, tf_output_vec[$2].dim_size(1) = $3
      +3847 0xb8a20 The size of `image_scales` (%d) is smaller than the size of `multi_level_merged_boxes` (%d).
      +3940 0xb8a7d  clusters.
      +3951 0xb8a88 fsync failed on 
      +3968 0xb8a99 Bad PRead arguments.  position: 
      +4001 0xb8aba tech.file.SymlinkData
      +4023 0xb8ad0 ' failed
      +4032 0xb8ad9 tech.file.LocalfileStatResult.xattr_values
      +4075 0xb8b04 FMT 
      +4080 0xb8b09 file/recordio/file.cc
      +4102 0xb8b1f Bad compression spec (unknown compressor): 
      +4146 0xb8b4b zippy encoder expects option '
      +4177 0xb8b6a net/proto/transpose.cc
      +4200 0xb8b81 databuffer_[hash_value] != nullptr
      +4235 0xb8ba4 DataBuffer_HasSingleBlock(*databuffer)
      +4274 0xb8bcb Strange sort_method encountered: 
      +4308 0xb8bed ERROR_INVALID_DESCRIPTOR
      +4333 0xb8c06 ' for metric: '
      +4349 0xb8c16  for label 
      +4361 0xb8c22 Monostate
      +4371 0xb8c2c util/time/capper.cc
      +4391 0xb8c40 Invalid Exemplar bucket number in DistributionProto: 
      +4445 0xb8c76 MobileSSDTfLiteClient
      +4467 0xb8c8c MobileSSDTfLiteClient: all of `external_files.anchor_file_*` and 'external_files.anchor_layers_file_*` are empty, the tflite model is assumed to contain postprocessing op.
      +4639 0xb8d38 labelmap_.item_size() > 0
      +4665 0xb8d52 ocr/google_ocr/eval/proto_converter.cc
      +4704 0xb8d79  defined in OcrSubgraph TemplateSubgraphOptions.
      +4753 0xb8daa SharedPoolExecutor requires num_threads argument.
      +4803 0xb8ddc bad parent_entity_id: 
      +4826 0xb8df3 moved.size() == descendants.size()
      +4861 0xb8e16  parents
      +4870 0xb8e1f HandleRequest unsupported
      +4896 0xb8e39 RegionDetectionEngine.detect
      +4925 0xb8e56 __stream_
      +4935 0xb8e60 mediapipe.tasks.components.processors.ImagePreprocessingGraph
      +4997 0xb8e9e options_.num_detection() > 0
      +5026 0xb8ebb Object detection models require TFLite Model Metadata but none was found
      +5099 0xb8f04 Using `class_name_whitelist` or `class_name_blacklist` requires labels to be present in the TFLite Model Metadata but none was found.
      +5233 0xb8f8a kOutPixelDetections(cc).IsConnected() || kOutPixelDetectionList(cc).IsConnected() || kOutPixelDetection(cc).IsConnected() || kOutRelativeDetections(cc).IsConnected() || kOutRelativeDetectionList(cc).IsConnected() || kOutRelativeDetection(cc).IsConnected()
      +5489 0xb908a Must connect at least one output stream.
      +5530 0xb90b3 Expected a model with 2 or 4 output tensors, found %d.
      +5585 0xb90ea FLOAT16
      +5593 0xb90f2 INT32
      +5599 0xb90f8 FLOAT8_E4M3FN
      +5613 0xb9106 input_tensors.size() == 4
      +5639 0xb9120 detection_scores_tensor->shape().dims[0] == 1
      +5685 0xb914e third_party/mediapipe/calculators/util/detection_label_id_to_text_calculator.cc
      +5765 0xb919e Expected non-empty score calibration file.
      +5808 0xb91c9 Could not parse score calibration parameter as float: %s.
      +5866 0xb9203 MovableSplitImageFrameVectorCalculator
      +5905 0xb922a drishti.SplitVectorCalculatorOptions
      +5942 0xb924f mediapipe.tasks.ScoreCalibrationCalculatorOptions.Sigmoid
      +6000 0xb9289 DENYLIST
      +6009 0xb9292 Failed to get image gradient, skipping entropy filtering: 
      +6068 0xb92cd desired_channel_bits = 
      +6092 0xb92e5 : DecodePNG error trapped.
      +6119 0xb9300 feature_id >= 0
      +6135 0xb9310 ./nlp/saft/components/common/mobile/fel/fel-parser.h
    
    ### TensorFlowModelRunnerConfig 0xe1a83 google_ocr.TensorFlowModelRunnerConfig
      -6059 0xe02d8 _src.getObj() != _dst.getObj()
      -6028 0xe02f7 bool cv::solve(InputArray, InputArray, OutputArray, int)
      -5971 0xe0330 %d@%llu
      -5963 0xe0338 OPENCV_LOG_TIMESTAMP
      -5942 0xe034d a_size.width == len
      -5922 0xe0361 download
      -5913 0xe036a _step
      -5907 0xe0370 new_rows > 0
      -5894 0xe037d total_sz
      -5885 0xe0386 m1.cols == m2.cols && m1.rows == m2.rows
      -5844 0xe03af OpenCV/MatExpr: processing of multi-channel arrays might be changed in the future: https://github.com/opencv/opencv/issues/16739
      -5715 0xe0430 MatExpr cv::Mat::t() const
      -5688 0xe044b third_party/OpenCV/public/modules/core/src/matrix_operations.cpp
      -5623 0xe048c getMat_
      -5615 0xe0494 !fixedSize() || ((cuda::GpuMat*)obj)->size() == Size(_cols, _rows)
      -5548 0xe04d7 (normType >> 1) >= 3 || func != 0
      -5514 0xe04f9 normType == NORM_INF || normType == NORM_L1 || normType == NORM_L2 || normType == NORM_L2SQR || ((normType == NORM_HAMMING || normType == NORM_HAMMING2) && src1.type() == CV_8U)
      -5336 0xe05ab int cv::cpu_baseline::normL1_(const void *, const uchar *, void *, int, int) [T = unsigned long, ST = double]
      -5226 0xe0619 int cv::cpu_baseline::normL1_(const void *, const uchar *, void *, int, int) [T = unsigned int, ST = double]
      -5117 0xe0686 Input image depth is not supported by function
      -5070 0xe06b5 OpenGL API call
      -5054 0xe06c5 POPCNT
      -5047 0xe06cc OPENCV_TRACE_LOCATION
      -5025 0xe06e2 UMat &cv::UMat::setTo(InputArray, InputArray)
      -4979 0xe0710 WARNING
      -4971 0xe0718 ocr/photo/utils/image_scale.cc
      -4940 0xe0737 Number of boxes = %d
      -4918 0xe074d Score for split distribution
      -4889 0xe076a Histogram
      -4879 0xe0774 profile '
      -4869 0xe077e Call to NULL read function
      -4842 0xe0799 bad header (invalid type)
      -4816 0xe07b3 extra compressed data
      -4794 0xe07c9 sPLT chunk has bad length
      -4768 0xe07e3 too many text chunks
      -4747 0xe07f8 Improper call to JPEG library in state %d
      -4705 0xe0822 Requested features are incompatible
      -4669 0xe0846 Unsupported JPEG process: SOF type 0x%02x
      -4627 0xe0870 Invalid JPEG file structure: SOS before SOF
      -4583 0xe089c JFIF extension marker: JPEG-compressed thumbnail image, length %u
      -4517 0xe08de Corrupt JPEG data: bad arithmetic code
      -4478 0xe0905 %ld%c
      -4472 0xe090b svebitperm
      -4461 0xe0916 CPU implementer
      -4445 0xe0926 CPU revision
      -4432 0xe0933 Error (generic)
      -4416 0xe0943 third_party/gloop/util/random/random_base.cc
      -4359 0xe097c NORWEGIAN_N
      -4347 0xe0988 KYRGYZ
      -4324 0xe099f LOZI
      -4311 0xe09ac token_suffix_symbolCharPropertyWrapper
      -4272 0xe09d3 ocr.photo.MutatorSettings
      -4246 0xe09ed -byte UTF-8 sequence 
      -4224 0xe0a03 asset manager not initialized
      -4194 0xe0a21 failed to read input stream
      -4166 0xe0a3d values->type
      -4153 0xe0a4a attention_logits->dims->size
      -4124 0xe0a67 Can't find 
      -4112 0xe0a73 bytemap range 
      -4094 0xe0a85 [:ascii:]
      -4084 0xe0a8f should never happen
      -4064 0xe0aa3 invalid repetition size
      -4033 0xe0ac2 Common
      -4022 0xe0acd Nyiakeng_Puachue_Hmong
      -3999 0xe0ae4 SignWriting
      -3987 0xe0af0 Tifinagh
      -3975 0xe0afc %s tensor %d is missing TensorMetadata.
      -3935 0xe0b24 third_party/tensorflow_lite_support/metadata/cc/metadata_extractor.cc
      -3865 0xe0b6a invalid block type

## ARM64 string xrefs

    ### TensorFlowModelRunnerConfig= target 0xb7b19 xref 0x52345c adrp+add {'name': 'Java_com_google_android_libraries_lens_ondevice_nativeapi_LodeSplitRegistry_initializePlayMlPackSplitHandler', 'start': 4572256, 'delta': 815100, 'outside_size': True}
    0x52341c:	add	x9, x9, #0x50
    0x523420:	cmp	x10, #0
    0x523424:	csel	x0, x9, x10, eq
    0x523428:	ldr	w9, [x0, #0x1c]
    0x52342c:	cmp	w9, #3
    0x523430:	b.ne	#0x523450
    0x523434:	adrp	x8, #0x12ae000
    0x523438:	add	x8, x8, #0x3a0
    0x52343c:	ldr	w9, [x0, #0x1c]
    0x523440:	cmp	w9, #3
    0x523444:	b.ne	#0x5234a0
    0x523448:	ldr	x8, [x0, #0x10]
    0x52344c:	b	#0x5234a4
    0x523450:	add	x8, sp, #8
    0x523454:	bl	#0x1029600
    0x523458:	adrp	x2, #0xb7000
    0x52345c:	add	x2, x2, #0xb19
    0x523460:	add	x0, sp, #8
    0x523464:	mov	x1, xzr
    0x523468:	mov	w3, #0x1c
    0x52346c:	bl	#0x11b3588
    0x523470:	ldr	q0, [x0]
    0x523474:	ldr	x8, [x0, #0x10]
    0x523478:	str	q0, [x19]
    0x52347c:	str	x8, [x19, #0x10]
    0x523480:	stp	xzr, xzr, [x0, #8]
    0x523484:	str	xzr, [x0]
    0x523488:	add	x0, sp, #8
    0x52348c:	bl	#0x11b3440
    0x523490:	ldp	x30, x19, [sp, #0x20]
    0x523494:	add	sp, sp, #0x30
    0x523498:	autiasp	
    0x52349c:	ret	
    0x5234a0:	add	x8, x8, #0x50
    0x5234a4:	ldr	x8, [x8, #0x38]
    0x5234a8:	adrp	x0, #0x14b000
    0x5234ac:	add	x0, x0, #0xcc
    0x5234b0:	and	x1, x8, #0xfffffffffffffffc
    
    ### Failed to modify graph with XNNPack delegate. target 0x7ed47 xref 0x534cf8 adrp+add {'name': 'Java_com_google_android_libraries_lens_ondevice_nativeapi_LodeSplitRegistry_initializePlayMlPackSplitHandler', 'start': 4572256, 'delta': 886936, 'outside_size': True}
    0x534cb8:	bl	#0x1065f84
    0x534cbc:	adrp	x1, #0x75000
    0x534cc0:	add	x1, x1, #0xd21
    0x534cc4:	add	x0, sp, #0x20
    0x534cc8:	mov	w2, #0x2d
    0x534ccc:	bl	#0x1065af0
    0x534cd0:	add	x0, sp, #0x20
    0x534cd4:	bl	#0x1066394
    0x534cd8:	add	x0, sp, #0x20
    0x534cdc:	b	#0x534d14
    0x534ce0:	bl	#0x5358bc
    0x534ce4:	mov	x0, sp
    0x534ce8:	mov	w2, #0x32d
    0x534cec:	mov	x3, xzr
    0x534cf0:	bl	#0x1065f84
    0x534cf4:	adrp	x1, #0x7e000
    0x534cf8:	add	x1, x1, #0xd47
    0x534cfc:	mov	x0, sp
    0x534d00:	mov	w2, #0x2d
    0x534d04:	bl	#0x1065af0
    0x534d08:	mov	x0, sp
    0x534d0c:	bl	#0x1066394
    0x534d10:	mov	x0, sp
    0x534d14:	bl	#0x1065f90
    0x534d18:	str	xzr, [x19]
    0x534d1c:	ldr	x19, [sp, #0xe0]
    0x534d20:	str	xzr, [sp, #0xe0]
    0x534d24:	cbz	x19, #0x534c88
    0x534d28:	mov	x0, x19
    0x534d2c:	bl	#0xfa8c48
    0x534d30:	mov	x0, x19
    0x534d34:	mov	w1, #0x1d0
    0x534d38:	bl	#0x11db070
    0x534d3c:	b	#0x534c88
    0x534d40:	bl	#0x5358bc
    0x534d44:	add	x0, sp, #0x20
    0x534d48:	mov	w2, #0x31c
    0x534d4c:	mov	x3, xzr
    
    ### ocr/google_ocr/detection/group_rpn_detector_v2.cc target 0x988e4 xref 0x72b834 adrp+add {'name': 'Java_com_google_android_libraries_lens_ondevice_nativeapi_LodeSplitRegistry_initializePlayMlPackSplitHandler', 'start': 4572256, 'delta': 2946004, 'outside_size': True}
    0x72b7f4:	add	x8, x8, #0x50
    0x72b7f8:	cmp	x9, #0
    0x72b7fc:	mov	x29, x2
    0x72b800:	mov	x20, x0
    0x72b804:	csel	x23, x8, x9, eq
    0x72b808:	bl	#0x4ae278
    0x72b80c:	mov	w19, w0
    0x72b810:	mov	x0, x20
    0x72b814:	mov	w1, wzr
    0x72b818:	bl	#0x4ae278
    0x72b81c:	cmp	w0, #0
    0x72b820:	ccmp	w19, #0, #4, gt
    0x72b824:	b.gt	#0x72b850
    0x72b828:	adrp	x1, #0x123000
    0x72b82c:	add	x1, x1, #0x489
    0x72b830:	adrp	x4, #0x98000
    0x72b834:	add	x4, x4, #0x8e4
    0x72b838:	mov	w0, #0xd
    0x72b83c:	mov	w2, #0x14
    0x72b840:	mov	w3, #0x42b
    0x72b844:	bl	#0x105e410
    0x72b848:	str	x0, [x24]
    0x72b84c:	b	#0x72cfb8
    0x72b850:	cmp	w19, w0
    0x72b854:	fmov	s8, #1.00000000
    0x72b858:	str	x20, [sp, #0x58]
    0x72b85c:	csel	w8, w19, w0, lo
    0x72b860:	csel	w9, w19, w0, hi
    0x72b864:	ldr	x20, [sp, #0x590]
    0x72b868:	ucvtf	s0, w8
    0x72b86c:	ucvtf	s1, w9
    0x72b870:	mov	x8, x23
    0x72b874:	ldrb	w9, [x8, #0x18]!
    0x72b878:	ldr	x10, [x8, #8]
    0x72b87c:	ldr	w11, [x8, #4]
    0x72b880:	mov	w21, w0
    0x72b884:	tst	w9, #1
    0x72b888:	fdiv	s0, s0, s1
    
    ### ocr/google_ocr/detection/group_rpn_detector_v2.cc target 0x988e4 xref 0x72bb38 adrp+add {'name': 'Java_com_google_android_libraries_lens_ondevice_nativeapi_LodeSplitRegistry_initializePlayMlPackSplitHandler', 'start': 4572256, 'delta': 2946776, 'outside_size': True}
    0x72baf8:	mov	x1, xzr
    0x72bafc:	bl	#0x736018
    0x72bb00:	add	x0, sp, #0x100
    0x72bb04:	bl	#0x4b2568
    0x72bb08:	add	x0, sp, #0x170
    0x72bb0c:	bl	#0x4ad7d8
    0x72bb10:	cmp	x19, #1
    0x72bb14:	b.ne	#0x72c534
    0x72bb18:	add	x0, sp, #0x1f0
    0x72bb1c:	bl	#0x4b2568
    0x72bb20:	add	x0, sp, #0x2a0
    0x72bb24:	bl	#0x4ad7d8
    0x72bb28:	b	#0x72bc14
    0x72bb2c:	adrp	x1, #0x13b000
    0x72bb30:	add	x1, x1, #0xf99
    0x72bb34:	adrp	x4, #0x98000
    0x72bb38:	add	x4, x4, #0x8e4
    0x72bb3c:	mov	w0, #0xd
    0x72bb40:	mov	w2, #0x15
    0x72bb44:	mov	w3, #0x457
    0x72bb48:	bl	#0x105e410
    0x72bb4c:	str	x0, [x24]
    0x72bb50:	b	#0x72cfa8
    0x72bb54:	ldr	s3, [x27, #0x1c]
    0x72bb58:	ldur	d4, [x8, #-8]
    0x72bb5c:	mov	v1.s[1], v2.s[0]
    0x72bb60:	ldr	x0, [sp, #0x58]
    0x72bb64:	add	x8, sp, #0x2a0
    0x72bb68:	mov	w1, #3
    0x72bb6c:	scvtf	s3, s3
    0x72bb70:	add	x21, sp, #0x2a0
    0x72bb74:	fdiv	s3, s3, s2
    0x72bb78:	scvtf	v2.2s, v4.2s
    0x72bb7c:	fdiv	v1.2s, v2.2s, v1.2s
    0x72bb80:	fmov	s2, #1.00000000
    0x72bb84:	fcmp	s3, s0
    0x72bb88:	fcsel	s0, s3, s0, mi
    0x72bb8c:	fcmp	s0, s2
    
    ### ocr/google_ocr/detection/group_rpn_detector_v2.cc target 0x988e4 xref 0x72bc98 adrp+add {'name': 'Java_com_google_android_libraries_lens_ondevice_nativeapi_LodeSplitRegistry_initializePlayMlPackSplitHandler', 'start': 4572256, 'delta': 2947128, 'outside_size': True}
    0x72bc58:	ldr	x8, [sp, #0xe8]
    0x72bc5c:	mov	w1, wzr
    0x72bc60:	mov	v0.s[1], w19
    0x72bc64:	ldr	x8, [x8]
    0x72bc68:	mov	w19, w0
    0x72bc6c:	mov	x0, x8
    0x72bc70:	scvtf	v8.2s, v0.2s
    0x72bc74:	bl	#0x4ae278
    0x72bc78:	fmov	s0, w0
    0x72bc7c:	fmov	s9, #0.50000000
    0x72bc80:	adrp	x8, #0x15e000
    0x72bc84:	fmov	s11, #-1.00000000
    0x72bc88:	ldr	s12, [x8, #0x4c0]
    0x72bc8c:	add	x27, sp, #0x2a0
    0x72bc90:	mov	w28, #0x37
    0x72bc94:	adrp	x25, #0x98000
    0x72bc98:	add	x25, x25, #0x8e4
    0x72bc9c:	mov	v0.s[1], w19
    0x72bca0:	scvtf	v0.2s, v0.2s
    0x72bca4:	fdiv	v0.2s, v8.2s, v0.2s
    0x72bca8:	mov	s1, v0.s[1]
    0x72bcac:	fcmp	s0, s1
    0x72bcb0:	fcsel	s10, s0, s1, mi
    0x72bcb4:	ldr	w8, [x22, #0x1c]
    0x72bcb8:	cmp	w23, w8
    0x72bcbc:	b.hs	#0x72bdc8
    0x72bcc0:	cmp	w23, #1
    0x72bcc4:	fcsel	s8, s10, s9, eq
    0x72bcc8:	fadd	s0, s8, s11
    0x72bccc:	fabs	s0, s0
    0x72bcd0:	fcmp	s0, s12
    0x72bcd4:	b.pl	#0x72bd0c
    0x72bcd8:	ldr	x0, [sp, #0xf0]
    0x72bcdc:	mov	x1, xzr
    0x72bce0:	ldr	x8, [x0, #-8]!
    0x72bce4:	str	xzr, [x0]
    0x72bce8:	str	x8, [sp, #0x2a0]
    0x72bcec:	bl	#0x736018
    
    ### ocr/google_ocr/detection/group_rpn_detector_v2.cc target 0x988e4 xref 0x72c520 adrp+add {'name': 'Java_com_google_android_libraries_lens_ondevice_nativeapi_LodeSplitRegistry_initializePlayMlPackSplitHandler', 'start': 4572256, 'delta': 2949312, 'outside_size': True}
    0x72c4e0:	ldr	x22, [sp, #0x60]
    0x72c4e4:	add	x0, sp, #0x4d0
    0x72c4e8:	mov	x1, xzr
    0x72c4ec:	bl	#0x736018
    0x72c4f0:	add	x0, sp, #0x170
    0x72c4f4:	bl	#0x4b2568
    0x72c4f8:	add	x0, sp, #0x2a0
    0x72c4fc:	bl	#0x4ad7d8
    0x72c500:	cmp	x29, #1
    0x72c504:	mov	x29, x23
    0x72c508:	b.eq	#0x72c044
    0x72c50c:	b	#0x72cec8
    0x72c510:	mov	w8, #0x37
    0x72c514:	mov	x0, x29
    0x72c518:	mov	w1, #0x506
    0x72c51c:	adrp	x2, #0x98000
    0x72c520:	add	x2, x2, #0x8e4
    0x72c524:	str	x8, [sp, #0x2a0]
    0x72c528:	bl	#0x105e5d0
    0x72c52c:	str	x0, [x24]
    0x72c530:	b	#0x72c4f8
    0x72c534:	add	x0, sp, #0x1f0
    0x72c538:	bl	#0x4b2568
    0x72c53c:	add	x0, sp, #0x2a0
    0x72c540:	bl	#0x4ad7d8
    0x72c544:	b	#0x72cf9c
    0x72c548:	ldp	x9, x10, [sp, #0xa0]
    0x72c54c:	mov	w11, #0xf0
    0x72c550:	mov	w12, #0x70
    0x72c554:	ldr	x14, [sp, #0xd8]
    0x72c558:	add	x0, sp, #0x2a0
    0x72c55c:	mov	x1, xzr
    0x72c560:	sub	x10, x10, x9
    0x72c564:	sub	x14, x14, x8
    0x72c568:	str	x9, [sp, #0x490]
    0x72c56c:	sdiv	x19, x10, x11
    0x72c570:	ldr	x11, [sp, #0x50]
    0x72c574:	ldp	x10, x11, [x11]
    
    ### ocr/google_ocr/detection/group_rpn_detector_v2.cc target 0x988e4 xref 0x72cd54 adrp+add {'name': 'Java_com_google_android_libraries_lens_ondevice_nativeapi_LodeSplitRegistry_initializePlayMlPackSplitHandler', 'start': 4572256, 'delta': 2951412, 'outside_size': True}
    0x72cd14:	mov	x0, x19
    0x72cd18:	mov	x1, x24
    0x72cd1c:	bl	#0xff1844
    0x72cd20:	mov	w27, #1
    0x72cd24:	b	#0x72cd6c
    0x72cd28:	mov	w0, #0xd
    0x72cd2c:	adrp	x1, #0x6e000
    0x72cd30:	add	x1, x1, #0xd9e
    0x72cd34:	mov	w2, #0x12
    0x72cd38:	mov	w3, #0x96e
    0x72cd3c:	adrp	x4, #0x97000
    0x72cd40:	add	x4, x4, #0x552
    0x72cd44:	bl	#0x105e410
    0x72cd48:	mov	w8, #0x37
    0x72cd4c:	mov	w1, #0x55f
    0x72cd50:	adrp	x2, #0x98000
    0x72cd54:	add	x2, x2, #0x8e4
    0x72cd58:	str	x8, [sp, #0x2a0]
    0x72cd5c:	bl	#0x105e5d0
    0x72cd60:	ldr	x8, [sp, #0x40]
    0x72cd64:	mov	w27, wzr
    0x72cd68:	str	x0, [x8]
    0x72cd6c:	ldr	x19, [sp, #0x2a0]
    0x72cd70:	tbnz	w19, #0, #0x72cd7c
    0x72cd74:	mov	x0, x19
    0x72cd78:	bl	#0x105cc60
    0x72cd7c:	cmp	x19, #1
    0x72cd80:	b.ne	#0x72cd94
    0x72cd84:	ldr	w8, [sp, #0x2a8]
    0x72cd88:	tbz	w8, #0, #0x72cd94
    0x72cd8c:	mov	x0, x24
    0x72cd90:	bl	#0x464df0
    0x72cd94:	ldr	x0, [sp, #0x70]
    0x72cd98:	cbz	x0, #0x72cdac
    0x72cd9c:	ldr	x8, [sp, #0x80]
    0x72cda0:	str	x0, [sp, #0x78]
    0x72cda4:	sub	x1, x8, x0
    0x72cda8:	bl	#0x11db070
    
    ### ocr/google_ocr/detection/group_rpn_detector_v2.cc target 0x988e4 xref 0x72ce48 adrp+add {'name': 'Java_com_google_android_libraries_lens_ondevice_nativeapi_LodeSplitRegistry_initializePlayMlPackSplitHandler', 'start': 4572256, 'delta': 2951656, 'outside_size': True}
    0x72ce08:	ldr	x19, [sp, #0x40]
    0x72ce0c:	ldrb	w8, [sp, #0x4b0]
    0x72ce10:	mov	x0, x19
    0x72ce14:	strb	wzr, [x0, #8]!
    0x72ce18:	strb	wzr, [x0, #0x10]
    0x72ce1c:	cbz	w8, #0x72ce30
    0x72ce20:	add	x1, sp, #0x4a0
    0x72ce24:	bl	#0x4ada08
    0x72ce28:	mov	w8, #1
    0x72ce2c:	strb	w8, [x19, #0x18]
    0x72ce30:	mov	w8, #1
    0x72ce34:	str	x8, [x19]
    0x72ce38:	b	#0x72ce78
    0x72ce3c:	mov	w8, #0x53f
    0x72ce40:	str	x8, [sp, #0x2a0]
    0x72ce44:	adrp	x8, #0x98000
    0x72ce48:	add	x8, x8, #0x8e4
    0x72ce4c:	str	x8, [sp, #0x2a8]
    0x72ce50:	bl	#0xdd35a8
    0x72ce54:	str	x0, [sp, #0x2b0]
    0x72ce58:	add	x0, sp, #0x2a0
    0x72ce5c:	bl	#0x464758
    0x72ce60:	ldr	x8, [sp, #0x40]
    0x72ce64:	cmp	x0, #1
    0x72ce68:	str	x0, [x8]
    0x72ce6c:	b.eq	#0x72d1c0
    0x72ce70:	add	x0, sp, #0x2a0
    0x72ce74:	bl	#0x460e74
    0x72ce78:	ldrb	w8, [sp, #0x490]
    0x72ce7c:	tst	w8, #0x3f
    0x72ce80:	b.eq	#0x72ce9c
    0x72ce84:	adrp	x1, #0x12cb000
    0x72ce88:	adrp	x2, #0x12cb000
    0x72ce8c:	add	x0, sp, #0x490
    0x72ce90:	ldr	x1, [x1, #0xfe0]
    0x72ce94:	ldr	x2, [x2, #0x9d0]
    0x72ce98:	bl	#0x105a5a4
    0x72ce9c:	ldrb	w8, [sp, #0x4b0]
    
    ### ocr/google_ocr/detection/group_rpn_detector_v2.cc target 0x988e4 xref 0x72cff0 adrp+add {'name': 'Java_com_google_android_libraries_lens_ondevice_nativeapi_LodeSplitRegistry_initializePlayMlPackSplitHandler', 'start': 4572256, 'delta': 2952080, 'outside_size': True}
    0x72cfb0:	str	x8, [sp, #0x2a0]
    0x72cfb4:	bl	#0x735f34
    0x72cfb8:	add	sp, sp, #0x500
    0x72cfbc:	bl	#0x7362c0
    0x72cfc0:	ldp	x28, x27, [sp, #0x40]
    0x72cfc4:	ldp	x29, x30, [sp, #0x30]
    0x72cfc8:	ldp	d9, d8, [sp, #0x20]
    0x72cfcc:	ldp	d11, d10, [sp, #0x10]
    0x72cfd0:	ldr	d12, [sp], #0x90
    0x72cfd4:	autiasp	
    0x72cfd8:	ret	
    0x72cfdc:	adrp	x0, #0x12d9000
    0x72cfe0:	add	x0, x0, #0xc58
    0x72cfe4:	bl	#0x106d7e0
    0x72cfe8:	tbz	w0, #0, #0x72b8c8
    0x72cfec:	adrp	x1, #0x98000
    0x72cff0:	add	x1, x1, #0x8e4
    0x72cff4:	add	x0, sp, #0x2a0
    0x72cff8:	mov	w2, #0x443
    0x72cffc:	mov	x3, xzr
    0x72d000:	bl	#0x1065f6c
    0x72d004:	ldr	x8, [sp, #0x2a8]
    0x72d008:	mov	w9, #1
    0x72d00c:	adrp	x1, #0x88000
    0x72d010:	add	x1, x1, #0x922
    0x72d014:	add	x0, sp, #0x2a0
    0x72d018:	mov	w2, #0x17
    0x72d01c:	str	w9, [x8, #0x2c]
    0x72d020:	bl	#0x1065af0
    0x72d024:	add	x0, sp, #0x2a0
    0x72d028:	add	x1, sp, #0x170
    0x72d02c:	str	s8, [sp, #0x170]
    0x72d030:	bl	#0x1065a00
    0x72d034:	bl	#0x1066394
    0x72d038:	add	x0, sp, #0x2a0
    0x72d03c:	bl	#0x1065f90
    0x72d040:	b	#0x72b8c8
    0x72d044:	bl	#0x7362e8
    
    ### ocr/google_ocr/detection/group_rpn_detector_v2.cc target 0x988e4 xref 0x72d08c adrp+add {'name': 'Java_com_google_android_libraries_lens_ondevice_nativeapi_LodeSplitRegistry_initializePlayMlPackSplitHandler', 'start': 4572256, 'delta': 2952236, 'outside_size': True}
    0x72d04c:	str	x8, [sp, #0x2a0]
    0x72d050:	bl	#0x105e5d0
    0x72d054:	str	x0, [x24]
    0x72d058:	b	#0x72c53c
    0x72d05c:	bl	#0x7362e8
    0x72d060:	mov	x0, x19
    0x72d064:	mov	w1, #0x46d
    0x72d068:	str	x8, [sp, #0x2a0]
    0x72d06c:	bl	#0x105e5d0
    0x72d070:	str	x0, [x24]
    0x72d074:	b	#0x72bc04
    0x72d078:	adrp	x0, #0x12d9000
    0x72d07c:	add	x0, x0, #0xc70
    0x72d080:	bl	#0x106d7e0
    0x72d084:	tbz	w0, #0, #0x72ba68
    0x72d088:	adrp	x1, #0x98000
    0x72d08c:	add	x1, x1, #0x8e4
    0x72d090:	add	x0, sp, #0x170
    0x72d094:	mov	w2, #0x47d
    0x72d098:	mov	x3, xzr
    0x72d09c:	bl	#0x1065f6c
    0x72d0a0:	ldr	x8, [sp, #0x178]
    0x72d0a4:	mov	w9, #1
    0x72d0a8:	adrp	x1, #0xda000
    0x72d0ac:	add	x1, x1, #0xa4c
    0x72d0b0:	add	x0, sp, #0x170
    0x72d0b4:	mov	w2, #0x11
    0x72d0b8:	str	w9, [x8, #0x2c]
    0x72d0bc:	bl	#0x1065af0
    0x72d0c0:	ldr	x28, [sp, #0x268]
    0x72d0c4:	mov	w1, #1
    0x72d0c8:	mov	x0, x28
    0x72d0cc:	bl	#0x4ae278
    0x72d0d0:	str	w0, [sp, #0x100]
    0x72d0d4:	add	x0, sp, #0x170
    0x72d0d8:	add	x1, sp, #0x100
    0x72d0dc:	bl	#0x1065888
    0x72d0e0:	adrp	x25, #0x5d000
    
    ### ocr/google_ocr/detection/group_rpn_detector_v2.cc target 0x988e4 xref 0x72d72c adrp+add {'name': 'Java_com_google_android_libraries_lens_ondevice_nativeapi_LodeSplitRegistry_initializePlayMlPackSplitHandler', 'start': 4572256, 'delta': 2953932, 'outside_size': True}
    0x72d6ec:	add	x8, sp, #0x670
    0x72d6f0:	bl	#0x72ad74
    0x72d6f4:	ldr	q0, [sp, #0x670]
    0x72d6f8:	ldr	q1, [sp, #0x680]
    0x72d6fc:	add	x0, sp, #0x580
    0x72d700:	ldr	x8, [sp, #0x690]
    0x72d704:	add	x1, sp, #0x120
    0x72d708:	str	wzr, [sp, #0x488]
    0x72d70c:	bl	#0x736460
    0x72d710:	bl	#0x72b650
    0x72d714:	add	x28, x28, #1
    0x72d718:	b	#0x72d51c
    0x72d71c:	mov	w8, #0x37
    0x72d720:	mov	x0, x29
    0x72d724:	mov	w1, #0x2dd
    0x72d728:	adrp	x2, #0x98000
    0x72d72c:	add	x2, x2, #0x8e4
    0x72d730:	str	x8, [sp, #0x460]
    0x72d734:	bl	#0x105e5d0
    0x72d738:	str	x0, [sp, #0x48]
    0x72d73c:	b	#0x72d610
    0x72d740:	ldp	x0, x10, [sp, #0x40]
    0x72d744:	add	x1, sp, #0x2e8
    0x72d748:	ldr	x9, [sp, #0x28]
    0x72d74c:	ldr	x2, [sp, #0x38]
    0x72d750:	add	x3, sp, #0x460
    0x72d754:	strb	wzr, [sp, #0x460]
    0x72d758:	ldr	x8, [x0]
    0x72d75c:	str	x10, [x9]
    0x72d760:	strb	wzr, [sp, #0x470]
    0x72d764:	ldr	x9, [x8, #0x28]
    0x72d768:	add	x8, sp, #0x2c8
    0x72d76c:	blr	x9
    0x72d770:	ldr	x0, [sp, #0x2c8]
    0x72d774:	cmp	x0, #1
    0x72d778:	b.ne	#0x72fe3c
    0x72d77c:	add	x8, sp, #0x1f0
    0x72d780:	fmov	s8, #1.00000000
    
    ### ocr/google_ocr/detection/group_rpn_detector_v2.cc target 0x988e4 xref 0x72e6a4 adrp+add {'name': 'Java_com_google_android_libraries_lens_ondevice_nativeapi_LodeSplitRegistry_initializePlayMlPackSplitHandler', 'start': 4572256, 'delta': 2957892, 'outside_size': True}
    0x72e664:	add	x8, sp, #0x670
    0x72e668:	add	x0, x8, #0x18
    0x72e66c:	bl	#0x731ccc
    0x72e670:	mov	w19, #1
    0x72e674:	b	#0x72e6b8
    0x72e678:	mov	w0, #0xd
    0x72e67c:	adrp	x1, #0x6e000
    0x72e680:	add	x1, x1, #0xd9e
    0x72e684:	mov	w2, #0x12
    0x72e688:	mov	w3, #0x96e
    0x72e68c:	adrp	x4, #0x97000
    0x72e690:	add	x4, x4, #0x552
    0x72e694:	bl	#0x105e410
    0x72e698:	mov	w8, #0x37
    0x72e69c:	mov	w1, #0x290
    0x72e6a0:	adrp	x2, #0x98000
    0x72e6a4:	add	x2, x2, #0x8e4
    0x72e6a8:	str	x8, [sp, #0x120]
    0x72e6ac:	bl	#0x105e5d0
    0x72e6b0:	str	x0, [sp, #0x50]
    0x72e6b4:	mov	w19, wzr
    0x72e6b8:	ldr	x0, [sp, #0x120]
    0x72e6bc:	tbnz	w0, #0, #0x72e6c4
    0x72e6c0:	bl	#0x105cc60
    0x72e6c4:	ldr	x0, [sp, #0x370]
    0x72e6c8:	cbz	x0, #0x72e6dc
    0x72e6cc:	ldr	x8, [sp, #0x380]
    0x72e6d0:	str	x0, [sp, #0x378]
    0x72e6d4:	sub	x1, x8, x0
    0x72e6d8:	bl	#0x11db070
    0x72e6dc:	add	x0, sp, #0x460
    0x72e6e0:	bl	#0x731924
    0x72e6e4:	add	x28, x28, #0x30
    0x72e6e8:	tbnz	w19, #0, #0x72e438
    0x72e6ec:	mov	w8, #0x2bd
    0x72e6f0:	ldr	x0, [sp, #0x50]
    0x72e6f4:	str	x8, [sp, #0x460]
    0x72e6f8:	adrp	x8, #0x98000
    
    ### ocr/google_ocr/detection/group_rpn_detector_v2.cc target 0x988e4 xref 0x72e6fc adrp+add {'name': 'Java_com_google_android_libraries_lens_ondevice_nativeapi_LodeSplitRegistry_initializePlayMlPackSplitHandler', 'start': 4572256, 'delta': 2957980, 'outside_size': True}
    0x72e6bc:	tbnz	w0, #0, #0x72e6c4
    0x72e6c0:	bl	#0x105cc60
    0x72e6c4:	ldr	x0, [sp, #0x370]
    0x72e6c8:	cbz	x0, #0x72e6dc
    0x72e6cc:	ldr	x8, [sp, #0x380]
    0x72e6d0:	str	x0, [sp, #0x378]
    0x72e6d4:	sub	x1, x8, x0
    0x72e6d8:	bl	#0x11db070
    0x72e6dc:	add	x0, sp, #0x460
    0x72e6e0:	bl	#0x731924
    0x72e6e4:	add	x28, x28, #0x30
    0x72e6e8:	tbnz	w19, #0, #0x72e438
    0x72e6ec:	mov	w8, #0x2bd
    0x72e6f0:	ldr	x0, [sp, #0x50]
    0x72e6f4:	str	x8, [sp, #0x460]
    0x72e6f8:	adrp	x8, #0x98000
    0x72e6fc:	add	x8, x8, #0x8e4
    0x72e700:	str	x8, [sp, #0x468]
    0x72e704:	bl	#0xdd35a8
    0x72e708:	str	x0, [sp, #0x470]
    0x72e70c:	add	x0, sp, #0x460
    0x72e710:	bl	#0x464758
    0x72e714:	ldr	x19, [sp, #0x28]
    0x72e718:	cmp	x0, #1
    0x72e71c:	str	x0, [sp, #0x120]
    0x72e720:	b.eq	#0x72fee0
    0x72e724:	add	x0, sp, #0x460
    0x72e728:	bl	#0x460e74
    0x72e72c:	ldr	x20, [sp, #0x58]
    0x72e730:	add	x24, sp, #0xb0
    0x72e734:	b	#0x72e7bc
    0x72e738:	ldr	q0, [sp, #0x670]
    0x72e73c:	add	x24, sp, #0xb0
    0x72e740:	add	x11, sp, #0x670
    0x72e744:	ldr	x8, [sp, #0x698]
    0x72e748:	ldr	x9, [sp, #0x6a0]
    0x72e74c:	ldur	q1, [x11, #0x48]
    0x72e750:	stur	q0, [x24, #0x78]
    
    ### ocr/google_ocr/detection/group_rpn_detector_v2.cc target 0x988e4 xref 0x72f830 adrp+add {'name': 'Java_com_google_android_libraries_lens_ondevice_nativeapi_LodeSplitRegistry_initializePlayMlPackSplitHandler', 'start': 4572256, 'delta': 2962384, 'outside_size': True}
    0x72f7f0:	mov	x0, x19
    0x72f7f4:	sub	x1, x8, x19
    0x72f7f8:	bl	#0x11db070
    0x72f7fc:	ldrb	w8, [sp, #0x408]
    0x72f800:	tst	w8, #0x3e
    0x72f804:	b.eq	#0x72f85c
    0x72f808:	adrp	x1, #0x12cb000
    0x72f80c:	adrp	x2, #0x12cb000
    0x72f810:	add	x0, sp, #0x408
    0x72f814:	ldr	x1, [x1, #0xb38]
    0x72f818:	ldr	x2, [x2, #0xb40]
    0x72f81c:	bl	#0x105a530
    0x72f820:	b	#0x72f85c
    0x72f824:	mov	w8, #0x15f
    0x72f828:	str	x8, [sp, #0x580]
    0x72f82c:	adrp	x8, #0x98000
    0x72f830:	add	x8, x8, #0x8e4
    0x72f834:	str	x8, [sp, #0x588]
    0x72f838:	bl	#0xdd35a8
    0x72f83c:	str	x0, [sp, #0x590]
    0x72f840:	add	x0, sp, #0x580
    0x72f844:	bl	#0x464758
    0x72f848:	cmp	x0, #1
    0x72f84c:	str	x0, [sp, #0x460]
    0x72f850:	b.eq	#0x72feec
    0x72f854:	add	x0, sp, #0x580
    0x72f858:	bl	#0x460e74
    0x72f85c:	ldr	x0, [sp, #0x418]
    0x72f860:	cbz	x0, #0x72f874
    0x72f864:	ldr	x8, [sp, #0x428]
    0x72f868:	str	x0, [sp, #0x420]
    0x72f86c:	sub	x1, x8, x0
    0x72f870:	bl	#0x11db070
    0x72f874:	add	x0, sp, #0x430
    0x72f878:	bl	#0x732b08
    0x72f87c:	add	x0, sp, #0x440
    0x72f880:	bl	#0x72b3a0
    0x72f884:	ldr	x0, [sp, #0x460]
    
    ### ocr/google_ocr/detection/group_rpn_detector_v2.cc target 0x988e4 xref 0x7362f0 adrp+add {'name': 'Java_com_google_android_libraries_lens_ondevice_nativeapi_LodeSplitRegistry_initializePlayMlPackSplitHandler', 'start': 4572256, 'delta': 2989712, 'outside_size': True}
    0x7362b0:	ldr	x30, [sp, #0x20]
    0x7362b4:	add	sp, sp, #0x50
    0x7362b8:	autiasp	
    0x7362bc:	ret	
    0x7362c0:	ldp	x20, x19, [sp, #0x80]
    0x7362c4:	ldp	x22, x21, [sp, #0x70]
    0x7362c8:	ldp	x24, x23, [sp, #0x60]
    0x7362cc:	ldp	x26, x25, [sp, #0x50]
    0x7362d0:	ret	
    0x7362d4:	sdiv	x10, x10, x11
    0x7362d8:	lsl	x11, x10, #1
    0x7362dc:	cmp	x11, x9
    0x7362e0:	csel	x9, x11, x9, hi
    0x7362e4:	ret	
    0x7362e8:	mov	w8, #0x37
    0x7362ec:	adrp	x2, #0x98000
    0x7362f0:	add	x2, x2, #0x8e4
    0x7362f4:	ret	
    0x7362f8:	mov	x21, x2
    0x7362fc:	mov	x19, x1
    0x736300:	mov	x20, x0
    0x736304:	ret	
    0x736308:	ldp	x20, x8, [x19]
    0x73630c:	ldr	x23, [x19, #0x10]
    0x736310:	sub	x2, x8, x20
    0x736314:	ret	
    0x736318:	mov	x21, x2
    0x73631c:	mov	x20, x1
    0x736320:	mov	x19, x0
    0x736324:	ret	
    0x736328:	stp	x26, x25, [sp, #0x50]
    0x73632c:	stp	x24, x23, [sp, #0x60]
    0x736330:	stp	x22, x21, [sp, #0x70]
    0x736334:	stp	x20, x19, [sp, #0x80]
    0x736338:	ret	
    0x73633c:	ldr	q0, [x21]
    0x736340:	ldr	x8, [x21, #0x10]
    0x736344:	ldr	q1, [x19]
    
    ### TfliteModelPooledCachedRunner::Init target 0x1342d0 xref 0x739f94 adrp+add {'name': 'Java_com_google_android_libraries_lens_ondevice_nativeapi_LodeSplitRegistry_initializePlayMlPackSplitHandler', 'start': 4572256, 'delta': 3005236, 'outside_size': True}
    0x739f54:	ldp	x30, x19, [sp], #0x10
    0x739f58:	autiasp	
    0x739f5c:	b	#0x11db070
    0x739f60:	paciasp	
    0x739f64:	stp	x29, x30, [sp, #-0x60]!
    0x739f68:	stp	x28, x27, [sp, #0x10]
    0x739f6c:	stp	x26, x25, [sp, #0x20]
    0x739f70:	stp	x24, x23, [sp, #0x30]
    0x739f74:	stp	x22, x21, [sp, #0x40]
    0x739f78:	stp	x20, x19, [sp, #0x50]
    0x739f7c:	sub	sp, sp, #0x250
    0x739f80:	mrs	x24, tpidr_el0
    0x739f84:	mov	x21, x1
    0x739f88:	mov	x19, x0
    0x739f8c:	ldr	x8, [x24, #0x28]
    0x739f90:	adrp	x1, #0x134000
    0x739f94:	add	x1, x1, #0x2d0
    0x739f98:	add	x0, sp, #0x1a0
    0x739f9c:	mov	x20, x2
    0x739fa0:	str	x8, [sp, #0x248]
    0x739fa4:	bl	#0x46086c
    0x739fa8:	add	x0, sp, #0x1a0
    0x739fac:	bl	#0x11b3440
    0x739fb0:	ldr	w8, [x21, #0x1c]
    0x739fb4:	cmp	w8, #7
    0x739fb8:	b.eq	#0x73a018
    0x739fbc:	adrp	x1, #0x9f000
    0x739fc0:	add	x1, x1, #0xcad
    0x739fc4:	adrp	x4, #0xeb000
    0x739fc8:	add	x4, x4, #0x3cb
    0x739fcc:	mov	w0, #9
    0x739fd0:	mov	w2, #0xf
    0x739fd4:	mov	w3, #0xe1
    0x739fd8:	bl	#0x105e410
    0x739fdc:	mov	x21, x0
    0x739fe0:	ldr	x8, [x24, #0x28]
    0x739fe4:	ldr	x9, [sp, #0x248]
    0x739fe8:	cmp	x8, x9
    
    ### TfliteModelPooledCachedRunner::RunWithContext target 0xa83a2 xref 0x73b478 adrp+add {'name': 'Java_com_google_android_libraries_lens_ondevice_nativeapi_LodeSplitRegistry_initializePlayMlPackSplitHandler', 'start': 4572256, 'delta': 3010584, 'outside_size': True}
    0x73b438:	stp	xzr, xzr, [sp, #0x98]
    0x73b43c:	str	xzr, [sp, #0x90]
    0x73b440:	str	x8, [sp, #0xd0]
    0x73b444:	bl	#0x4b6088
    0x73b448:	b	#0x73b800
    0x73b44c:	adrp	x1, #0x104000
    0x73b450:	add	x1, x1, #0x18b
    0x73b454:	bl	#0x73fd2c
    0x73b458:	mov	w2, #0x14
    0x73b45c:	mov	w3, #0x20d
    0x73b460:	bl	#0x105e410
    0x73b464:	str	x0, [x19]
    0x73b468:	b	#0x73b800
    0x73b46c:	ldrb	w8, [sp, #0x10]
    0x73b470:	ldp	x13, x12, [sp, #0x18]
    0x73b474:	adrp	x9, #0xa8000
    0x73b478:	add	x9, x9, #0x3a2
    0x73b47c:	mov	w10, #0x2e
    0x73b480:	tst	w8, #1
    0x73b484:	lsr	x8, x8, #1
    0x73b488:	add	x11, sp, #0x10
    0x73b48c:	stp	x9, x10, [sp, #0x90]
    0x73b490:	csinc	x9, x12, x11, ne
    0x73b494:	add	x0, sp, #0x90
    0x73b498:	csel	x8, x13, x8, ne
    0x73b49c:	add	x1, sp, #0xd0
    0x73b4a0:	stp	x9, x8, [sp, #0xd0]
    0x73b4a4:	add	x8, sp, #0x70
    0x73b4a8:	bl	#0x1078984
    0x73b4ac:	add	x0, sp, #0x70
    0x73b4b0:	bl	#0x11b3440
    0x73b4b4:	ldp	x23, x8, [sp, #0x28]
    0x73b4b8:	mov	w9, #0x18
    0x73b4bc:	sub	x8, x8, x23
    0x73b4c0:	mov	x0, x23
    0x73b4c4:	sdiv	x24, x8, x9
    0x73b4c8:	add	x8, sp, #0x70
    0x73b4cc:	mov	x1, x24
    
    ### TfliteModelPooledXNNPackCached::InsertInterpreter target 0xe34e3 xref 0x73b574 adrp+add {'name': 'Java_com_google_android_libraries_lens_ondevice_nativeapi_LodeSplitRegistry_initializePlayMlPackSplitHandler', 'start': 4572256, 'delta': 3010836, 'outside_size': True}
    0x73b534:	adrp	x8, #0x12d9000
    0x73b538:	ldr	w1, [x8, #0xd48]
    0x73b53c:	cmp	w1, #1
    0x73b540:	b.ge	#0x73b9f0
    0x73b544:	ldr	x9, [x21, #8]
    0x73b548:	cbz	x9, #0x73b630
    0x73b54c:	ldr	x8, [x21, #0x10]
    0x73b550:	stp	x9, x8, [sp, #0xd8]
    0x73b554:	cbz	x8, #0x73b564
    0x73b558:	add	x1, x8, #8
    0x73b55c:	mov	w0, #1
    0x73b560:	bl	#0x11dce80
    0x73b564:	mov	w23, #1
    0x73b568:	str	x23, [sp, #0xd0]
    0x73b56c:	b	#0x73b6c0
    0x73b570:	adrp	x1, #0xe3000
    0x73b574:	add	x1, x1, #0x4e3
    0x73b578:	add	x0, sp, #0x90
    0x73b57c:	add	x20, sp, #0x90
    0x73b580:	bl	#0x46086c
    0x73b584:	add	x0, sp, #0x90
    0x73b588:	bl	#0x11b3440
    0x73b58c:	adrp	x8, #0x12d9000
    0x73b590:	ldr	w1, [x8, #0xd18]
    0x73b594:	cmp	w1, #1
    0x73b598:	b.ge	#0x73ba48
    0x73b59c:	add	x8, sp, #0x90
    0x73b5a0:	mov	x0, x21
    0x73b5a4:	mov	w1, #1
    0x73b5a8:	mov	x2, x23
    0x73b5ac:	mov	x3, x24
    0x73b5b0:	bl	#0x73a9cc
    0x73b5b4:	mov	w0, #0xa0
    0x73b5b8:	bl	#0x11e1d98
    0x73b5bc:	adrp	x8, #0x1200000
    0x73b5c0:	add	x8, x8, #0x5c0
    0x73b5c4:	mov	x23, x0
    0x73b5c8:	stp	xzr, xzr, [x0, #8]
    
    ### TfliteModelPooledXNNPackCached::AllocateModelTensors target 0x5ea62 xref 0x73bcc4 adrp+add {'name': 'Java_com_google_android_libraries_lens_ondevice_nativeapi_LodeSplitRegistry_initializePlayMlPackSplitHandler', 'start': 4572256, 'delta': 3012708, 'outside_size': True}
    0x73bc84:	add	sp, sp, #0x50
    0x73bc88:	autiasp	
    0x73bc8c:	ret	
    0x73bc90:	adrp	x0, #0x97000
    0x73bc94:	add	x0, x0, #0x208
    0x73bc98:	adrp	x1, #0x10b000
    0x73bc9c:	add	x1, x1, #0xbbb
    0x73bca0:	bl	#0x11b5cb8
    0x73bca4:	paciasp	
    0x73bca8:	sub	sp, sp, #0x80
    0x73bcac:	stp	x30, x23, [sp, #0x50]
    0x73bcb0:	stp	x22, x21, [sp, #0x60]
    0x73bcb4:	stp	x20, x19, [sp, #0x70]
    0x73bcb8:	mov	x20, x1
    0x73bcbc:	mov	x22, x0
    0x73bcc0:	adrp	x1, #0x5e000
    0x73bcc4:	add	x1, x1, #0xa62
    0x73bcc8:	add	x0, sp, #0x20
    0x73bccc:	mov	x19, x4
    0x73bcd0:	mov	x23, x3
    0x73bcd4:	mov	x21, x2
    0x73bcd8:	bl	#0x46086c
    0x73bcdc:	add	x0, sp, #0x20
    0x73bce0:	bl	#0x11b3440
    0x73bce4:	ldr	x8, [x19, #0x70]
    0x73bce8:	cmp	x20, x23
    0x73bcec:	ldr	x8, [x8]
    0x73bcf0:	ldp	x8, x9, [x8, #0x128]
    0x73bcf4:	sub	x8, x9, x8
    0x73bcf8:	asr	x8, x8, #2
    0x73bcfc:	ccmp	x8, x20, #0, eq
    0x73bd00:	b.ne	#0x73bd40
    0x73bd04:	cbz	x20, #0x73bdac
    0x73bd08:	ldr	x8, [x19, #0x70]
    0x73bd0c:	ldr	w1, [x21], #4
    0x73bd10:	mov	x2, x22
    0x73bd14:	ldr	x0, [x8]
    0x73bd18:	bl	#0xfb1810
    
    ### InterpreterFactoryCallbackXNNPack target 0xfaac5 xref 0x73f40c adrp+add {'name': 'Java_com_google_android_libraries_lens_ondevice_nativeapi_LodeSplitRegistry_initializePlayMlPackSplitHandler', 'start': 4572256, 'delta': 3026860, 'outside_size': True}
    0x73f3cc:	mov	x0, x19
    0x73f3d0:	mov	w1, #0x30
    0x73f3d4:	bl	#0x11db070
    0x73f3d8:	ldp	x30, x19, [sp, #0x10]
    0x73f3dc:	add	sp, sp, #0x20
    0x73f3e0:	autiasp	
    0x73f3e4:	ret	
    0x73f3e8:	paciasp	
    0x73f3ec:	str	x29, [sp, #-0x40]!
    0x73f3f0:	stp	x30, x23, [sp, #0x10]
    0x73f3f4:	stp	x22, x21, [sp, #0x20]
    0x73f3f8:	stp	x20, x19, [sp, #0x30]
    0x73f3fc:	sub	sp, sp, #0x1c0
    0x73f400:	mov	x20, x0
    0x73f404:	ldr	x22, [x0, #8]
    0x73f408:	adrp	x1, #0xfa000
    0x73f40c:	add	x1, x1, #0xac5
    0x73f410:	add	x0, sp, #0x40
    0x73f414:	mov	x19, x8
    0x73f418:	bl	#0x46086c
    0x73f41c:	add	x0, sp, #0x40
    0x73f420:	bl	#0x11b3440
    0x73f424:	add	x0, sp, #0x108
    0x73f428:	bl	#0xc1c11c
    0x73f42c:	ldr	w8, [x22, #0x7c]
    0x73f430:	str	xzr, [sp, #0x1c8]
    0x73f434:	cmp	w8, #1
    0x73f438:	b.lt	#0x73f464
    0x73f43c:	ldr	x1, [x22, #0xe0]
    0x73f440:	add	x0, sp, #0x40
    0x73f444:	add	x2, sp, #0x108
    0x73f448:	mov	x3, xzr
    0x73f44c:	bl	#0xfa9f3c
    0x73f450:	ldr	w2, [x22, #0x7c]
    0x73f454:	add	x0, sp, #0x40
    0x73f458:	add	x1, sp, #0x1c8
    0x73f45c:	bl	#0xfaa4b8
    0x73f460:	b	#0x73f484
    
    ### Failed to modify graph with XNNPack delegate. target 0x7ed47 xref 0x73f6a8 adrp+add {'name': 'Java_com_google_android_libraries_lens_ondevice_nativeapi_LodeSplitRegistry_initializePlayMlPackSplitHandler', 'start': 4572256, 'delta': 3027528, 'outside_size': True}
    0x73f668:	add	x1, x1, #0xd21
    0x73f66c:	add	x0, sp, #0x40
    0x73f670:	mov	w2, #0x2d
    0x73f674:	bl	#0x1065af0
    0x73f678:	add	x0, sp, #0x40
    0x73f67c:	bl	#0x1066394
    0x73f680:	add	x0, sp, #0x40
    0x73f684:	bl	#0x1065f90
    0x73f688:	str	xzr, [x19]
    0x73f68c:	b	#0x73f60c
    0x73f690:	bl	#0x73fd48
    0x73f694:	add	x0, sp, #8
    0x73f698:	mov	w2, #0x1c1
    0x73f69c:	mov	x3, xzr
    0x73f6a0:	bl	#0x1065f84
    0x73f6a4:	adrp	x1, #0x7e000
    0x73f6a8:	add	x1, x1, #0xd47
    0x73f6ac:	add	x0, sp, #8
    0x73f6b0:	mov	w2, #0x2d
    0x73f6b4:	bl	#0x1065af0
    0x73f6b8:	add	x0, sp, #8
    0x73f6bc:	bl	#0x1066394
    0x73f6c0:	add	x0, sp, #8
    0x73f6c4:	bl	#0x1065f90
    0x73f6c8:	str	xzr, [x19]
    0x73f6cc:	b	#0x73f604
    0x73f6d0:	bl	#0x73fd48
    0x73f6d4:	add	x0, sp, #0x18
    0x73f6d8:	mov	w2, #0x19d
    0x73f6dc:	mov	x3, xzr
    0x73f6e0:	bl	#0x1065f84
    0x73f6e4:	adrp	x1, #0x67000
    0x73f6e8:	add	x1, x1, #0x153
    0x73f6ec:	add	x0, sp, #0x18
    0x73f6f0:	mov	w2, #0x24
    0x73f6f4:	bl	#0x1065af0
    0x73f6f8:	add	x0, sp, #0x18
    0x73f6fc:	add	x1, sp, #0x40
    
    ### Failed to modify graph with XNNPack delegate. target 0x7ed47 xref 0x747de4 adrp+add {'name': 'Java_com_google_android_libraries_lens_ondevice_nativeapi_LodeSplitRegistry_initializePlayMlPackSplitHandler', 'start': 4572256, 'delta': 3062148, 'outside_size': True}
    0x747da4:	bl	#0xde6dd8
    0x747da8:	adrp	x9, #0x12cc000
    0x747dac:	mov	x1, sp
    0x747db0:	ldr	x9, [x9, #0x6f0]
    0x747db4:	ldr	x8, [x21, #0x218]
    0x747db8:	stp	x0, x9, [sp]
    0x747dbc:	mov	x0, x8
    0x747dc0:	bl	#0x534e1c
    0x747dc4:	mov	w20, w0
    0x747dc8:	ldr	x0, [sp]
    0x747dcc:	str	xzr, [sp]
    0x747dd0:	cbz	x0, #0x747ddc
    0x747dd4:	ldr	x8, [sp, #8]
    0x747dd8:	blr	x8
    0x747ddc:	cbz	w20, #0x747e74
    0x747de0:	adrp	x1, #0x7e000
    0x747de4:	add	x1, x1, #0xd47
    0x747de8:	adrp	x4, #0xb0000
    0x747dec:	add	x4, x4, #0x3fb
    0x747df0:	mov	w0, #0x35
    0x747df4:	mov	w2, #0x2d
    0x747df8:	mov	w3, #0xdc
    0x747dfc:	bl	#0x105e410
    0x747e00:	str	x0, [x19]
    0x747e04:	b	#0x747e60
    0x747e08:	mov	w8, #0xcd
    0x747e0c:	adrp	x9, #0xb0000
    0x747e10:	add	x9, x9, #0x3fb
    0x747e14:	mov	x0, x22
    0x747e18:	stp	x8, x9, [sp, #0x10]
    0x747e1c:	bl	#0xdd35a8
    0x747e20:	str	x0, [sp, #0x20]
    0x747e24:	add	x0, sp, #0x10
    0x747e28:	bl	#0x464758
    0x747e2c:	cmp	x0, #1
    0x747e30:	str	x0, [x19]
    0x747e34:	b.eq	#0x747ec4
    0x747e38:	ldr	x19, [sp, #0x20]
    
    ### ocr/google_ocr/detection/group_rpn_detector_utils.cc target 0x7690e xref 0x759f48 adrp+add {'name': 'Java_com_google_android_libraries_lens_ondevice_nativeapi_LodeSplitRegistry_initializePlayMlPackSplitHandler', 'start': 4572256, 'delta': 3136232, 'outside_size': True}
    0x759f08:	add	x1, sp, #0xf4
    0x759f0c:	mov	x0, x20
    0x759f10:	str	w8, [sp, #0xf4]
    0x759f14:	bl	#0x1065888
    0x759f18:	bl	#0x1066394
    0x759f1c:	add	x0, sp, #0x88
    0x759f20:	bl	#0x1065f90
    0x759f24:	b	#0x759e14
    0x759f28:	ldr	x17, [sp, #0x30]
    0x759f2c:	mov	w10, #0x14
    0x759f30:	add	x20, x20, #1
    0x759f34:	b	#0x759c30
    0x759f38:	mov	x23, xzr
    0x759f3c:	mov	w19, #0x14
    0x759f40:	mov	w21, #1
    0x759f44:	adrp	x29, #0x76000
    0x759f48:	add	x29, x29, #0x90e
    0x759f4c:	adrp	x25, #0x12d9000
    0x759f50:	adrp	x26, #0x98000
    0x759f54:	add	x26, x26, #0x9e4
    0x759f58:	mov	w22, #3
    0x759f5c:	adrp	x27, #0x5d000
    0x759f60:	add	x27, x27, #0x8fd
    0x759f64:	cmp	x23, x17
    0x759f68:	b.eq	#0x75a0b4
    0x759f6c:	ldr	x8, [sp, #0x98]
    0x759f70:	lsr	x9, x23, #6
    0x759f74:	ldr	x8, [x8, x9, lsl #3]
    0x759f78:	lsr	x8, x8, x23
    0x759f7c:	tbnz	w8, #0, #0x75a0ac
    0x759f80:	add	x0, sp, #0xb0
    0x759f84:	mov	w1, w23
    0x759f88:	bl	#0x78c018
    0x759f8c:	ldr	x8, [sp, #0x68]
    0x759f90:	nop	
    0x759f94:	madd	x20, x23, x19, x8
    0x759f98:	mov	x28, x1
    0x759f9c:	str	x0, [sp, #0xf8]
    
    ### ocr/google_ocr/detection/group_rpn_detector_utils.cc target 0x7690e xref 0x75a65c adrp+add {'name': 'Java_com_google_android_libraries_lens_ondevice_nativeapi_LodeSplitRegistry_initializePlayMlPackSplitHandler', 'start': 4572256, 'delta': 3138044, 'outside_size': True}
    0x75a61c:	ldr	x21, [x26]
    0x75a620:	ldr	x27, [x26, #0x38]
    0x75a624:	add	x8, sp, #0x110
    0x75a628:	add	x0, x26, #0x70
    0x75a62c:	bl	#0x56f154
    0x75a630:	str	w25, [sp, #0x7c]
    0x75a634:	cbz	w20, #0x75a690
    0x75a638:	tbnz	w20, #0x1f, #0x75a918
    0x75a63c:	sxtw	x8, w20
    0x75a640:	add	x19, x8, x8, lsl #4
    0x75a644:	lsl	x0, x19, #2
    0x75a648:	bl	#0x11e1d98
    0x75a64c:	add	x19, x0, x19, lsl #2
    0x75a650:	mov	x25, x0
    0x75a654:	b	#0x75a698
    0x75a658:	adrp	x19, #0x76000
    0x75a65c:	add	x19, x19, #0x90e
    0x75a660:	mov	w0, #0xd
    0x75a664:	adrp	x1, #0x98000
    0x75a668:	add	x1, x1, #0xa05
    0x75a66c:	mov	w2, #0x10
    0x75a670:	mov	w3, #0x439
    0x75a674:	mov	x4, x19
    0x75a678:	bl	#0x105e410
    0x75a67c:	mov	w1, #0x482
    0x75a680:	mov	x2, x19
    0x75a684:	bl	#0x105e5d0
    0x75a688:	str	x0, [sp, #0x70]
    0x75a68c:	b	#0x75a830
    0x75a690:	mov	x25, xzr
    0x75a694:	mov	x19, xzr
    0x75a698:	mov	x23, xzr
    0x75a69c:	mov	w28, w20
    0x75a6a0:	mov	x29, x25
    0x75a6a4:	cmp	x28, x23
    0x75a6a8:	b.eq	#0x75a7f4
    0x75a6ac:	ldr	w20, [x21, x23, lsl #2]
    0x75a6b0:	cmn	w20, #1
    
    ### ocr/google_ocr/detection/group_rpn_detector_utils.cc target 0x7690e xref 0x75a880 adrp+add {'name': 'Java_com_google_android_libraries_lens_ondevice_nativeapi_LodeSplitRegistry_initializePlayMlPackSplitHandler', 'start': 4572256, 'delta': 3138592, 'outside_size': True}
    0x75a840:	ldr	x0, [sp, #0x88]
    0x75a844:	ldr	x8, [sp, #0x98]
    0x75a848:	sub	x1, x8, x0
    0x75a84c:	bl	#0x11db070
    0x75a850:	cmp	w25, #2
    0x75a854:	add	x22, x22, #1
    0x75a858:	b.lt	#0x75a4b8
    0x75a85c:	b	#0x75a898
    0x75a860:	ldp	x8, x9, [sp, #0x40]
    0x75a864:	stp	x8, x8, [x9, #0x10]
    0x75a868:	mov	w8, #1
    0x75a86c:	stp	x8, x21, [x9]
    0x75a870:	b	#0x75a8e4
    0x75a874:	adrp	x1, #0xe3000
    0x75a878:	add	x1, x1, #0x5b8
    0x75a87c:	adrp	x4, #0x76000
    0x75a880:	add	x4, x4, #0x90e
    0x75a884:	mov	w0, #0x35
    0x75a888:	mov	w2, #0x2c
    0x75a88c:	mov	w3, #0x45f
    0x75a890:	bl	#0x105e410
    0x75a894:	str	x0, [sp, #0x70]
    0x75a898:	ldr	x8, [sp, #0x48]
    0x75a89c:	ldr	x9, [sp, #0x70]
    0x75a8a0:	str	x9, [x8]
    0x75a8a4:	cbz	x21, #0x75a8e4
    0x75a8a8:	ldr	x20, [sp, #0x40]
    0x75a8ac:	mov	x19, x20
    0x75a8b0:	cmp	x19, x21
    0x75a8b4:	b.eq	#0x75a8d8
    0x75a8b8:	mov	x8, x19
    0x75a8bc:	ldr	x0, [x19, #-0x18]!
    0x75a8c0:	cbz	x0, #0x75a8b0
    0x75a8c4:	ldur	x9, [x8, #-8]
    0x75a8c8:	stur	x0, [x8, #-0x10]
    0x75a8cc:	sub	x1, x9, x0
    0x75a8d0:	bl	#0x11db070
    0x75a8d4:	b	#0x75a8b0
    
    ### ocr/google_ocr/detection/group_rpn_detector_utils.cc target 0x7690e xref 0x75b2c4 adrp+add {'name': 'Java_com_google_android_libraries_lens_ondevice_nativeapi_LodeSplitRegistry_initializePlayMlPackSplitHandler', 'start': 4572256, 'delta': 3141220, 'outside_size': True}
    0x75b284:	ldrb	w8, [sp, #0xf8]
    0x75b288:	tbz	w8, #0, #0x75b29c
    0x75b28c:	ldr	x8, [sp, #0xf8]
    0x75b290:	ldr	x0, [sp, #0x108]
    0x75b294:	and	x1, x8, #0xfffffffffffffffe
    0x75b298:	bl	#0x11db070
    0x75b29c:	add	x0, sp, #0xd0
    0x75b2a0:	bl	#0x1065f90
    0x75b2a4:	b	#0x75af9c
    0x75b2a8:	ldr	x8, [x9, #0x28]
    0x75b2ac:	ldr	x9, [sp, #0x248]
    0x75b2b0:	cmp	x8, x9
    0x75b2b4:	b.ne	#0x75b438
    0x75b2b8:	adrp	x1, #0x7f000
    0x75b2bc:	add	x1, x1, #0xf8f
    0x75b2c0:	adrp	x4, #0x76000
    0x75b2c4:	add	x4, x4, #0x90e
    0x75b2c8:	mov	w0, #0xd
    0x75b2cc:	mov	w2, #0x17
    0x75b2d0:	mov	w3, #0x48c
    0x75b2d4:	add	sp, sp, #0x250
    0x75b2d8:	bl	#0x5a5b7c
    0x75b2dc:	ldp	x29, x30, [sp, #0x40]
    0x75b2e0:	ldp	d9, d8, [sp, #0x30]
    0x75b2e4:	ldp	d11, d10, [sp, #0x20]
    0x75b2e8:	ldp	d13, d12, [sp, #0x10]
    0x75b2ec:	ldr	d14, [sp], #0xa0
    0x75b2f0:	autiasp	
    0x75b2f4:	b	#0x105e410
    0x75b2f8:	ldp	x9, x8, [x19, #0x18]
    0x75b2fc:	add	x0, sp, #0x120
    0x75b300:	add	x2, sp, #0xf8
    0x75b304:	strb	wzr, [sp, #0xf8]
    0x75b308:	sub	x8, x8, x9
    0x75b30c:	mov	w9, #0x120
    0x75b310:	sdiv	x1, x8, x9
    0x75b314:	bl	#0x4832d8
    0x75b318:	ldr	x0, [x19, #0x30]
    
    ### ocr/google_ocr/detection/group_rpn_detector_utils.cc target 0x7690e xref 0x75b588 adrp+add {'name': 'Java_com_google_android_libraries_lens_ondevice_nativeapi_LodeSplitRegistry_initializePlayMlPackSplitHandler', 'start': 4572256, 'delta': 3141928, 'outside_size': True}
    0x75b548:	bl	#0x477f34
    0x75b54c:	ldp	x8, x9, [sp, #0x50]
    0x75b550:	mov	w10, wzr
    0x75b554:	cmp	x8, x9
    0x75b558:	b.eq	#0x75b568
    0x75b55c:	str	w10, [x8], #4
    0x75b560:	add	w10, w10, #1
    0x75b564:	b	#0x75b554
    0x75b568:	lsr	x26, x20, #2
    0x75b56c:	mov	w8, wzr
    0x75b570:	mov	w27, wzr
    0x75b574:	mov	w9, #1
    0x75b578:	adrp	x20, #0x12d9000
    0x75b57c:	add	x20, x20, #0xf38
    0x75b580:	adrp	x24, #0x12d9000
    0x75b584:	adrp	x21, #0x76000
    0x75b588:	add	x21, x21, #0x90e
    0x75b58c:	mov	w28, #3
    0x75b590:	adrp	x22, #0xa0000
    0x75b594:	add	x22, x22, #0xfb2
    0x75b598:	str	x9, [sp, #0x40]
    0x75b59c:	cmp	w8, w26
    0x75b5a0:	str	w8, [sp, #0x28]
    0x75b5a4:	b.ge	#0x75b684
    0x75b5a8:	ldr	x9, [sp, #0x10]
    0x75b5ac:	ldr	w9, [x9, w8, sxtw #2]
    0x75b5b0:	cmp	w9, w8
    0x75b5b4:	b.ne	#0x75b5dc
    0x75b5b8:	add	x0, sp, #0x40
    0x75b5bc:	add	x1, sp, #0x28
    0x75b5c0:	bl	#0x4ed270
    0x75b5c4:	tbz	w1, #0, #0x75b5d0
    0x75b5c8:	ldr	w8, [sp, #0x28]
    0x75b5cc:	str	w8, [x0]
    0x75b5d0:	add	w8, w27, #1
    0x75b5d4:	str	w27, [x0, #4]
    0x75b5d8:	mov	w27, w8
    0x75b5dc:	ldr	w1, [x24, #0xf40]
    
    ### ocr/google_ocr/detection/group_rpn_detector_utils.cc target 0x7690e xref 0x75b694 adrp+add {'name': 'Java_com_google_android_libraries_lens_ondevice_nativeapi_LodeSplitRegistry_initializePlayMlPackSplitHandler', 'start': 4572256, 'delta': 3142196, 'outside_size': True}
    0x75b654:	mov	w8, wzr
    0x75b658:	stp	w9, wzr, [x0]
    0x75b65c:	b	#0x75b664
    0x75b660:	ldr	w8, [x0, #4]
    0x75b664:	add	x1, sp, #0x68
    0x75b668:	mov	x0, x23
    0x75b66c:	str	w8, [sp, #0x68]
    0x75b670:	bl	#0x1065888
    0x75b674:	bl	#0x1066394
    0x75b678:	add	x0, sp, #0x98
    0x75b67c:	bl	#0x1065f90
    0x75b680:	b	#0x75b5e8
    0x75b684:	ldp	x9, x8, [sp, #0x10]
    0x75b688:	adrp	x20, #0x12d9000
    0x75b68c:	add	x20, x20, #0xf50
    0x75b690:	adrp	x21, #0x76000
    0x75b694:	add	x21, x21, #0x90e
    0x75b698:	adrp	x29, #0x12d9000
    0x75b69c:	adrp	x22, #0x134000
    0x75b6a0:	add	x22, x22, #0x406
    0x75b6a4:	sub	x8, x8, x9
    0x75b6a8:	mov	w24, #3
    0x75b6ac:	adrp	x23, #0xa0000
    0x75b6b0:	add	x23, x23, #0xfcd
    0x75b6b4:	lsr	x28, x8, #2
    0x75b6b8:	sub	x28, x28, #1
    0x75b6bc:	tbnz	w28, #0x1f, #0x75b7cc
    0x75b6c0:	ldr	x8, [sp, #0x10]
    0x75b6c4:	mov	w9, w28
    0x75b6c8:	str	w9, [sp, #0x28]
    0x75b6cc:	mov	w10, w9
    0x75b6d0:	ldr	w9, [x8, w9, sxtw #2]
    0x75b6d4:	cmp	w9, w10
    0x75b6d8:	b.ne	#0x75b6c8
    0x75b6dc:	ldr	w1, [x29, #0xf58]
    0x75b6e0:	cmp	w1, #3
    0x75b6e4:	b.ge	#0x75b71c
    0x75b6e8:	add	x0, sp, #0x40
    
    ### ocr/google_ocr/detection/group_rpn_detector_utils.cc target 0x7690e xref 0x75baa8 adrp+add {'name': 'Java_com_google_android_libraries_lens_ondevice_nativeapi_LodeSplitRegistry_initializePlayMlPackSplitHandler', 'start': 4572256, 'delta': 3143240, 'outside_size': True}
    0x75ba68:	mov	x21, x2
    0x75ba6c:	str	x1, [sp, #0x30]
    0x75ba70:	stp	x8, x19, [sp, #8]
    0x75ba74:	add	x19, sp, #0x158
    0x75ba78:	bl	#0xd8f104
    0x75ba7c:	str	xzr, [sp, #0x1d8]
    0x75ba80:	bl	#0x11b2640
    0x75ba84:	adrp	x8, #0x12cc000
    0x75ba88:	fmov	s8, #0.25000000
    0x75ba8c:	mov	x22, xzr
    0x75ba90:	ldr	x8, [x8, #0xf10]
    0x75ba94:	mov	x20, xzr
    0x75ba98:	mov	w23, wzr
    0x75ba9c:	mov	w24, #0x70
    0x75baa0:	mov	w25, #0x120
    0x75baa4:	adrp	x26, #0x76000
    0x75baa8:	add	x26, x26, #0x90e
    0x75baac:	add	x8, x8, #0x10
    0x75bab0:	stp	xzr, x0, [sp, #0x1c8]
    0x75bab4:	stp	xzr, x8, [sp, #0x1b8]
    0x75bab8:	stp	xzr, xzr, [sp, #0x1a8]
    0x75babc:	ldp	x8, x9, [x21]
    0x75bac0:	sub	x9, x9, x8
    0x75bac4:	sdiv	x9, x9, x24
    0x75bac8:	cmp	x9, x20
    0x75bacc:	b.ls	#0x75bc78
    0x75bad0:	madd	x28, x20, x24, x8
    0x75bad4:	mov	x27, xzr
    0x75bad8:	ldp	x9, x8, [x28, #0x18]
    0x75badc:	sub	x8, x8, x9
    0x75bae0:	sdiv	x8, x8, x25
    0x75bae4:	cmp	x8, x27
    0x75bae8:	b.ls	#0x75bbcc
    0x75baec:	ldr	x8, [x28, #0x30]
    0x75baf0:	lsr	x9, x27, #6
    0x75baf4:	ldr	x8, [x8, x9, lsl #3]
    0x75baf8:	lsr	x8, x8, x27
    0x75bafc:	tbnz	w8, #0, #0x75bbc4
    
    ### ocr/google_ocr/detection/group_rpn_detector_utils.cc target 0x7690e xref 0x75d6e4 adrp+add {'name': 'Java_com_google_android_libraries_lens_ondevice_nativeapi_LodeSplitRegistry_initializePlayMlPackSplitHandler', 'start': 4572256, 'delta': 3150468, 'outside_size': True}
    0x75d6a4:	adrp	x1, #0x1068000
    0x75d6a8:	add	x1, x1, #0xa74
    0x75d6ac:	ldr	x8, [x8, #0x698]
    0x75d6b0:	adrp	x2, #0xb8000
    0x75d6b4:	add	x2, x2, #0xa20
    0x75d6b8:	add	x0, sp, #0x48
    0x75d6bc:	add	x4, sp, #0x60
    0x75d6c0:	mov	w3, #0x5c
    0x75d6c4:	mov	w5, #2
    0x75d6c8:	stp	x19, x8, [sp, #0x60]
    0x75d6cc:	stp	x10, x8, [sp, #0x70]
    0x75d6d0:	stp	xzr, xzr, [sp, #0x48]
    0x75d6d4:	str	xzr, [sp, #0x58]
    0x75d6d8:	bl	#0x10686a8
    0x75d6dc:	tbz	w0, #0, #0x75dab0
    0x75d6e0:	adrp	x3, #0x76000
    0x75d6e4:	add	x3, x3, #0x90e
    0x75d6e8:	add	x1, sp, #0x48
    0x75d6ec:	mov	w0, #0x35
    0x75d6f0:	mov	w2, #0x618
    0x75d6f4:	bl	#0x105e4e4
    0x75d6f8:	ldrb	w8, [sp, #0x48]
    0x75d6fc:	mov	x19, x0
    0x75d700:	tbz	w8, #0, #0x75d714
    0x75d704:	ldr	x8, [sp, #0x48]
    0x75d708:	ldr	x0, [sp, #0x58]
    0x75d70c:	and	x1, x8, #0xfffffffffffffffe
    0x75d710:	bl	#0x11db070
    0x75d714:	mov	x0, x19
    0x75d718:	ldp	x20, x19, [sp, #0x110]
    0x75d71c:	ldp	x22, x21, [sp, #0x100]
    0x75d720:	ldp	x24, x23, [sp, #0xf0]
    0x75d724:	ldp	x26, x25, [sp, #0xe0]
    0x75d728:	ldp	x28, x27, [sp, #0xd0]
    0x75d72c:	ldp	x29, x30, [sp, #0xc0]
    0x75d730:	ldp	d9, d8, [sp, #0xb0]
    0x75d734:	ldp	d11, d10, [sp, #0xa0]
    0x75d738:	ldp	d13, d12, [sp, #0x90]
    

## Recovered protobuf descriptors

