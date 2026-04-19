from fastapi import FastAPI, UploadFile, File
from fastapi.responses import StreamingResponse
import asyncio
from concurrent.futures import ThreadPoolExecutor
import shutil
import os
from main import Main


app = FastAPI()
executor = ThreadPoolExecutor()
main = None
output_path = None

os.makedirs("uploads", exist_ok=True)

@app.post("/start")
async def start(output: str, file: UploadFile = File(...)):
    global main, output_path, raw_path
    file_path = f"uploads/{file.filename}"
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    raw_path = os.path.join(output, "temp.mp4")
    output_path = os.path.join(output, "output.mp4")
    main = Main(file_path, output)
    asyncio.get_event_loop().run_in_executor(executor, main.run)
    return {"status": "processing"}

@app.get("/status")
def status():
    if main is None:
        return {"status": "idle"}
    if main.worker.is_alive():
        return {"status": "processing"}
    return {"status": "done"}

@app.get("/video")
def get_video():
    if output_path is None or not os.path.exists(output_path):
        return {"error": "no video yet"}
    
    def iterfile():
        with open(output_path, "rb") as f:
            yield from f
            
    return StreamingResponse(iterfile(), media_type="video/mp4")