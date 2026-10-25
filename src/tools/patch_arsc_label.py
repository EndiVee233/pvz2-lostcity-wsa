import struct, sys

def uleb(data, off):
    r = 0; s = 0
    while True:
        b = data[off]; off += 1
        r |= (b & 0x7f) << s
        if not (b & 0x80): break
        s += 7
    return r, off

def main(path, out, idx, new_s):
    data = bytearray(open(path, 'rb').read())
    typ, hsize, size = struct.unpack_from('<HHI', data, 8)
    assert typ == 0x0002
    base = 12
    typ, hsize, size = struct.unpack_from('<HHI', data, base)
    assert typ == 0x0001
    count, style_count, flags, strings_start, styles_start = struct.unpack_from('<IIIII', data, base+8)
    utf8 = bool(flags & 0x100)
    offsets = list(struct.unpack_from('<%dI' % count, data, base+28))
    idx = int(idx)
    p = base + strings_start + offsets[idx]
    nb = new_s.encode('utf-8')
    if utf8:
        n1, q1 = uleb(data, p)
        n2, q2 = uleb(data, q1)
        total = (q2 + n2 - p) + 1
        newdata = bytes([len(new_s)]) + bytes([len(nb)]) + nb + b'\0'
    else:
        n = struct.unpack_from('<H', data, p)[0]
        q = p + 2
        if n & 0x8000:
            n = ((n & 0x7fff) << 16) | struct.unpack_from('<H', data, q)[0]
            q += 2
        total = (q - p) + n*2 + 2
        newdata = struct.pack('<H', len(new_s)) + new_s.encode('utf-16-le') + b'\0\0'
    if len(newdata) > total:
        print('too long', len(newdata), total); sys.exit(1)
    data[p:p+len(newdata)] = newdata
    data[p+len(newdata):p+total] = b'\0' * (total - len(newdata))
    open(out, 'wb').write(data)
    print('patched arsc idx', idx, '->', new_s, len(newdata), '/', total)

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
