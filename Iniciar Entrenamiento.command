#!/bin/bash
cd "$(dirname "$0")/docs"
(sleep 1 && open http://localhost:8848) &
python3 -m http.server 8848
