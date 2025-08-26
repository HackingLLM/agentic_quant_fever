# The script that runs evaluations in our red-teaming writeup.
# We run 10 times for each trace to get the average result.

echo "run eval.py --type file --trace important_first"
python eval.py --type file --trace important_first > important_first.txt
sleep 2
echo "------------------------"

echo "run eval.py --type file --trace useless_first"
python eval.py --type file --trace useless_first > useless_first.txt
sleep 2
echo "------------------------"

echo "run eval.py --type file --trace shuffle"
python eval.py --type file --trace shuffle > shuffle.txt
sleep 2
echo "------------------------"

# shuffle is a pseudo-random trace, if interested in real random trace, please run --trace random 
# python eval.py --type file --trace random

# change the quantative target (90) to qualitative target (most)
echo "run eval.py --type file --trace shuffle --file-target most"
python eval.py --type file --trace shuffle --file-target most > shuffle_most.txt
sleep 2
echo "------------------------"

# various reasoning level {low, medium, high}
echo "run eval.py --type file --trace shuffle --reasoning-level low"
python eval.py --type file --trace shuffle --reasoning-level low > shuffle_low.txt
sleep 2
echo "------------------------"

echo "run eval.py --type file --trace shuffle --reasoning-level medium"
python eval.py --type file --trace shuffle --reasoning-level medium > shuffle_medium.txt
sleep 2
echo "------------------------"

echo "run eval.py --type file --trace shuffle --reasoning-level high"
python eval.py --type file --trace shuffle --reasoning-level high > shuffle_high.txt
sleep 2
echo "------------------------"

# memory management, default prompt config is 50% memory reduction, explicit safety
# check README.md for other prompt options
echo "run eval.py --type memory"
python eval.py --type memory > memory.txt
sleep 2 
echo "------------------------"