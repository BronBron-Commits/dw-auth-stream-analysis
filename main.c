#include <stdio.h>
#include <stdint.h>
#include <winsock2.h>

#include "net.h"
#include "proto.h"

int main(void) {
    SOCKET s = net_connect("auth.deltaworlds.com", 6671);
    if (s == INVALID_SOCKET) {
        printf("connect failed\n");
        return 1;
    }

    /* Set receive timeout so we never block forever */
    DWORD timeout_ms = 5000;
    setsockopt(
        s,
        SOL_SOCKET,
        SO_RCVTIMEO,
        (const char*)&timeout_ms,
        sizeof(timeout_ms)
    );

    /* H01: 10-byte opener */
    uint8_t h01[] = {
        0x00, 0x0a,
        0x00, 0x00, 0x00, 0x24,
        0x00, 0x02,
        0x00, 0x00
    };

    send(s, (const char*)h01, sizeof(h01), 0);
    printf("[TX] H01 sent (%zu bytes)\n", sizeof(h01));

    uint8_t msg[8192];
    uint16_t len;

    while (1) {
        printf("[RX] waiting for next message...\n");

        int r = recv_message(s, msg, sizeof(msg), &len);
        if (r == -2) {
            printf("[RX] message too large\n");
            break;
        }
        if (r < 0) {
            printf("[RX] connection closed or timeout\n");
            break;
        }

        printf("[RX] message len = %u\n", len);
    }

    closesocket(s);
    WSACleanup();
    return 0;
}
