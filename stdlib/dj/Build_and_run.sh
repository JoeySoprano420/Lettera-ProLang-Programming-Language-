python3 src/main.py tests/realmix.let
llc output.bc -filetype=obj -o output.o
clang output.o src/dj_runtime_audio.c -lsndfile -lportaudio -o realmix.out
./realmix.out
