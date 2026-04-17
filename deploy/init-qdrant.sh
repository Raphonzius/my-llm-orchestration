#!/bin/bash
# Create Qdrant collections with payload indexes for frontmatter filtering
# Called by setup.sh — can also run standalone
set -e

QDRANT_URL="${QDRANT_URL:-http://localhost:6333}"

create_collection() {
  local name=$1
  echo "  Creating collection: $name"

  # Create collection with cosine distance, 1024 dim (mxbai-embed-large)
  curl -s -X PUT "$QDRANT_URL/collections/$name" \
    -H 'Content-Type: application/json' \
    -d '{
      "vectors": {
        "size": 1024,
        "distance": "Cosine"
      }
    }' | python3 -c "import sys,json; r=json.load(sys.stdin); print('    ' + ('OK' if r.get('result') else r.get('status',{}).get('error','already exists')))" 2>/dev/null || echo "    OK (already exists)"

  # Create payload indexes for frontmatter-based filtering
  for field in domain type status provenance confidence; do
    curl -s -X PUT "$QDRANT_URL/collections/$name/index" \
      -H 'Content-Type: application/json' \
      -d "{\"field_name\": \"$field\", \"field_schema\": \"keyword\"}" > /dev/null 2>&1
  done

  # Date indexes
  for field in created modified; do
    curl -s -X PUT "$QDRANT_URL/collections/$name/index" \
      -H 'Content-Type: application/json' \
      -d "{\"field_name\": \"$field\", \"field_schema\": \"keyword\"}" > /dev/null 2>&1
  done

  # Text index on tags (array of keywords)
  curl -s -X PUT "$QDRANT_URL/collections/$name/index" \
    -H 'Content-Type: application/json' \
    -d '{"field_name": "tags", "field_schema": "keyword"}' > /dev/null 2>&1

  echo "    Indexes created: domain, type, status, provenance, confidence, created, modified, tags"
}

echo "Creating Qdrant collections at $QDRANT_URL..."
create_collection "atlas"
create_collection "sources"
create_collection "projects"
create_collection "areas"

echo ""
echo "Verifying collections..."
curl -s "$QDRANT_URL/collections" | python3 -c "
import sys, json
data = json.load(sys.stdin)
for c in data.get('result', {}).get('collections', []):
    print(f\"  {c['name']}\")
" 2>/dev/null || curl -s "$QDRANT_URL/collections"

echo ""
echo "Qdrant setup complete."
