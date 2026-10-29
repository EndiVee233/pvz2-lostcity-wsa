"""Original ARM slot growth, creation, reference release and deferred cleanup.

Descriptor tree insertion/deletion/rebalancing run as original instructions.
Only allocation/libc, registry singleton and external object/callback bodies are
controlled. Normalized snapshots include every slot word and both list links.
"""
import hashlib
import json
import struct
import shutil
from native_emulation_support import base, machine
from unicorn import UC_HOOK_CODE, UcError
from unicorn.arm_const import *
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM

OUT = base / 'native_analysis/core_round13/engine_slots'
OUT.mkdir(parents=True, exist_ok=True)
STORE, REG, INPUT, DEST, DESC = 0x6000000, 0x6001000, 0x6002000, 0x6002100, 0x6002200
STACK, STOP = 0x4080000, 0x5000100
ANCHORS = [0xc, 0x30, 0x54, 0x78]
TAGS = [0xfffffffc + i for i in range(4)]
OBJECT = 0x600a000
FUNCTIONS = dict(grow=0x11e5f08, take=0x11e60e8, recycle=0x11e6168,
                create=0x11ed120, retain=0x11e6424, release=0x11e6450,
                refs=0x11e6600, drain=0x11e6b0c, set_object=0x11e66cc,
                set_mode=0x11e66f0, mode=0x11e6740, set_bit28=0x11e6778,
                bit28=0x11e67b8, set_lazy=0x11e67dc, lazy=0x11e681c,
                describe=0x11e6840, resolve=0x11e6620, lookup=0x11e62c8)
SCENARIOS = []

def step(op, a=0, b=0, c=0, h=0, d=(4, 5, 6)):
    return dict(op=op, a=a & 0xffffffff, b=b & 0xffffffff, c=c & 0xffffffff, h=h, d=list(d))

def scenario(label, steps, capacity=0, seed=0, type_id=2):
    SCENARIOS.append(dict(label=label, capacity=capacity, seed=seed, type=type_id, steps=steps))

scenario('automatic-growth-empty', [step('take'), step('take'), step('grow', 300), step('take')])
for capacity in [1, 256, 511, 512, 513, 1024]:
    scenario(f'automatic-growth-{capacity}', [step('take')], capacity=capacity, seed=capacity)
scenario('growth-preserves-four-lists', [step('take'), step('recycle', 0, 1), step('take'),
    step('write', 1, 3, 0xfffffffe), step('recycle', 1), step('take'), step('grow', 12), step('take')], capacity=5)
for index, capacity, seed in [(0, 3, 1), (65535, 65537, 65536), (65536, 65538, 65537)]:
    generations = [0, 1, 0xfffffc, 0xfffffd, 0xfffffe, 0xffffff, 0xfffffffd, 0xfffffffe, 0xffffffff]
    for gen in generations:
        scenario(f'recycle-{index}-{gen:08x}', [step('write', index, 3, gen),
            step('recycle', index), step('take')], capacity=capacity, seed=seed)
    scenario(f'defer-drain-{index}', [step('write', index, 3, 0xffffff),
        step('write', index, 2, OBJECT), step('recycle', index, 1), step('drain')], capacity=capacity, seed=seed)
for mode in [0, 1, 2, 3, 0xffffffff]:
    for marked in [0, 1, 255]:
        scenario(f'create-release-{mode}-{marked}', [step('create', OBJECT, mode, marked),
            step('lookup'), step('describe'), step('resolve'), step('refs'), step('mode'),
            step('bit28'), step('lazy'), step('release'), step('lookup'), step('release'),
            step('drain'), step('create', OBJECT + 32, h=1), step('lookup', h=0), step('lookup', h=1)], capacity=3)
