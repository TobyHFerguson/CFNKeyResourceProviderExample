# ERRORS
The AWS parser seems to have an error.

In particular, it generates invalid code in its `models.py` from the schema.

Concretely, the schema `toby-ec2-keypair.json` defines a property `PublicKeys` which has a referenced object type. The reference is `Key` and the object type has a key called `keymaterial` and a value of string type. This can be seen below:

```json
    "definitions": {
        "Key" : {
            "type": "object",
            "properties":  {
                "keymaterial" : {
                    "type": "string"
                }
            },
            "required": ["keymaterial"]
        }
    },
.
.
.
    "properties": {
        "PublicKeys": {
            "description": "The public key material.",
            "$ref": "#/definitions/Key"
        },
```
The code generated in `models.py` for the `ResourceModel._deserialize` method should reference the provided JSON using the `PublicKeys` keyname, but instead it uses the name of the type (`Keys`), thus:

```python
            PublicKeys=Key._deserialize(json_data.get("Key")),
```

The correct code would be:
```python
            PublicKeys=Key._deserialize(json_data.get("PublicKeys")),
```

The result of this incorrectly generated code is that when one passes in an event (`sam-tests/create.json`) with a value for `PropertyKeys` the resulting model object isn't built correctly and the value in the model is `None`.


## To reproduce
Simply run `full_build.sh` (put the `bin` directory on your path - this shell script references another one in the `bin` directory) - the system will build, and then run. It'll throw an error

## To correct
Simply edit `models.py` and run full_build.sh again - the assertion won't be thrown. 
