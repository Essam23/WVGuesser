# new widevine-l3-guesser is faster more than this version

https://github.com/Satsuoni/widevine-l3-guesser

---

# WVGuesser

`WVGuesser`是[widevine-l3-guesser](https://github.com/Satsuoni/widevine-l3-guesser)的离线版本实现

# 使用

## 插件安装

解压`WVGuesser-plugin.zip`，然后`加载已解压的扩展程序`

打开使用widevine的网站，播放视频后会自动下载一个配置文件

即`offline_config.json`，把它放到当前目录下即可

如果只是测试，可以跳过这一步，已经内置了一个配置文件了

## 本地破解

如果是exe版本，直接将`offline_config.json`拖到`wvguesser_v1.5.0.exe`上即可

运行程序，等待解密

- `python -m wvguesser.main`

or

- `python -m wvguesser.main offline_config.json`

历史结果将保存至`wvkeys.txt`，最新的key在最前面

根据现有算法，只能是单线程

效果演示，3600X 175s左右出结果

![](/images/oCam_2021_07_31_05_10_50_756.gif)

# main.exe

该程序是辅助程序，不是主程序

- Linux直接使用g++编译
- Windows使用mingw64编译

```bash
g++ -o main -pthread -std=gnu++0x -static main.cpp misc.cpp codelift.cpp algebra.cpp allocate.cpp integer.cpp
```

# 打包

```bash
pyinstaller -n wvguesser_v1.5.0 -F wvguesser\__main__.py
```

# 推荐更好的方案

~~不太会C++所以就用了python~~

- 纯C++完成调用