for gen, index, capacity, seed in [(0xfffffffc, 0, 2, 0), (0xfffffffd, 0, 2, 0),
        (0xfffffd, 65536, 65538, 65536), (0xfffffe, 65536, 65538, 65536)]:
    scenario(f'last-reusable-{index}-{gen:08x}', [step('write', index, 3, gen),
        step('create', OBJECT), step('release'), step('lookup'), step('create', OBJECT + 32, h=1)],
        capacity=capacity, seed=seed)
for flags in [0, 1, 2, 0x3ffffff, 0x4000000, 0x80000001, 0xffffffff]:
    scenario(f'ref-flags-{flags:08x}', [step('create', 0), step('write', 0, 4, flags),
        step('refs'), step('retain'), step('refs'), step('release'), step('refs')], capacity=2)
for bad in ['stale', 'wrong_type', 'out_of_range', 'zero']:
    h = [0, 0] if bad == 'zero' else [0x20000 if bad == 'stale' else 0x10002 if bad == 'out_of_range' else 0x10000,
                                         (3 if bad == 'wrong_type' else 2) << 17]
    scenario(f'invalid-{bad}', [step('create', OBJECT), step('handle', *h, h=1),
        *[step(op, 7, h=1) for op in ['retain', 'refs', 'release', 'set_object', 'set_mode',
            'mode', 'set_bit28', 'bit28', 'set_lazy', 'lazy']]], capacity=2)
for initial_flags in [0, 0x80000001, 0xffffffff, 0x60000001]:
    scenario(f'flag-mutations-{initial_flags:08x}', [step('create', OBJECT), step('write', 0, 4, initial_flags),
        *[s for value in [0, 1, 2, 3, 0xffffffff] for s in [step('set_mode', value), step('mode')]],
        *[s for value in [0, 1, 0xffffffff] for s in [step('set_bit28', value), step('bit28'), step('set_lazy', value), step('lazy')]],
        step('set_object', OBJECT + 32), step('resolve')], capacity=2)
for created, released, mutate in [(0, 0, 0xffffffff), (1, 1, 0xffffffff), (2, 2, 0xffffffff),
                                  (0, 2, 1), (0, 2, 2), (2, 2, 0)]:
    scenario(f'callbacks-{created}-{released}-{mutate}', [step('callbacks', created, released, mutate),
        step('create', OBJECT), step('retain'), step('release'), step('release'), step('drain')], capacity=3)
scenario('duplicate-descriptors', [step('create', OBJECT), step('create', OBJECT + 32, h=1),
    step('release', h=0), step('release', h=1)], capacity=3)
scenario('multiple-tree-insert-erase', [*[step('create', OBJECT + i * 32, h=i, d=(k, i, 9))
        for i, k in enumerate([4, 1, 8, 0xffffffff, 0, 0x80000000, 3])],
    step('grow', 16), *[step('release', h=i) for i in [3, 0, 5, 2, 1, 6, 4]]], capacity=8)
scenario('multiple-deferred-reverse-drain', [step('create', OBJECT + i * 32, 1, h=i, d=(i, 5, 6)) for i in range(3)] +
    [step('release', h=i) for i in range(3)] + [step('grow', 8), step('drain')], capacity=4)
for type_id in [2, 0x2001]:
    scenario(f'default-descriptor-{type_id}', [step('create_default', OBJECT), step('describe'), step('release')],
        capacity=2, type_id=type_id)
scenario('null-object', [step('create', 0), step('release'), step('drain')], capacity=2)
scenario('grow-same-capacity', [step('create', OBJECT), step('grow', 3), step('release')], capacity=3)

u, imports = machine()
u.mem_map(0x8000000, 0x4000000)
cursor = 0x8000000
handles = [[0, 0] for _ in range(8)]
events = []
created_count = released_count = 0
mutate_mode = 0xffffffff
allocation_count = free_count = 0

def put(address, *values):
    u.mem_write(address, struct.pack('<' + 'I' * len(values), *values))

def words(address, count=1):
    return list(struct.unpack('<' + 'I' * count, u.mem_read(address, count * 4)))

