python3 src/main.py tests/effects_demo.let
llc output.bc -filetype=obj -o output.o
clang output.o src/dj_runtime_audio.c -lsndfile -lportaudio -lm -o effects_demo.out
./effects_demo.out
