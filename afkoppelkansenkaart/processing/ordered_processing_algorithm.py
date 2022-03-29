from qgis.core import QgsProcessingAlgorithm

class OrderedProcessingAlgorithm(QgsProcessingAlgorithm):
    def __init__(self, order: int = 0):
        super().__init__()
        self.order = order

    