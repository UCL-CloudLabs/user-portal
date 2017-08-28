import os
import sys

our_folder = os.path.dirname(__file__)
sys.path.insert(0, our_folder)

from autoapp import app as application
