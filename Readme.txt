关于本项目
==========
本项目是基于TCP/IP的socket编程的FTP文件传输系统，包括FTP服务器与客户端。其中客户端使用PyQt的GUI框架。

#作者
张敏 5140219246

#依赖关系
PyQt4.x

#使用方法
```bash
$./modify
$gnome-terminal
$./server
$./clientGui
```

>注意：
0.执行./server前先执行./modify，用于修正账户中文件夹的绝对路径。
1.在server.py中键入Y进入设置模式，键入N进入通信模式。
2.FTP服务器默认端口号为9000，默认FTP路径为127.0.0.1。其中FTP路径可以修改成本地IP地址。
3.原始登录账号root，密码root；账号Michelle，密码public；以及匿名登录。

#平台
该FTP文件传输系统可以在Linux操作系统下运行。
