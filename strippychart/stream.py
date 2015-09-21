import time
from PyQt5 import QtCore


class Stream:
    def __init__(self):
        self._data = {'x': [], 'y': []}
        pass

    def get_x(self):
        return self._data['x']

    def get_y(self):
        return self._data['y']

    def get(self):
        return self._data


class TimeFunctionStream(Stream):
    def __init__(self, function):
        # figure out the 'proper' way
        Stream.__init__(self)

        self._start = time.monotonic()
        self._timer = QtCore.QTimer()
        self._timer.timeout.connect(self._add)
        self._timer.start(0.002 * 1000)

        self._function = function

    def _add(self):
        x = time.monotonic() - self._start
        y = self._function(x)

        self._data['x'].append(x)
        self._data['y'].append(y)
