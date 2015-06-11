#!/usr/bin/env bash
fail() {
  echo "Failed to Setup: ${1}"
  exit 1
}

PYTHON="$(which python)"

if [ ! -x "${PYTHON}" ]
then
  fail "You must install Python to use this setup script."
fi

${PYTHON} setup.py