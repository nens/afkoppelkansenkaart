from qgis.core import QgsProcessingAlgorithm

"""
/***************************************************************************
 OrderedProcessingAlgorithm

 An extended processing algorithm that keeps track of order.
                              -------------------
        begin                : 2022-03-01
        copyright            : (C) 2022 by Nelen en Schuurmans
        email                : leendert.vanwolfswinkel@nelen-schuurmans.nl
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
class OrderedProcessingAlgorithm(QgsProcessingAlgorithm):
    def __init__(self, order: int = 0):
        super().__init__()
        self.order = order

    