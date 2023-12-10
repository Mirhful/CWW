import PyQt5
import pygismeteo
import datetime
import time
from threading import Timer
import math
import sys
import os
import sqlite3
import requests
from PyQt5 import uic
from PyQt5 import QtGui, QtWidgets, QtCore
from PyQt5.QtGui import QKeyEvent, QIcon, QPixmap, QFont, QImage
from PyQt5.QtCore import Qt, QSize, QCoreApplication
from PyQt5.QtWidgets import QApplication, QDialog, QMainWindow, QLabel, QLineEdit, QPushButton, QSystemTrayIcon, \
    QWidget, QAction, QMenu, qApp, QMessageBox, QFileDialog, QComboBox
import resources.images.wtf
import resources.icons.work_icons

from pyfiglet import Figlet


# import datetime as dt
# import pendulum


def application():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    # settings_window = Settings_Widget()
    # forecast_window = Forecast_Widget()
    # options = Options()
    # tray = Tray_menu()
    # tray.check_start_is_first()
    sys.exit(app.exec_())


def get_info_by_ip(ip='127.0.0.1'):
    try:
        response = requests.get(url=f'http://ip-api.com/json/{ip}').json()
        # print(response)
        data = {'[IP]': response.get('query'),
                '[Int prov]': response.get('isp'),
                '[Org]': response.get('org'),
                '[Country]': response.get('country'),
                '[Country Code]': response.get('countryCode'),
                '[Region Name]': response.get('regionName'),
                '[City]': response.get('city'),
                '[ZIP]': response.get('zip'),
                '[Time Zone]': response.get('timezone'),
                '[Lat]': response.get('lat'),
                '[Lon]': response.get('lon'),
                }
        # for k, v in data.items():
        #     print(f'{k} : {v}')
        return data
    except requests.exceptions.ConnectionError:
        return Exception()
        print('[!] Проверьте, пожалуйста, ваше интернет-соединение!')


class My_Gismeteo:
    def __init__(self, geo_data):
        self.gismeteo = pygismeteo.Gismeteo()
        self.geo_data = geo_data
        self.search_results = self.gismeteo.search.by_query(self.geo_data['[City]'])
        self.city_id = self.search_results[0].id
        self.data_current = self.gismeteo.current.by_id(self.city_id)
        self.data_step24 = self.gismeteo.step24.by_id(self.city_id, days=7)


class Forecast_Widget(QMainWindow):
    def __init__(self, path="UI/Forecast_Widget.ui"):
        super().__init__()
        self.path_ui = path
        uic.loadUi(self.path_ui, self)
        self.setFixedSize(self.width(), self.height())
        self.gismeteo = My_Gismeteo(geo_data)
        # self.changeBackground()
        # self.gismeteo = Gismeteo()
        # if options.dict_options['path_ui'] != "UI/Forecast_Widget2.ui":
        #     self.show_current_time()

    def get_weather(self, mode=''):
        if mode == 'current_weather':
            weather_data = self.gismeteo.current.by_id(self.city_id)
        elif mode == '7days_weather':
            weather_data = self.gismeteo.step24.by_id(self.city_id, days=7)
        return weather_data

    def update_data_screen(self):
        match self.path:
            case "UI/Forecast_Widget_new.ui":
                self.set_labels_days()
            case "UI/Forecast_Widget2_new.ui":
                self.set_labels_days()
            case "UI/Forecast_Widget3_new.ui":
                self.set_labels_days()

    def set_labels_days(self):
        days_of_week = datetime.datetime.now()
        rus_days_full = {'Monday': 'Понедельник', 'Tuesday': 'Вторник', 'Wednesday': 'Среда', \
                         'Thursday': 'Четверг', 'Friday': 'Пятница', 'Saturday': 'Суббота', \
                         'Sunday': 'Воскресенье'}
        cur_day = days_of_week.strftime("%A")
        self.lbl_day.setText(rus_days_full[cur_day])
        rus_days = ['Вск', 'Пнд', 'Втр', 'Срд', 'Чтв', 'Птн', 'Сбт']
        cur_num_day = int(days_of_week.strftime('%w'))
        rus_days = rus_days[cur_num_day + 1::] + rus_days[:cur_num_day + 1:]
        self.lbl_day2.setText(rus_days[0])
        self.lbl_day3.setText(rus_days[1])
        self.lbl_day4.setText(rus_days[2])
        self.lbl_day5.setText(rus_days[3])

    def showEvent(self, event):
        self.update_data_screen()

