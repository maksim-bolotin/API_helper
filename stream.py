import cv2
from aiohttp import web

async def video_feed(request):
    cap = cv2.VideoCapture(0)  # Открываем веб-камеру

    async def stream():
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            _, buffer = cv2.imencode('.jpg', frame)
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
    return web.Response(body=stream(), content_type='multipart/x-mixed-replace; boundary=frame')

app = web.Application()
app.router.add_get('/video', video_feed)
web.run_app(app, host='localhost', port=8080)


# curl -X POST "http://localhost:8000/detect/gesture/stream?stream_url=rtsp://http://localhost:8080/video"
# curl -N -X POST "http://localhost:8000/detect/gesture/stream?stream_url=rtsp://http://localhost:8080/video"