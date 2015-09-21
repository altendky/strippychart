#!/usr/bin/env python3

import sys
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5 import QtCore
from PyQt5.QtGui import QPen, QColor
import qcustomplot
from qcustomplot import QCP
import time
import math
from generated.strippychart_ui import Ui_MainWindow
from stream import *

            # from before_replot() to filter down to only visible (+ one each way) data
            # to theoretically be more efficient and to make autoscale-y work on only
            # the visible data
            # continue
            # x_data = []
            # y_data = []
            # last_pair = None
            # for x, y in stream.get():
            #     found_first = False
            #     found_last = False
            #     if self._plot.xAxis.range().contains(x):
            #         if not found_first:
            #             # handle a point off the edge to make sure the plot makes it to the edge
            #             found_first = True
            #             if last_pair is not None:
            #                 x_data.append(last_pair[0])
            #                 y_data.append(last_pair[1])
            #         x_data.append(x)
            #         y_data.append(y)
            #     elif found_first and not found_last:
            #         # one past the last one
            #         found_last = True
            #         x_data.append(x)
            #         y_data.append(y)
            #
            #     last_pair = [x, y]
            #
            # self._plot.graph(index).setData(x_data, y_data)


class Plot(Ui_MainWindow):
    def __init__(self, main_window):
        self.setupUi(main_window)

        self._start = time.monotonic()

        self._streams = []

        self._plot.resize(450, 350)
        self._plot.move(300, 300)
        self._plot.setWindowTitle('Simple')
        self._plot.yAxis.setRange(-1.2, 1.2)

        self._plot.replot()

        self._replot_timer = QtCore.QTimer()
        self._replot_timer.timeout.connect(self._plot.replot)
        self._update_rate = 60
        self._update_period = 1 / self._update_rate
        self.reset_replot_timer()

        self._res = 100
        self._width = 3
        self._plot_range = None
        self.set_range([-self._width, 0])

        self._colors = ['blue', 'red', 'green', 'cyan', 'magenta', 'yellow']

        self._plot.legend.setVisible(True)
        self._plot.setInteraction(QCP.iRangeDrag, True)
        self._plot.beforeReplot.connect(self.before_replot)
        self._plot.afterReplot.connect(self.after_replot)

        # http://www.qcustomplot.com/index.php/tutorials/specialcases/scrollbar
        self.horizontalScrollBar.valueChanged.connect(self.x_scrollbar_changed)
        self._plot.xAxis.rangeChanged.connect(self.x_axis_changed)

        self._plot.show()

    def reset_replot_timer(self):
        self._replot_timer.stop()
        self._replot_timer.start(self._update_period * 1000)

    def x_scrollbar_changed(self, value):
        if abs(self._plot.xAxis.range().lower - value / self._res) > 1 / self._res:
            # if user is dragging plot, we don't want to replot twice
            self._plot.xAxis.setRange(value / self._res, self._plot.xAxis.range().size(), QtCore.Qt.AlignLeft)

    def x_axis_changed(self, new_range):
        self.horizontalScrollBar.setValue(round(new_range.lower * self._res))
        self.horizontalScrollBar.setPageStep(round(new_range.size() * self._res))
        self.horizontalScrollBar.setMaximum((self.now() - self._width) * self._res)

    def add_stream(self, stream):
        if stream not in self._streams:
            self._streams.append(stream)
            self._plot.addGraph()
            index = self._plot.graphCount() - 1
            pen = QPen()
            pen.setColor(QColor(self._colors[index]))
            pen.setWidth(3)
            self._plot.graph(index).setPen(pen)

    def before_replot(self):
        now = self.now()

        if self.horizontalScrollBar.value() >= self.horizontalScrollBar.maximum() - 10:
            self.set_range([now - self._width, now])
        else:
            scrollbar_start = self.horizontalScrollBar.value() / self._res
            self.set_range([scrollbar_start, scrollbar_start + self._width])

        min_y = float("inf")
        max_y = float("-inf")
        for index, stream in enumerate(self._streams):
            data = stream.get()
            self._plot.graph(index).setData(data['x'], data['y'])

            for x, y in zip(data['x'], data['y']):
                if self._plot_range[0] <= x <= self._plot_range[1]:
                    min_y = min(min_y, y)
                    max_y = max(max_y, y)

        if self.autoscaleY.isChecked():
            delta_y = max_y - min_y

            if delta_y > 0:
                margin = 5 / 100 * delta_y
            else:
                margin = 1

                if delta_y < 0:
                    min_y = 0
                    max_y = 0

            self._plot.yAxis.setRange(qcustomplot.QCPRange(min_y - margin, max_y + margin))

        self.x_axis_changed(qcustomplot.QCPRange(*self._plot_range))

    def after_replot(self):
        self.reset_replot_timer()

    def set_range(self, new_range):
        self._plot_range = new_range
        self._plot.xAxis.setRange(qcustomplot.QCPRange(*self._plot_range))

    def now(self):
        return time.monotonic() - self._start


if __name__ == '__main__':
    
    app = QApplication(sys.argv)
    main_window = QMainWindow()

    plot = Plot(main_window)
    plot.add_stream(TimeFunctionStream(lambda x: math.sin(0.5*x)))
    plot.add_stream(TimeFunctionStream(lambda x: math.sin(7*x) / 3 + 0.4))
    # plot.add_stream(TimeFunctionStream(lambda x: math.tan(2*x)))

    # n = 1
    # plot.add_stream(TimeFunctionStream(lambda x: sum([math.sin(2*(i*2 + 1)*x)/(i*2 + 1) for i in range(0, n)])))
    # m = 4
    # plot.add_stream(TimeFunctionStream(lambda x: sum([math.sin(2*(i*2 + 1)*x)/(i*2 + 1) for i in range(0, m)])))

    main_window.show()

    sys.exit(app.exec_())
