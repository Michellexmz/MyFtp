import json
import os

def write(object):
	json.dumps(object)
	with open("account.json", "w") as f:
		json.dump(object, f, indent = 2)

if __name__ == '__main__':
	with open("account.json", "r") as f:
		accounts = json.load(f)
	path = os.path.abspath("")
	for i in accounts:
		suffix = accounts[i]["home"].split("/")[-1]
		accounts[i]["home"] = os.path.join(path, suffix)
	write(accounts)