# CrowdSequence Repository

This is the basic scaffolding for CrowdSequence, an app we hopefully actually build!

## Setup

### Compile Protobufs

Download Protobufs using homebrew. Protobufs allow us to have one centralized spot to type our objects, and can be serialized before going over the web socket.
```
brew install protobuf
```

Compile protobufs for Python + the FastAPI instance. This can be run using:
```
protoc -I=./proto --python_out=./server/models ./proto/models.proto
```

Then compile the protobufs for Typescript files. This can be run using:
```
protoc --plugin="protoc-gen-ts=./node_modules/.bin/protoc-gen-ts" --js_out="import_style=commonjs,binary:./client/src/models" --ts_out="./client/src/models" ./proto/models.proto
```

To do this easily, just run the `proto` script using npm.
```
npm run proto
```

### Backend

Run the following commands to install all the backend dependencies for the project, and then run it locally on port 8000.

```
poetry install
poetry run start
```

### Frontend 

Run the following commands to install all dependencies and run the application locally.

```
cd frontend 
npm install
npm run start
```

## Deployments

The FastAPI instance deploys the frontend of the project. The frontend can be compiled and adjusted to be served by the backend using the following command in the root directory.
```
npm run build
```