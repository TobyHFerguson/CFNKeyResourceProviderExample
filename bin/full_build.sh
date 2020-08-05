cfn validate && 
cfn generate && 
cfn submit --dry-run && 
pip install ptvsd -t build && 
create_test_events.sh CREATE templates/create.json >sam-tests/create.json &&
sam local invoke TestEntrypoint -e sam-tests/create.json -d 5890