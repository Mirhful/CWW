import datetime

import PyQt5
import math
import sys
import datetime as dt
import time
# import pendulum
import sqlite3
from PyQt5 import uic
from PyQt5 import QtGui, QtWidgets, QtCore
from PyQt5.QtGui import QKeyEvent, QIcon, QPixmap, QFont, QImage
from PyQt5.QtCore import Qt, QSize, QCoreApplication
from PyQt5.QtWidgets import QApplication, QDialog, QMainWindow, QLabel, QLineEdit, QPushButton, QSystemTrayIcon, \
    QWidget, QAction, QMenu, qApp, QMessageBox, QFileDialog, QComboBox
from pygismeteo import Gismeteo
from threading import Timer
import os
import resources.images.wtf
import resources.icons.work_icons


class CbUnit(QComboBox):
    def __init__(self, wg):
        super().__init__(wg)
        self.move(240, 212)
        self.resize(52, 36)
        self.setEditText("Укажите градусы Цельсия или Фаренгейта")
        self.insertItem(0, '°C')
        self.insertItem(1, '℉')
        self.setStyleSheet(f"background: #FFFFFF;\nborder: 2px solid #000000")

        self.currentIndexChanged.connect(self.index_changed)

    def index_changed(self, index):
        if index == 0:
            options.set_options('units', 'c')
        elif index == 1:
            options.set_options('units', 'f')


class Options:
    def __init__(self):
        self.dict_options = {'place': '', 'unit': '', 'path_ui': '', 'path_wp': ''}
        if not self.create_db():
            QMessageBox.critical(settings_window, 'Критическая ошибка', "Не удалось создать базу данных",
                                 QMessageBox.Close)
            sys.exit()

    def set_options(self, key='default', value=''):  # нужно сделать загрузку из db
        if key == 'default':
            self.dict_options['place'] = 'Москва'
            self.dict_options['unit'] = 'c'
            self.dict_options['path_ui'] = 'UI/Forecast_Widget.ui'
            self.dict_options['path_wp'] = ''
            txt_sql = f"""
                                UPDATE options
                                SET value = 'Москва'
                                WHERE key = 'place';
                                UPDATE options
                                SET value = 'c'
                                WHERE key = 'unit';
                                UPDATE options
                                SET value = 'UI/Forecast_Widget.ui'
                                WHERE key = 'path_ui';
                                UPDATE options
                                SET value = ''
                                WHERE key = 'path_wp'
                                """
            print(txt_sql)
            self.cursor.executescript(txt_sql).fetchall()
        else:
            if value in self.dict_options.items():
                self.dict_options[value] = key
            txt_sql = f"""
                    UPDATE options
                    SET value = '{value}'
                    WHERE key = '{key}'
                    """
            print(txt_sql)
            self.cursor.executescript(txt_sql).fetchall()
            self.get_options()

    def get_options(self):
        self.get_options_from_db()
        print(self.dict_options)
        return self.dict_options

    def create_db(self):
        try:
            self.db = sqlite3.connect("cww.db")
            self.cursor = self.db.cursor()
            txt_sql = """
            CREATE TABLE IF NOT EXISTS temperature (
                place_id          INTEGER  NOT NULL
                                           REFERENCES places (place_id),
                temperature_min_c INTEGER,
                temperature_max_c INTEGER,
                data              DATETIME,
                UNIQUE(place_id, data)
            );
            """
            self.cursor.execute(txt_sql).fetchall()
            txt_sql = """
            CREATE TABLE IF NOT EXISTS places (
                place_id   INTEGER UNIQUE
                                   PRIMARY KEY AUTOINCREMENT
                                   NOT NULL
                                   REFERENCES temperature (place_id),
                place_name STRING
            );
            """
            self.cursor.execute(txt_sql).fetchall()
            txt_sql = """
            CREATE TABLE IF NOT EXISTS options (
                key STRING (15),
                value STRING
            );
            INSERT INTO options(key, value)
            SELECT 'units', 'c'
            WHERE NOT EXISTS (SELECT 1 FROM options WHERE key = 'units' AND value IS NOT NULL);

            INSERT INTO options(key, value)
            SELECT 'place', ''
            WHERE NOT EXISTS (SELECT 1 FROM options WHERE key = 'place' AND (value IS NOT NULL OR value != ''));

            INSERT INTO options(key, value)
            SELECT 'path_ui', 'UI/Forecast_Widget.ui'
            WHERE NOT EXISTS (SELECT 1 FROM options WHERE key = 'path_ui' AND (value IS NOT NULL OR value != ''));

            INSERT INTO options(key, value)
            SELECT 'path_wp', ''
            WHERE NOT EXISTS (SELECT 1 FROM options WHERE key = 'path_wp' AND value IS NOT NULL);
            """
            self.cursor.executescript(txt_sql).fetchall()
            self.db.commit()
            return True
        except Exception as e:
            print(e)
            return False

    def get_options_from_db(self):
        txt_sql = """
                SELECT value FROM options
                WHERE key == 'place' AND value IS NOT NULL
                """
        res = self.cursor.execute(txt_sql).fetchone()
        if len(res[0]) > 0:
            self.dict_options['place'] = res[0]

        txt_sql = """
                SELECT value FROM options
                WHERE key == 'units' AND value IS NOT NULL
                """
        res = self.cursor.execute(txt_sql).fetchone()
        print(res)
        if len(res[0]) > 0:
            self.dict_options['unit'] = res[0]

        txt_sql = """
                SELECT value FROM options
                WHERE key == 'path_ui' AND value IS NOT NULL
                """
        res = self.cursor.execute(txt_sql).fetchone()
        print(res)
        if len(res[0]) > 0:
            self.dict_options['path_ui'] = res[0]

        txt_sql = """
                SELECT value FROM options
                WHERE key == 'path_wp' AND value IS NOT NULL
                """
        res = self.cursor.execute(txt_sql).fetchone()
        print(res)
        if len(res[0]) > 0:
            self.dict_options['path_wp'] = res[0]


