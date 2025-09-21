#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <openssl/sha.h>

extern char __start__lettera_seal;
extern char __stop__lettera_seal;

// Simulated recomputation of seal (in real use, you'd hash AST+IR)
char *recompute_seal(const char *input) {
    unsigned char hash[SHA256_DIGEST_LENGTH];
    SHA256((const unsigned char *)input, strlen(input), hash);

    char *hex = malloc(SHA256_DIGEST_LENGTH * 2 + 1);
    for (int i = 0; i < SHA256_DIGEST_LENGTH; i++) {
        sprintf(hex + (i * 2), "%02x", hash[i]);
    }
    hex[SHA256_DIGEST_LENGTH * 2] = '\0';
    return hex;
}

void lettera_verify() {
    size_t len = &__stop__lettera_seal - &__start__lettera_seal;
    char *seal = NULL;

    if (len > 0) {
        seal = malloc(len + 1);
        memcpy(seal, &__start__lettera_seal, len);
        seal[len] = '\0';
    } else {
        // Fallback: try reading from seal.txt
        FILE *f = fopen("seal.txt", "r");
        if (f) {
            fseek(f, 0, SEEK_END);
            len = ftell(f);
            fseek(f, 0, SEEK_SET);
            seal = malloc(len + 1);
            fread(seal, 1, len, f);
            seal[len] = '\0';
            fclose(f);
            fprintf(stderr, "[Lettera] Warning: seal section missing, using fallback file.\n");
        } else {
            fprintf(stderr, "[Lettera] Warning: no seal found in binary or fallback file.\n");
            return;
        }
    }

    // Recompute hash (simulated here with dummy input)
    const char *dummy_input = "AST+IR";
    char *expected = recompute_seal(dummy_input);

    int verbose = getenv("LETTERA_VERBOSE") != NULL;

    if (verbose) {
        printf("[Lettera Seal] Embedded: %s\n", seal);
        printf("[Lettera Seal] Expected : %s\n", expected);
    }

    if (strcmp(seal, expected) == 0) {
        if (verbose) printf("[Lettera] Seal verification passed.\n");
    } else {
        fprintf(stderr, "[Lettera] Seal verification FAILED.\n");
    }

    free(seal);
    free(expected);
}
