import struct, sys

RES_STRING_POOL_TYPE = 0x0001

def uleb(data, off):
    r = 0; s = 0
    while True:
        b = data[off]; off += 1
        r |= (b & 0x7f) << s
        if not (b & 0x80): break
        s += 7
    return r, off

def main(path, out, old, new):
    data = bytearray(open(path, 'rb').read())
    # first chunk after XML header is string pool
    typ, hsize, size = struct.unpack_from('<HHI', data, 8)
    assert typ == RES_STRING_POOL_TYPE, hex(typ)
    base = 8
    count, style_count, flags, strings_start, styles_start = struct.unpack_from('<IIIII', data, base+8)
    utf8 = bool(flags & (1 << 8))
    offsets = list(struct.unpack_from('<%dI' % count, data, base+28))
    strings = []
    for o in offsets:
        p = base + strings_start + o
        if utf8:
            n, p2 = uleb(data, p)
            m, p3 = uleb(data, p2)
            strings.append(data[p3:p3+m].decode('utf-8', 'replace'))
        else:
            n = struct.unpack_from('<H', data, p)[0]
            p2 = p+2
            if n & 0x8000:
                n = ((n & 0x7fff) << 16) | struct.unpack_from('<H', data, p2)[0]
                p2 += 2
            strings.append(data[p2:p2+n*2].decode('utf-16-le', 'replace'))
    print('strings', len(strings), 'utf8', utf8)
    for old_s, new_s in [(old, new)]:
        if old_s not in strings:
            print('old not found:', old_s); continue
        idx = strings.index(old_s)
        p = base + strings_start + offsets[idx]
        if utf8:
            n1, q1 = uleb(data, p)
            n2, q2 = uleb(data, q1)
            end = q2 + n2
            total = (end - p) + 1  # + NUL
            nb = new_s.encode('utf-8')
            newdata = bytes([len(new_s)]) + bytes([len(nb)]) + nb + b'\0'
            if len(newdata) > total:
                print('too long', len(newdata), total); continue
            data[p:p+len(newdata)] = newdata
            data[p+len(newdata):p+total] = b'\0' * (total - len(newdata))
            print('patched %r -> %r (%d/%d bytes)' % (old_s, new_s, len(newdata), total))
        else:
            n = struct.unpack_from('<H', data, p)[0]
            q = p + 2
            if n & 0x8000:
                n = ((n & 0x7fff) << 16) | struct.unpack_from('<H', data, q)[0]
                q += 2
            total = (q - p) + n*2 + 2
            nb = new_s.encode('utf-16-le')
            newdata = struct.pack('<H', len(new_s)) + nb + b'\0\0'
            if len(newdata) > total:
                print('too long', len(newdata), total); continue
            data[p:p+len(newdata)] = newdata
            data[p+len(newdata):p+total] = b'\0' * (total - len(newdata))
            print('patched utf16 %r -> %r' % (old_s, new_s))
    open(out, 'wb').write(data)

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
