#include "proto.h"

int recv_exact(SOCKET s, uint8_t *buf, int len) {
    int got = 0;
    while (got < len) {
        int r = recv(s, (char*)buf + got, len - got, 0);
        if (r <= 0)
            return -1;
        got += r;
    }
    return got;
}

int recv_u16_be(SOCKET s, uint16_t *out) {
    uint8_t b[2];
    if (recv_exact(s, b, 2) < 0)
        return -1;

    *out = ((uint16_t)b[0] << 8) | b[1];
    return 0;
}

int recv_message(SOCKET s, uint8_t *buf, int bufcap, uint16_t *out_len) {
    uint16_t len;

    if (recv_u16_be(s, &len) < 0)
        return -1;

    if (len > bufcap)
        return -2;

    if (recv_exact(s, buf, len) < 0)
        return -1;

    *out_len = len;
    return 0;
}
