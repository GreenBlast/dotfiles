#!/bin/bash

if [ "$#" -ne 2 ]; then
    echo "Usage: ${0} main_file.gcno project_name"
    exit 1
fi

FILENAME=`realpath $1`
FILEDIR=`dirname $1`
PROJECTNAME=$2

echo -e "${FILENAME} is filename \n${PROJECTNAME} is project name \n${FILEDIR} is dir"

sudo gcov $FILENAME

sudo lcov --capture --directory $FILEDIR --output-file  "${PROJECTNAME}.info"

genhtml "${PROJECTNAME}.info" --output-directory "${PROJECTNAME}_CODE_COVERAGE"
