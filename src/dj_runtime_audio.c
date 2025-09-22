#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <portaudio.h>
#include <sndfile.h>
#include <math.h>

// Simple audio buffer struct
typedef struct {
    SNDFILE *file;
    SF_INFO info;
    float *buffer;
    int position;
    int frames;
} Track;

// PortAudio callback for playback
static int pa_callback(const void *input, void *output,
                       unsigned long frameCount,
                       const PaStreamCallbackTimeInfo* timeInfo,
                       PaStreamCallbackFlags statusFlags,
                       void *userData) {
    Track *track = (Track*)userData;
    float *out = (float*)output;

    for (unsigned long i = 0; i < frameCount * track->info.channels; i++) {
        if (track->position < track->frames) {
            out[i] = track->buffer[track->position++];
        } else {
            out[i] = 0.0f; // silence after EOF
        }
    }
    return (track->position >= track->frames) ? paComplete : paContinue;
}

// Load track into memory
Track* load_track(const char *filename) {
    Track *t = malloc(sizeof(Track));
    t->info.format = 0;
    t->file = sf_open(filename, SFM_READ, &t->info);
    if (!t->file) {
        fprintf(stderr, "[DJ] Error: could not open %s\n", filename);
        free(t);
        return NULL;
    }
    t->frames = t->info.frames * t->info.channels;
    t->buffer = malloc(sizeof(float) * t->frames);
    sf_readf_float(t->file, t->buffer, t->info.frames);
    sf_close(t->file);
    t->position = 0;
    return t;
}

// Play track
void dj_play(const char *filename) {
    Pa_Initialize();
    Track *track = load_track(filename);
    if (!track) return;

    PaStream *stream;
    Pa_OpenDefaultStream(&stream, 0, track->info.channels,
                         paFloat32, track->info.samplerate,
                         512, pa_callback, track);
    Pa_StartStream(stream);

    while (Pa_IsStreamActive(stream)) {
        Pa_Sleep(100);
    }

    Pa_CloseStream(stream);
    Pa_Terminate();

    free(track->buffer);
    free(track);
    printf("[DJ] Finished playing %s\n", filename);
}

// Crossfade between two tracks
void dj_crossfade(const char *a, const char *b, int duration) {
    Track *t1 = load_track(a);
    Track *t2 = load_track(b);

    if (!t1 || !t2) return;

    Pa_Initialize();
    PaStream *stream;
    Pa_OpenDefaultStream(&stream, 0, t1->info.channels,
                         paFloat32, t1->info.samplerate,
                         512, NULL, NULL);

    Pa_StartStream(stream);

    int fadeFrames = duration * t1->info.samplerate;
    for (int i = 0; i < fadeFrames; i++) {
        float alpha = (float)i / fadeFrames; // fade curve
        int pos1 = t1->position++;
        int pos2 = t2->position++;
        if (pos1 < t1->frames && pos2 < t2->frames) {
            float mixed = (1.0f - alpha) * t1->buffer[pos1] + alpha * t2->buffer[pos2];
            Pa_WriteStream(stream, &mixed, 1);
        }
    }

    Pa_StopStream(stream);
    Pa_CloseStream(stream);
    Pa_Terminate();

    free(t1->buffer); free(t1);
    free(t2->buffer); free(t2);
    printf("[DJ] Crossfaded %s -> %s in %ds\n", a, b, duration);
}
