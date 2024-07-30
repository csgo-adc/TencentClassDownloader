## TencentClassDownloader
腾讯课堂视频下载脚本

## 开始
### 1、配置环境
运行环境 Python3

#### 安装依赖
```
pip install -r requirements.txt
```

### 2、获取cookie
以谷歌浏览器为例，打开腾讯视频并登陆，键盘F12，找到network——点击Doc（如果没有数据，刷新一下界面），找到cookie等信息，拷贝粘贴到目录下的cookie文件中


### 3、配置conf
修改目录中到config.conf文件，

```
[QQ] # 你当前课程所属的QQ号
number = 123456789

[url] # 课程链接，一定要按照 https://ke.qq.com/webcourse/xxxxx/xxxxx形式粘贴
url = https://ke.qq.com/webcourse/12345678/123456789

[process] # 下载视频的线程数，视你电脑能力而定，可以尽量多开一些
process_num = 8

[output] # 下载视频存放的路径
save_path = D:\\txktDownload\

[clarity] # 清晰度，目前只设置了 1 2 3 三种，其中 1 为最清晰， 3为最不清晰， 2为两者之间， 实际情况看你的课程支持哪些清晰度。
clarity = 1
```


### 4、运行main.py
```
python3 main.py
```
等着下载完成就可以了，下载过的视频会自动跳过，如需重新下载请删除原来的视频。
