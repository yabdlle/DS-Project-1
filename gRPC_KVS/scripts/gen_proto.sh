#!/usr/bin/env bash

# This option will stop immediately on errors
set -e

# NOTE: All paths are set as absolute paths based on the dev container setup

# Directory treated as the root of the proto namespace (Must contain kvstore.proto)
PROTO_ROOT="/workspaces/project_1/gRPC_KVS/proto"

# Output directory where to generate the python code
OUT_DIR="/workspaces/project_1/gRPC_KVS/src/kvstore"

# Relative path to the proto file
PROTO_FILE="/workspaces/project_1/gRPC_KVS/proto/kvstore.proto"

# Remove the old source directory
rm -rf "${OUT_DIR}"
mkdir -p "${OUT_DIR}"

# Ensure the __init__.py file exists in the generated folder so python can discover it like a library
touch "${OUT_DIR}/__init__.py"

echo "Generating gRPC Python code..."

# Python command to generate the gRPC Python
python -m grpc_tools.protoc -I "${PROTO_ROOT}" --python_out="${OUT_DIR}" --pyi_out="${OUT_DIR}" --grpc_python_out="${OUT_DIR}" "${PROTO_FILE}"

read -n 1 -p "Complete! Press any key to continue"
echo