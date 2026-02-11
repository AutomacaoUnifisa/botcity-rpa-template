#!/bin/bash
set -e

mkdir -p dist
rm -f dist/bot.zip

zip -r dist/bot.zip bot.py requirements.txt botcity/ src/ -x "**/__pycache__/*"

echo "Build concluído!"