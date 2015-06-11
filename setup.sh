#!/usr/bin/env bash
fail() {
  echo "Failed to Setup: ${1}"
  exit 1
}

find_python() {
  for name in python2.7 python2 python
  do
    if which ${name} > /dev/null
    then
      echo ${name}
      return
     fi
  done
}

PYTHON=$(find_python)

if [ -z "${PYTHON}" ]
then
  fail "You must install Python to use this setup script."
fi

${PYTHON} setup.py
