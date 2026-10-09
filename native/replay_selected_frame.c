/* Exercise the same selected-frame socket client without invoking capture. */
#include "gocr_frame_transport.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main(int argc, char** argv)
{
    if (argc != 2) return 2;
    FILE* file = fopen(argv[1], "rb");
    if (!file) return 1;
    char line[128]; int width, height;
    if (!fgets(line,sizeof(line),file) || strcmp(line,"P6\n")
        || !fgets(line,sizeof(line),file) || sscanf(line,"%d %d",&width,&height)!=2
        || width!=1280 || height!=720
        || !fgets(line,sizeof(line),file) || strcmp(line,"255\n")) {
        fclose(file); return 1;
    }
    unsigned char* pixels = malloc(1280u*720u*3u);
    if (!pixels || fread(pixels,3,1280u*720u,file)!=1280u*720u) {
        fclose(file); free(pixels); return 1;
    }
    fclose(file);
    int code = gocr_submit_selected_rgb(pixels,width,height,1,0);
    free(pixels);
    return code ? 1 : 0;
}
