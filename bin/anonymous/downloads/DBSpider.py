# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup
import requests
import string
import sys
import re
import time
import urllib2
import urllib
import StringIO
import gzip
import json
import ssl

reload(sys)
sys.setdefaultencoding('utf-8')

headers = {
    "cookie":'q_c1=24f5be339b774d588b7d6f4977c04f8e|1459604708000|1459604708000; l_cap_id="OGY1YTJjZTUyOTYxNDBiMWIxYzUxZmUyYTNhYWE4MDM=|1459604708|2b30de2e77fc5b3fa36f440ea3743a61a3f020a7"; cap_id="OTY0ZDg0MmVhNWQ2NGJjN2I0OGFkNWMyYzIzMDFkYzc=|1459604708|ceb7674bb0b839455a275d262a27c6f43a51efe7"; d_c0="AGCAU8PhtQmPTuVwkaQigsTBD44AonPs-oA=|1459604708"; _za=2d62287a-7acd-4bed-8788-cb07c3552190; login="ODBlMTQwYjQ4YzA5NDU0N2FjOTk3MTZmMzRkNGQ4NTI=|1459604718|f9f92b0fd9d42cba870200ad10373f1b7d36bf0b"; z_c0="QUJCS2tJRXNUUWdYQUFBQVlRSlZUUnRhSjFlSVNkNEw5anFkM0tJQkc5a0tBRFlUc1NaRFd3PT0=|1459604763|9808229832bebb652b6d7d3a905c89156bd82115"; _xsrf=a38833c6c6c29e620afa9decf72ec23a; _ga=GA1.2.301500917.1459604768; __utma=51854390.301500917.1459604768.1459766524.1459768989.3; __utmc=51854390; __utmz=51854390.1459768989.3.3.utmcsr=zhihu.com|utmccn=(referral)|utmcmd=referral|utmcct=/topic/19575211; __utmv=51854390.100--|2=registration_date=20150627=1^3=entry_date=20150627=1',
    "user-agent":"Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:44.0) Gecko/20100101 Firefox/44.0",
    "accept":"text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "accept-encoding":"gzip, deflate, br",
    "referer":"https://www.zhihu.com/topic/19575211/top-answers"
}

baseURL = "https://www.zhihu.com"
url_slaves = 'https://www.zhihu.com/topic/19575211/followers'

ff = file("dbtest2.txt", 'w') #打开文件

def getPage(url):   #通过URL进入网页，返回网页源代码
    request = urllib2.Request(url)
    request.add_header("cookie",'q_c1=24f5be339b774d588b7d6f4977c04f8e|1459604708000|1459604708000; l_cap_id="OGY1YTJjZTUyOTYxNDBiMWIxYzUxZmUyYTNhYWE4MDM=|1459604708|2b30de2e77fc5b3fa36f440ea3743a61a3f020a7"; cap_id="OTY0ZDg0MmVhNWQ2NGJjN2I0OGFkNWMyYzIzMDFkYzc=|1459604708|ceb7674bb0b839455a275d262a27c6f43a51efe7"; d_c0="AGCAU8PhtQmPTuVwkaQigsTBD44AonPs-oA=|1459604708"; _za=2d62287a-7acd-4bed-8788-cb07c3552190; login="ODBlMTQwYjQ4YzA5NDU0N2FjOTk3MTZmMzRkNGQ4NTI=|1459604718|f9f92b0fd9d42cba870200ad10373f1b7d36bf0b"; z_c0="QUJCS2tJRXNUUWdYQUFBQVlRSlZUUnRhSjFlSVNkNEw5anFkM0tJQkc5a0tBRFlUc1NaRFd3PT0=|1459604763|9808229832bebb652b6d7d3a905c89156bd82115"; _xsrf=a38833c6c6c29e620afa9decf72ec23a; _ga=GA1.2.301500917.1459604768; __utma=51854390.301500917.1459604768.1459766524.1459768989.3; __utmc=51854390; __utmz=51854390.1459768989.3.3.utmcsr=zhihu.com|utmccn=(referral)|utmcmd=referral|utmcct=/topic/19575211; __utmv=51854390.100--|2=registration_date=20150627=1^3=entry_date=20150627=1')
    request.add_header("user-agent","Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:44.0) Gecko/20100101 Firefox/44.0")
    request.add_header("accept","text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8")
    request.add_header("accept-encoding","gzip, deflate, br")
    request.add_header("referer","https://www.zhihu.com/topic/19575211/top-answers")
    
    try: #异常处理
    	response = urllib2.urlopen(request, timeout = 10)
    	content = StringIO.StringIO(response.read())
    except urllib2.HTTPError as e:
    	print type(e)
    	return 'Error'
    except ssl.SSLError as e:
    	print type(e)
    	return 'Error'
    except :
    	print "Unknown Error"
    	return 'Error'

    html = gzip.GzipFile(fileobj = content)
    return html.read()

