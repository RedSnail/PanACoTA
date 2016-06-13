#!/usr/bin/python
# -*- coding: utf-8 -*-:
"""
Script generating the .prt and .gen files with the appropriate headers.

.prt : contains AA sequences for each gene of the genome.
From .faa generated by Prokka, and .lst (generated from the .tbl Prokka output).

.gen : contains nuc sequences for all annotated sequences of the genome.
From .ffn generated by Prokka, and .lst (generated from the .tbl Prokka output)

headers : start, end, strand, type, gembase_gene_id, genName, "| " product " | " ECnum " | " inf2

@author: GEM, Institut Pasteur

November 2015
"""

import sys
import os


def main(prokkaseqs, lstinfo):
    """ Main method """
    ffnseq = prokkaseqs + ".ffn"
    faaseq = prokkaseqs + ".faa"
    fileID = prokkaseqs.split(os.sep)[-1]
    speID = fileID.split('.')[0]
    lstfile = os.path.join(lstinfo, "LSTINFO", fileID + ".lst")
    # create folder 'Genes' if doesn't already exist
    if not os.path.isdir(os.path.join(lstinfo, "Genes")):
        os.mkdir(os.path.join(lstinfo, "Genes"))
    # idem for 'Proteins' folder
    if not os.path.isdir(os.path.join(lstinfo, "Proteins")):
        os.mkdir(os.path.join(lstinfo, "Proteins"))
    genseq = os.path.join(lstinfo, "Genes", fileID + ".gen")
    prtseq = os.path.join(lstinfo, "Proteins", fileID + ".prt")
    create_gen(ffnseq, lstfile, genseq, speID)
    create_prt(faaseq, lstfile, prtseq)


def create_gen(ffnseq, lstfile, genseq, speID):
    """ 
    Generate .gen file, from sequences contained in .ffn, but changing the
    headers using the information in .lst
    """
    clusterID = 1
    with open(ffnseq, "r") as ffn:
        with open(lstfile, "r") as lst:
            with open(genseq, "w") as gen:
                for line in ffn:
                    # header starting with PROKKA<geneID>: not a crispr
                    if line.startswith(">PROKKA"):
                        # get geneID of this header, and the next line of the lst file
                        genID = line.split()[0].split("_")[1]
                        lstline = lst.readline()
                        genIDlst = lstline.split("\t")[4].split("_")[1]
                        # check that genID is the same as the lst line
                        if (genID == genIDlst):
                            write_header(lstline, gen)
                        else:
                            print "ERROR, missing info for gene", line
                    # header starting with species ID: CRISPR
                    elif line.startswith(">" + speID):
                        # get next line of lst file
                        lstline = lst.readline()
                        # check cluster ID is the same as in the current lst line
                        clusterIDlst = int(lstline.split("\t")[4].split("_CRISPR")[1])
                        if (clusterID == clusterIDlst):
                            write_header(lstline, gen)
                            clusterID += 1
                        else:
                            print "ERROR, missing info for gene", line
                    # header strating with other than PROKKA and SAEN: error, check file!
                    elif line.startswith(">"):
                        print "error!"
                        sys.exit(1)
                    # not header: inside sequence, copy it to .gen file
                    else:
                        gen.write(line)


def create_prt(faaseq, lstfile, prtseq):
    """
    Generate .prt file, from sequences in .faa, but changing the headers
    using information in .lst
    """
    with open(faaseq, "r") as faa:
        with open(lstfile, "r") as lst:
            with open(prtseq, "w") as prt:
                for line in faa:
                    # all header lines must start with PROKKA_<geneID>
                    if line.startswith(">PROKKA"):
                        # get gene ID
                        genID = int(line.split()[0].split("_")[1])
                        genIDlst = 0
                        # get line of lst corresponding to the gene ID
                        while (genID > genIDlst):
                            lstline = lst.readline()
                            IDlst = lstline.split("\t")[4].split("_")[1]
                            # don't cast to int if info for a crispr
                            if(IDlst.isdigit()):
                                genIDlst = int(IDlst)
                        # check that genID is the same as the lst line
                        if (genID == genIDlst):
                            write_header(lstline, prt)
                        else:
                            print "ERROR, missing info for gene", line
                    # header starting by somethng else than PROKKA: error, check file!
                    elif line.startswith(">"):
                        print "error!", line
                        sys.exit(1)
                    # not header: inside sequence, copy it to the .prt file
                    else:
                        prt.write(line)


def write_header(lstline, outfile):
    """
    write heaader to output file. Header is generated from the lst line.
    """
    name = lstline.split("\t")[4]
    size = int(lstline.split("\t")[1]) - int(lstline.split("\t")[0]) + 1
    geneName = lstline.split("\t")[5]
    info = lstline.split("\t")[6]
    towrite = " ".join([name, str(size), geneName, info])
    outfile.write(">" + towrite)


def parse():
    """
    Method to create a parser for command-line options
    """
    import argparse
    parser = argparse.ArgumentParser(description="To run all scripts")
    # Create command-line parser for all options and arguments to give
    parser.add_argument("-p", "--prokkaseqs", dest="prokkaseqs",
                        help=("path to Prokka ffn and faa files, without extension. ex: "
                              "/home/Prokka/SAEN.1015.00001"), required=True)
    parser.add_argument("-l", "--lstinfo", dest="lstinfo",
                        help=("path to directory containing 'LSTINFO' folder, and the future"
                              " 'Genes' and 'Proteins' folders."), required=True)
    return parser.parse_args()


if __name__ == '__main__':
    OPTIONS = parse()
    main(OPTIONS.prokkaseqs, OPTIONS.lstinfo)