# -*- coding: utf-8 -*-
import string
import re

f = open("result.txt")
ff = file("res.txt", 'w')

while True:
	line = f.readline()
	if "Name:" in line:
		sex_check = f.readline()
		while "Name:" in sex_check:
			line = sex_check
			sex_check = f.readline()
		if "Sex:" in sex_check:
			topic_check = f.readline()
			if "Topic:" in topic_check:
				print "Please Wait.."
				ff.write("---Begin---\n" + line + sex_check + topic_check)
				topic_check = f.readline()
				while "Error:" not in topic_check:
					ff.write(topic_check)
					topic_check = f.readline()
				if "Error:" in topic_check:
					ff.write("---End---\n\n")

	if not line:
		break

line = f.readline()
ff.write(line)

count = 0

while "---Begin---" in line:
	name = f.readline()
	ff.write(name)
	print name
	ff.write(f.readline())
	ff.write(f.readline())
	topic_name = f.readline()

	while "---End---" not in topic_name:
		if topic_name == "\n":
			topic_name = f.readline()
			continue
		if "根话题" not in topic_name:
			topic_name = topic_name.splitlines()

			if "-" not in topic_name[0]:
				topic_name.append( " - 「根话题」 -" )
			else:
				topic_name.append( "「根话题」 -" )
			topic_name = "".join(topic_name)
			#topic_name.replace("\n","根话题 -\n")
			#topic_name = "根话题 -" + topic_name
			count += 1
			ff.write(topic_name + '\n')
			topic_name = f.readline()
			continue
		ff.write(topic_name)
		topic_name = f.readline()

	ff.write("---End---\n")
	ff.write(f.readline())
	ff.write(f.readline())

	if not line:
		break

print count
f.close()
ff.close()


f.close()
#ff.close()
