from zipfile import ZipFile
import os

ROOT_DIR_FILES = [
    '__init__.py',
    'afkoppelkansenkaart.py',
    'afkoppelkansenkaart_dockwidget.py',
    'afkoppelkansenkaart_dockwidget_base.ui',
    'constants.py',
    'database.py',
    'icon.png',
    'icon_with_gutter_pipe.png',
    'metadata.txt',
    'reload.png',
    'resources.py',
    'resources_rc.py',
    'resources.qrc',
    'tasks.py',
]

DIRECTORIES = [
    'processing',
    'sql',
    'style'

]


def zipdir(path, ziph, path_in_zip):
    # ziph is zipfile handle
    for root, dirs, files in os.walk(path):
        for file in files:
            file_path = os.path.join(root, file)
            zip_file_path = os.path.join(path_in_zip, file_path )
            ziph.write(file_path, zip_file_path)


# create a ZipFile object
try:
    os.remove('afkoppelrendementskaart.zip')
except FileNotFoundError:
    pass
zip = ZipFile('afkoppelrendementskaart.zip', 'w')

# Files in root
for file in ROOT_DIR_FILES:
    zip.write(file, os.path.join('afkoppelkansenkaart', os.path.basename(file)))

# Folders in root
for directory in DIRECTORIES:
    zipdir(directory, zip, 'afkoppelkansenkaart')

# close the Zip File
zip.close()