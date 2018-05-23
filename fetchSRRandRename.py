#!/usr/bin/python

import sys
import os.path
import argparse
import re
import logging
import warnings
import csv
import subprocess
#import commands

## Retreived fastq files from NCBI SRA; Uses SRR IDs from 3rd colummn of input table.csv
## 
## Does not assume table .tsv file is sorted

## Requires sratoolkit/2.8.X or higher

## Function: A closure for fastq file extension checking

def fastq_check(expected_ext1, expected_ext2, openner):
	def extension(filename):
		if not (filename.lower().endswith(expected_ext1) or filename.lower().endswith(expected_ext2)):
			raise ValueError()
		return openner(filename)
	return extension

## Function: A closure for .tsv or .csv extension checking

def tsv_check(expected_ext1, expected_ext2, openner):
	def extension(filename):
		if not (filename.lower().endswith(expected_ext1) or filename.lower().endswith(expected_ext2)):
			raise ValueError()
		return openner(filename)
	return extension


def readable_dir(prospective_dir):
	if not os.path.isdir(prospective_dir):
    		raise argparse.ArgumentTypeError("readable_dir:{0} is not a valid path".format(prospective_dir))
	if os.access(prospective_dir, os.R_OK):
		if( not prospective_dir.endswith("/") ):
			prospective_dir = prospective_dir + "/"
		return prospective_dir
	else:
		raise argparse.ArgumentTypeError("readable_dir:{0} is not a readable dir".format(prospective_dir))



logger = logging.getLogger("fetchSRRandRename.py")
logger.setLevel(logging.INFO)


parser = argparse.ArgumentParser(description='retreive SRA WGS records according to table.csv', usage="fetchSRRandRename.py nameFiles/table.tsv --outDir Project/reads/ --verbose (Y/N)")


#parser.add_argument("fastq", type=fastq_check('.fastq', 'fastq.gz', argparse.FileType('r')))

parser.add_argument("table", type=tsv_check('.tsv', '.csv', argparse.FileType('r')))

## output folder
parser.add_argument('--outDir', '-D', default='SEQ_Fetch', type=readable_dir, action='store')

parser.add_argument("--verbose", default='N', type = lambda s : s.lower(), choices=['Y','N'])

args = parser.parse_args()

tsvFilePath = args.table.name

lineCountFwd=0

## Get file path

def getFilePath(filePathString):
	splitStr = re.split(pattern='/', string=filePathString)
	folderCount = len(splitStr) - 1
	isolatePath=splitStr[0]
	ii = 0
	while ii < folderCount:
		isolatePath = isolatePath + "/" + splitStr[ii]
		ii = ii + 1
	return isolatePath

## Get SRR fastq name

def getIsolateStr(filePathString):
	splitStr = re.split(pattern='/', string=filePathString)
	fileNameIdx = len(splitStr) - 1
	fileString = splitStr[fileNameIdx]
	isolateString = re.split(pattern=r'_(1|2)\.', string=splitStr[fileNameIdx])
	return isolateString



#myID = getIsolateStr(fastqFilePath)

#myPath = getFilePath(fastqFilePath)

#print(myID[0])

tsvRead = open(args.table.name, 'r')

matrixText = csv.reader(tsvRead, delimiter='\t')

tableText = [row for row in matrixText]


### First pass of tableText: retrieve SRR IDs from NCBI

idx = 0

myID = []

tmp_log_file = open("tmp_log_file.txt", 'w')

while idx < len(tableText):
	if(len(tableText[idx]) == 3):
		srrName = tableText[idx][2].rstrip()
		os.system("prefetch -c {} &> {}".format(srrName, "tmp_log_file.txt"))
		finLine = os.popen("cat {} | tail -1".format("tmp_log_file.txt")).read()
		#print(finLine)	
		if(not(re.search(r'cannot be found', string=finLine, flags=re.IGNORECASE))):
			os.system("vdb-validate {}".format(tableText[idx][2]))
			os.system("fastq-dump --split-files --gzip {} --outdir {}".format(srrName, args.outDir))
			myID.append(tableText[idx][2])
	idx = idx + 1

print(myID)


origWD = os.getcwd()
os.chdir(args.outDir)

### Second pass of tableText: Change SRR file names

idx = 0;

while idx < len(myID):
	fastqFilePath1 = myID[idx].rstrip() + "_1.fastq.gz"
	fastqFilePath2 = myID[idx].rstrip() + "_2.fastq.gz"
	idx2 = 0
	while idx2 < len(tableText):
		if((myID[idx] == tableText[idx2][2]) and (len(tableText[idx2]) == 3)):
			print(tableText[idx2])
			replacement1 = re.sub(myID[idx], tableText[idx2][0], fastqFilePath1)
			replacement2 = re.sub(myID[idx], tableText[idx2][0], fastqFilePath2)
			replacement1 = re.sub(r'_1\.fastq\.gz', '_R1_001\.fastq\.gz', replacement1)
			replacement2 = re.sub(r'_2\.fastq\.gz', '_R2_001\.fastq\.gz', replacement2)
			os.system("mv -v {} {}".format(fastqFilePath1, replacement1))
			os.system("mv -v {} {}".format(fastqFilePath2, replacement2))
		idx2 = idx2 + 1
	idx = idx + 1

os.chdir(origWD)
