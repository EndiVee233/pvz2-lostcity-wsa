param([string]$Zig = 'K:\pvz2-tools\zig\zig-windows-x86_64-0.13.0\zig.exe', [switch]$LibraryOnly)
$ErrorActionPreference = 'Stop'
Push-Location $PSScriptRoot
try {
    New-Item -ItemType Directory -Force build | Out-Null
    & $Zig c++ -std=c++17 -Wall -Wextra -Werror -O0 -g -I include -c src/profile_store.cpp -o build/profile_store.o
    if ($LASTEXITCODE -ne 0) { throw 'Profile library compilation failed' }
    & $Zig c++ -std=c++17 -Wall -Wextra -Werror -O0 -g -I include -c src/profile_dirty.cpp -o build/profile_dirty.o
    if ($LASTEXITCODE -ne 0) { throw 'Dirty state compilation failed' }
    & $Zig c++ -std=c++17 -Wall -Wextra -Werror -O0 -g -I include -c src/engine_handles.cpp -o build/engine_handles.o
    if ($LASTEXITCODE -ne 0) { throw 'Engine handle compilation failed' }
    & $Zig c++ -std=c++17 -Wall -Wextra -Werror -O0 -g -I include -c src/engine_registry.cpp -o build/engine_registry.o
    if ($LASTEXITCODE -ne 0) { throw 'Engine registry compilation failed' }
    & $Zig c++ -std=c++17 -Wall -Wextra -Werror -O0 -g -I include -c src/engine_slots.cpp -o build/engine_slots.o
    if ($LASTEXITCODE -ne 0) { throw 'Engine slot compilation failed' }
    & $Zig c++ -std=c++17 -Wall -Wextra -Werror -O0 -g -I include -c src/engine_slot_index.cpp -o build/engine_slot_index.o
    if ($LASTEXITCODE -ne 0) { throw 'Recovered descriptor index compilation failed' }
    & $Zig c++ -std=c++17 -Wall -Wextra -Werror -O0 -g -I include -c src/engine_intern.cpp -o build/engine_intern.o
    if ($LASTEXITCODE -ne 0) { throw 'Engine intern pool compilation failed' }
    & $Zig c++ -std=c++17 -Wall -Wextra -Werror -O0 -g -I include -c src/engine_name_index.cpp -o build/engine_name_index.o
    if ($LASTEXITCODE -ne 0) { throw 'Name index compilation failed' }
    & $Zig c++ -std=c++17 -Wall -Wextra -Werror -O0 -g -I include -c src/engine_store.cpp -o build/engine_store.o
    if ($LASTEXITCODE -ne 0) { throw 'Owned store compilation failed' }
    & $Zig c++ -std=c++17 -Wall -Wextra -Werror -O0 -g -I include -c src/engine_package_paths.cpp -o build/engine_package_paths.o
    if ($LASTEXITCODE -ne 0) { throw 'Package paths compilation failed' }
    & $Zig c++ -std=c++17 -Wall -Wextra -Werror -O0 -g -I include -c src/engine_rton_writer.cpp -o build/engine_rton_writer.o
    if ($LASTEXITCODE -ne 0) { throw 'RTON writer compilation failed' }
    & $Zig c++ -std=c++17 -Wall -Wextra -Werror -O0 -g -I include -c src/engine_rton_input.cpp -o build/engine_rton_input.o
    if ($LASTEXITCODE -ne 0) { throw 'RTON input compilation failed' }
    & $Zig c++ -std=c++17 -Wall -Wextra -Werror -O0 -g -I include -c src/engine_rton_normalizer.cpp -o build/engine_rton_normalizer.o
    if ($LASTEXITCODE -ne 0) { throw 'RTON normalizer compilation failed' }
    & $Zig c++ -std=c++17 -Wall -Wextra -Werror -O0 -g -I include -c src/engine_rton_reader.cpp -o build/engine_rton_reader.o
    if ($LASTEXITCODE -ne 0) { throw 'Indexed RTON reader compilation failed' }
    & $Zig c++ -std=c++17 -Wall -Wextra -Werror -O0 -g -I include -c src/engine_rton_scalars.cpp -o build/engine_rton_scalars.o
    if ($LASTEXITCODE -ne 0) { throw 'RTON scalar compilation failed' }
    & $Zig c++ -std=c++17 -Wall -Wextra -Werror -O0 -g -I include -c src/engine_reference_reader.cpp -o build/engine_reference_reader.o
    if ($LASTEXITCODE -ne 0) { throw 'Reference reader compilation failed' }
    & $Zig c++ -std=c++17 -Wall -Wextra -Werror -O0 -g -I include -c src/engine_reflection.cpp -o build/engine_reflection.o
    if ($LASTEXITCODE -ne 0) { throw 'Reflection data runtime compilation failed' }
    & $Zig c++ -std=c++17 -Wall -Wextra -Werror -O0 -g -I include -c src/engine_wave_data.cpp -o build/engine_wave_data.o
    if ($LASTEXITCODE -ne 0) { throw 'Wave data compilation failed' }
    & $Zig c++ -std=c++17 -Wall -Wextra -Werror -O0 -g -I include -c src/engine_level_data.cpp -o build/engine_level_data.o
    if ($LASTEXITCODE -ne 0) { throw 'Level data compilation failed' }
    & $Zig c++ -std=c++17 -Wall -Wextra -Werror -O0 -g -I include -c src/engine_win_condition.cpp -o build/engine_win_condition.o
    if ($LASTEXITCODE -ne 0) { throw 'Win condition compilation failed' }
    & $Zig ar rcs build/pvz2_profiles.lib build/profile_store.o build/profile_dirty.o build/engine_handles.o build/engine_registry.o build/engine_slots.o build/engine_slot_index.o build/engine_intern.o build/engine_name_index.o build/engine_store.o build/engine_package_paths.o build/engine_rton_writer.o build/engine_rton_input.o build/engine_rton_normalizer.o build/engine_rton_reader.o build/engine_rton_scalars.o build/engine_reference_reader.o build/engine_reflection.o build/engine_wave_data.o build/engine_level_data.o build/engine_win_condition.o
    if ($LASTEXITCODE -ne 0) { throw 'Profile library archive failed' }
    if ($LibraryOnly) { return }
    & $Zig c++ -std=c++17 -Wall -Wextra -Werror -O0 -g -I include tests/profile_tests.cpp build/pvz2_profiles.lib -o build/profile_tests.exe
    if ($LASTEXITCODE -ne 0) { throw 'Profile executable link failed' }
    & ./build/profile_tests.exe
    if ($LASTEXITCODE -ne 0) { throw 'Profile behavior checks failed' }
    & $Zig c++ -std=c++17 -Wall -Wextra -Werror -O0 -g -I include tests/dirty_tests.cpp build/pvz2_profiles.lib -o build/dirty_tests.exe
    if ($LASTEXITCODE -ne 0) { throw 'Dirty state executable link failed' }
    & ./build/dirty_tests.exe
    if ($LASTEXITCODE -ne 0) { throw 'Dirty state behavior checks failed' }
    & $Zig c++ -std=c++17 -Wall -Wextra -Werror -O0 -g -I include tests/engine_handle_tests.cpp build/pvz2_profiles.lib -o build/engine_handle_tests.exe
    if ($LASTEXITCODE -ne 0) { throw 'Engine handle executable link failed' }
    & ./build/engine_handle_tests.exe
    if ($LASTEXITCODE -ne 0) { throw 'Engine handle differential checks failed' }
    & $Zig c++ -std=c++17 -Wall -Wextra -Werror -O0 -g -I include tests/engine_registry_tests.cpp build/pvz2_profiles.lib -o build/engine_registry_tests.exe
    if ($LASTEXITCODE -ne 0) { throw 'Engine registry executable link failed' }
    & ./build/engine_registry_tests.exe
    if ($LASTEXITCODE -ne 0) { throw 'Engine registry differential checks failed' }
    & $Zig c++ -std=c++17 -Wall -Wextra -Werror -O0 -g -I include tests/engine_slot_tests.cpp build/pvz2_profiles.lib -o build/engine_slot_tests.exe
    if ($LASTEXITCODE -ne 0) { throw 'Engine slot executable link failed' }
    & ./build/engine_slot_tests.exe
    if ($LASTEXITCODE -ne 0) { throw 'Engine slot differential checks failed' }
    & $Zig c++ -std=c++17 -Wall -Wextra -Werror -O0 -g -I include tests/descriptor_index_tests.cpp build/pvz2_profiles.lib -o build/descriptor_index_tests.exe
    if ($LASTEXITCODE -ne 0) { throw 'Descriptor index executable link failed' }
    & ./build/descriptor_index_tests.exe
    if ($LASTEXITCODE -ne 0) { throw 'Descriptor index differential checks failed' }
    & $Zig c++ -std=c++17 -Wall -Wextra -Werror -O0 -g -I include tests/engine_intern_tests.cpp build/pvz2_profiles.lib -o build/engine_intern_tests.exe
    if ($LASTEXITCODE -ne 0) { throw 'Engine intern executable link failed' }
    & ./build/engine_intern_tests.exe
    if ($LASTEXITCODE -ne 0) { throw 'Engine intern differential checks failed' }
    & $Zig c++ -std=c++17 -Wall -Wextra -Werror -O0 -g -I include tests/name_index_tests.cpp build/pvz2_profiles.lib -o build/name_index_tests.exe
    if ($LASTEXITCODE -ne 0) { throw 'Name index executable link failed' }
    & ./build/name_index_tests.exe
    if ($LASTEXITCODE -ne 0) { throw 'Name index differential checks failed' }
    & $Zig c++ -std=c++17 -Wall -Wextra -Werror -O0 -g -I include tests/owned_store_tests.cpp build/pvz2_profiles.lib -o build/owned_store_tests.exe
    if ($LASTEXITCODE -ne 0) { throw 'Owned store executable link failed' }
    & ./build/owned_store_tests.exe
    if ($LASTEXITCODE -ne 0) { throw 'Owned store differential checks failed' }
    & $Zig c++ -std=c++17 -Wall -Wextra -Werror -O0 -g -I include tests/store_package_tests.cpp build/pvz2_profiles.lib -o build/store_package_tests.exe
    if ($LASTEXITCODE -ne 0) { throw 'Store package executable link failed' }
    & ./build/store_package_tests.exe
    if ($LASTEXITCODE -ne 0) { throw 'Store package differential checks failed' }
    & $Zig c++ -std=c++17 -Wall -Wextra -Werror -O0 -g -I include tests/rton_metadata_tests.cpp build/pvz2_profiles.lib -o build/rton_metadata_tests.exe
    if ($LASTEXITCODE -ne 0) { throw 'RTON metadata executable link failed' }
    & ./build/rton_metadata_tests.exe
    if ($LASTEXITCODE -ne 0) { throw 'RTON metadata byte/cache checks failed' }
    & $Zig c++ -std=c++17 -Wall -Wextra -Werror -O0 -g -I include tests/rton_input_tests.cpp build/pvz2_profiles.lib -o build/rton_input_tests.exe
    if ($LASTEXITCODE -ne 0) { throw 'RTON input executable link failed' }
    & ./build/rton_input_tests.exe
    if ($LASTEXITCODE -ne 0) { throw 'RTON input value/position checks failed' }
    & $Zig c++ -std=c++17 -Wall -Wextra -Werror -O0 -g -I include tests/rton_normalizer_tests.cpp build/pvz2_profiles.lib -o build/rton_normalizer_tests.exe
    if ($LASTEXITCODE -ne 0) { throw 'RTON normalizer executable link failed' }
    & ./build/rton_normalizer_tests.exe
    if ($LASTEXITCODE -ne 0) { throw 'RTON normalizer byte/table checks failed' }
    & $Zig c++ -std=c++17 -Wall -Wextra -Werror -O0 -g -I include tools/rton_normalize.cpp build/pvz2_profiles.lib -o build/rton_normalize.exe
    if ($LASTEXITCODE -ne 0) { throw 'RTON normalization tool link failed' }
    & $Zig c++ -std=c++17 -Wall -Wextra -Werror -O0 -g -I include tests/rton_reader_tests.cpp build/pvz2_profiles.lib -o build/rton_reader_tests.exe
    if ($LASTEXITCODE -ne 0) { throw 'Indexed RTON reader executable link failed' }
    & ./build/rton_reader_tests.exe
    if ($LASTEXITCODE -ne 0) { throw 'Indexed RTON reader return/cursor checks failed' }
    & $Zig c++ -std=c++17 -Wall -Wextra -Werror -O0 -g -I include tools/rton_inspect.cpp build/pvz2_profiles.lib -o build/rton_inspect.exe
    if ($LASTEXITCODE -ne 0) { throw 'RTON inspection tool link failed' }
    & $Zig c++ -std=c++17 -Wall -Wextra -Werror -O0 -g -I include tests/rton_scalar_tests.cpp build/pvz2_profiles.lib -o build/rton_scalar_tests.exe
    if ($LASTEXITCODE -ne 0) { throw 'RTON scalar executable link failed' }
    & ./build/rton_scalar_tests.exe
    if ($LASTEXITCODE -ne 0) { throw 'RTON scalar bits/cursor checks failed' }
    & $Zig c++ -std=c++17 -Wall -Wextra -Werror -O0 -g -I include tests/reflection_chain_tests.cpp build/pvz2_profiles.lib -o build/reflection_chain_tests.exe
    if ($LASTEXITCODE -ne 0) { throw 'Reflection chain executable link failed' }
    & ./build/reflection_chain_tests.exe
    if ($LASTEXITCODE -ne 0) { throw 'Reflection chain full-state checks failed' }
    & $Zig c++ -std=c++17 -Wall -Wextra -Werror -O0 -g -I include tools/rton_load_objects.cpp build/pvz2_profiles.lib -o build/rton_load_objects.exe
    if ($LASTEXITCODE -ne 0) { throw 'Object data loader tool link failed' }
    & $Zig c++ -std=c++17 -Wall -Wextra -Werror -O0 -g -I include tests/rton_float_tests.cpp build/pvz2_profiles.lib -o build/rton_float_tests.exe
    if ($LASTEXITCODE -ne 0) { throw 'RTON float executable link failed' }
    & ./build/rton_float_tests.exe
    if ($LASTEXITCODE -ne 0) { throw 'RTON float bits/cursor checks failed' }
    & $Zig c++ -std=c++17 -Wall -Wextra -Werror -O0 -g -I include tests/intro_reflection_tests.cpp build/pvz2_profiles.lib -o build/intro_reflection_tests.exe
    if ($LASTEXITCODE -ne 0) { throw 'Inherited reflection executable link failed' }
    & ./build/intro_reflection_tests.exe
    if ($LASTEXITCODE -ne 0) { throw 'Inherited reflection full-state checks failed' }
    & $Zig c++ -std=c++17 -Wall -Wextra -Werror -O0 -g -DPVZ2_RAILCART_FIXTURES=1 -I include tests/intro_reflection_tests.cpp build/pvz2_profiles.lib -o build/railcart_reflection_tests.exe
    if ($LASTEXITCODE -ne 0) { throw 'Railcart reflection executable link failed' }
    & ./build/railcart_reflection_tests.exe
    if ($LASTEXITCODE -ne 0) { throw 'Railcart reflection nested-record checks failed' }
    & $Zig c++ -std=c++17 -Wall -Wextra -Werror -O0 -g -DPVZ2_SEEDBANK_FIXTURES=1 -I include tests/intro_reflection_tests.cpp build/pvz2_profiles.lib -o build/seedbank_reflection_tests.exe
    if ($LASTEXITCODE -ne 0) { throw 'SeedBank reflection executable link failed' }
    & ./build/seedbank_reflection_tests.exe
    if ($LASTEXITCODE -ne 0) { throw 'SeedBank reflection enum/bool/list checks failed' }
    & $Zig c++ -std=c++17 -Wall -Wextra -Werror -O0 -g -DPVZ2_WAVE_FIXTURES=1 -I include tests/intro_reflection_tests.cpp build/pvz2_profiles.lib -o build/wave_reflection_tests.exe
    if ($LASTEXITCODE -ne 0) { throw 'Wave reflection executable link failed' }
    & ./build/wave_reflection_tests.exe
    if ($LASTEXITCODE -ne 0) { throw 'Wave reflection nested-reference checks failed' }
    & $Zig c++ -std=c++17 -Wall -Wextra -Werror -O0 -g -DPVZ2_LEVEL_FIXTURES=1 -I include tests/intro_reflection_tests.cpp build/pvz2_profiles.lib -o build/level_reflection_tests.exe
    if ($LASTEXITCODE -ne 0) { throw 'Level reflection executable link failed' }
    & ./build/level_reflection_tests.exe
    if ($LASTEXITCODE -ne 0) { throw 'Level reflection module-reference checks failed' }
    & $Zig c++ -std=c++17 -Wall -Wextra -Werror -O0 -g -I include tests/sundropper_tests.cpp build/pvz2_profiles.lib -o build/sundropper_tests.exe
    if ($LASTEXITCODE -ne 0) { throw 'SunDropper executable link failed' }
    & ./build/sundropper_tests.exe
    if ($LASTEXITCODE -ne 0) { throw 'SunDropper field checks failed' }
    & $Zig c++ -std=c++17 -Wall -Wextra -Werror -O0 -g -I include tests/sundropper_package_tests.cpp build/pvz2_profiles.lib -o build/sundropper_package_tests.exe
    if ($LASTEXITCODE -ne 0) { throw 'SunDropper real-package integration executable link failed' }
    # Requires local plaintext game resources; run explicitly with two file paths.
    & $Zig c++ -std=c++17 -Wall -Wextra -Werror -O0 -g -I include tests/win_condition_tests.cpp build/pvz2_profiles.lib -o build/win_condition_tests.exe
    if ($LASTEXITCODE -ne 0) { throw 'Win condition link failed' }
    & ./build/win_condition_tests.exe
    if ($LASTEXITCODE -ne 0) { throw 'Win condition checks failed' }
    & $Zig c++ -std=c++17 -Wall -Wextra -Werror -O0 -g -DPVZ2_WIN_PACKAGE=1 -I include tests/sundropper_package_tests.cpp build/pvz2_profiles.lib -o build/win_package_tests.exe
    if ($LASTEXITCODE -ne 0) { throw 'Win package link failed' }
    & $Zig c++ -std=c++17 -Wall -Wextra -Werror -O0 -g -I include tests/danger_module_tests.cpp build/pvz2_profiles.lib -o build/danger_module_tests.exe
    if ($LASTEXITCODE -ne 0) { throw 'Danger module link failed' }
    & ./build/danger_module_tests.exe
    if ($LASTEXITCODE -ne 0) { throw 'Danger module field checks failed' }
    & $Zig c++ -std=c++17 -Wall -Wextra -Werror -O0 -g -DPVZ2_DANGER_PACKAGE=1 -I include tests/sundropper_package_tests.cpp build/pvz2_profiles.lib -o build/danger_package_tests.exe
    if ($LASTEXITCODE -ne 0) { throw 'Danger package link failed' }
    & $Zig c++ -std=c++17 -Wall -Wextra -Werror -O0 -g -I include tests/brain_properties_tests.cpp build/pvz2_profiles.lib -o build/brain_properties_tests.exe
    if ($LASTEXITCODE -ne 0) { throw 'Brain properties link failed' }
    & ./build/brain_properties_tests.exe
    if ($LASTEXITCODE -ne 0) { throw 'Brain property checks failed' }
    & $Zig c++ -std=c++17 -Wall -Wextra -Werror -O0 -g -DPVZ2_BRAIN_PACKAGE=1 -I include tests/sundropper_package_tests.cpp build/pvz2_profiles.lib -o build/brain_package_tests.exe
    if ($LASTEXITCODE -ne 0) { throw 'Brain package link failed' }
} finally { Pop-Location }