# class Options:
#     def __init__(self):
#         self.dict_options = {'place': '', 'unit': '', 'path_ui': '', 'path_wp': ''}
#         if not self.create_db():
#             QMessageBox.critical(settings_window, 'Критическая ошибка', "Не удалось создать базу данных",
#                                  QMessageBox.Close)
#             sys.exit()
#
#     def set_options(self, key='default', value=''):  # нужно сделать загрузку из db
#         if key == 'default':
#             self.dict_options['place'] = 'Москва'
#             self.dict_options['unit'] = 'c'
#             self.dict_options['path_ui'] = 'UI/Forecast_Widget.ui'
#             self.dict_options['path_wp'] = ''
#             txt_sql = f"""
#                                 UPDATE options
#                                 SET value = 'Москва'
#                                 WHERE key = 'place';
#                                 UPDATE options
#                                 SET value = 'c'
#                                 WHERE key = 'unit';
#                                 UPDATE options
#                                 SET value = 'UI/Forecast_Widget.ui'
#                                 WHERE key = 'path_ui';
#                                 UPDATE options
#                                 SET value = ''
#                                 WHERE key = 'path_wp'
#                                 """
#             print(txt_sql)
#             self.cursor.executescript(txt_sql).fetchall()
#         else:
#             if value in self.dict_options.items():
#                 self.dict_options[value] = key
#             txt_sql = f"""
#                     UPDATE options
#                     SET value = '{value}'
#                     WHERE key = '{key}'
#                     """
#             print(txt_sql)
#             self.cursor.executescript(txt_sql).fetchall()
#             self.get_options()
#
#     def get_options(self):
#         self.get_options_from_db()
#         print(self.dict_options)
#         return self.dict_options
#
#     def create_db(self):
#         try:
#             self.db = sqlite3.connect("cww.db")
#             self.cursor = self.db.cursor()
#             txt_sql = """
#             CREATE TABLE IF NOT EXISTS temperature (
#                 place_id          INTEGER  NOT NULL
#                                            REFERENCES places (place_id),
#                 temperature_min_c INTEGER,
#                 temperature_max_c INTEGER,
#                 data              DATETIME,
#                 UNIQUE(place_id, data)
#             );
#             """
#             self.cursor.execute(txt_sql).fetchall()
#             txt_sql = """
#             CREATE TABLE IF NOT EXISTS places (
#                 place_id   INTEGER UNIQUE
#                                    PRIMARY KEY AUTOINCREMENT
#                                    NOT NULL
#                                    REFERENCES temperature (place_id),
#                 place_name STRING
#             );
#             """
#             self.cursor.execute(txt_sql).fetchall()
#             txt_sql = """
#             CREATE TABLE IF NOT EXISTS options (
#                 key STRING (15),
#                 value STRING
#             );
#             INSERT INTO options(key, value)
#             SELECT 'units', 'c'
#             WHERE NOT EXISTS (SELECT 1 FROM options WHERE key = 'units' AND value IS NOT NULL);
#
#             INSERT INTO options(key, value)
#             SELECT 'place', ''
#             WHERE NOT EXISTS (SELECT 1 FROM options WHERE key = 'place' AND (value IS NOT NULL OR value != ''));
#
#             INSERT INTO options(key, value)
#             SELECT 'path_ui', 'UI/Forecast_Widget.ui'
#             WHERE NOT EXISTS (SELECT 1 FROM options WHERE key = 'path_ui' AND (value IS NOT NULL OR value != ''));
#
#             INSERT INTO options(key, value)
#             SELECT 'path_wp', ''
#             WHERE NOT EXISTS (SELECT 1 FROM options WHERE key = 'path_wp' AND value IS NOT NULL);
#             """
#             self.cursor.executescript(txt_sql).fetchall()
#             self.db.commit()
#             return True
#         except Exception as e:
#             print(e)
#             return False
#
#     def get_options_from_db(self):
#         txt_sql = """
#                 SELECT value FROM options
#                 WHERE key == 'place' AND value IS NOT NULL
#                 """
#         res = self.cursor.execute(txt_sql).fetchone()
#         if len(res[0]) > 0:
#             self.dict_options['place'] = res[0]
#
#         txt_sql = """
#                 SELECT value FROM options
#                 WHERE key == 'units' AND value IS NOT NULL
#                 """
#         res = self.cursor.execute(txt_sql).fetchone()
#         print(res)
#         if len(res[0]) > 0:
#             self.dict_options['unit'] = res[0]
#
#         txt_sql = """
#                 SELECT value FROM options
#                 WHERE key == 'path_ui' AND value IS NOT NULL
#                 """
#         res = self.cursor.execute(txt_sql).fetchone()
#         print(res)
#         if len(res[0]) > 0:
#             self.dict_options['path_ui'] = res[0]
#
#         txt_sql = """
#                 SELECT value FROM options
#                 WHERE key == 'path_wp' AND value IS NOT NULL
#                 """
#         res = self.cursor.execute(txt_sql).fetchone()
#         print(res)
#         if len(res[0]) > 0:
#             self.dict_options['path_wp'] = res[0]


if __name__ == '__main__':
    preview_text = Figlet(font='slant')
    print(preview_text.renderText('IP INFO'))
    ip = input('Пожалуйста, введите ваш ip адрес: ')
    geo_data = get_info_by_ip(ip=ip)
    application()
    # options = Options()
    # options.get_options()
    # tray = Tray_menu()
    # settings_window = Settings_Widget()
    # forecast_window = Forecast_Widget()
    # tray.check_start_is_first()
