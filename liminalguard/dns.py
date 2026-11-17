import struct

MAX_QUERY = 4096


def question(packet):
    if len(packet) < 12 or len(packet) > 65535:
        raise ValueError("Invalid DNS length")
    if struct.unpack_from("!H", packet, 4)[0] != 1:
        raise ValueError("One DNS question required")
    labels, offset, end, seen = [], 12, None, set()
    while True:
        if offset in seen or len(seen) >= 128 or offset >= len(packet):
            raise ValueError("Invalid DNS name")
        seen.add(offset)
        size = packet[offset]
        if size & 0xC0 == 0xC0:
            if offset + 1 >= len(packet):
                raise ValueError("Incomplete DNS pointer")
            if end is None:
                end = offset + 2
            offset = ((size & 63) << 8) | packet[offset + 1]
            continue
        if size & 0xC0 or size > 63:
            raise ValueError("Invalid DNS label")
        offset += 1
        if not size:
            end = end or offset
            break
        if offset + size > len(packet):
            raise ValueError("Incomplete DNS label")
        labels.append(packet[offset:offset + size].lower())
        offset += size
    if sum(len(label) + 1 for label in labels) + 1 > 255 or end + 4 > len(packet):
        raise ValueError("Invalid DNS question")
    kind, family = struct.unpack_from("!HH", packet, end)
    return (tuple(labels), kind, family), end + 4


def validate_query(packet):
    if len(packet) > MAX_QUERY:
        raise ValueError("DNS query too large")
    identity, end = question(packet)
    flags = struct.unpack_from("!H", packet, 2)[0]
    if flags & 0xF800 or identity[2] != 1:
        raise ValueError("Only standard Internet DNS queries are supported")
    return identity, end


def response(query, code=2, truncated=False):
    validate_query(query)
    flags = 0x8080 | (struct.unpack_from("!H", query, 2)[0] & 0x0100) | code
    if truncated:
        flags |= 0x0200
    # Rebuild the question so pointers cannot reference discarded sections.
    identity, _ = question(query)
    name = b"".join(bytes([len(label)]) + label for label in identity[0]) + b"\0"
    return query[:2] + struct.pack("!HHHHH", flags, 1, 0, 0, 0) + name + struct.pack("!HH", *identity[1:])


def validate_reply(query, reply):
    if len(reply) > 65535 or len(reply) < 12:
        raise ValueError("Invalid upstream reply size")
    if reply[:2] != query[:2] or not (reply[2] & 0x80):
        raise ValueError("Unexpected upstream reply")
    if question(reply)[0] != question(query)[0]:
        raise ValueError("Upstream question mismatch")
    return reply


def addresses(reply):
    _, position = question(reply)
    result = []
    for _ in range(struct.unpack_from("!H", reply, 6)[0]):
        while True:
            if position >= len(reply):
                raise ValueError("Incomplete answer name")
            size = reply[position]
            position += 1
            if size & 0xC0 == 0xC0:
                position += 1
                break
            if not size:
                break
            if size & 0xC0:
                raise ValueError("Invalid answer label")
            position += size
        if position + 10 > len(reply):
            raise ValueError("Incomplete answer record")
        kind, family, _, size = struct.unpack_from("!HHIH", reply, position)
        position += 10
        data = reply[position:position + size]
        if len(data) != size:
            raise ValueError("Incomplete answer")
        if family == 1 and ((kind == 1 and size == 4) or (kind == 28 and size == 16)):
            result.append(data)
        position += size
    return result
