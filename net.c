#include "net.h"
#include <stdio.h>
#include <ws2tcpip.h>

SOCKET net_connect(const char *host, uint16_t port) {
    WSADATA wsa;
    SOCKET s = INVALID_SOCKET;
    struct addrinfo hints = {0};
    struct addrinfo *res = NULL;
    char portstr[16];

    if (WSAStartup(MAKEWORD(2,2), &wsa) != 0)
        return INVALID_SOCKET;

    hints.ai_family   = AF_INET;
    hints.ai_socktype = SOCK_STREAM;

    snprintf(portstr, sizeof(portstr), "%u", port);

    if (getaddrinfo(host, portstr, &hints, &res) != 0)
        return INVALID_SOCKET;

    s = socket(res->ai_family, res->ai_socktype, res->ai_protocol);
    if (s == INVALID_SOCKET)
        goto done;

    if (connect(s, res->ai_addr, (int)res->ai_addrlen) != 0) {
        closesocket(s);
        s = INVALID_SOCKET;
        goto done;
    }

done:
    if (res)
        freeaddrinfo(res);
    return s;
}
