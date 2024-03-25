#!/bin/bash

# find all .py files except those in "excluded_folder"
excluded_folder="src/pingubot"
files=$(find . -name "*.py" -not -path "*$excluded_folder/*" -type f)

# open each file and insert the license header
for file in $files; do
  if ! grep -q Copyright $file
  then
      cat copyright.txt $file >$file.new && mv $file.new $file
  fi
done

# find all .js or .jsx files except those in "excluded_folder"
excluded_folder="src/frontend/node_modules"
files=$(find ./src/frontend -name "*.jsx" -not -path "*$excluded_folder/*" -type f)

# open each file and insert the license header
for file in $files; do
  if ! grep -q Copyright $file
  then
      cat copyright.txt $file >$file.new && mv $file.new $file
  fi
done