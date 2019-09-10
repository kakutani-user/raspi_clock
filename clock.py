#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys, os
import tkinter as tk
from tkinter import font
import webbrowser
import requests
from datetime import datetime
import time
from bs4 import BeautifulSoup
# from googletrans import Translator
import concurrent.futures
import wave
import pyaudio
from PIL import Image, ImageTk

#raspi_clockまでのパス
path = '/home/pi/raspi_clock'
bgcolor = '#a563f8' #'#13290B'
fgcolor = '#f7e8ff' #'#D3F7C6'

executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)

#GUI設定
root = tk.Tk()
# スクリーンサイズを取得
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
root.overrideredirect(1)
root.configure(bg=bgcolor)
root.title(u"Clock")
root.geometry(str(screen_width)+"x"+str(screen_height))
root.geometry("%dx%d+0+0" % (screen_width, screen_height))
root.focus_set()

root.bind("<Escape>", lambda e: e.widget.quit())

# キャンバスの設定
canvas = tk.Canvas(root, width=screen_width, height=screen_height, bg=bgcolor)
canvas.place(x=0,y=0)

margin_width = screen_width/20
margin_height = screen_height/20
# 枠線
canvas.create_rectangle(margin_width, margin_height, screen_width-margin_width, screen_height-margin_height, width=margin_height/10,outline=fgcolor)

# 日付と時刻の横線
canvas.create_line(margin_width, margin_height*5, screen_width-margin_width, margin_height*5, width=margin_height/15, fill=fgcolor)
# 時刻と天気気温の横線
canvas.create_line(margin_width, margin_height*11, screen_width-margin_width, margin_height*11, width=margin_height/15, fill=fgcolor)
# 気温と降水確率の横線
canvas.create_line(margin_width*(23/5), margin_height*13, screen_width-margin_width, margin_height*13, width=margin_height/15, fill=fgcolor)
# 降水確率の横線
canvas.create_line(margin_width*(23/5), margin_height*(29/2), screen_width-margin_width, margin_height*(29/2), width=margin_height/20, fill=fgcolor)
# 降水確率と風向きの横線
canvas.create_line(margin_width*(23/5), margin_height*17, screen_width-margin_width, margin_height*17, width=margin_height/15, fill=fgcolor)

# 時間の縦線
canvas.create_line(margin_width*6, margin_height*5, margin_width*6, margin_height*11, width=margin_height/20, fill=fgcolor)
canvas.create_line(margin_width*8, margin_height*5, margin_width*8, margin_height*11, width=margin_height/20, fill=fgcolor)
canvas.create_line(margin_width*13, margin_height*5, margin_width*13, margin_height*11, width=margin_height/20, fill=fgcolor)
canvas.create_line(margin_width*15, margin_height*5, margin_width*15, margin_height*11, width=margin_height/20, fill=fgcolor)
# 天気と降水確率の縦線
canvas.create_line(margin_width*(23/5), margin_height*11, margin_width*(23/5), margin_height*19, width=margin_height/15, fill=fgcolor)
# 降水確率の縦線
canvas.create_line(margin_width*(187/25), margin_height*13, margin_width*(187/25), margin_height*17, width=margin_height/20, fill=fgcolor)
canvas.create_line(margin_width*(259/25), margin_height*13, margin_width*(259/25), margin_height*17, width=margin_height/20, fill=fgcolor)
canvas.create_line(margin_width*(331/25), margin_height*13, margin_width*(331/25), margin_height*17, width=margin_height/20, fill=fgcolor)
canvas.create_line(margin_width*(403/25), margin_height*13, margin_width*(403/25), margin_height*17, width=margin_height/20, fill=fgcolor)
# 最高気温と最低気温の縦線
canvas.create_line(margin_width*(59/5), margin_height*11, margin_width*(59/5), margin_height*13, width=margin_height/20, fill=fgcolor)

# 画像の取得
img = Image.open(path + '/img/okayu.png')
img = img.resize((int(margin_height*5), int(margin_height*5)))
img.save(path+'/img/okayu_modi.png')
imgtk = ImageTk.PhotoImage(file=path+'/img/okayu_modi.png')
canvas.create_image(margin_width*17, margin_height*8, image=imgtk)

