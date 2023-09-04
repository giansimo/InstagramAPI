import json

class Account:

    def __init__(self, d=None):
        if d is not None:
            for key, value in d.items():
                setattr(self, key, value)

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__,
                          sort_keys=True, indent=4)

