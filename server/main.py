import uvicorn
import uuid 
import json

import random
import string


from typing import Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .models import models_pb2 as models
from .utils import ConnectionManager
from .init import init_server, init_manager

from google.protobuf import json_format

# Initialize the fastAPI application.
app = FastAPI()
app.mount("/static", StaticFiles(directory="server/static"), name="static")

templates = Jinja2Templates(directory="server/templates")

# Allow CORS witj the application.
origins = ["*"]
app.add_middleware(
  CORSMiddleware,
  allow_origins=origins,
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"]
)

# Create the root server for the application. This maps 
# UUIDs -> Rooms, which allow us to handle our room management
# across all the tracks being created and updated.
server = init_server()
manager = init_manager()

@app.get("/")
def serve_frontend(request: Request):
  return templates.TemplateResponse("index.html", {
    "request": request
  })


@app.get("/api/hello")
def hello_world():
  return "world"


# generates random unique room id
# used in REST api before websocket connection
@app.post("/api/generateRoomId/")
async def generate_room_id(room_settings: Request):
  settings = models.CreateRoom()
  room_settings = await room_settings.json()
  settings.ParseFromString(to_binary_string(room_settings.encode("utf-8")))
  print(settings)
  id = ''
  while True:
    id = ''.join([random.choice(string.ascii_letters
              + string.digits) for _ in range(6)])

    if (id not in tempRooms):
      break
  room = models.Room()
  room.measures = settings.measures
  room.subdivision = settings.subdivisions

  tempRooms[id] = room
  websockets[id] = {}
  return id

# to_binary_string allows us to decode the serialized data we get from
# our frontend typescript code.
def to_binary_string(x): 
  x = x.decode('utf-8').split(',') 
  return bytes(list(map(lambda i: int(i), x)))



# handle_transaction allows us to organize actions we want to take
# from the websocket.
def handle_transaction(roomId: str, clientId: str, action: str, payload: str):
  print(action)
  
  # First we convert the payload.
  converted_payload = to_binary_string(payload.encode("utf-8"))

  if (action == 'hello world'):
    # Example of a bar encoded payload.
    newbar = models.Bar()
    newbar.ParseFromString(converted_payload)

    print(newbar)
  
  if (action == 'create room'):
    tempRooms[roomId]['users'] = [clientId]
    print(tempRooms)

  if (action == 'join room'):
    tempRooms[roomId]['users'].add(clientId)
    print(tempRooms)

  

#  websocket used when joining room
@app.websocket("/api/ws/room/{roomId}/user/{clientId}")
async def websocket_endpoint(websocket: WebSocket, roomId: str, clientId: str):
  await manager.connect(websocket)
  print("was able to connect to the websocket")

  room = tempRooms[roomId]
  if (room.owner == ''):
    room.owner = clientId
  
  room.users.append(clientId)
  websockets[roomId][clientId] = websocket

  track = room.tracks[clientId]
  track.ownerName = clientId
  noteSequences = []
  for _ in range(5):
    sequence = models.NoteSequence()
    sequence.length[:] = [0 for _ in range(room.measures * room.subdivision)]
    noteSequences.append(sequence)
  track.sequence.extend(noteSequences)

  await manager.send_message(json.dumps({'action': 'room settings', 'payload': {'isOwner': room.owner == clientId, 'numMeasures': room.measures, 'numSubdivisions': room.subdivision, 'users': list(websockets[roomId].keys())} }), websocket)

  if(len(room.users) > 1):
    for conn in websockets[roomId].values():
      if(conn != websocket):
        await manager.send_message(json.dumps({'action': 'room join', 'payload': {'name': clientId}}), conn)

  # print(dict(tempRooms[roomId].tracks))
  while True:
    try:
      # Wait for any message from the client.
      data = await websocket.receive_text()

      print("Websocket end recieved data", data)
      
      transaction = json.loads(data)
      handle_transaction(roomId, clientId, transaction["action"], transaction["payload"])
      
      # Send message to the client.
      await manager.send_message("response", websocket)
    except WebSocketDisconnect:
      manager.disconnect(websocket)

# temporary map for room id to sequences array
tempRooms = {}
# temporary map for websocket cause protbufs can't store websocket class (prolly just gonna ditch protobufs, sorry Lasse)
websockets = {}


def start():
  """Launched with `poetry run start` at root level"""
  uvicorn.run("server.main:app", host="0.0.0.0", port=8000, reload=True)