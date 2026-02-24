#! /usr/bin/env bash

export ZIP_NAME="project1"
export ZIP_DIR="zip/$ZIP_NAME"

rm -f $ZIP_NAME.zip
rm -rf $ZIP_DIR
mkdir -p $ZIP_DIR

mkdir -p $ZIP_DIR/ingestion/RAG
cp -r ingestion/RAG/pdf_ingestor.py $ZIP_DIR/ingestion/RAG/
cp -r ingestion/ingestion_client.py $ZIP_DIR/ingestion/

cp -r mcp_server/ $ZIP_DIR/
cp -r server/ $ZIP_DIR/
cp -r tests/ $ZIP_DIR/
cp -r docs/ $ZIP_DIR/

echo "Zipping..."
cd zip/
zip $ZIP_NAME.zip -r $ZIP_NAME
mv $ZIP_NAME.zip ..
cd ..
echo "Written to $ZIP_NAME.zip. Inspect $ZIP_DIR/ to confirm contents"

