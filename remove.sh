#! /bin/bash

FILES=$(ls glfs-* 2>/dev/null)

INSTALL_DIR="/usr/local/share"
PATH_DIR="/usr/local/bin"

rm -rf "$INSTALL_DIR/glfs-tools"

for file in $FILES; do
	sudo rm "$PATH_DIR/$file"
done

echo "done."