class AudioPlayer:
    
    def __init__(self):
        self.paused = 0

    def PlayWavFie(self, Filename = "test.wav"):
        try:
            wf = wave.open(Filename, "r")
        except FileNotFoundError: #ファイルが存在しなかった場合
            print("[Error 404] No such file or directory: " + Filename)
            return 0
        # 他の音が再生されていたら停止
        self.paused = 1
            
        # PyAudioのインスタンスを生成 (1)
        p = pyaudio.PyAudio()

        # 再生用のコールバック関数を定義 (2)
        def callback(in_data, frame_count, time_info, status):
            data = wf.readframes(frame_count)
            return (data, pyaudio.paContinue)

        # Streamを生成(3)
        stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                        channels=wf.getnchannels(),
                        rate=wf.getframerate(),
                        output=True,
                        stream_callback=callback)

        # Streamをつかって再生開始 (4)
        stream.start_stream()

        # 再生中はひとまず待っておきます (5)
        self.paused = 0
        while stream.is_active():
            if self.paused:
                self.paused = 0
                break
            time.sleep(0.1)

        # 再生が終わると、ストリームを停止・解放 (6)
        stream.stop_stream()
        stream.close()
        wf.close()

        # close PyAudio (7)
        p.terminate()

    def stopWavFlag(self):
        self.paused = 1

audioplayer = AudioPlayer()
timeplayer = AudioPlayer()


def update_canvas():
    #canvas.update()
    update_time()
    root.after(250, update_canvas)


def update_time():
    now = datetime.today()
    font_date = font.Font(family='Helvetica', size=int(margin_width*0.9))
    font_timenum = font.Font(family='Helvetica', size=int(margin_width*1.7))
    font_second = font.Font(family='Helvetica', size=int(margin_width))
    
    canvas.delete('date')
    datenow = now.strftime('%Y/%m/%d')
    week = ['Mon', 'Tue', 'Wed', 'Tue', 'Fri', 'Sat', 'Sun']
    datenow += ' (' + week[now.weekday()] + ')'
    canvas.create_text(margin_width*10, margin_height*3.2,text=datenow, tag='date', fill=fgcolor, font=font_date)
    
    canvas.delete('time')
    s_hour = '{0:0>2d}'.format(now.hour)
    canvas.create_text(margin_width*3.5, margin_height*8.2, text=s_hour, tag='time',fill=fgcolor, font=font_timenum)
    s_minute = '{0:0>2d}'.format(now.minute)
    canvas.create_text(margin_width*10.5, margin_height*8.2, text=s_minute, tag='time', fill=fgcolor, font=font_timenum)
    s_second =  '{0:0>2d}'.format(now.second)
    canvas.create_text(margin_width*14, margin_height*9.2, text=s_second, tag='time', fill=fgcolor, font=font_second)
    canvas.create_text(margin_width*7, margin_height*7.9, text=':', tag='time', fill=fgcolor, font=font_timenum)
    
    if now.minute == 0 and now.second == 0:
        executor.submit(update_weather)
    elif now.minute == 0 and now.second == 5:
        filename = path+'/music/time'+ str(now.hour) + '.wav'
        executor.submit(timeplayer.PlayWavFie, filename)


