#!/usr/bin/env bash
exec fceux -b 8 --newppu 1 --sound 0 --nogui --playmov $MOVIE --loadlua imgpipe.lua $GAME
