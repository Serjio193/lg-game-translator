#define _GNU_SOURCE
#include <dlfcn.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

static const char *libs[] = {
    "libvtcapture.so",
    "libdile_vt.so",
    "libhalgal.so",
    NULL
};

int main(void) {
    printf("LG Game Translator capture probe v0.1\n");
    printf("pid=%ld\n", (long)getpid());

    int found = 0;
    for (int i = 0; libs[i]; ++i) {
        dlerror();
        void *h = dlopen(libs[i], RTLD_NOW | RTLD_LOCAL);
        if (h) {
            printf("[OK] dlopen(%s)\n", libs[i]);
            dlclose(h);
            found++;
        } else {
            const char *e = dlerror();
            printf("[--] %s: %s\n", libs[i], e ? e : "not available");
        }
    }

    printf("loadable_capture_libraries=%d\n", found);
    printf("NOTE: v0.1 performs discovery only; no capture API is called yet.\n");
    return found ? 0 : 2;
}
