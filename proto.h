#ifndef PROTO_H
#define PROTO_H

#include <winsock2.h>
#include <stdint.h>

int recv_exact(SOCKET s, uint8_t *buf, int len);
int recv_u16_be(SOCKET s, uint16_t *out);
int recv_message(SOCKET s, uint8_t *buf, int bufcap, uint16_t *out_len);

#endif
