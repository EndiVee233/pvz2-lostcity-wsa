#@category APKAnalysis
from ghidra.app.decompiler import DecompInterface
from ghidra.util.task import ConsoleTaskMonitor
import os

args = getScriptArgs()
output = args[0]
if not os.path.isdir(output):
    os.makedirs(output)
name = currentProgram.getName()
decomp = DecompInterface()
decomp.openProgram(currentProgram)
monitor = ConsoleTaskMonitor()
count = 0
failed = []
destination = os.path.join(output, name + '.c')
with open(destination, 'w') as out:
    out.write('/* Ghidra-generated pseudocode; recovered types and names may be inaccurate. */\n')
    funcs = list(currentProgram.getFunctionManager().getFunctions(True))
    for function in funcs:
        if function.isExternal() or function.isThunk():
            continue
        if name == 'libSrc.so' and not (function.getName() == 'JNI_OnLoad' or function.getName().startswith('Java_')):
            continue
        try:
            disassemble(function.getEntryPoint())
            result = decomp.decompileFunction(function, 20, monitor)
            if result and result.decompileCompleted():
                out.write('\n/* Address: ' + str(function.getEntryPoint()) + ' */\n')
                out.write(result.getDecompiledFunction().getC())
                count += 1
            else:
                failed.append(function.getName())
        except Exception as error:
            failed.append(function.getName() + ': ' + str(error))
decomp.dispose()
with open(os.path.join(output, name + '.status.txt'), 'w') as out:
    out.write('Exported functions: %d\nFailed: %d\n%s\n' % (count, len(failed), '\n'.join(failed)))
print('NATIVE_EXPORT %s: %d functions, %d failed' % (name, count, len(failed)))
