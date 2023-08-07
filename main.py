import threading
import time
from concurrent.futures import ThreadPoolExecutor

from fastapi import FastAPI, HTTPException, Request, File, Depends, Header, Form
from fastapi import UploadFile
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from jwt.exceptions import PyJWTError
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import Response
import SQL
import uuid, os
from datetime import datetime, timedelta
from pdf2docx import Converter
import asyncio
app = FastAPI()
security = HTTPBearer()

SECRET_KEY = "pdfpack123"
ALGORITHM = "HS256"

ALLOWED_ORIGIN = "http://127.0.0.1"  # Replace with your allowed site URL

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/token")
async def get_token(request: Request):

  origin = request.headers.get('origin')
  if origin != ALLOWED_ORIGIN:
    raise HTTPException(status_code=403, detail="Access denied")

  # with ThreadPoolExecutor() as executor:
  #   t1 = executor.submit(generate_token)
  #   print("token thread started")
  #   token = t1.result()
  #   # print("token:", token)
  loop = asyncio.get_event_loop()
  try:
    token = await loop.run_in_executor(None, generate_token)
    print("get_token:", token)
    return {"token": token}
  except Exception as e:
    return {"error": str(e)}
  
  


def generate_token() -> str:
  
  print("token thread started")
  issued_at = datetime.now()
  not_before = issued_at + timedelta(
      minutes=2)  # Token is not valid before 1 minute from issuance
  payload = {
      "authorized": True,
      "jti": str(uuid.uuid4()),  # Generate a unique ID for each token
      "iat": issued_at,
      "nbf": not_before
  }
  unique_id = payload["jti"]
  token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

  return token, unique_id, not_before



def upload(file: UploadFile = File(...), 
  unique_id: str = Form(...), 
  expiration: str = Form(...),  
  auth: HTTPAuthorizationCredentials = Depends(security)):

  print("Upload thread started")
  pdf_name = file.filename
  user_file_name = pdf_name[:-4]
  doc_name = pdf_name[:-4] + ".docx"

  try:
    # 1 print("filename:", file.filename)
    contents = file.file.read()
    with open("storage/" + unique_id + "_" + pdf_name, 'wb') as f:
      f.write(contents)
      # print(f'File stored locally: {"storage/" + unique_id + "_" + pdf_name}')
      #insert into DB
      SQL.insert_data(auth.credentials, expiration, user_file_name,
                      "storage/" + unique_id + "_" + pdf_name,
                      "storage/" + unique_id + "_" + doc_name, unique_id, 1 )
      SQL.delete_data()
      # return {"message": "File uploaded successfully"}
  except Exception as e:
    return {"message": str(e)}


@app.post("/upload")
async def upload_file(file: UploadFile = File(...), 
  unique_id: str = Form(...), 
  expiration: str = Form(...), 
  auth: HTTPAuthorizationCredentials = Depends(security)):

  print(file.filename)
  expiration = datetime_object = datetime.strptime(expiration, '%Y-%m-%dT%H:%M:%S.%f')
  loop = asyncio.get_event_loop()
  try:
    await loop.run_in_executor(None, upload, file,unique_id,expiration, auth)
    print("Upload thread ENEDED")
    return 
  except Exception as e:
    return {"error": str(e)}

  # t = threading.Thread(target=upload, args=[file,unique_id,expiration, auth])
  # t.start()
  # return t.join()



def convert(auth: HTTPAuthorizationCredentials = Depends(security)):
  print("------------------------------")
  print("CONVERT thread started")
  # print(auth)
  print("------------------------------")

  try:
    verification = SQL.verify_token(auth.credentials)
    print("VERIFICATION:",verification)
    if verification == 1:
      paths = SQL.file_path(auth.credentials)

      pdf_file_path = paths[0][0]
      doc_file_path = paths[0][1]

      print("CONVERTING:", pdf_file_path)

      cv = Converter(pdf_file_path)
      cv.convert(doc_file_path)
      cv.close()

      return {"Value": True}
    else:
      return {"message": "JWT token is invalid or not found"}
  except HTTPException as e:
    return e.detail



@app.post("/convert")
async def convert_pdf_to_docx(auth: HTTPAuthorizationCredentials = Depends(security)):
  loop = asyncio.get_event_loop()
  try:
    # Using asyncio.run to run the `convert` function asynchronously
    Value = await loop.run_in_executor(None, convert, auth)
    return {"Value": Value}
  except Exception as e:
    return {"error": str(e)}



@app.post("/get_local_token")
async def get_local_token(
    auth: HTTPAuthorizationCredentials = Depends(security)):

  token_local = auth.credentials
  paths = SQL.file_path(token_local)

  doc_file_path = paths[0][1]
  file_name = paths[0][2]
  print("Getting DOC path:", doc_file_path)
  global doc_file
  global doc_file_name
  doc_file = doc_file_path
  doc_file_name = file_name + ".docx"



@app.get("/file_data")
async def get_file_data():
  file_name = doc_file_name

  return {"file_name": file_name}



@app.get("/download")
async def download_file():
  print("Downloading DOC:", doc_file)
  try:
    with open(doc_file, "rb") as file:
      file_content = file.read()
      print("file length:", len(file_content))
  except FileNotFoundError:
    return {"message": "File not found"}

  media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
  headers = {
    "Content-Disposition": f"attachment;filename={doc_file_name}"}

  return Response(content=file_content, media_type=media_type, headers=headers)




if __name__ == '__main__':
  import uvicorn
  uvicorn.run(app, host="0.0.0.0", port=8000)
