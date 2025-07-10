import sys
import time
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import QApplication


class TaskWorker(QThread):
    finished = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(self, task_function, *args, **kwargs):
        super().__init__()
        self.task_function = task_function
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:
            result = self.task_function(*self.args, **self.kwargs)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


if __name__ == "__main__":
    #TEST HILOS
    app = QApplication(sys.argv)

    def example_task(x, y):
        #time.sleep(20)  # Para prueba pon 2 segundos, no 200
        return x + y

    worker = TaskWorker(example_task, 5, 10)
    worker.finished.connect(lambda result: print(f"Resultado: {result}"))
    worker.error.connect(lambda err: print(f"Error: {err}"))
    worker.start()

    sys.exit(app.exec_())
