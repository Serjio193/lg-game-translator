/* Local consumer hook only. Capture, frame selection and HyperHDR are untouched. */
#define _POSIX_C_SOURCE 200809L
#include "gocr_frame_transport.h"
#include <arpa/inet.h>
#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/time.h>
#include <sys/un.h>
#include <unistd.h>

#define REPLY_LIMIT (4u * 1024u * 1024u)
#define MODE_FILE "/media/developer/apps/usr/palm/applications/org.webosbrew.piccap/gocr-mode.conf"
#define RESULT_FILE "/tmp/piccap-gocr-latest.json"

bool gocr_selected_frame_enabled(void)
{
    const char* path = getenv("PICCAP_GOCR_MODE_FILE");
    FILE* file = fopen(path ? path : MODE_FILE, "r");
    if (!file) return false;
    char mode[32] = {0};
    bool read = fgets(mode, sizeof(mode), file) != NULL;
    fclose(file);
    mode[strcspn(mode, "\r\n")] = 0;
    return read && (!strcmp(mode, "TV_CROP") || !strcmp(mode, "TV_FULL"));
}

static void number(uint8_t* output, uint64_t value, int bytes)
{
    for (int i = bytes-1; i >= 0; --i) {
        output[i] = (uint8_t)value;
        value >>= 8;
    }
}

static int send_all(int fd, const void* bytes, size_t size)
{
    const uint8_t* current = bytes;
    while (size) {
        ssize_t sent = send(fd, current, size, MSG_NOSIGNAL);
        if (sent < 0 && errno == EINTR) continue;
        if (sent <= 0) return -1;
        current += sent; size -= (size_t)sent;
    }
    return 0;
}

static int receive_all(int fd, void* bytes, size_t size)
{
    uint8_t* current = bytes;
    while (size) {
        ssize_t received = recv(fd, current, size, 0);
        if (received < 0 && errno == EINTR) continue;
        if (received <= 0) return -1;
        current += received; size -= (size_t)received;
    }
    return 0;
}

static int publish(const void* bytes, size_t size)
{
    const char* temporary = RESULT_FILE ".tmp";
    int fd = open(temporary, O_WRONLY | O_CREAT | O_TRUNC | O_NOFOLLOW, 0600);
    if (fd < 0) return -1;
    const uint8_t* current = bytes;
    size_t remaining = size;
    while (remaining) {
        ssize_t written = write(fd, current, remaining);
        if (written < 0 && errno == EINTR) continue;
        if (written <= 0) { close(fd); unlink(temporary); return -1; }
        current += written; remaining -= (size_t)written;
    }
    if (close(fd) || rename(temporary, RESULT_FILE)) {
        unlink(temporary); return -1;
    }
    return 0;
}

int gocr_submit_selected_rgb(const uint8_t* rgb, int width, int height,
    uint64_t sequence, uint64_t captured_ms)
{
    int result = -1, fd = -1;
    char* reply = NULL;
    if (!rgb || width != 1280 || height != 720) goto finish;
    const char* path = getenv("PICCAP_GOCR_SOCKET");
    if (!path) path = "/tmp/gocr-frame.sock";
    struct sockaddr_un address = {.sun_family = AF_UNIX};
    if (strlen(path) >= sizeof(address.sun_path)) goto finish;
    strcpy(address.sun_path, path);
    fd = socket(AF_UNIX, SOCK_STREAM, 0);
    if (fd < 0) goto finish;
    struct timeval timeout = {.tv_sec = 300};
    if (setsockopt(fd, SOL_SOCKET, SO_SNDTIMEO, &timeout, sizeof(timeout))
        || setsockopt(fd, SOL_SOCKET, SO_RCVTIMEO, &timeout, sizeof(timeout))
        || connect(fd, (struct sockaddr*)&address, sizeof(address))) goto finish;
    const uint32_t pixels = 1280u * 720u * 3u;
    uint8_t header[28] = {'G','F','R','1'};
    number(header+4, (uint64_t)width, 2); number(header+6, (uint64_t)height, 2);
    number(header+8, sequence, 8); number(header+16, captured_ms, 8);
    number(header+24, pixels, 4);
    uint32_t network_size;
    if (send_all(fd, header, sizeof(header)) || send_all(fd, rgb, pixels)
        || receive_all(fd, &network_size, sizeof(network_size))) goto finish;
    uint32_t size = ntohl(network_size);
    if (!size || size > REPLY_LIMIT) goto finish;
    reply = malloc((size_t)size+1);
    if (!reply || receive_all(fd, reply, size)) goto finish;
    reply[size] = 0;
    // The local root-owned server emits canonical JSON and explicit errors.
    if (!strstr(reply, "\"schema\":\"gocr.worker.v1\"")) goto finish;
    result = publish(reply, size);
finish:
    if (fd >= 0) close(fd);
    free(reply);
    if (result) {
        char error[160];
        int size = snprintf(error, sizeof(error),
            "{\"schema\":\"gocr.worker.error.v1\",\"sequence\":%llu,\"error\":\"selected_frame_failed\"}",
            (unsigned long long)sequence);
        if (size > 0) (void)publish(error, (size_t)size);
    }
    return result;
}
