"""Execute original ARM/Thumb descriptor RB trees and capture exact topology.

No tree operations are mocked. Only operator new/delete are controlled. Pointer
links are normalized to sorted-key ranks so a host-pointer C++ tree can compare
every color, parent/child link, header extreme and value without address casts.
"""
import hashlib
import itertools
import json
import random
import shutil
import struct
from native_emulation_support import base, machine
from unicorn import UC_HOOK_CODE, UcError
from unicorn.arm_const import *
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM, CS_MODE_THUMB

OUT = base / 'native_analysis/core_round14/descriptor_index'
OUT.mkdir(parents=True, exist_ok=True)
TREE, HEADER, KEY, KEY_REF = 0x6000000, 0x6000004, 0x6000200, 0x6000300
STACK, STOP = 0x4080000, 0x5000100
NULL, HEAD = 0xffffffff, 0xfffffffe
FUNCTIONS = {'lower_bound': 0x11e5b08, 'unique_position': 0x11ecc78,
             'hinted_position': 0x11ecdc8, 'insert_node': 0x11ecff0,
             'rotate_left': 0x14e2c4c, 'rotate_right': 0x14e2c7c,
             'previous': 0x14e2cac, 'next': 0x14e2cf0, 'previous_wrapper': 0x14e2d58,
             'insert_rebalance': 0x14e2d78, 'erase_rebalance': 0x14e2e64}
SCENARIOS = []

def action(op, key, number=0, hint=None):
    return dict(op=op, key=list(key), value=[number & 0xffffffff, (number * 0x12345 + 7) & 0xffffffff],
                hint=list(hint) if hint is not None else None)

def key(i):
    return (i, 5, 9)

for ins in itertools.permutations(range(3)):
    for erase in itertools.permutations(range(3)):
        SCENARIOS.append(dict(label=f'exhaustive3-{ins}-{erase}', steps=
            [action('put', key(i), i + 1) for i in ins] + [action('erase', key(i)) for i in erase]))
for ins in itertools.permutations(range(4)):
    for erase in [ins, ins[::-1], (1, 3, 0, 2)]:
        SCENARIOS.append(dict(label=f'ordered4-{ins}-{erase}', steps=
            [action('put', key(i), i + 1) for i in ins] + [action('erase', key(i)) for i in erase]))
rng = random.Random(0x50565a32)
for n in range(32):
    ins = list(range(7)); erase = ins.copy()
    rng.shuffle(ins); rng.shuffle(erase)
    SCENARIOS.append(dict(label=f'seven-node-{n}', steps=[action('put', key(i), i + 1) for i in ins] +
                          [action('erase', key(i)) for i in erase]))
baseline = [(i, 0, 0) for i in [0, 2, 4, 6, 8, 10, 12]]
for hint in [None] + baseline:
    for q in range(15):
        SCENARIOS.append(dict(label=f'hint-{hint}-query-{q}', steps=
            [action('put', k, i + 1) for i, k in enumerate(baseline)] +
            [action('insert', (q, 0, 0), 0xabcdef01, hint), action('find', (q, 0, 0))]))
boundary_keys = [(0, 0, 0), (0, 0, 0xffffffff), (0, 1, 0), (0, 0x80000000, 0),
    (0, 0xffffffff, 0xffffffff), (1, 0, 0), (0x7fffffff, 0xffffffff, 0),
    (0x80000000, 0, 0), (0xffffffff, 0, 0), (0xffffffff, 0xffffffff, 0xffffffff)]
SCENARIOS.append(dict(label='unsigned-three-word-order', steps=
    [action('put', k, i + 1) for i, k in enumerate(boundary_keys[::-1])] +
    [action('find', k) for k in boundary_keys] + [action('erase', k) for k in boundary_keys]))
SCENARIOS.append(dict(label='duplicate-overwrite-and-missing-erase', steps=[
    action('find', key(0)), action('erase', key(0)), action('put', key(0), 1),
    action('insert', key(0), 2), action('find', key(0)), action('put', key(0), 3),
    action('find', key(0)), action('erase', key(0)), action('erase', key(0))]))
