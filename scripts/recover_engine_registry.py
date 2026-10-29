"""Execute the original registry/name/descriptor chain; mock only external services.

Ghidra addresses use the ELF load bias 0x10000. Expected fixture outputs come
from ARM execution, not from a Python reimplementation of the recovered code.
"""
import hashlib
import json
import shutil
import struct
from native_emulation_support import base, machine
from unicorn import UC_HOOK_CODE, UcError
from unicorn.arm_const import *
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM

out = base / 'native_analysis/core_round12/engine_registry'
out.mkdir(parents=True, exist_ok=True)
REG, STORE, SLOTS = 0x6000000, 0x6001000, 0x8000000
DEST, INPUT, QUERY = 0x6002000, 0x6002100, 0x6002200
STOP, STACK = 0x5000100, 0x4080000
KEYS = [0, 1, 7, 0x7fffffff, 0x80000000, 0xfffffffe, 0xffffffff]
DESCRIPTORS = [(1, 5, 9), (1, 5, 0x80000000), (1, 6, 0),
               (4, 5, 6), (0x80000000, 0, 1),
               (0xffffffff, 0, 1), (0xffffffff, 0xffffffff, 0xffffffff)]
FUNCTIONS = {'named_store': 0x11e7570, 'describe': 0x11e6840,
             'descriptor': 0x11e6890, 'name': 0x11e6a90,
             'canonical': 0x11e761c, 'object': 0x1ea034}
CASES = []

def packed(index, generation, type_id):
    if index < 0x10000:
        return [((generation << 16) | index) & 0xffffffff,
                (type_id << 17) | (generation >> 16)]
    return [((generation << 24) | index) & 0xffffffff,
            (type_id << 17) | (generation >> 8) | 0x10000]

def symbolic(store_id, object_id, extra_flag=0):
    return [object_id | ((store_id & 1) << 31),
            0x80000000 | (store_id >> 1) | extra_flag]

def add(function, label, **kw):
    c = dict(function=function, label=label, query=KEYS[3], descriptor=list(DESCRIPTORS[3]),
             source=symbolic(KEYS[3], KEYS[3]), base_index=0, generation=0x123456,
             type=2, bank_code=2, empty=0, mismatch=-1, callbacks=0, lazy=False, ready=True)
    c.update(kw)
    CASES.append(c)

for q in KEYS + [2, 6, 8, 0x7ffffffe, 0x80000001, 0xfffffffd]:
    add('named_store', f'unsigned-key-{q:08x}', query=q)
add('named_store', 'empty', empty=1)
for bank in [0, 1, 2, 3, 0x2000, 0x2001, 0x2002, 0xffffffff]:
    add('named_store', f'bank-{bank:08x}', bank_code=bank)
for index in [0, 3, 6, 7, 0xffff, 0x10000, 0x10002]:
    for state in ['valid', 'stale', 'wrong_type']:
        start = 0xfffc if index >= 0xffff else 0
        h = packed(index, 0x123456 + (state == 'stale'), 3 if state == 'wrong_type' else 2)
        add('describe', f'index-{index:08x}-{state}', base_index=start, source=h)
for i, key in enumerate(DESCRIPTORS):
    add('descriptor', f'exact-{i}', descriptor=list(key))
    add('descriptor', f'wide-{i}', descriptor=list(key), base_index=0xfffc)
for key in [(0, 0, 0), (1, 5, 8), (1, 5, 10), (1, 5, 0xffffffff),
            (1, 6, 1), (4, 5, 5), (4, 5, 7), (0xffffffff, 0xffffffff, 0xfffffffe)]:
    add('descriptor', f'missing-{key}', descriptor=list(key))
add('descriptor', 'empty', empty=4)
for word in range(3):
    add('descriptor', f'slot-descriptor-mismatch-{word}', mismatch=word)
for generation in [0, 0xffff, 0x10000, 0x7fffffff, 0xffffffff]:
    add('descriptor', f'normal-generation-{generation:08x}', generation=generation)
for generation in [0, 0xffff, 0x10000, 0xffffff]:
    add('descriptor', f'wide-generation-{generation:08x}', generation=generation, base_index=0xfffc)
for q in KEYS + [2, 8, 0x80000001]:
    add('name', f'unsigned-key-{q:08x}', query=q)