class MyGismeteo:
    def __init__(self):
        self.gismeteo = Gismeteo()
        self.search_results = self.gismeteo.search.by_query(options.get_options()['place'])
        self.city_id = self.search_results[0].id
        self.data_current = self.gismeteo.current.by_id(self.city_id)
        self.data_step24 = self.gismeteo.step24.by_id(self.city_id, days=7)


class City_Input(QLineEdit):
    def __init__(self, wg):
        super().__init__(wg)
        self.move(40, 112)
        self.resize(230, 44)
        self.setStyleSheet("background-color: rgb(255, 255, 255);\nborder: 2px solid #000000;")
        self.check_error = 0
        self.setFocus()

    def keyPressEvent(self, event):
        super().keyPressEvent(event)
        global forecast_window
        k = event.key()
        if k == Qt.Key_Enter or k == Qt.Key_Return:
            if forecast_window.test_input_place(self.displayText()):
                self.check_error = 0
                options.set_options('place', self.displayText())
                # options.dict_options['place'] = self.displayText()
                forecast_window.destroy()
                forecast_window = Forecast_Widget(options.dict_options['path_ui'])
                settings_window.change_window()
                # settings_window.hide()
                # forecast_window.show()
            else:
                self.check_error = 1
                QMessageBox.question(self, 'Ошибка ввода', "Такого места не существует", QMessageBox.Ok)


