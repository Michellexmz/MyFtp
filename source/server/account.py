import json

with open("account.json", "r") as f:
	accounts = json.load(f)

def write(object):
	json.dumps(object)
	with open("account.json", "w") as f:
		json.dump(object, f, indent = 2)
