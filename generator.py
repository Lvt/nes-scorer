#!/usr/bin/env python3
import argparse
import math
import os
import random
import sys
from random import randint

lineCountHeader=14
lineCountFM2=10000
mutationPercentage=2.5
populationLimit=50

FM2Header="version 3\nemuVersion 9816\nrerecordCount 52180\npalFlag 0\nromFilename Super Mario Bros. 3 (U) (PRG0) [!]\nromChecksum base64:t2+XitMHbqZ/KwrKc5nJ6Q==\nguid 3910245D-A6E2-E190-05B8-14AE7A7AC1CA\nfourscore 0\nport0 1\nport1 1\nport2 0\nFDS 0\n"
firstHeader="|1|........|........||\n"

allInputs = []
for first in ["..", "R.", ".L"]:
	for second in ["..", "D.", ".U"]:
		for start in [".", "T"]:
			for select in [".", "S"]:
				for a in [".", "A"]:
					for b in [".", "B"]:
						allInputs.append("|0|" + first + second + start + select + a + b + "|........||\n")


def hashOnlyInputs(filename):
	f = open(filename, "r")
	# skip Header
	for i in range(0, lineCountHeader):
		f.readline()

	hashValue = f.read()
	f.close()
	return hash(hashValue)

def conceive(father, mother, childName):
	childHandle = open(childName, "w")
	fatherHandle = open(father, "r")
	motherHandle = open(mother, "r")

	childHandle.write(FM2Header + "comment father " + father + " mother " + mother + "\n" + firstHeader)
	# skip Header
	for i in range(0, lineCountHeader):
		fatherHandle.readline()
		motherHandle.readline()


	for i in range(0, lineCountFM2):
		fatherLine = fatherHandle.readline()
		motherLine = motherHandle.readline()
		if randint(0, 100) < mutationPercentage:
			childHandle.write(random.choice(allInputs))
		else:
			childHandle.write(random.choice([fatherLine, motherLine]))

	motherHandle.close()
	fatherHandle.close()
	childHandle.close()

def generateRandomFM2(filename):
	f = open(filename, "w")
	f.write(FM2Header)
	f.write("comment author Init Random File\n")
	f.write(firstHeader)

	# generate more inputs - speed increase
	twoInputs = []
	for input1 in allInputs:
		for input2 in allInputs:
			twoInputs.append(input1 + input2)

	for i in range(0, int(lineCountFM2 / 2)):
		f.write(random.choice(twoInputs))

	f.close()

def selectFM2(foldername):
    files = sorted(list(os.listdir(foldername)))
    files = files[-populationLimit:]
    selectedElement = round(math.sqrt(randint(0,len(files)*len(files))))
    return foldername + "/" + files[min(selectedElement, len(files)-1)]

#generateRandomFM2("father.fm2")
#generateRandomFM2("mother.fm2")
#conceive("father.fm2", "mother.fm2", "child.fm2")

#print(hashOnlyInputs("child.fm2"))

parser = argparse.ArgumentParser(description='Generate fceux movies')
parser.add_argument('--random', '-r', help='generate random movie')
parser.add_argument('--child', '-c', help='generate child')
parser.add_argument('--mother', '-m', help='mother of child')
parser.add_argument('--father', '-f', help='father of child')
parser.add_argument('--parentfolder', '-p', help='folder of potential parent movies')
args = parser.parse_args()

if args.random:
    generateRandomFM2(args.random)
    sys.exit(0)

if args.child:
    father = args.father
    mother = args.mother
    if not father:
        father = selectFM2(args.parentfolder)
    if not mother:
        mother = selectFM2(args.parentfolder)
    conceive(father, mother, args.child)
    sys.exit(0)

print("no argument found")
sys.exit(1)
