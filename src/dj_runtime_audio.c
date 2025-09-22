#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <portaudio.h>
#include <sndfile.h>
#include <math.h>

// Track buffer
typedef struct {
    SNDFILE *file;
    SF_INFO info;
    float *buffer;
    int frames;
    int position;
} Track;

Track* load_track(const char *filename) {
    Track *t = malloc(sizeof(Track));
    t->info.format = 0;
    t->file = sf_open(filename, SFM_READ, &t->info);
    if (!t->file) {
        fprintf(stderr, "[DJ] Error opening %s\n", filename);
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

// Low-pass filter (simple 1-pole IIR)
void lowpass_filter(float *buffer, int frames, float alpha) {
    float prev = buffer[0];
    for (int i = 1; i < frames; i++) {
        buffer[i] = alpha * buffer[i] + (1 - alpha) * prev;
        prev = buffer[i];
    }
}

// High-pass filter
void highpass_filter(float *buffer, int frames, float alpha) {
    float prev_in = buffer[0], prev_out = buffer[0];
    for (int i = 1; i < frames; i++) {
        float out = alpha * (prev_out + buffer[i] - prev_in);
        buffer[i] = out;
        prev_in = buffer[i];
        prev_out = out;
    }
}

// EQ (3-band simple)
void eq_apply(float *buffer, int frames, float bass, float mid, float treble) {
    for (int i = 0; i < frames; i++) {
        float x = buffer[i];
        buffer[i] = (bass * 0.4f + mid * 0.4f + treble * 0.2f) * x;
    }
}

// Loop a segment
void dj_loop(const char *filename, int start_sec, int length_sec, int repeat) {
    Track *t = load_track(filename);
    if (!t) return;
    int start = start_sec * t->info.samplerate;
    int length = length_sec * t->info.samplerate;
    if (start + length > t->frames) length = t->frames - start;

    Pa_Initialize();
    PaStream *stream;
    Pa_OpenDefaultStream(&stream, 0, t->info.channels,
                         paFloat32, t->info.samplerate,
                         512, NULL, NULL);
    Pa_StartStream(stream);

    for (int r = 0; r < repeat; r++) {
        Pa_WriteStream(stream, &t->buffer[start], length);
    }

    Pa_StopStream(stream);
    Pa_CloseStream(stream);
    Pa_Terminate();

    free(t->buffer); free(t);
    printf("[DJ] Loop %d sec from %d s, repeated %d times\n", length_sec, start_sec, repeat);
}

// Drop effect (bass emphasis)
void dj_drop(const char *filename, int intensity) {
    Track *t = load_track(filename);
    if (!t) return;

    // simple bass boost: scale low freqs
    for (int i = 0; i < t->frames; i++) {
        t->buffer[i] *= (1.0f + intensity * 0.1f);
    }

    Pa_Initialize();
    PaStream *stream;
    Pa_OpenDefaultStream(&stream, 0, t->info.channels,
                         paFloat32, t->info.samplerate,
                         512, NULL, NULL);
    Pa_StartStream(stream);
    Pa_WriteStream(stream, t->buffer, t->frames);
    Pa_StopStream(stream);
    Pa_CloseStream(stream);
    Pa_Terminate();

    free(t->buffer); free(t);
    printf("[DJ] Drop applied with intensity %d\n", intensity);
}

// Wrappers
void dj_filter(const char *filename, const char *type, const char *param) {
    Track *t = load_track(filename);
    if (!t) return;
    if (strcmp(type, "lowpass") == 0) {
        lowpass_filter(t->buffer, t->frames, atof(param));
        printf("[DJ] Low-pass filter applied alpha=%s\n", param);
    } else if (strcmp(type, "highpass") == 0) {
        highpass_filter(t->buffer, t->frames, atof(param));
        printf("[DJ] High-pass filter applied alpha=%s\n", param);
    }
    Pa_Initialize();
    PaStream *stream;
    Pa_OpenDefaultStream(&stream, 0, t->info.channels,
                         paFloat32, t->info.samplerate,
                         512, NULL, NULL);
    Pa_StartStream(stream);
    Pa_WriteStream(stream, t->buffer, t->frames);
    Pa_StopStream(stream);
    Pa_CloseStream(stream);
    Pa_Terminate();
    free(t->buffer); free(t);
}
