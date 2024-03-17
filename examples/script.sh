#!/bin/bash

set -eu

function add_args() {
    argparser setup --prog "$0" --desc "Test script."
    argparser add FILE        file
    argparser add WORKERS  -l num-workers  -s n --type int --default 8
    argparser add USER_IDS -l user-ids     -s u --type int --nargs "*"
    argparser add BETA     -l experimental      --action store_true
    argparser add LANGUAGE -l lang              --choices en de ja
}

eval $(add_args | argparser parse "$@")

echo $FILE
echo $WORKERS
echo ${USER_IDS[@]}
$BETA && echo T || echo F
echo $LANGUAGE