class Settings_Widget(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("UI/CWW_alpha.ui", self)
        self.cb = CbUnit(self)
        self.cb.show()
        self.place_input = City_Input(self)
        self.window_sizes = [660, 120, 600, 800]
        self.dict_sizes = {(600, 800): "UI/Forecast_Widget.ui", (540, 720): "UI/Forecast_Widget2.ui",
                           (480, 640): "UI/Forecast_Widget3.ui"}
        time_now = dt.datetime.now().strftime("%H:%M")
        self.lblTime.setText(time_now)
        self.start_timer()
        self.run()
        self.btnSetSize1.clicked.connect(lambda _: self.change_forecast_window_size((480, 640)))
        self.btnSetSize2.clicked.connect(lambda _: self.change_forecast_window_size((540, 720)))
        self.btnSetSize3.clicked.connect(lambda _: self.change_forecast_window_size((600, 800)))

    def change_window(self):
        settings_window.hide()
        forecast_window.show()

    def run(self):
        self.setFixedSize(self.window_sizes[2], self.window_sizes[3])
        self.setWindowTitle('Custom Weather Widget')

    def start_timer(self):
        self.t = Timer(60, self.show_current_time)
        self.t.start()

    def show_current_time(self):
        time_now = dt.datetime.now().strftime("%H:%M")
        self.lblTime.setText(time_now)
        self.start_timer()

    def change_forecast_window_size(self, sizes):
        self.set_color_button()
        self.change_forecast_window_size2(sizes)

    def change_forecast_window_size2(self, sizes):
        self.forecast_window_sizes = sizes
        options.set_options('path_ui', self.dict_sizes[sizes])
        if forecast_window.test_input_place(options.get_options()['place']):
            options.set_options('place', self.place_input.displayText())

    def set_color_button(self):
        self.sender().setStyleSheet("""color: #FFE3E3;
                        position: absolute; width: 122px; height: 80px; left: 0.35px; top: 0.53px; font-family: 'Inter';
                        font-style: normal; font-weight: 600; font-size: 20px; line-height: 100%; display: flex;
                        align-items: center; text-align: center; letter-spacing: 0.1em; mix-blend-mode: difference;
                        border: 4px solid #8CE9D8; filter: drop-shadow(0px 0px 20px rgba(250, 237, 190, 0.85));
                        border-radius: 20px;""")
        list_btn = [self.btnSetSize1, self.btnSetSize2, self.btnSetSize3]
        list_btn.remove(self.sender())
        print(list_btn)
        for el in list_btn:
            el.setStyleSheet("""color: #FFE3E3; position: absolute; width: 122px; height: 80px; left: 0.35px;
                            top: 0.53px; font-family: 'Inter';
                            font-style: normal; font-weight: 600; font-size: 20px; line-height: 100%; display: flex;
                            align-items: center; text-align: center; letter-spacing: 0.1em; mix-blend-mode: difference;
                            border: 4px solid #FFE3E3; filter: drop-shadow(0px 0px 20px rgba(250, 237, 190, 0.85));
                            border-radius: 20px;""")

    def keyPressEvent(self, event):
        k = event.key()
        if k == Qt.Key_Escape:
            self.destroy()

    def index_changed(self, index):
        print(index)
        if index == 1:
            options.set_options('units', 'c')
        elif index == 2:
            options.set_options('units', 'f')

    def closeEvent(self, event):
        global forecast_window
        try:
            self.t.cancel()
            forecast_window.t.cancel()
            forecast_window.t_w.cancel()
        except:
            pass
        if not forecast_window.test_input_place(self.place_input.displayText()):
            res = QMessageBox.warning(self, 'Ошибка ввода', "Такого места не существует", QMessageBox.Ok,
                                      QMessageBox.Close)
            if res == QMessageBox.Ok:
                self.place_input.setFocus()
                event.ignore()
        else:
            forecast_window.destroy()
            forecast_window = Forecast_Widget(options.dict_options['path_ui'])
            self.change_window()

    def showEvent(self, event):
        self.place_input.setText(options.dict_options['place'])
        if options.dict_options['unit'] == 'c':
            self.cb.setCurrentIndex(0)
        elif options.dict_options['unit'] == 'f':
            self.cb.setCurrentIndex(1)


class Forecast_Widget(QMainWindow):  # CWW Window
    def __init__(self, path="UI/Forecast_Widget.ui"):
        super().__init__()
        self.path_ui = path
        uic.loadUi(self.path_ui, self)
        self.setFixedSize(self.width(), self.height())
        self.changeBackground()
        self.gismeteo = Gismeteo()
        if options.dict_options['path_ui'] != "UI/Forecast_Widget2.ui":
            self.show_current_time()

    def changeBackground(self):
        if options.get_options()['path_wp'] != '':
            self.lbl_background.setPixmap(QPixmap(options.get_options()['path_wp']))

    def closeEvent(self, event):
        global settings_window
        try:
            self.t.cancel()
            self.t_w.cancel()
            settings_window.t.cancel()
        except:
            pass

    def showEvent(self, event):
        self.get_weather()

    def start_timer(self):
        self.t = Timer(60, self.show_current_time)
        self.t.start()

    def start_weather_timer(self):
        self.t_w = Timer(3600, self.get_weather)
        self.t_w.start()
        tray.change_tray_icon()

    def show_current_time(self):
        time_now = dt.datetime.now().strftime("%H:%M")
        self.lbl_time.setText(time_now)
        self.start_timer()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.change_window()

    def change_window(self):
        print('forecast widget show settings_window and hide self')
        forecast_window.hide()
        settings_window.show()

    def get_weather(self):  # сделать try except и доставать данные из db
        datetime_now = dt.datetime.now()
        description_full = ''
        self.setLabelsDays()
        opt = options.get_options()
        gismeteo = MyGismeteo()
        self.data_current = gismeteo.data_current
        data_step24 = gismeteo.data_step24
        print(data_step24[0].date.local, data_step24[1].date.local)
        print('Selected UI:', options.dict_options['path_ui'])
        if options.dict_options['path_ui'] == "UI/Forecast_Widget3.ui":
            for el in self.data_current.description.full.split()[:-1]:
                description_full += el + '\n'
            description_full += self.data_current.description.full.split()[-1]
            self.lbl_day1.setText(datetime_now.strftime("%A"))
            self.lbl_weather_description.setText(description_full)
            print(self.data_current.description.full)
        else:
            self.lbl_town_name.setText(options.dict_options['place'])
        self.w1.setIcon(QIcon(f"resources/icons/project_icons/{self.data_current.icon}.svg"))
        self.w2.setIcon(QIcon(f"resources/icons/project_icons/{data_step24[1].icon}.svg"))
        self.w3.setIcon(QIcon(f"resources/icons/project_icons/{data_step24[2].icon}.svg"))
        self.w4.setIcon(QIcon(f"resources/icons/project_icons/{data_step24[3].icon}.svg"))
        self.w5.setIcon(QIcon(f"resources/icons/project_icons/{data_step24[4].icon}.svg"))
        if options.dict_options['path_ui'] != "UI/Forecast_Widget.ui":
            self.w6.setIcon(QIcon(f"resources/icons/project_icons/{data_step24[5].icon}.svg"))
            self.w7.setIcon(QIcon(f"resources/icons/project_icons/{data_step24[6].icon}.svg"))
        if opt['unit'] == 'c':
            if options.dict_options['path_ui'] != "UI/Forecast_Widget3.ui":
                self.lbl_temp_day1.setText(f"{round(data_step24[1].temperature.air.min.c)}/"
                                           f"{round(data_step24[1].temperature.air.max.c)}°C")
                self.lbl_temp_day2.setText(f"{round(data_step24[2].temperature.air.min.c)}/"
                                           f"{round(data_step24[2].temperature.air.max.c)}°C")
                self.lbl_temp_day3.setText(f"{round(data_step24[3].temperature.air.min.c)}/"
                                           f"{round(data_step24[3].temperature.air.max.c)}°C")
                self.lbl_temp_day4.setText(f"{round(data_step24[4].temperature.air.min.c)}/"
                                           f"{round(data_step24[4].temperature.air.max.c)}°C")
            self.lbl_temperature.setText(f"{round(self.data_current.temperature.air.c)}°C")
        elif opt['unit'] == 'f':
            if options.dict_options['path_ui'] != "UI/Forecast_Widget3.ui":
                self.lbl_temp_day1.setText(f"{round(data_step24[1].temperature.air.min.f)}/"
                                           f"{round(data_step24[1].temperature.air.max.f)}°F")
                self.lbl_temp_day2.setText(f"{round(data_step24[2].temperature.air.min.f)}/"
                                           f"{round(data_step24[2].temperature.air.max.f)}°F")
                self.lbl_temp_day3.setText(f"{round(data_step24[3].temperature.air.min.f)}/"
                                           f"{round(data_step24[3].temperature.air.max.f)}°F")
                self.lbl_temp_day4.setText(f"{round(data_step24[4].temperature.air.min.f)}/"
                                           f"{round(data_step24[4].temperature.air.max.f)}°F")
            self.lbl_temperature.setText(f"{round(self.data_current.temperature.air.f)}°F")
        else:
            raise ValueError("Неизвестное значение unit")
        if options.dict_options['path_ui'] != "UI/Forecast_Widget2.ui":
            self.start_weather_timer()

    def setLabelsDays(self):
        days_of_week = dt.datetime.now()
        rus_days_full = {'Monday': 'Понедельник', 'Tuesday': 'Вторник', 'Wednesday': 'Среда', \
                         'Thursday': 'Четверг', 'Friday': 'Пятница', 'Saturday': 'Суббота', \
                         'Sunday': 'Воскресенье'}
        cur_day = days_of_week.strftime("%A")
        self.lbl_day1.setText(rus_days_full[cur_day])
        rus_days = ['Вск', 'Пнд', 'Втр', 'Срд', 'Чтв', 'Птн', 'Сбт']
        cur_num_day = int(days_of_week.strftime('%w'))
        rus_days = rus_days[cur_num_day + 1::] + rus_days[:cur_num_day + 1:]
        self.lbl_day2.setText(rus_days[0])
        self.lbl_day3.setText(rus_days[1])
        self.lbl_day4.setText(rus_days[2])
        self.lbl_day5.setText(rus_days[3])

    def test_input_place(self, place):
        try:
            res = self.gismeteo.search.by_query(place)
            if len(res) > 0:
                return True
            else:
                return False
        except Exception as e:
            return False


class Tray_menu:
    def __init__(self):
        self.tray = QSystemTrayIcon(QIcon("resources/icons/gismeteo-icons/new/d_c1.svg"))
        self.menu = QMenu()
        self.menu.addAction('Показать').triggered.connect(self.weather_show)
        self.settings = self.menu.addMenu('Настройки')
        self.settings.addAction('Город/Единицы измерения').triggered.connect(self.settings_show)
        self.settings.addAction('Настройки по умолчанию').triggered.connect(self.set_default)
        self.theme = self.settings.addMenu('Сменить тему')
        self.theme.addAction("Большая тема").triggered.connect(lambda _: self.change_theme('theme_big_1'))
        self.theme.addAction("Средняя тема").triggered.connect(lambda _: self.change_theme('theme_medium_1'))
        self.theme.addAction("Маленькая тема").triggered.connect(lambda _: self.change_theme('theme_small_1'))
        self.settings.addAction('Сменить фон').triggered.connect(self.change_background)
        self.menu.addAction('О программе').triggered.connect(self.show_html_file)
        self.menu.addAction('Выход').triggered.connect(self.close_app)
        self.tray_handler()

    def tray_handler(self):
        self.tray.setContextMenu(self.menu)
        self.tray.setVisible(True)

    def set_default(self):
        options.set_options('default')

    def change_tray_icon(self):
        self.icon = QIcon(f"resources/icons/gismeteo-icons/new/{forecast_window.data_current.icon}")
        self.tray.setIcon(self.icon)

    def weather_show(self):
        global forecast_window
        if forecast_window.test_input_place(options.get_options()['place']):
            forecast_window.destroy()
            forecast_window = Forecast_Widget(options.get_options()['path_ui'])
            print('trash', options.get_options()['path_ui'])
            forecast_window.show()
        else:
            QMessageBox.critical(settings_window, 'Критическая ошибка', "Не удалось создать базу данных",
                                 QMessageBox.Close)

    def settings_show(self):
        print('tray_menu show settings_window')
        settings_window.show()

    def show_html_file(self):
        import webbrowser
        import codecs
        new = 1
        template_read = codecs.open('template.html', 'r', "utf-8", errors='ignore')
        gismeteo = MyGismeteo()
        data = template_read.readlines()
        new_data = ""
        for i in range(len(data)):
            if "@cww_ico_weather" in data[i]:
                new_data += data[i][:data[i].find("@cww_ico_weather")] \
                            + f"resources/icons/gismeteo-icons/new/{gismeteo.data_current.icon}.svg" \
                            + data[i][data[i].find("@cww_ico_weather") + 16:]
            elif "@cww_temp" in data[i]:
                new_data += data[i][:data[i].find("@cww_temp")] \
                            + f"{gismeteo.data_current.temperature.air.c}°C" \
                            + data[i][data[i].find("@cww_temp") + 9:]
            else:
                new_data += data[i]
        html_file = codecs.open("cww_info.html", 'w', "utf-8", errors='ignore')
        html_file.write(new_data)
        print(data)
        template_read.close()
        html_file.close()
        url = "cww_info.html"
        webbrowser.open(url, new=new)

    def change_background(self):
        global forecast_window
        fname = QFileDialog.getOpenFileName(forecast_window, 'Выбрерите изображение', '', \
                                            'Картинка (*.jpg);;Картинка (*.png)')[0]
        file = QPixmap(f"{fname}")
        options.set_options('path_wp', fname)
        forecast_window.destroy()
        forecast_window = Forecast_Widget(options.get_options()['path_ui'])
        forecast_window.lbl_background.setPixmap(file)
        forecast_window.show()

    def close_app(self):
        try:
            settings_window.t.cancel()
            forecast_window.t.cancel()
            forecast_window.t_w.cancel()
        except:
            pass
        settings_window.destroy()
        forecast_window.destroy()
        os._exit(0)

    def check_start_is_first(self):
        options.get_options()
        if len(options.dict_options['place']) < 1:
            settings_window.show()

    def change_theme(self, param):
        global forecast_window
        forecast_window.destroy()
        if param == 'theme_big_1':
            settings_window.change_forecast_window_size2((600, 800))
            forecast_window = Forecast_Widget('UI/Forecast_Widget.ui')
            options.set_options('path_ui', 'UI/Forecast_Widget.ui')
        elif param == 'theme_medium_1':
            settings_window.change_forecast_window_size2((540, 720))
            forecast_window = Forecast_Widget('UI/Forecast_Widget2.ui')
            options.set_options('path_ui', 'UI/Forecast_Widget2.ui')
        elif param == 'theme_small_1':
            settings_window.change_forecast_window_size2((480, 640))
            forecast_window = Forecast_Widget('UI/Forecast_Widget3.ui')
            options.set_options('path_ui', 'UI/Forecast_Widget3.ui')
        forecast_window.show()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    options = Options()
    options.get_options()
    tray = Tray_menu()
    settings_window = Settings_Widget()
    forecast_window = Forecast_Widget()
    tray.check_start_is_first()

    sys.exit(app.exec_())