def allocate(size):
    global cursor, allocation_count
    address = cursor
    cursor += (size + 63) & ~63
    assert cursor < 0xc000000
    u.mem_write(address, b'\xcc' * size)
    allocation_count += 1
    return address

def slot_address(h):
    index = h[0] & (0xffffff if h[1] & 0x10000 else 0xffff)
    return words(STORE + 4)[0] + index * 32

def record_event(kind, index, h, slot):
    s = words(slot, 8)
    events.extend([kind, index, *h, s[4], s[3], s[5], words(STORE + 0x50)[0], words(STORE + 0xf8)[0]])

def hook(uc, address, size, _):
    global free_count
    name = imports.get(address)
    if name == 'malloc' or address == 0x14d1a7c:
        uc.reg_write(UC_ARM_REG_R0, allocate(uc.reg_read(UC_ARM_REG_R0)))
    elif name in ('memset', 'memcpy'):
        dest, source, length = [uc.reg_read(r) for r in (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2)]
        uc.mem_write(dest, bytes([source & 255]) * length if name == 'memset' else bytes(uc.mem_read(source, length)))
    elif name == 'free' or address == 0x14d2e94:
        free_count += 1
    elif address == 0x11e74b4:
        uc.reg_write(UC_ARM_REG_R0, REG)
    elif address in (0x5000200, 0x5000204, 0x5000300, 0x5000304):
        created = address < 0x5000300
        index = (address - (0x5000200 if created else 0x5000300)) // 4
        callbacks = STORE + (0x400 if created else 0x500)
        assert uc.reg_read(UC_ARM_REG_R0) == callbacks + index * 24
        h = words(uc.reg_read(UC_ARM_REG_R1), 2)
        slot = slot_address(h)
        record_event(0 if created else 1, index, h, slot)
        if not created and mutate_mode != 0xffffffff:
            flags = words(slot + 16)[0] & 0x9fffffff
            put(slot + 16, flags | (0x40000000 if mutate_mode == 1 else 0x20000000 if mutate_mode == 2 else 0))
    elif address == 0x5000400:
        obj = uc.reg_read(UC_ARM_REG_R0)
        slots, cap = words(STORE + 4, 2)
        raw = struct.unpack('<' + 'I' * (cap * 8), uc.mem_read(slots, cap * 32))
        matches = [i for i in range(cap) if raw[i * 8 + 2] == obj]
        assert matches
        record_event(2, 0, [obj, 0], slots + matches[0] * 32)
    elif name:
        raise AssertionError(f'unexpected import {name}')
    else:
        return
    uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR))

u.hook_add(UC_HOOK_CODE, hook)

def call(address, args, extras=()):
    u.reg_write(UC_ARM_REG_SP, STACK)
    u.reg_write(UC_ARM_REG_LR, STOP)
    saved = [UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7,
             UC_ARM_REG_R8, UC_ARM_REG_R9, UC_ARM_REG_R10, UC_ARM_REG_R11]
    for i, r in enumerate(saved):
        u.reg_write(r, 0xabc00000 + i)
    for r, value in zip([UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3], list(args) + [0] * 4):
        u.reg_write(r, value)
    if extras:
        put(STACK, *extras)
    u.emu_start(address, STOP, count=8000000)
    assert u.reg_read(UC_ARM_REG_PC) == STOP
    assert u.reg_read(UC_ARM_REG_SP) == STACK
    assert all(u.reg_read(r) == 0xabc00000 + i for i, r in enumerate(saved))
    return u.reg_read(UC_ARM_REG_R0)