for n in range(8):
    keys = [(i // 8, (i % 8) * 0x20000000, (i * 11) & 0xffffffff) for i in range(40)]
    live = set(); steps = []
    for i in range(180):
        k = rng.choice(keys)
        op = rng.choices(['put', 'insert', 'erase', 'find'], [3, 3, 3, 1])[0]
        hint = rng.choice(sorted(live)) if op == 'insert' and live and rng.randrange(4) else None
        steps.append(action(op, k, i + 0x1000, hint))
        if op in ['put', 'insert']: live.add(k)
        elif op == 'erase': live.discard(k)
    remaining = sorted(live); rng.shuffle(remaining)
    steps += [action('erase', k) for k in remaining]
    SCENARIOS.append(dict(label=f'mixed-fixed-seed-{n}', steps=steps))

u, imports = machine()
u.mem_map(0x8000000, 0x100000)
cursor = 0x8000000
allocations, frees = set(), set()
hits = {name: 0 for name in FUNCTIONS}
deletion_features = {}
coverage = {}
phase = ''
last_addresses = {}

def put(address, *values):
    u.mem_write(address, struct.pack('<' + 'I' * len(values), *values))

def words(address, count=1):
    return list(struct.unpack('<' + 'I' * count, u.mem_read(address, count * 4)))

def hook(uc, address, size, _):
    global cursor
    for name, entry in FUNCTIONS.items():
        if address == entry:
            hits[name] += 1
    # Branch landmarks from original Thumb deletion, useful without claiming
    # exhaustive instruction/branch coverage of the entire C++ runtime.
    if phase == 'erase' and 0x14e2e64 <= address < 0x14e30d8:
        coverage[f'{address:08x}'] = coverage.get(f'{address:08x}', 0) + 1
    if address == 0x14d1a7c:
        size = uc.reg_read(UC_ARM_REG_R0)
        assert size == 0x28
        result = cursor; cursor += 0x40
        assert cursor < 0x8100000
        allocations.add(result)
        uc.mem_write(result, b'\xcc' * size)
        uc.reg_write(UC_ARM_REG_R0, result)
    elif address == 0x14d2e94:
        p = uc.reg_read(UC_ARM_REG_R0)
        assert p in allocations and p not in frees
        frees.add(p)
    elif address in imports:
        raise AssertionError(f'unexpected import {imports[address]}')
    else:
        return
    uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR))

u.hook_add(UC_HOOK_CODE, hook)

def call(address, args):
    u.reg_write(UC_ARM_REG_SP, STACK)
    u.reg_write(UC_ARM_REG_LR, STOP)
    saved = [UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7,
             UC_ARM_REG_R8, UC_ARM_REG_R9, UC_ARM_REG_R10, UC_ARM_REG_R11]
    for i, reg in enumerate(saved): u.reg_write(reg, 0xabc00000 + i)
    for reg, value in zip([UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3], list(args) + [0] * 4):
        u.reg_write(reg, value)
    u.emu_start(address, STOP, count=100000)
    assert u.reg_read(UC_ARM_REG_PC) == STOP and u.reg_read(UC_ARM_REG_SP) == STACK
    assert all(u.reg_read(reg) == 0xabc00000 + i for i, reg in enumerate(saved))
    return u.reg_read(UC_ARM_REG_R0)

def lookup(k):
    put(KEY, *k)
    return call(FUNCTIONS['lower_bound'], [words(HEADER + 4)[0], HEADER, KEY])

def snapshot():
    global last_addresses
    color, root, minimum, maximum = words(HEADER, 4)
    count = words(TREE + 0x14)[0]
    nodes = []; seen = set()
    def visit(n, parent, lo=None, hi=None):
        if not n: return 1
        assert n in allocations and n not in frees and n not in seen
        seen.add(n)
        values = words(n, 10)
        c, p, left, right = values[:4]
        k = tuple(values[4:7])
        assert p == parent and c in [0, 1]
        assert (lo is None or lo < k) and (hi is None or k < hi)
        if c == 0:
            assert not left or words(left)[0] == 1
            assert not right or words(right)[0] == 1
        a = visit(left, n, lo, k)
        nodes.append(n)
        b = visit(right, n, k, hi)
        assert a == b
        return a + c
    assert color == 0
    if root:
        assert words(root)[0] == 1
        visit(root, HEADER)
        assert minimum == nodes[0] and maximum == nodes[-1]
    else:
        assert minimum == maximum == HEADER
    assert len(nodes) == count and allocations - frees == set(nodes)
    last_addresses = {tuple(words(n + 16, 3)): n for n in nodes}
    ranks = {n: i for i, n in enumerate(nodes)}
    ranks.update({0: NULL, HEADER: HEAD})
    data = [color, ranks[root], ranks[minimum], ranks[maximum], count]
    for n in nodes:
        v = words(n, 10)
        data.extend([v[0], *[ranks[p] for p in v[1:4]], *v[4:7], *v[8:10]])
    return data