add('name', 'empty-name-tree', empty=2)
add('name', 'empty-descriptor-tree', empty=4)
add('name', 'descriptor-mismatch', mismatch=2)
for fn in ['canonical', 'object']:
    for h in [[0, 0], packed(3, 0x123456, 2), packed(3, 0x123457, 2),
              packed(7, 0x123456, 2), packed(3, 0x123456, 3)]:
        add(fn, f'direct-{h}', source=h)
    for store_id, obj_id, flag in [(0, 0, 0), (1, 1, 0), (7, 7, 0),
                                   (KEYS[3], KEYS[3], 0), (KEYS[3], KEYS[3], 0x40000000),
                                   (2, 7, 0), (7, 2, 0)]:
        add(fn, f'symbolic-{store_id}-{obj_id}-{flag}', source=symbolic(store_id, obj_id, flag))
    for empty in [1, 2, 4]:
        add(fn, f'empty-tree-{empty}', empty=empty)
    for bank in [0, 3, 0x2001, 0xffffffff]:
        add(fn, f'bank-{bank:08x}', bank_code=bank,
            type=0x2001 if bank == 0x2001 else 2)
    add(fn, 'wide', base_index=0xfffc)
    add(fn, 'slot-mismatch', mismatch=0)
for count in [0, 1, 2]:
    add('object', f'lazy-{count}', lazy=True, ready=False, callbacks=count)
add('object', 'empty-nonlazy', ready=False, callbacks=2)
add('object', 'ready-lazy', lazy=True, ready=True, callbacks=2)

u, imports = machine()
u.mem_map(SLOTS, 0x210000)
events = []
callback_slot = 0

def put(address, *values):
    u.mem_write(address, struct.pack('<' + 'I' * len(values), *values))

def words(address, count):
    return list(struct.unpack('<' + 'I' * count, u.mem_read(address, count * 4)))

def hook(uc, address, size, _):
    if address == 0x11f13a8:
        uc.reg_write(UC_ARM_REG_R0, 0x600e000)
    elif address in (0x11f153c, 0x11f1f08, 0x11f14cc):
        operation = {0x11f153c: 'retain', 0x11f1f08: 'release', 0x11f14cc: 'text'}[address]
        events.append([operation, uc.reg_read(UC_ARM_REG_R1)])
        if operation == 'text':
            uc.reg_write(UC_ARM_REG_R0, 0x600f000)
    elif address in (0x5000200, 0x5000204):
        index = (address - 0x5000200) // 4
        assert uc.reg_read(UC_ARM_REG_R0) == STORE + 0x500 + index * 24
        assert words(uc.reg_read(UC_ARM_REG_R1), 2) == expected_callback_handle
        events.append(['callback', index])
        put(callback_slot + 8, 0x12345678 + index)
    elif address in imports:
        raise AssertionError(f'unexpected external call: {imports[address]}')
    else:
        return
    uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR))

u.hook_add(UC_HOOK_CODE, hook)

def tree(addresses, offset):
    def build(indices):
        if not indices:
            return 0
        middle = len(indices) // 2
        i = indices[middle]
        put(addresses[i] + 8, build(indices[:middle]), build(indices[middle + 1:]))
        return addresses[i]
    return build(list(range(len(addresses))))