#从粉丝关注的话题页面获取粉丝关注的话题名称以及父话题名称
def get_topic_name(flower_url):
    topic_url = flower_url+'/topics' #获取用户关注的话题URL
    wb_data = getPage(topic_url) #解析用户关注的话题主页
    if wb_data == 'Error':
    	return "Error"   #若获取网页信息出错，函数中断

    soup = BeautifulSoup(wb_data)

    topic_names = soup.select('#zh-profile-topic-list > div > div > a > strong')  #获取用户关注的话题名称(解析格式)
    topic_urls = soup.select('#zh-profile-topic-list > div > div > a:nth-of-type(2) ')  #获取用户关注的话题URL(解析形式)

    ff.write("Topic:" + '\n')

    for topic_name,topic_url in zip(topic_names,topic_urls):
        topic_organize_url = 'https://www.zhihu.com' + topic_url.get('href') + '/organize/entire' #获得话题组织-完整话题结构页面URL
        wb_data2 = getPage(topic_organize_url)

        if wb_data2 == 'Error':
        	return "Error"

        topic_list = []

        keyword = re.compile("<ul><li>.*")
        matches = keyword.findall(wb_data2) #在源代码中找到与该正则表达式匹配的行

        for match in matches:
        	pattern = re.compile(r".*entire\">(?P<name>.+?)</.*")
        	match_res = pattern.search(match).group("name") #将没用的信息替换掉
        	topic_list.insert(0, match_res)

        	if "strong" in match:  #选取话题
        		break

        for i in range(len(topic_list)):
        	ff.write(topic_list[i]+' - ')

        ff.write('\n')
        print "My Topic"

        time.sleep(5) #每隔5个时间单位打开一个网站，模拟人浏览网站行为，防止被反爬虫机制发现

    return "Fine"

def main():
	wb_data = getPage(url_slaves)
	soup = BeautifulSoup(wb_data)

	xsrf = soup.find('input', attrs = {'name': '_xsrf'}).get('value') #找到网站的xsrf参数

	data = {'offset' : 0,
	'start' : '',
	'_xsrf' : xsrf
	}

	while data['offset'] <= 5000: #加载前每页显示的用户数为20个
		res  = requests.post(url_slaves, headers = headers, data = data) #模拟网站信息，进行请求

		j = res.json()['msg']
		data['offset'] += j[0] #获取json解析的第一个参数
		soup = BeautifulSoup(j[1]) #获取json解析的第二个参数
		divs = soup.find_all('div', class_='zm-person-item')

		reNUM = re.compile(r'[^\d]*(\d+).*')
		data['start'] = int(reNUM.match(divs[-1]['id']).group(1))

		if data['offset'] <= 4000:
			num = ( 5000 - data['offset'] ) / 20
			print "Please wait." 
			print "Counting " + str(num)
			continue

		for div in divs:
			h2 = div.h2
			username = h2.a.text.encode('utf-8') #对中文进行编码
			ff.write('Name:' +username+ '\n')
			
            #查找包含每个用户识别码的行
			keyword = re.compile('/people/.*')
			userid = h2.findAll(attrs = { "href" : keyword})
			uid = re.sub(".*href=\"(.+)\">.*", "\g<1>", str(userid)) #获取每个用户的URL
			user_url = baseURL + uid

			user_doc = getPage(user_url)
			if user_doc == 'Error': #若出现错误，跳过该用户，继续爬下一个用户信息
				ff.write("Error:1\n")
				continue

			soup = BeautifulSoup(user_doc)

			sexs = soup.select('body > div.zg-wrap.zu-main.clearfix > div.zu-main-content > div > div.zm-profile-header.ProfileCard > div.zm-profile-header-main > div.body.clearfix > div > div > div.items > div:nth-of-type(1) > span.info-wrap > span.item.gender > i')

			if(len(sexs)) == 0: #若性别列表为空，则进行相应处理
				sex = "unknown"
				continue
			else:
				sex = re.sub(".*profile\-(\w.+)\".*", "\g<1>", str(sexs[0]))
			
			ff.write('Sex:' +sex +'\n')
			print "My name is " + username

			check = get_topic_name(user_url)

			if check == "Fine":
				ff.write("Error:0\n")
			else:
				ff.write("Error:1\n")

		time.sleep(3)

	ff.close()

if __name__ == '__main__':
	main()
	print "Spider Complete!"

