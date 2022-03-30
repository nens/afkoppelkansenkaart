from qgis.core import QgsTask

import processing

def import_layer_to_postgis(task: QgsTask, layer_id, processing_args):
    processing.runAndLoadResults("qgis:importintopostgis", processing_args, feedback=feedback)