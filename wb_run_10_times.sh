#!/bin/bash

for i in {1..10}
do
    echo "run fixed_trace_eval_fixed.py $i-th time："
    python fixed_trace_eval_fixed.py
    sleep 2
    echo "------------------------"
done