#!/usr/bin/env bash
[ -d build ] && rm -rf build
mkdir -p build/tmp/
cp -R tools setup.bat setup.py setup.sh build/tmp/
cd build/tmp/
zip -r ../dsa-installer.zip .
