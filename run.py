#!/usr/bin/env python3

import pstats, io
from pstats import SortKey
import argparse
import shutil
import socket
import subprocess
import time
from time import perf_counter
import os
import glob
import imageio
import numpy
import skimage, skimage.io
from skimage import color, transform
from functools import reduce

start_time = perf_counter()

# cli arguments

parser = argparse.ArgumentParser(description='Evaluate an fceux movie')
parser.add_argument('--movie', '-m', required=True, help='fceux movie to play')
parser.add_argument('--game', '-g', required=True, help='fceux game to play')
parser.add_argument('--run', '-r', default='./fceux.sh', help='fceux game to play')
parser.add_argument('--listen', '-l', default='127.0.0.1', help='listen ip')
parser.add_argument('--port', '-p', default='0', help='listen port (default random)')
parser.add_argument('--bench', '-b', type=bool, default=False, help='benchmark (cProfile)')
parser.add_argument('--copy', '-c', help='copy to folder/<score>_<hash>.fm2')
args = parser.parse_args()

print("# " + args.game + " -- " + args.movie + " -- " + args.run)

if args.bench:
    import cProfile
    print("# enable benchmark")
    pr = cProfile.Profile()
    pr.enable()

# constants

x = 256
y = 240
raw_argb_image_size = x * y * 4
downscale_x = x
downscale_y = y
dimensions = downscale_x*downscale_y*3
projections = 96
bits_per_hash = 63
hashtables = 48
tables = []

# https://dilbert.com/strip/2001-10-25
numpy.random.seed(999999)

for i in range(hashtables):
    tables.append({})

projection = numpy.random.randn(projections, dimensions)
hashbits = []
for i in range(hashtables):
    hashbits.append(numpy.random.permutation(projections)[0:bits_per_hash])

powersoftwo = [1]
for i in range(1,bits_per_hash):
    powersoftwo.append(powersoftwo[-1]*2)

powersoftwo = numpy.array(powersoftwo)

def lshash(img):
    projected = projection.dot(img)
    bits = list(map(lambda x: 0 if x <= 0 else 1, projected))
    perms = list(map(lambda l: powersoftwo.dot(list(map(lambda i: bits[i], l))), hashbits))
    return perms

def hashFM2(filename):
        f = open(filename, "r")
        # skip Header
        for i in range(0, 14):
                f.readline()

        hashValue = f.read()
        f.close()
        return hash(hashValue)

# listen for incoming connections

serversocket = socket.create_server((args.listen, int(args.port)), reuse_port=True)
host = serversocket.getsockname()[0]
port = serversocket.getsockname()[1]
print("# listen on port " + host + ":" + str(port))
print("# waiting for new connection")

fceux_env = os.environ.copy()
fceux_env["MOVIE"] = args.movie
fceux_env["GAME"] = args.game
fceux_env["CONNECT_IP"] = args.listen
if args.listen == '0.0.0.0':
    if host == '0.0.0.0':
        fceux_env["CONNECT_IP"] = "127.0.0.1"
    else:
        fceux_env["CONNECT_IP"] = host
fceux_env["CONNECT_PORT"] = str(port)
subprocess.Popen(args.run, env=fceux_env)

connection, remoteaddr = serversocket.accept()
print("# connection from " + str(remoteaddr))

connection.setsockopt(socket.SOL_TCP, socket.TCP_NODELAY, 1) 
connection.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, raw_argb_image_size)
connection.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, raw_argb_image_size * 2)

def read_img_data(buf):
    bytes_recd = connection.recv_into(buf, raw_argb_image_size, socket.MSG_WAITALL)
    if bytes_recd < raw_argb_image_size:
        print("expected to read " + str(raw_argb_image_size) + " bytes, got " + str(bytes_recd))
        return False
    return buf

raw_image_buffer = bytearray(raw_argb_image_size)
rawhashes = {}
rgb = numpy.zeros((y, x, 3), dtype=numpy.uint8)
duplicates = 0
frame = 0
score = 0
quality_score = 0
while True:
    data = read_img_data(raw_image_buffer)
    if not data: break
    frame += 1

    rawhash = hash(str(data))
    if rawhash in rawhashes:
        duplicates = duplicates + 1
        continue
    rawhashes[rawhash] = 1

    for iy in range(y):
        for ix in range(x):
            rgb[iy][ix][0] = data[iy*x*4+ix*4+1]
            rgb[iy][ix][1] = data[iy*x*4+ix*4+2]
            rgb[iy][ix][2] = data[iy*x*4+ix*4+3]

    img = rgb
    if downscale_x != x or downscale_y != y:
        img = skimage.transform.resize(rgb, (downscale_x,downscale_y), anti_aliasing=True)
    img = img.flatten()
    hashes = lshash(img)
    found = 0
    not_found = 0
    for i in range(hashtables):
        if hashes[i] in tables[i]:
            found = found + 1
        else:
            tables[i][hashes[i]] = 1
            not_found = not_found + 1
    if found <= 1:
        score = score + 1
    quality_score = quality_score + not_found / (found + not_found)

print("FRAMES: " + str(frame))
print("DUPS: " + str(duplicates))
print("SCORE: " + str(score))
print("QSCORE: " + str(quality_score))
print("U: " + str(reduce(lambda l,r: (l + len(r)), [0] + tables)))

if args.copy:
    h = hashFM2(args.movie)
    outputfile = args.copy + "/" + str(int(quality_score)).zfill(8) + "_" + str(h) + ".fm2"
    print("# copy " + args.movie + " to " + outputfile)
    shutil.copyfile(args.movie, outputfile)

end_time = perf_counter()
print("# time elapsed: ", end_time - start_time, "seconds")

if args.bench:
    pr.disable()
    s = io.StringIO()
    sortby = SortKey.CUMULATIVE
    ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
    ps.print_stats()
    print(s.getvalue())
