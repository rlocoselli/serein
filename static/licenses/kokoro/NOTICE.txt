# Kokoro voice models

Model: Kokoro-82M v1.0, published by hexgrad, Apache License 2.0.
Original model card: https://huggingface.co/hexgrad/Kokoro-82M
Voice catalogue and training-source acknowledgements:
https://huggingface.co/hexgrad/Kokoro-82M/blob/main/VOICES.md

ONNX conversion and runtime: thewh1teagle/kokoro-onnx (MIT).
https://github.com/thewh1teagle/kokoro-onnx
Pinned model files: release model-files-v1.1. File SHA256 values are recorded
in scripts/prepare_kokoro.py and checked before use.

French voice ff_siwis: Kokoro credits the SIWIS French Speech Synthesis
Database (CC BY), Junichi Yamagishi, Pierre-Edouard Honnet, Philip Garner,
and Alexandros Lazaridis (2017). University of Edinburgh, CSTR.
https://doi.org/10.7488/ds/1705
Source and dataset attribution:
https://datashare.ed.ac.uk/handle/10283/2353
The voice is synthetic; no endorsement by the dataset contributors is implied.

Serein uses the English, French, Italian, Spanish and Brazilian Portuguese
voices listed in kokoro_engine.py. The files are pre-generated locally and
can be bundled in the Android app. The model weights are not bundled in APKs.
