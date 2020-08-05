# ERRORS
This system doesn't work properly, and I don't know why.

Basically, replacing a `string` with reference to an object defined in the `definitions` section of the schema results in the data from the event not being used when I run
```
sam local invoke TestEntrypoint -e sam-tests/create.json
```

## To reproduce
Simply run `bin/full_build.sh`, and when the system pauses then debug `src/toby_ec2_keypair/handlers.py`.

Run to line 42, then go look at the `model` and you'll see that the `PublicKeys` value is `None` - it should be an object 
thus:

```javascript
{ "keymaterial": "ssh ...."}
```
