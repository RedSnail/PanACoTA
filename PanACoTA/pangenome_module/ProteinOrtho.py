#!/usr/bin/env python3
# coding: utf-8

# ###############################################################################
# This file is part of PanACOTA.                                                #
#                                                                               #
# Authors: Amandine Perrin                                                      #
# Copyright © 2018-2020 Institut Pasteur (Paris).                               #
# See the COPYRIGHT file for details.                                           #
#                                                                               #
# PanACOTA is a software providing tools for large scale bacterial comparative  #
# genomics. From a set of complete and/or draft genomes, you can:               #
#    -  Do a quality control of your strains, to eliminate poor quality         #
# genomes, which would not give any information for the comparative study       #
#    -  Uniformly annotate all genomes                                          #
#    -  Do a Pan-genome                                                         #
#    -  Do a Core or Persistent genome                                          #
#    -  Align all Core/Persistent families                                      #
#    -  Infer a phylogenetic tree from the Core/Persistent families             #
#                                                                               #
# PanACOTA is free software: you can redistribute it and/or modify it under the #
# terms of the Affero GNU General Public License as published by the Free       #
# Software Foundation, either version 3 of the License, or (at your option)     #
# any later version.                                                            #
#                                                                               #
# PanACOTA is distributed in the hope that it will be useful, but WITHOUT ANY   #
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS     #
# FOR A PARTICULAR PURPOSE. See the Affero GNU General Public License           #
# for more details.                                                             #
#                                                                               #
# You should have received a copy of the Affero GNU General Public License      #
# along with PanACOTA (COPYING file).                                           #
# If not, see <https://www.gnu.org/licenses/>.                                  #
# ###############################################################################

"""
A class for launching mmseqs clusterisation

@author RedSnail
October 2021
"""

import progressbar
import threading
import os
import sys
import copy
import time
import glob
import re

from PanACoTA.pangenome_module.Clusterisator import Clusterisator, infinite_progressbar
from PanACoTA import utils

class ProteinOrtho(Clusterisator):
    def __init__(self, po_mode, name, outdir, prt_path, threads, panfile, quiet):
        self.po_mode = po_mode
        self.name = name

        super(ProteinOrtho, self).__init__(threads, outdir, prt_path, panfile, quiet)

        if panfile is None:
            self.panfile_tmp = f"PanGenome-{name}-clust-{self.infoname}.lst"
        else:
            self.panfile_tmp = panfile

        self.panfile_tmp = os.path.join(outdir, self.panfile_tmp)
        self.wd = os.getcwd()
        self.tmpdir = os.path.join(self.wd, self.tmpdir)
        self.prt_path = os.path.join(self.wd, self.prt_path)
        self.log_path = os.path.join(self.wd, self.log_path)

    @property
    def panfile(self):
        return self.panfile_tmp

    @property
    def method_name(self):
        return "proteinortho"

    @property
    def info_string(self):
        return ("Will run ProteinOrtho with:\n"
                f"\t- search method {self.po_mode}")

    @property
    def infoname(self):
        if self.threads != 1:
            threadinfo = "-th" + str(self.threads)
        else:
            threadinfo = ""
        infoname = self.po_mode + "-search" + threadinfo
        return infoname

    @property
    def expected_files(self):
        return ["this", "files", "never", "gonna", "exist"]

    def run_cmds(self, cmds):
        os.chdir(self.tmpdir)
        super(ProteinOrtho, self).run_cmds(cmds)
        os.chdir(self.wd)

    @property
    def tmp_files_cmds(self):
        protfiles = " ".join(glob.glob(f"{self.prt_path}/*.prt"))
        return [(f"proteinortho -step=1 -cpus={self.threads} -p={self.po_mode} "
                 f"-project={self.name} -temp={self.tmpdir} {protfiles}",
                 f"An error occured while database building. View {self.log_path} for logs"),
                (f"proteinortho -step=2 -cpus={self.threads} -p={self.po_mode} "
                 f"-project={self.name} -temp={self.tmpdir} {protfiles}",
                 f"An error occured while all-vs-all blast. View {self.log_path} for logs")]

    @property
    def clustering_files(self):
        return ["these", "files", "never", "gonna", "exist"]

    @property
    def clust_cmds(self):
        protfiles = " ".join(glob.glob(f"{self.prt_path}/*.prt"))
        resfiles = glob.glob(f"{self.name}.*")
        return [(f"proteinortho -step=3 -cpus={self.threads} -project={self.name} -temp={self.tmpdir} {protfiles}",
                 f"An error occured while database building. View {self.log_path} for logs")]

    def parse_to_pangenome(self):
        with open(os.path.join(self.tmpdir, f"{self.name}.proteinortho.tsv")) as tsv:
             lists = [list(filter(lambda a: len(a) > 0, re.split("[ \\*,\t\n]", line)[3:])) for line in tsv]

        lists = lists[1:]
        return dict(zip(range(1, len(lists) + 1), lists))