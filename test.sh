#!/bin/bash

rm test.glfs
./glfs-mkfs test.glfs


read -p "How many files to write? " num_tests

for i in $(seq 1 $num_tests);
do
    ./glfs-add test.glfs cat.txt $i.txt
done