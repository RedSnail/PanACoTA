#!/usr/bin/env python3
# coding: utf-8

"""
Functions to:
- convert prokka tbl file to our tab file
- convert prokka ffn and faa headers to our format
- Create the database, with the following folders in the given "res_path":
    - Proteins: multifasta with all CDS in aa
    - Replicons: multifasta of genome
    - Genes: multifasta of all genes in nuc
    - LSTINFO: information on annotation. Columns are: `start end strand type locus
    gene_name | product | EC_number | inference2` with the same types as prokka file,
    and strain is C (complement) or D (direct). Locus is:
    `<genome_name>.<i or b><contig_num>_<protein_num>`

@author gem
April 2017
"""

import subprocess
import os
import logging
from logging.handlers import RotatingFileHandler
import sys
import shlex

def install_all():
    """
    Install all needed software(s).
    First, check if dependencies are installed.
    If at least one dependency is not installed, install it.
    Then, install totomain.
    """
    to_install = check_dependencies()
    if to_install != []:
        os.makedirs("dependences", exist_ok=True)
        os.makedirs("binaries", exist_ok=True)
        if "barrnap" in to_install:
            ret = install_barrnap()
            if ret != 0:
                logger.warning("Barrnap was not installed (see above). Prokka will "
                               "not predict RNA.")
        if "prokka" in to_install:
            install_prokka()
        logger.info("Finalizing dependences installation")
        os.environ["PATH"] += os.pathsep + os.path.join(os.getcwd(), "binaries")
    logger.info("Installing totomain")
    cmd = "pip3 install ."
    error = "A problem occurred while trying to install totomain."
    run_cmd(cmd, error)


def check_dependencies():
    """
    Check that all required tools are available.

    - if prokka is not installed:
        - if barrnap is not installed: check that wget and tar are available
        - check that git is available
    - check that pip3 is available
    """
    to_install = []
    if target == "install":
        if not cmd_exists("prokka"):
            if not cmd_exists("barrnap"):
                if not cmd_exists("wget"):
                    logger.error(("You need wget to install barrnap, the RNA predictor"
                                  " used by prokka."))
                    sys.exit(1)
                if not cmd_exists("tar"):
                    logger.error(("You need tar to install barrnap, the RNA predictor"
                                  " used by prokka."))
                    sys.exit(1)
            to_install.append("barrnap")
            if not cmd_exists("git"):
                logger.error("You need git to install prokka.")
                sys.exit(1)
            to_install.append("prokka")
        if not cmd_exists("pip3"):
            logger.error("You need pip3 to install the pipeline.")
            sys.exit(1)
    return to_install


def install_barrnap():
    """
    Install barrnap, the RNA predictor used by prokka
    """
    logger.info("Installing barrnap...")
    cmd = "wget https://github.com/tseemann/barrnap/archive/0.8.tar.gz"
    error = "A problem occurred while trying to download barrnap. See log above."
    ret = run_cmd(cmd, error)
    if ret != 0:
        return ret
    cmd = "tar -xf 0.8.tar.gz"
    error = "A problem occurred while untaring barrnap. See log above."
    ret = run_cmd(cmd, error)
    if ret != 0:
        return ret
    cmd = "rm 0.8.tar.gz"
    error = "A problem occurred while removing barrnap archive. See log above."
    ret = run_cmd(cmd, error)
    cmd = "mv barrnap-0.8 dependences"
    error = ("A problem occurred while moving barrnap package to "
             "dependencies folder. See log above.")
    ret = run_cmd(cmd, error)
    os.symlink(os.path.join("dependences", "barrnap-0.8", "bin", "barrnap"),
               os.path.join("binaries", "barrnap"))
    return 0


def install_prokka():
    """
    Install prokka
    """
    logger.info("Installing prokka...")
    cmd = "git clone https://github.com/tseemann/prokka.git"
    error = "A problem occurred while trying to download prokka. See log above."
    ret = run_cmd(cmd, error, eof=True)
    cmd = "mv prokka dependences"
    error = "A problem occurred while moving prokka to 'dependences'. See log above."
    ret = run_cmd(cmd, error, eof=True)
    cmd = os.path.join("dependencies", "prokka", "bin", "prokka") +  " --setupdb"
    error = "A problem occurred while initializing prokka db. See log above."
    ret = run_cmd(cmd, error, eof=True)
    os.symlink(os.path.join("dependences", "prokka", "bin", "prokka"),
               os.path.join("binaries", "prokka"))


def run_cmd(cmd, error, eof=False):
    """
    Run the given command line. If the return code is not 0, print error message
    if eof (exit on fail) is True, exit program if error code is not 0.
    """
    retcode = subprocess.call(shlex.split(cmd))
    if retcode != 0:
        logger.error(error)
        if eof:
            sys.exit(retcode)
    return retcode


def cmd_exists(cmd):
    """
    Check if the command is in $PATH and can then be executed
    """
    torun = "command -v " + cmd
    trying = subprocess.Popen(torun.split(), stdout=subprocess.PIPE)
    out, _ = trying.communicate()
    if trying.returncode == 0:
        if os.path.isfile(out.strip()):
            return True
    return False


def parse():
    """
    Method to create a parser for command-line options
    """
    import argparse
    parser = argparse.ArgumentParser(description=("Script to install, clean or uninstall "
                                                  "pipelineannotation"))
    # Create command-line parser for all options and arguments to give
    targets = ['install', 'clean', 'uninstall']
    parser.add_argument("target", default='install', choices=targets,
                        help=("Choose what you want to do:\n"
                              " - install: install the pipeline and its dependences. If not "
                              "already installed by user, dependences packages will be downloaded "
                              "and built in 'dependences' folder, and their binary files will be "
                              "put to 'binaries'.\n"
                              " - clean: clean dependences: for dependences which were installed "
                              "via this script, uninstall them, and remove their downloaded "
                              "sources from 'dependencies' folder. Can be used if the user wants "
                              "to install another version of the dependencies.\n"
                              " - uninstall: uninstall the pipeline, as well as the dependences "
                              "which were installed for it (in 'dependences' folder).\n"
                              "Default is %(default)s"))
    args = parser.parse_args()
    return args


if __name__ == '__main__':
    logger = logging.getLogger()
    level = logging.INFO
    logger.setLevel(level)
    # create formatter for log messages: "timestamp :: level :: message"
    formatterFile = logging.Formatter('[%(asctime)s] :: %(levelname)s :: %(message)s')
    formatterStream = logging.Formatter('  * %(message)s')
    # Create handler 1: writing to 'logfile'
    logfile = "install.log"
    logfile_handler = RotatingFileHandler(logfile, 'w', 1000000, 5)
    # set level to the same as the logger level
    logfile_handler.setLevel(level)
    logfile_handler.setFormatter(formatterFile)  # add formatter
    logger.addHandler(logfile_handler)  # add handler to logger
    # Create handler 3: write to stdout
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(level)  # write any message
    stream_handler.setFormatter(formatterStream)
    logger.addHandler(stream_handler)  # add handler to logger

    OPTIONS = parse()

    target = OPTIONS.target
    if target == "install":
        install_all()
    # elif OPTIONS.target == "clean":
    #     clean_all()
    # else:
    #     uninstall_all()