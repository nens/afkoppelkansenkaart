import os
import shutil

PLUGIN_DIR_NAME = "afkoppelkansenkaart"

this_dir = os.path.dirname(os.path.realpath(__file__))
home_dir = os.path.expanduser("~")
env_name = "3Di" # QGIS or 3Di (modeller interface)
dest_dir_plug = os.path.join(
    home_dir, "AppData", "Roaming", env_name, "QGIS3", "profiles", "default", "python", "plugins", PLUGIN_DIR_NAME
)
print(dest_dir_plug)
src_dir_plug = os.path.join(this_dir, PLUGIN_DIR_NAME)
try:
    shutil.rmtree(dest_dir_plug)
except OSError:
    pass  # directory not present at all
shutil.copytree(src_dir_plug, dest_dir_plug)