def initialize(scenario):
    global cursor, allocation_count, free_count
    cursor = 0x8000000
    allocation_count = free_count = 0
    u.mem_write(STORE, bytes(0x20000))
    put(STORE, scenario['type'])
    put(REG + 0x18, 0x87654321)
    for offset in ANCHORS:
        put(STORE + offset, STORE + offset, STORE + offset)
    put(STORE + 0xe8, 0, 0, STORE + 0xe8, STORE + 0xe8)
    for i in range(8):
        put(OBJECT + i * 32, OBJECT + 0x300)
    put(OBJECT + 0x300 + 20, 0x5000400)
    if scenario['capacity']:
        call(FUNCTIONS['grow'], [STORE, scenario['capacity']])
    # Bulk fixture setup equivalent to taking seed slots; it avoids recording
    # 65k setup calls. The operations under comparison still run original ARM.
    seed = scenario['seed']
    if seed:
        slots, cap = words(STORE + 4, 2)
        lists = [list(range(cap - 1, seed - 1, -1)), list(range(seed)), [], []]
        for offset, indices in zip(ANCHORS, lists):
            anchor = STORE + offset
            addresses = [slots + i * 32 for i in indices]
            put(anchor, addresses[0] if addresses else anchor, addresses[-1] if addresses else anchor)
            for i, address in enumerate(addresses):
                put(address, addresses[i + 1] if i + 1 < len(addresses) else anchor, addresses[i - 1] if i else anchor)
        put(STORE + 0x2c, cap - seed)

