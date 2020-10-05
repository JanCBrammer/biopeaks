# -*- coding: utf-8 -*-
"""Instantiate the QApplication."""

import sys
from PySide2.QtWidgets import QApplication
from .model import Model
from .view import View
from .controller import Controller


class Application(QApplication):
    """GUI application.

    See also
    --------
    model.Model, view.View, controller.Controller
    """
    def __init__(self, sys_argv):
        super(Application, self).__init__(sys_argv)
        self._model = Model()
        self._controller = Controller(self._model)
        self._view = View(self._model, self._controller)


def main():
    """Command line entry point.

    Called when 'biopeaks' command is executed on the command line.

    See Also
    --------
    setup : See entry_points argument
    """
    app = Application(sys.argv)
    app._view.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
