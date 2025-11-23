#!/bin/bash
# Generate Python stubs from proto files
# Run this script from the project root directory

set -e

PROTO_DIR="protos"
OUTPUT_DIR="protos"

echo "Generating Python stubs from proto files..."

# Generate NLP service stubs
python -m grpc_tools.protoc \
  -I${PROTO_DIR} \
  --python_out=${OUTPUT_DIR} \
  --grpc_python_out=${OUTPUT_DIR} \
  ${PROTO_DIR}/nlp_service.proto

echo "Generated nlp_service_pb2.py and nlp_service_pb2_grpc.py"

# Generate Summary service stubs
python -m grpc_tools.protoc \
  -I${PROTO_DIR} \
  --python_out=${OUTPUT_DIR} \
  --grpc_python_out=${OUTPUT_DIR} \
  ${PROTO_DIR}/summary_service.proto

echo "Generated summary_service_pb2.py and summary_service_pb2_grpc.py"

# Copy generated files to service directories
echo "Copying stubs to service directories..."

# NLP service
cp ${OUTPUT_DIR}/nlp_service_pb2.py src/core/nlp_insights/
cp ${OUTPUT_DIR}/nlp_service_pb2_grpc.py src/core/nlp_insights/

# Summary service
cp ${OUTPUT_DIR}/summary_service_pb2.py src/core/summary_generator/
cp ${OUTPUT_DIR}/summary_service_pb2_grpc.py src/core/summary_generator/

echo "✓ Proto stub generation complete!"