def snapshot():
    slots, capacity = words(STORE + 4, 2)
    data = [capacity, *[words(STORE + o)[0] for o in [0x2c, 0x50, 0x74, 0x98]]]
    def normalized(address):
        if STORE + 0xc <= address <= STORE + 0x78 and address - STORE in ANCHORS:
            return TAGS[ANCHORS.index(address - STORE)]
        assert slots <= address < slots + capacity * 32 and (address - slots) % 32 == 0, hex(address)
        return (address - slots) // 32
    for offset in ANCHORS:
        data.extend(normalized(v) for v in words(STORE + offset, 2))
    if capacity:
        raw = list(struct.unpack('<' + 'I' * (capacity * 8), u.mem_read(slots, capacity * 32)))
        for i in range(capacity):
            raw[i * 8] = normalized(raw[i * 8])
            raw[i * 8 + 1] = normalized(raw[i * 8 + 1])
        data.extend(raw)
    entries = []
    def visit(node):
        if not node:
            return
        visit(words(node + 8)[0])
        entries.extend(words(node + 16, 3) + words(node + 32, 2))
        visit(words(node + 12)[0])
    visit(words(STORE + 0xec)[0])
    data.append(len(entries) // 5)
    assert data[-1] == words(STORE + 0xf8)[0]
    data.extend(entries)
    blob = struct.pack('<' + 'I' * len(data), *data)
    digest = 0xcbf29ce484222325
    for byte in blob:
        digest = ((digest ^ byte) * 0x100000001b3) & 0xffffffffffffffff
    return dict(capacity=capacity, counts=data[1:5], descriptor_count=len(entries) // 5,
                normalized_fnv1a64=f'{digest:016x}')

checks = 0
for sc in SCENARIOS:
    initialize(sc)
    handles = [[0, 0] for _ in range(8)]
    created_count = released_count = 0
    mutate_mode = 0xffffffff
    sc['initial'] = snapshot()
    for number, s in enumerate(sc['steps']):
        events = []
        op, a, b, c, h = [s[k] for k in ['op', 'a', 'b', 'c', 'h']]
        put(INPUT, *handles[h])
        put(DEST, 0xdeadbeef, 0xdeadbeef, 0xdeadbeef, 0xdeadbeef)
        result = []
        try:
            if op == 'callbacks':
                created_count, released_count, mutate_mode = a, b, c
                for offset, count, block, fn in [(0x118, a, 0x400, 0x5000200), (0x128, b, 0x500, 0x5000300)]:
                    put(STORE + offset, STORE + block, STORE + block + count * 24)
                    for i in range(count):
                        put(STORE + block + i * 24 + 20, fn + i * 4)
            elif op == 'write':
                put(words(STORE + 4)[0] + a * 32 + b * 4, c)
            elif op == 'handle':
                handles[h] = [a, b]
            elif op == 'grow':
                call(FUNCTIONS[op], [STORE, a])
            elif op == 'take':
                address = call(FUNCTIONS[op], [STORE])
                result = [(address - words(STORE + 4)[0]) // 32]
            elif op == 'recycle':
                call(FUNCTIONS[op], [STORE, words(STORE + 4)[0] + a * 32, b])
            elif op in ('create', 'create_default'):
                put(DESC, *s['d'])
                assert call(FUNCTIONS['create'], [DEST, STORE, a, b], [c, DESC if op == 'create' else 0]) == DEST
                handles[h] = words(DEST, 2)
                result = handles[h]
                assert words(DEST + 8, 2) == [0xdeadbeef] * 2
            elif op == 'drain':
                call(FUNCTIONS[op], [STORE])
            elif op == 'describe':
                assert call(FUNCTIONS[op], [DEST, STORE, INPUT]) == DEST
                result = words(DEST, 3)
                assert words(DEST + 12) == [0xdeadbeef]
            else:
                r = call(FUNCTIONS[op], [STORE, INPUT, a])
                if op not in ('retain',):
                    result = [int(bool(r)) if op == 'lookup' else r]
            s['result'] = result
            s['events'] = events
            s['snapshot'] = snapshot()
        except (UcError, AssertionError) as error:
            raise RuntimeError(f"{sc['label']}/{number}/{op} PC={u.reg_read(UC_ARM_REG_PC):08x}: {error}") from error
        checks += 1
    sc['allocation_calls'], sc['free_calls'] = allocation_count, free_count

md = Cs(CS_ARCH_ARM, CS_MODE_ARM)
ranges = [(0x11e5f08, 0x11e62c8), (0x11e6424, 0x11e6620), (0x11e66cc, 0x11e6840),
          (0x11e6b0c, 0x11e6b70), (0x11ed120, 0x11ed354), (0x11f173c, 0x11f17b4)]
assembly = [f'{i.address:08x}: {i.mnemonic:8} {i.op_str}' for a, b in ranges
            for i in md.disasm(bytes(u.mem_read(a, b - a)), a)]
(OUT / 'instructions.asm').write_text('\n'.join(assembly) + '\n', encoding='utf-8')
folder = OUT / 'pseudocode'
folder.mkdir(exist_ok=True)
for address in list(FUNCTIONS.values()) + [0x11f173c, 0x11ecff0, 0x14e2e64]:
    for p in (base / 'native_analysis/core_round3/full_library/functions').glob(f'{address:08x}_*.c'):
        shutil.copy2(p, folder / p.name)
record = dict(original_sha256=hashlib.sha256((base / 'raw/lib/armeabi/libSrc.so').read_bytes()).hexdigest(),
              scenarios_passed=len(SCENARIOS), checkpoints=checks, scenarios=SCENARIOS,
              snapshot_format='Little-endian u32: capacity,free/live/deferred/retired counts, four next/prev anchors, '
                'all slot words (links normalized to indices or fffffffc..ffffffff), descriptor entry count, '
                'sorted descriptor(3 words)/handle(2 words) entries. FNV-1a64 over the bytes.',
              scope='Original ARM growth relocates every link. Original descriptor RB insertion/erase/rebalance runs. '
                'Controlled allocator never fails; libc memory operations, registry singleton and external callbacks/destructors mocked. '
                'Bulk seed setup constructs the state after take calls. Callback mutation limited to mode bits; no pool movement/reentrancy/concurrency.')
(OUT / 'validation.json').write_text(json.dumps(record, indent=2), encoding='utf-8')
print('PASS', len(SCENARIOS), 'original ARM slot scenarios;', checks, 'state checkpoints')