checkpoints = 0
for sc in SCENARIOS:
    cursor = 0x8000000
    allocations, frees = set(), set()
    u.mem_write(TREE, bytes(0x1000))
    put(HEADER, 0, 0, HEADER, HEADER)
    sc['initial'] = snapshot()
    for i, s in enumerate(sc['steps']):
        phase = s['op']
        before_addresses = last_addresses.copy()
        try:
            k = s['key']
            before = words(TREE + 0x14)[0]
            found = lookup(k)
            exists = found != HEADER and words(found + 16, 3) == k
            if phase == 'find':
                s['result'] = [1, *words(found + 32, 2)] if exists else [0]
            elif phase == 'erase':
                s['result'] = [int(exists)]
                if exists:
                    v = words(found, 4)
                    shape = 'two' if v[2] and v[3] else 'left' if v[2] else 'right' if v[3] else 'leaf'
                    feature = shape + ('-black' if v[0] else '-red')
                    deletion_features[feature] = deletion_features.get(feature, 0) + 1
                    assert call(FUNCTIONS['erase_rebalance'] | 1, [found, HEADER]) == found
                    call(0x14d2e94 | 1, [found])
                    put(TREE + 0x14, before - 1)
            else:
                if phase == 'put' and exists:
                    result = found
                else:
                    hint = found if phase == 'put' else HEADER if s['hint'] is None else lookup(s['hint'])
                    if phase == 'insert' and s['hint'] is not None:
                        assert hint != HEADER and words(hint + 16, 3) == s['hint']
                    # lookup(hint) changed the query scratch; restore inserted key.
                    put(KEY, *k); put(KEY_REF, KEY)
                    result = call(FUNCTIONS['insert_node'], [TREE, hint, 0, KEY_REF])
                    assert result != HEADER and words(result + 16, 3) == k
                inserted = words(TREE + 0x14)[0] != before
                if phase == 'put' or inserted: put(result + 32, *s['value'])
                s['result'] = [] if phase == 'put' else [int(inserted)]
            s['state'] = snapshot()
            assert all(n == last_addresses[k] for k, n in before_addresses.items() if k in last_addresses)
            checkpoints += 1
        except (UcError, AssertionError) as error:
            raise RuntimeError(f"{sc['label']}/{i}/{phase} PC={u.reg_read(UC_ARM_REG_PC):08x}: {error}") from error
    # Snapshot already verified every remaining allocation is an attached node.
    sc['allocation_calls'], sc['delete_calls'] = len(allocations), len(frees)

assert all(hits.values()), hits
for name, a, b, mode in [('descriptor_arm', 0x11ecc78, 0x11ed120, CS_MODE_ARM),
                        ('tree_thumb', 0x14e2c4c, 0x14e30d8, CS_MODE_THUMB)]:
    md = Cs(CS_ARCH_ARM, mode)
    assembly = [f'{x.address:08x}: {x.mnemonic:8} {x.op_str}' for x in md.disasm(bytes(u.mem_read(a, b - a)), a)]
    (OUT / (name + '.asm')).write_text('\n'.join(assembly) + '\n', encoding='utf-8')
folder = OUT / 'pseudocode'; folder.mkdir(exist_ok=True)
for address in FUNCTIONS.values():
    for p in (base / 'native_analysis/core_round3/full_library/functions').glob(f'{address:08x}_*.c'):
        shutil.copy2(p, folder / p.name)
record = dict(original_sha256=hashlib.sha256((base / 'raw/lib/armeabi/libSrc.so').read_bytes()).hexdigest(),
              scenarios_passed=len(SCENARIOS), checkpoints=checkpoints,
              function_entry_hits=hits, deletion_shapes=deletion_features,
              deletion_instruction_hits=coverage, scenarios=SCENARIOS,
              state_format='Header color, root/min/max key ranks, size; then key-ordered nodes: '
                'color,parent/left/right key ranks,key[3],handle[2]. Header=fffffffe; null=ffffffff. '
                'Full integer arrays compared, not hashes.',
              scope='Original ARM hint handling/unique lookup and Thumb rotations/insert/erase fixup. '
                'Only operator new/delete mocked with successful allocation; padding word ignored. '
                'Checks root/header, all links/colors/values, red-black invariants, allocation membership, surviving node addresses, stack and saved registers. '
                'No allocation failures, invalid hints, iterator misuse, reentrancy or concurrency.')
(OUT / 'validation.json').write_text(json.dumps(record, indent=2), encoding='utf-8')
print('PASS', len(SCENARIOS), 'original ARM/Thumb descriptor tree scenarios;', checkpoints, 'exact-state checkpoints')
print('Original function entry hits:', hits)
