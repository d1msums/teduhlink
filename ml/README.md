# TeduhLink local people-counting test

1. Run 1_SETUP.cmd once with internet access. It creates a separate Python environment and downloads Ultralytics/OpenCV and their dependencies, including PyTorch. Downloads may be large; allow time and sufficient disk space. Existing sensor/backend programs are separate.
2. Close other camera apps. Run 2_START_CAMERA.cmd. First run downloads pretrained yolov8n.pt if needed. Consenting participants only.
3. Drag a rectangle around the test rest area; press Enter to accept. Escape cancels. The initial selection image is frozen while selecting, then the live camera runs.
4. Green boxes have their centre inside the rectangle and contribute to the count. Grey boxes are outside. Raw count is the current detection result; stable count is the median of three recent results (within five seconds). The demonstration limit is three people. This is current occupancy, not cumulative entrants or vacant seats.
5. Test empty, 1, 2 and 3 people; seated people; a person outside the rectangle; people partially hiding one another. Expect mistakes and note them. Q exits; R resets the selected area. Close/restart if the camera freezes.
6. If the wrong camera opens, edit --camera 0 to --camera 1 in 2_START_CAMERA.cmd and retry. Check Windows camera permissions and close Camera, Teams, Zoom or other applications using the webcam.
7. The code runs locally on CPU, saves no footage, and does not upload counts to the backend yet. The model download uses internet; inference is local. This is not a remote 5G demonstration.
8. The next implementation stage is a background latest-frame capture source, reliable capture timestamps, backend count ingestion with expiry, and rider UI integration. Current synchronous capture is a detector test; camera-driver buffering or a blocked capture/inference call can delay/freeze the local window. Do not present it as a validated live availability service.

Validation performed at creation: Python syntax parsing and matching documented Ultralytics prediction API. Dependencies, model download and camera inference have not been run on this laptop by the assistant. Record your installed versions (setup writes installed-versions.txt) and test accuracy rather than assuming it.

References:
- https://docs.ultralytics.com/models/yolov8/
- https://docs.ultralytics.com/modes/predict/
