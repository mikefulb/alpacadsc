#!/usr/bin/env bash

# launch a python script in anaconda env

# add any command line arguments to invocation like 'launch.sh arg1 arg2 ...'

MY_ENV="pyastro37"
MY_DIR="/home/msf/Projects/Astronomy/Utilities/dsc_alpaca_server/scripts"
MY_PGM="DaveEkSettingCirclesServer.py"
MY_PY="python3"

# get conda setup
echo "Activating $MY_ENV"
eval "$(/home/msf/anaconda3/bin/conda shell.bash hook)"

conda activate $MY_ENV

cd $MY_DIR

echo "Running $MY_PY $MY_DIR/$MY_PGM ${@:1}"
$MY_PY $MY_DIR/$MY_PGM ${@:1}
status=$?
if test $status -ne 0
then
    echo "Error running script!"
    echo "Press ENTER to exit"
    read
fi

'
