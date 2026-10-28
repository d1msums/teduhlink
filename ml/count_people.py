"""Local camera proof of concept. No uploads or image recording."""
import argparse
from collections import deque
from pathlib import Path
import statistics
import time
import json
import uuid
from urllib.request import Request, urlopen


def main():
    import cv2
    from ultralytics import YOLO

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--upload', action='store_true')
    parser.add_argument('--camera', type=int, default=0)
    parser.add_argument('--capacity', type=int, default=3)
    parser.add_argument('--confidence', type=float, default=0.4)
    args = parser.parse_args()
    if args.capacity < 1 or not 0 < args.confidence < 1:
        parser.error('Capacity must be positive; confidence must be between 0 and 1.')
    root = Path(__file__).resolve().parent
    token_path = root.parent / 'teduhlink-backend/data/device-token.txt'
    token = token_path.read_text().strip() if args.upload else ''
    if args.upload and args.capacity != 3:
        parser.error('The backend demo capacity is fixed at 3.')
    session = uuid.uuid4().hex
    sequence = 0
    last_upload = 0.0
    def publish(count, captured):
        nonlocal sequence, last_upload
        if not args.upload:
            return
        sequence += 1
        age = max(0, int((time.monotonic()-captured)*1000))
        payload = dict(stop_id='A',session_id=session,sequence=sequence,
                       estimated_count=count,observation_age_ms=age)
        request = Request('http://127.0.0.1:8000/api/occupancy-readings',
            data=json.dumps(payload).encode(),headers={'Content-Type':'application/json',
            'Authorization':'Bearer '+token})
        try:
            with urlopen(request,timeout=1) as response:
                print('COUNT UPLOAD',response.status,'count=',count,flush=True)
        except Exception as error:
            print('Count upload failed:',str(error),flush=True)
        last_upload = time.monotonic()
    publish(None,time.monotonic())
    print('Loading pretrained YOLOv8n. The first run may download model weights.', flush=True)
    model = YOLO(str(root / 'yolov8n.pt'))
    camera = cv2.VideoCapture(args.camera, cv2.CAP_DSHOW)
    if not camera.isOpened():
        camera.release()
        raise SystemExit('Cannot open camera. Close Camera/Teams/Zoom; try camera 1.')
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    window = 'TeduhLink - LOCAL CAMERA TEST'
    history = deque(maxlen=3)
    region = None
    try:
        # Allow automatic exposure to settle.
        frame = None
        for _ in range(15):
            ok, frame = camera.read()
            if not ok:
                raise RuntimeError('Camera opened but no image arrived.')
        while True:
            if region is None:
                print('Drag a rectangle around the rest area. Press Enter. Escape cancels.', flush=True)
                region = cv2.selectROI('Select rest area', frame, showCrosshair=True, fromCenter=False)
                cv2.destroyWindow('Select rest area')
                if region[2] <= 0 or region[3] <= 0:
                    print('No area selected. Exiting.')
                    break
                history.clear()
            read_started = time.monotonic()
            ok, frame = camera.read()
            if not ok:
                history.clear()
                print('CAMERA UNAVAILABLE - no valid count. Exiting.', flush=True)
                break
            result = model.predict(frame, classes=[0], conf=args.confidence,
                                   imgsz=640, device='cpu', verbose=False)[0]
            rx, ry, rw, rh = map(int, region)
            count = 0
            for box in result.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                cx, cy = (x1+x2)/2, (y1+y2)/2
                inside = rx <= cx <= rx+rw and ry <= cy <= ry+rh
                if inside:
                    count += 1
                colour = (40, 190, 40) if inside else (140, 140, 140)
                cv2.rectangle(frame, (x1,y1), (x2,y2), colour, 2)
                cv2.circle(frame, (int(cx),int(cy)), 3, colour, -1)
            now = time.monotonic()
            while history and now-history[0][0] > 5:
                history.popleft()
            if now-read_started <= 5:
                history.append((read_started, count))
            else:
                history.clear()
            usable = len(history)==3 and now-history[0][0] <= 5
            stable = int(statistics.median(n for _,n in history)) if usable else None
            if args.upload and now-last_upload >= 1:
                publish(stable, history[0][0] if stable is not None else now)
            status = 'UNKNOWN / WARMING UP' if stable is None else (
                'AT LIMIT' if stable >= args.capacity else 'BELOW LIMIT')
            cv2.rectangle(frame,(rx,ry),(rx+rw,ry+rh),(255,180,0),2)
            # Put text on a separate strip so it does not hide people.
            import numpy as np
            strip = np.zeros((105, frame.shape[1], 3), dtype=frame.dtype)
            lines = [f'LOCAL TEST | raw: {count} | stable: {stable if stable is not None else "--"}',
                     f'{status} | demo limit: {args.capacity}',
                     'Q: quit   R: redraw area   People estimate, not vacant seats']
            for i, line in enumerate(lines):
                cv2.putText(strip,line,(10,25+30*i),cv2.FONT_HERSHEY_SIMPLEX,0.5,(255,255,255),1)
            cv2.imshow(window, np.vstack([strip,frame]))
            key=cv2.waitKey(1)&0xff
            if key in (ord('q'),27):
                break
            if key==ord('r'):
                publish(None,time.monotonic())
                region=None
    finally:
        publish(None,time.monotonic())
        camera.release()
        cv2.destroyAllWindows()

if __name__=='__main__':
    main()
