#ifndef NET_H
#define NET_H

#include <winsock2.h>
#include <stdint.h>

SOCKET net_connect(const char *host, uint16_t port);

#endif
