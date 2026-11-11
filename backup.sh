#!/bin/bash

PROJECTFOLDER=$(basename "$PWD")
DEST_FOLDER=Python

ARCHIVE=$PROJECTFOLDER.zip
ARCHIVEFOLDER=$HOME/\!MyDoc/floppi/$DEST_FOLDER/$PROJECTFOLDER

if ! [ -d $ARCHIVEFOLDER ]
then
    mkdir -p $ARCHIVEFOLDER
fi

cd ..

zip -r $ARCHIVE $PROJECTFOLDER -x@./$PROJECTFOLDER/excludezip.txt

#zip -r $ARCHIVE $PROJECTFOLDER -x "**/app-spotter/binaries/*"
mv $ARCHIVE $ARCHIVEFOLDER
autoname --pattern:YYMMDDhhmmss $ARCHIVEFOLDER/$ARCHIVE
cd $PROJECTFOLDER