def update_weather():
    # 天気予報の取得
    #tenki.jpの目的の地域のページのURL(岐阜県岐阜市)
    url = 'https://tenki.jp/forecast/5/24/5210/21201/'

    #HTTPリクエスト
    req = requests.get(url)

    #プロキシ環境下の場合は以下を記述
    """
    proxies = {
        #自分のプロキシのアドレスを記述
        "http":"http://proxy.xxx.xxx.xxx:8080",
        "https":"http://proxy.xxx.xxx.xxx:8080"
    }
    req = requests.get(url, proxies=proxies)
    """

    bsObj = BeautifulSoup(req.content, "html.parser")
    canvas.delete('weather')

    today = bsObj.find(class_="today-weather")

    # translator = Translator()

    font_weather = font.Font(family='Helvetica', size=int(margin_width*0.5))
    weather = today.p.string
    
    #weather_trans = translator.translate(weather, src='ja', dest='en')
    #weather = (weather_trans.text).split()

    for i in range(len(weather)):
        canvas.create_text(margin_width*(14/5), margin_height*(12+i*2), text=weather[i], tag='weather', fill=fgcolor, font=font_weather)

    temp = today.div.find(class_="date-value-wrap")
    temp = temp.find_all("dd")
    temp_max = temp[0].span.string
    temp_min = temp[2].span.string
    temp_max_dif = temp[1].string
    temp_min_dif = temp[3].string

    temp_max_str = '最高気温 : ' + temp_max + '℃ ' + temp_max_dif
    temp_min_str = '最低気温 : ' + temp_min + '℃ ' + temp_min_dif

    font_temp = font.Font(family='Helvetica', size=int(margin_width*0.5))
    canvas.create_text(margin_width*(41/5), margin_height*12, text=temp_max_str, tag='weather', fill=fgcolor, font=font_temp)
    canvas.create_text(margin_width*(77/5), margin_height*12, text=temp_min_str, tag='weather', fill=fgcolor, font=font_temp)
    
    rain = today.find_all('td')
    font_rain = font_temp = font.Font(family='Helvetica', size=int(margin_width*0.35))
    canvas.create_text(margin_width*(151/25), margin_height*(55/4), text='時', tag='weather', fill=fgcolor, font=font_rain)
    canvas.create_text(margin_width*(151/25), margin_height*(63/4), text='確率', tag='weather', fill=fgcolor, font=font_rain)
    for i in range(4):
        time_s = '{0:0>2d}'.format(i*6)
        canvas.create_text(margin_width*((223+72*i)/25), margin_height*(55/4), text=time_s, tag='weather', fill=fgcolor, font=font_rain)
        percent_s = rain[i].text
        canvas.create_text(margin_width*((223+72*i)/25), margin_height*(63/4), text=percent_s, tag='weather', fill=fgcolor, font=font_rain)

    wind_s = rain[4].text
    canvas.create_text(margin_width*(59/5), margin_height*18, text=wind_s, tag='weather', fill=fgcolor, font=font_temp)


def endup(event):
    audioplayer.stopWavFlag()
    timeplayer.stopWavFlag()
    root.quit()

# 終了ボタンを作成
end_button = tk.Button(text=u"x", fg=fgcolor, bg=bgcolor)
end_button.bind("<Button-1>", endup)
end_button.place(x=screen_width-margin_width+5, y=5)

def play_music(event, filename):
    executor.submit(audioplayer.PlayWavFie, filename)
def stop_music(event, player):
    player.stopWavFlag()
    
# ボイスボタン
play_voice_btn1 = tk.Button(text=u'羊', fg=fgcolor, bg=bgcolor)
filename = path+'/music/hituzi.wav'
play_voice_btn1.bind("<Button-1>", lambda event, arg=filename: play_music(event, arg))
play_voice_btn1.place(x=screen_width-margin_width+2, y=margin_height*2)
play_voice_btn2 = tk.Button(text=u'罵', fg=fgcolor, bg=bgcolor)
filename = path+'/music/batou.wav'
play_voice_btn2.bind("<Button-1>", lambda event, arg=filename: play_music(event, arg))
play_voice_btn2.place(x=screen_width-margin_width+2, y=margin_height*4)
play_voice_btn3 = tk.Button(text=u'悲', fg=fgcolor, bg=bgcolor)
filename = path+'/music/koutei.wav'
play_voice_btn3.bind("<Button-1>", lambda event, arg=filename: play_music(event, arg))
play_voice_btn3.place(x=screen_width-margin_width+2, y=margin_height*6)
stop_voice_btn4 = tk.Button(text=u'■', fg=fgcolor, bg=bgcolor)
stop_voice_btn4.bind("<Button-1>",  lambda event, arg=audioplayer: stop_music(event, arg))
stop_voice_btn4.place(x=screen_width-margin_width+2, y=margin_height*8)


executor.submit(update_canvas)
update_weather()
root.mainloop()
