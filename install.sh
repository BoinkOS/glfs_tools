#! /bin/bash

FILES=$(ls glfs-* 2>/dev/null)

INSTALL_DIR="/usr/local/share"
PATH_DIR="/usr/local/bin"

if [ ! -d "$INSTALL_DIR" ]; then
	echo "install directory $INSTALL_DIR doesn't exist."
	exit 1
fi

mkdir "$INSTALL_DIR/glfs-tools"

for file in $FILES; do
	echo "installing $file..."

	chmod +x "$file"

	sudo cp "$file" "$INSTALL_DIR/glfs-tools"
done

sudo cp glfsimage.py "$INSTALL_DIR/glfs-tools"

for file in $FILES; do
	echo "linking $file..."
	
	sudo ln -s "$INSTALL_DIR/glfs-tools/$file" "$PATH_DIR/$file" 
done

echo "done."