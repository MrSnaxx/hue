import copy
from sys import argv

import numpy as np
from PIL import Image
from PyQt5 import QtWidgets, Qt
from PyQt5.QtGui import QPixmap, QPainter, QColor
from PyQt5.QtWidgets import QFileDialog, QMessageBox
from pyqtgraph import SignalProxy
from PyQt5 import uic
# from converted_ui import Ui_MainWindow
import pyqtgraph as pg

Ui_MainWindow,_ = uic.loadUiType("hue/interface.ui")
class Redactor(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self):
        super(Redactor, self).__init__()
        self.setupUi(self)
        self.img = None
        self.image_view = pg.ImageView()
        self.image_layout.addWidget(self.image_view)
        self.image_view.ui.histogram.hide()
        self.image_view.ui.roiBtn.hide()
        self.image_view.ui.menuBtn.hide()
        self.n = 13
        self.create_square(self.n, 1)
        self.square_item = pg.ImageItem(self.square, axisOrder="row-major")
        self.image_view.addItem(self.square_item)
        self.load_image_action.triggered.connect(self.load_image)
        self.save_image_action.triggered.connect(self.save_image)
        self.rp=self.redHist.addPlot()
        self.gp = self.greenHist.addPlot()
        self.bp = self.blueHist.addPlot()

    def make_hists(self, ):
        pass

    def load_image(self):
        self.image_view.clear()
        filename = QFileDialog.getOpenFileName(self, "Загрузка изображения", "", "Image (*.png *.tiff *.bmp)")
        if filename[0] == "":
            QMessageBox.about(self, "Ошибка", "Файл не выбран")
            return
        filepath = filename[0]
        self.img = Image.open(filepath)
        print(type(self.img))
        # Преобразование изображения в массив numpy
        img_array = np.flipud(np.rot90(np.array(self.img)))
        # Вычисляем среднее значение интенсивности для каждого пикселя
        intensity = np.mean(img_array, axis=2)
        # # Создаем чёрно-белое изображение, повторяя массив интенсивности для каждого канала
        #
        # img_array = np.stack((intensity, intensity, intensity), axis=2)
        self.img = img_array
        self.img_original = copy.deepcopy(self.img)
        self.img_height = img_array.shape[1]
        self.img_width = img_array.shape[0]
        # Отображение изображения в ImageView
        self.image_view.setImage(img_array)
        self.image_view.getView().setMouseEnabled(x=False, y=False)
        self.proxy = SignalProxy(self.image_view.scene.sigMouseMoved, rateLimit=60, slot=self.mouseMoved)

        self.get_red_negation.stateChanged.connect(self.update_view)
        self.get_green_negation.stateChanged.connect(self.update_view)
        self.get_blue_negation.stateChanged.connect(self.update_view)
        self.get_brightness_negation.stateChanged.connect(self.update_view)
        self.red_intensity.valueChanged.connect(self.update_view)
        self.green_intensity.valueChanged.connect(self.update_view)
        self.blue_intensity.valueChanged.connect(self.update_view)
        self.brightness_intensity.valueChanged.connect(self.update_view)
        # Рисование квадрата на ImageView
        #self.image_view.getView().scene().sigMouseClicked.connect()

    def create_square(self, n, w=5):
        self.square = []
        for _ in range(w):
            self.square.append([[255, 255, 255, 255]] * n)
        for _ in range(n - 2 - (w - 1) * 2):
            self.square.append(
                [[255, 255, 255, 255]] * (w) + [[0, 0, 0, 0]] * (n - 2 - (w - 1) * 2) + [[255, 255, 255, 255]] * (w))
        for _ in range(w):
            self.square.append([[255, 255, 255, 255]] * n)
        self.square = np.array(self.square)

    def mouseMoved(self, e):
        plot_pos = self.image_view.getView().mapToView(e[0])
        upper_border = plot_pos.y() - self.n//2 >= 0
        left_border = plot_pos.x() - self.n//2 >= 0
        right_border = plot_pos.x() + self.n//2 <= self.img_width
        bottom_border = plot_pos.y() + self.n // 2 <= self.img_height

        check_borders = upper_border and left_border and right_border and bottom_border
        if check_borders:
            self.square_item.setRect(pg.QtCore.QRectF(plot_pos.x()-self.n//2, plot_pos.y()-self.n//2, self.n, self.n))

        elif right_border and upper_border and bottom_border:
            self.square_item.setRect(
                pg.QtCore.QRectF(0, plot_pos.y() - self.n // 2, self.n, self.n))

        elif left_border and upper_border and bottom_border:
            self.square_item.setRect(
                pg.QtCore.QRectF(self.img_width - self.n, plot_pos.y() - self.n // 2, self.n, self.n))

        elif right_border and left_border and bottom_border:
            self.square_item.setRect(
                pg.QtCore.QRectF(plot_pos.x()-self.n//2, 0, self.n, self.n))

        elif left_border and right_border and upper_border:
            self.square_item.setRect(
                pg.QtCore.QRectF(plot_pos.x() - self.n // 2, self.img_height - self.n,  self.n, self.n))

    def save_image(self):
        if self.img is None:
            QMessageBox.about(self, "Ошибка", "Нечего сохранять")
            return
        filename = QFileDialog.getSaveFileName(self, "Open Image", "hue", "Image Files (*.png *.tiff *.bmp)")
        print(filename)
        if filename[0] == "":
            QMessageBox.about(self, "Ошибка", "Путь сохранения не выбран")
            return
        self.image_view.getImageItem().save(filename[0])

    def change_brightness(self):
        brightness = self.brightness_intensity.value()
        self.img[:, :, 3] = brightness

    def change_color_intensity(self, sender=None):
        if sender is None:
            sender = self.sender()
        if sender == "red_intensity":
            intensity = self.red_intensity.value() / 10
            channel = 0
        elif sender == "green_intensity":
            intensity = self.green_intensity.value() / 10
            channel = 1
        elif sender == "blue_intensity":
            intensity = self.blue_intensity.value() / 10
            channel = 2
        else:
            intensity = 0
            channel = 0
        self.img[:, :, channel] = np.clip(self.img[:, :, channel] * intensity, 1, 255)


    def negate_rgb(self, channel=None):
        if channel == "red":
            self.img[:, :, 0] = 255 - self.img[:, :, 0]
        elif channel == "green":
            self.img[:, :, 1] = 255 - self.img[:, :, 1]
        elif channel == "blue":
            self.img[:, :, 2] = 255 - self.img[:, :, 2]
        else:
            self.img[:, :, 0:3] = np.array([255, 255, 255]) - self.img[:, :, 0:3]


    def update_view(self):
        self.img = copy.deepcopy(self.img_original)
        if self.get_red_negation.isChecked():
            self.negate_rgb("red")
        if self.get_green_negation.isChecked():
            self.negate_rgb("green")
        if self.get_blue_negation.isChecked():
            self.negate_rgb("blue")
        if self.get_brightness_negation.isChecked():
            self.negate_rgb()
        self.change_color_intensity("red_intensity")
        self.change_color_intensity("green_intensity")
        self.change_color_intensity("blue_intensity")
        self.change_brightness()
        self.image_view.clear()
        self.image_view.setImage(self.img)

if __name__ == "__main__":
    application = QtWidgets.QApplication(argv)
    program = Redactor()
    program.show()
    exit(application.exec_())
