#!/usr/bin/env python
# -*- coding: utf-8 -*-
import StringIO
import gzip
import urllib
import urllib2
import httplib
from bs4 import BeautifulSoup
import re
import string
import sys
import time
import ssl

reload(sys)
sys.setdefaultencoding('utf-8')

home_url = 'https://pt.sjtu.edu.cn/'
torrents_list_url = 'https://pt.sjtu.edu.cn/torrents.php'

def getPage(url):
    request = urllib2.Request(url)
    request.add_header("cookie","PHPSESSID=e437f03cc7=58ee4171d1212c3d33b9b9; bgPicName=Default; __utmt=1; c_expiresintv=0; c_secure_uid=ODIyNTE%3D; c_secure_pass=eff4b6141c0066a96e2b2eeebcc8485a; c_secure_ssl=eWVhaA%3D%3D; c_secure_login=bm9wZQ%3D%3D; __utma=248584774.1646623820.1458039768.1458039768.1458044708.2; __utmb=248584774.3.10.1458044708; __utmc=248584774; __utmz=248584774.1458039768.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none)")
    request.add_header("user-agent","Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.75 Safari/537.36")
    request.add_header("accept","text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8")
    request.add_header("accept-encoding","gzip, deflate, sdch")
    request.add_header("referer","https://pt.sjtu.edu.cn/index.php")
    
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

TRIES = 5
def main():
    list_head_doc = getPage(torrents_list_url)
    soup = BeautifulSoup(list_head_doc)
    page_outer = soup.html.body.findAll(attrs = {"class" : "outer"})
    
    list_url_base = "https://pt.sjtu.edu.cn/torrents.php?inclbookmarked=0&incldead=0&spstate=0&page="
    torrent_file = file('res.txt', 'w')
    errorFile = file("error.txt", "w")

    class Torrent:
        def _init_(self):
            self.torrent_title = ''
            self.type = ''

    torrent = Torrent()

    for i in range(100):
        print "Crawing  Page " + str(i)
        list_url = list_url_base + str(i)
        list_doc = ""
        for retry in range(TRIES):
            list_doc = getPage(list_url)
            if list_doc == "Error":
                continue
            if list_doc != 'Error':
                break

        if list_doc == "Error":
            errorFile.write(list_url + '\n')
            continue

        soup = BeautifulSoup(list_doc)

        page_outer = soup.html.body.findAll(attrs = {"class" : "outer"})
        soup = BeautifulSoup(str(page_outer))

        keyword = re.compile("details\.php\?id=\d+\&hit=1|details\.php\?id=\d+\&hit=1\&hitfrom=sticky")
        keyword_b = re.compile("<a title=\".*</b></a>")

        data = keyword.findall(list_doc)
        torrent_title = keyword_b.findall(list_doc)
        torrent_name = []
        for k in range(len(torrent_title)):
            pattern = re.compile(".*<b>\[(?P<name>.+?)\].*")
            if pattern.search(torrent_title[k]) == None:
                name = "None"
            else:
                name = pattern.search(torrent_title[k]).group("name")
            #print name
            torrent_name.append(name)
        #print "Length is:" + str(len(torrent_name))

        uid_list = []
        for j in range(len(data)):
            uid = re.sub(".*id=(\d+)\&hit.*", "\g<1>",data[j])
            if uid in uid_list:
                continue
            else:
                uid_list.append(uid)

        for j in range(len(uid_list)):
            if torrent_name[j] == "None":
                continue
            num = i * 50 + j + 1
            print "Crawing Torrent " + str(num)
            torrent = Torrent()
            page_outer = soup.html.body.findAll(attrs = {"class" : "outer"})
            soup = BeautifulSoup(str(page_outer))

            torrent_types = soup.findAll(attrs = {"class" : "nobr"})
            keyword_a = re.compile("pic\/category\/chd\/colytorrents\/chs\/.*\.png")
            torrenttype_doc = soup.findAll(attrs = {"src" : keyword_a})

            torrent_type = torrenttype_doc[j+27]['alt']
            typelist = ['华语电影', '欧美电影', '亚洲电影',  '港台电视剧', '亚洲电视剧', '大陆电视剧', '欧美电视剧']
            check = False
            for m in range(len(typelist)):
                if typelist[m]==torrent_type:
                    check = True

            if check == False:
                continue

            torrent_file.write("片名:"+torrent_name[j]+'\n'+"类型:"+torrent_type+'\n')
            print torrent_name[j]
            
            torrent.uid = uid_list[j]
            torrentid_url = home_url + 'details.php?id=' + torrent.uid
            
            torrentid_doc = ""
            for retry in range(TRIES):
                torrentid_doc = getPage(torrentid_url)
                #print torrentid_doc
                if torrentid_doc == "Error":
                    continue
                if torrentid_doc != 'Error':
                        break

            if torrentid_doc == "Error":
                errorFile.write(torrentid_url + '\n')
                continue

            pagedes = re.compile(r'<td class="rowfollow".+?<b>分辨率:.+?</td>')
            kinds = re.compile(r"类　　别.+")
            year = re.compile(r"年　　代.+")
            country = re.compile(r"国　　家.+")
            language = re.compile(r"语　　言.+")
            hotlist = re.compile(r'<tr>.+?热度表.+?</tr>')
            downlist = [pagedes, year, country, language, hotlist, kinds]
            for k in range(6):
                matches=downlist[k].findall(torrentid_doc)
                for match in matches:
                    if k==0:
                        match_res = re.sub(".*分辨率.*</b>(1080p|1080i|720p|SD|其他).*", "\g<1>", match)
                        torrent_file.write("分辨率:"+match_res+'\n')
                        #print match_res
                    if k==5:
                        typePattern = re.compile(r"类　　别　(?P<type>.+?)<.*")
                        if typePattern.search(match) == None:
                            continue
                        match_res = typePattern.search(match).group("type")
                        strlist = ['剧情', '喜剧', '动作', '爱情', '科幻', '动画', '悬疑', '惊悚', '恐怖', '纪录片'\
                        '短片', '情色', '同性', '音乐', '歌舞', '家庭', '儿童', '传记', '历史', '战争', '犯罪', \
                        '西部', '奇幻', '冒险', '灾难', '武侠', '古装', '运动', '黑色电影']
                        for n in range(len(strlist)):
                                pattern = re.compile(strlist[n])
                                res = pattern.search(match_res)
                                if res == None:
                                    #print strlist[n] + ":0"
                                    torrent_file.write(strlist[n] + ":0" + '\n')
                                else:
                                    #print strlist[n] + ":1"
                                    torrent_file.write(strlist[n] + ":1" + '\n')
                    if k==1:
                        match_res = re.sub(r"年　　代.*(\w.{3})<.*", "\g<1>", match)
                        torrent_file.write("年代:"+match_res+'\n')
                        #print match_res
                    if k==2:
                        countryPattern = re.compile(r"国　　家　(?P<country>.+?)<.*")
                        if countryPattern.search(match) == None:
                            continue
                        match_res = countryPattern.search(match).group("country")
                        torrent_file.write("国家:"+match_res+'\n')
                        #print match_res
                    if k==3:
                        langPattern = re.compile(r"语　　言　(?P<language>.+?)<.*")
                        if langPattern.search(match) == None:
 