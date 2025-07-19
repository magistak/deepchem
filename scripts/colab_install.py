"""
Original code by @philopon
https://gist.github.com/philopon/a75a33919d9ae41dbed5bc6a39f5ede2
"""

import sys
import os
import requests
import subprocess
import shutil
from logging import getLogger, StreamHandler, INFO

logger = getLogger(__name__)
logger.addHandler(StreamHandler())
logger.setLevel(INFO)

default_channels = [
    "conda-forge",
]
default_packages = [
    "openmm=8.0.0",
    "pdbfixer=1.9.0",
]


def install(
    chunk_size=4096,
    file_name="Miniconda3-latest-Linux-x86_64.sh",
    url_base="https://repo.anaconda.com/miniconda/",
    conda_path=os.path.expanduser(os.path.join("~", "miniconda")),
    add_python_path=True,
    additional_channels=[],
    additional_packages=[],
):
  """Install conda packages on Google Colab

    Example:
    import conda_installer
    conda_installer.install()
  """

  python_version = "3.10"
  python_path = os.path.join(
      conda_path,
      "lib",
      f"python{python_version}",
      "site-packages",
  )

  if add_python_path and python_path not in sys.path:
    logger.info("add {} to PYTHONPATH".format(python_path))
    sys.path.append(python_path)

  packages = list(set(default_packages + additional_packages))
  is_installed = []
  for package in packages:
    package_dir = "simtk" if package.startswith("openmm") else package.split("=")[0]
    is_installed.append(os.path.isdir(os.path.join(python_path, package_dir)))

  if all(is_installed):
    logger.info("all packages are already installed")
    return

  url = url_base + file_name
  logger.info("python version: {}".format(python_version))

  if os.path.isdir(conda_path):
    logger.warning("remove current miniconda")
    shutil.rmtree(conda_path)
  elif os.path.isfile(conda_path):
    logger.warning("remove {}".format(conda_path))
    os.remove(conda_path)

  logger.info('fetching installer from {}'.format(url))
  res = requests.get(url, stream=True)
  res.raise_for_status()
  with open(file_name, 'wb') as f:
    for chunk in res.iter_content(chunk_size):
      f.write(chunk)
  logger.info('done')

  logger.info('installing miniconda to {}'.format(conda_path))
  subprocess.check_call(["bash", file_name, "-b", "-p", conda_path])
  logger.info('done')

  logger.info("configuring conda-forge only")
  subprocess.check_call([
      os.path.join(conda_path, "bin", "conda"), "config", "--remove-key", "channels"
  ])
  subprocess.check_call([
      os.path.join(conda_path, "bin", "conda"), "config", "--add", "channels", "conda-forge"
  ])
  subprocess.check_call([
      os.path.join(conda_path, "bin", "conda"), "config", "--set", "channel_priority", "strict"
  ])

  logger.info("installing openmm, pdbfixer")
  subprocess.check_call([
      os.path.join(conda_path, "bin", "conda"),
      "install",
      "--yes",
      "--override-channels",
      "-c", "conda-forge",
      f"python={python_version}",
      *packages,
  ])
  logger.info("done")
  logger.info("conda packages installation finished!")


if __name__ == "__main__":
  install()