for c in CASES:
    u.mem_write(REG, bytes(0x20000))
    u.mem_write(SLOTS, bytes(0x210000))
    put(REG, REG + 0x300, REG + 0x308, REG + 0x308,
        REG + 0x400, REG + 0x40c, REG + 0x40c)
    put(REG + 0x300, 0, STORE)
    put(REG + 0x400, 0, 0, STORE)
    put(STORE, c['type'], SLOTS, c['base_index'] + 7)
    store_nodes = [REG + 0x10000 + i * 64 for i in range(7)]
    name_nodes = [REG + 0x11000 + i * 64 for i in range(7)]
    descriptor_nodes = [REG + 0x12000 + i * 64 for i in range(7)]
    for i, (name, descriptor) in enumerate(zip(KEYS, DESCRIPTORS)):
        put(store_nodes[i] + 16, name, c['bank_code'])
        put(name_nodes[i] + 16, name, 0, *descriptor)
        index = c['base_index'] + i
        handle = packed(index, c['generation'], c['type'])
        put(descriptor_nodes[i] + 16, *descriptor, 0, *handle)
        actual_descriptor = list(descriptor)
        if i == 3 and c['mismatch'] >= 0:
            actual_descriptor[c['mismatch']] ^= 1
        slot = SLOTS + index * 32
        put(slot + 8, 0x12345678 if c['ready'] else 0,
            c['generation'], 0x08000000 if c['lazy'] else 0, *actual_descriptor)
    roots = [tree(nodes, 0) for nodes in (store_nodes, name_nodes, descriptor_nodes)]
    put(REG + 0x24, 0 if c['empty'] & 1 else roots[0])
    put(STORE + 0x104, 0 if c['empty'] & 2 else roots[1])
    put(STORE + 0xec, 0 if c['empty'] & 4 else roots[2])
    put(STORE + 0x138, STORE + 0x500, STORE + 0x500 + c['callbacks'] * 24)
    for i in range(c['callbacks']):
        put(STORE + 0x500 + i * 24 + 20, 0x5000200 + i * 4)
    callback_slot = SLOTS + (c['base_index'] + 3) * 32
    expected_callback_handle = packed(c['base_index'] + 3, c['generation'], c['type'])
    put(DEST, *([0xdeadbeef] * 4))
    put(INPUT, *c['source'])
    put(QUERY, *(c['descriptor'] if c['function'] == 'descriptor' else [c['query']]))
    fn = c['function']
    args = {'named_store': [REG, QUERY], 'describe': [DEST, STORE, INPUT],
            'descriptor': [DEST, STORE, QUERY], 'name': [DEST, STORE, QUERY],
            'canonical': [DEST, REG, INPUT], 'object': [REG, INPUT]}[fn]
    u.reg_write(UC_ARM_REG_SP, STACK)
    u.reg_write(UC_ARM_REG_LR, STOP)
    preserved = [UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7,
                 UC_ARM_REG_R8, UC_ARM_REG_R9, UC_ARM_REG_R10, UC_ARM_REG_R11]
    for i, reg in enumerate(preserved):
        u.reg_write(reg, 0xabc00000 + i)
    for reg, value in zip([UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3], args + [0] * 4):
        u.reg_write(reg, value)
    events = []
    try:
        u.emu_start(FUNCTIONS[fn], STOP, count=10000)
    except (UcError, AssertionError) as error:
        raise RuntimeError(f"{fn}/{c['label']} at {u.reg_read(UC_ARM_REG_PC):08x}: {error}") from error
    assert u.reg_read(UC_ARM_REG_PC) == STOP, c
    assert u.reg_read(UC_ARM_REG_SP) == STACK, c
    assert all(u.reg_read(reg) == 0xabc00000 + i for i, reg in enumerate(preserved)), c
    size = 3 if fn == 'describe' else 2 if fn in ('descriptor', 'name', 'canonical') else 0
    if size:
        assert u.reg_read(UC_ARM_REG_R0) == DEST, c
        c['result'] = words(DEST, size)
    else:
        c['result'] = [u.reg_read(UC_ARM_REG_R0)]
    assert words(DEST + size * 4, 4 - size) == [0xdeadbeef] * (4 - size), c
    c['events'] = events

# Save the exact decoded instructions beside the existing Ghidra pseudocode.
md = Cs(CS_ARCH_ARM, CS_MODE_ARM)
ranges = [(0x11e6840, 0x11e6b0c), (0x11e7570, 0x11e7710), (0x1ea034, 0x1ea0ac)]
assembly = []
for start, end in ranges:
    for instruction in md.disasm(bytes(u.mem_read(start, end - start)), start):
        assembly.append(f'{instruction.address:08x}: {instruction.mnemonic:8} {instruction.op_str}')
(out / 'instructions.asm').write_text('\n'.join(assembly) + '\n', encoding='utf-8')
pseudo = out / 'pseudocode'
pseudo.mkdir(exist_ok=True)
for address in FUNCTIONS.values():
    for path in (base / 'native_analysis/core_round3/full_library/functions').glob(f'{address:08x}_*.c'):
        shutil.copy2(path, pseudo / path.name)
record = dict(original_sha256=hashlib.sha256((base / 'raw/lib/armeabi/libSrc.so').read_bytes()).hexdigest(),
              cases_passed=len(CASES), cases=CASES,
              executed_original_functions=[f'{v:08x}' for v in FUNCTIONS.values()] +
                  ['001e9bb4', '011e62c8', '011e7538', '011e6620'],
              scope='Original ARM tree traversal, symbolic conversion, descriptor packing and object resolution run together. '
                    'Only intern singleton/retain/release/text services and external lazy callback bodies are mocked. '
                    'Seven-node balanced read-only trees; no insertion, balancing, allocation, invalid descriptor-index handles, '
                    'concurrent mutation, or real resource loading. Stack, callee-saved registers and output canaries checked.')
(out / 'validation.json').write_text(json.dumps(record, indent=2), encoding='utf-8')
print('PASS', len(CASES), 'original ARM engine registry checks')
