
import sqlite3
import string
import re


conn = sqlite3.connect('zhihuDB.sqlite')
cur = conn.cursor()

cur.execute('''DROP TABLE IF EXISTS Users''')

cur.execute('''DROP TABLE IF EXISTS Topics''')

cur.execute('''CREATE TABLE Users (name TEXT, sex TEXT, topic TEXT REFERENCES Topics(topic), PRIMARY KEY (name, topic))''')

cur.execute('''CREATE TABLE Topics (topic TEXT PRIMARY KEY, parentopic TEXT, count INTEGER)''')


fname = raw_input('Enter file name: ')
count = 0
if(len(fname) < 1): fname = 'dbtest.txt'
fh = open(fname)
topic_fl = 0
for line in fh:
    print line
    if line.startswith('Name:'):
        pieces = line.split(":")
        name_tmp = pieces[1]
        name_tmp.replace("\n","")
        continue
    elif line.startswith('Sex:'):
        episodes = line.split(":")
        sex_tmp = episodes[1]
        sex_tmp.replace("\n","")
        continue
    elif line.startswith('Error:'):
        topic_fl = 0
    elif line.startswith('Topic:'):
        topic_fl = 1
        continue
    elif topic_fl == 1:
        sequence = line.split(' - ')
        topic_tmp = sequence[0]
        conn.text_factory = str
        for i in range(len(sequence)-1):
            cur.execute('SELECT topic FROM Topics WHERE topic = ?', (sequence[i],))
            row = cur.fetchone()
            if row is None:
                cur.execute('''INSERT INTO Topics (topic, parentopic, count) VALUES (?,?,1)''', (sequence[i],sequence[i+1],))
                #conn.commit()
                #i = i + 1
            else:
                cur.execute('UPDATE Topics SET count = count + 1 WHERE topic = ?', (sequence[i],))
                #conn.commit()
                #break
        #cur.execute('''INSERT INTO Users (name, sex, topic) VALUES (?, ?, ?)''', (name_tmp,sex_tmp,topic_tmp))
conn.commit()
cur.close()
