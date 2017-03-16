import json

with open("host_port.json", "r") as f:
	info = json.load(f)

def write(object):
	json.dumps(object)
	with open("host_port.json", "w") as f:
		json.dump(object, f, indent = 2)