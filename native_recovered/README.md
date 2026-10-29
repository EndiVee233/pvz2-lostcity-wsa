# 已恢复原生代码的独立编译工程

第三十三轮新增 ZombiesAteYourBrainsProperties 的 ZombieWinPositionX 字段（默认 -80.0），8 项原 ARM 位模式检查通过。可选第十五类模式在真实跨包装载中连接 8 条关卡模块引用，LevelModules 创建 6/66 个声明；失败玩法尚未实现。默认检查累计 45,591 项检查点。

公开仓库不附带大型生成诊断输入。可运行 `./build.ps1 -LibraryOnly -Zig C:\tools\zig\zig.exe` 独立编译静态库；不要求原游戏库、APK 或诊断输入。完整诊断需在持有原输入的本地工作区通过对应恢复/导出脚本生成 `tests/*_fixtures.inc`。CMake 可设置 `-DPVZ2_BUILD_DIAGNOSTICS=OFF` 关闭诊断目标，此路径未实测。

第三十二轮新增 DangerRoomModuleProperties：实际原工厂/反射读取的世界引用与设计器引用列表，77 个字段/解析身份检查点和 3 项宿主清理检查通过。`--danger-module` 可启用十四类；真实 Cowboy 模块连接增至 7 条，LevelModules 创建 5/66 个声明。实际玩法和被引用的设计器类仍未恢复。新增默认检查后，累计 45,583 项检查点通过；见根目录第三十二轮报告。

第三十一轮新增 `engine_win_condition.cpp`：原 ZombiesDeadWinCon 结束条件判断的有界实现，15 个原 ARM 返回值/分支/回调顺序场景通过。新增可选 ZombiesDeadWinConProperties 工厂后，真实跨包检查的模块连接从上一轮 5 条增至 6 条，LevelModules 创建 4/66 个声明。普通构建累计 45,506 项检查；完整棋盘、胜利事件和 Android 引擎尚未接入。见根目录第三十一轮报告。

最新第二十轮之后的进度已推进到第三十轮：默认装载工具仍保留第二十九轮十一类配置，新增 `--sundropper` 可启用第十二类 SunDropperProperties。五个浮点字段经原 ARM 工厂/反射读取核对，25 个新增字段检查通过。独立跨包场景读取真实 Cowboy 和 LevelModules 明文，模块连接从 4 增为 5；LevelModules 仍只创建 3/66 个声明，不具备阳光生成的游戏行为。详见根目录第三十轮报告。

这是从原生档案管理和引擎对象基础层恢复出的 C++17 模块，已在 Windows x64 编译和运行。它不是完整游戏，不能替换 Android 的 `libSrc.so`。

当前进度为第二十九轮：支持十一种具体数据类，加入 LevelDefinition 的关卡文本、奖励、模块引用、警告和 16 位字段。19 个编译单元、22 个检查程序累计通过 45,466 项，本轮新增 282 个原 ARM 数据状态检查点。Cowboy DangerRoom 的 5/5 个声明可创建，四条本包模块引用已连接，仍有 16 条外部符号引用未加载目标。GameFeature 元素读取仍受限，数据对象不执行游戏行为或回调，APK 未替换原引擎。[本轮报告](../第二十九轮关卡定义与模块连接恢复结果.md)，[全源码构建进度](../完全从源码编译进度.md)。

## 构建

本机已校验的便携 Zig 0.13.0 工具链位于 `K:\pvz2-tools\zig\zig-windows-x86_64-0.13.0`。执行：

```powershell
./build.ps1
# 其他位置的工具链：
./build.ps1 -Zig C:\tools\zig\zig.exe
```

生成 `build/pvz2_profiles.lib` 和 `build/profile_tests.exe`，随后运行行为检查。也提供标准 CMake 工程，可使用支持 C++17 的其他编译器构建；本轮实际验证的是上述 Zig 构建路径，未运行 CMake。

第十轮新增 `src/profile_dirty.cpp`，生成第二个程序 `build/dirty_tests.exe`。当前实测输出为 `PASS 18 profile lifecycle checks` 和 `PASS 47 dirty-state checks`。新增的四项原生操作包括修改标记、修改时间选择、保存请求门控和创建时间设置；源码中的 `DirtyServices` 保留尚未恢复的时钟服务和存储调度接口，客户端需要提供实现。它们已编入同一个静态库，但内存 ProfileStore 后端尚未自动调用这些新接口，检查程序直接调用恢复函数验证行为。

第十一轮开始恢复引擎对象系统：`src/engine_handles.cpp` 包含四个原函数的语义恢复和一个句柄解码辅助函数。新增 `build/engine_handle_tests.exe`，已通过 37 项与原始 ARM 结果的差分检查。参考数据由 `scripts/recover_engine_handles.py` 执行原始指令生成，再由 `scripts/export_engine_handle_fixtures.py` 转成已提交到本地工程的 C++ 输入。普通构建直接使用该输入文件，不需要运行模拟器。

这里的槽位、类型库选择、代数校验和符号句柄引用顺序来自原指令；资源加载回调和字符串驻留表仍通过接口接入。它们尚未替换 ProfileStore 的宿主句柄实现，也未接入 APK。源码中的两张类型表名称仅用于区分存储位置，不能据此推断它们的完整业务用途。

第十二轮新增 `src/engine_registry.cpp` 和 `include/engine_registry.hpp`，恢复六个原函数：按驻留名称编号查询类型库、读取槽位描述符、描述符转句柄、对象名称转句柄、名称句柄转直接句柄、注册表对象解析。新增 `build/engine_registry_tests.exe`，138 项原始 ARM/C++ 差分检查全部通过；当前四个程序合计 240 项检查通过。静态库无需原始 `.so` 即可构建和链接，完整游戏仍不能由这些源码生成。

本轮 ARM 检查让新恢复的六个函数和之前的赋值、槽位查找、类型表查询、延迟解析函数一起执行；仅驻留表服务和外部资源回调使用受控实现。覆盖无符号名称编号的高位边界、三字描述符的逐字比较、两种句柄编码在 `0x10000` 索引处的转换、槽位描述符不一致、空树、两张表的越界/空项、直接句柄失效、名称句柄引用顺序，以及零/一/两个延迟回调。检查输入来自原 ARM 实际结果，不在 C++ 检查中重新计算预期结果。

如需重新生成本轮参考数据，在工程父目录运行：

```powershell
python scripts/recover_engine_registry.py
python scripts/export_engine_registry_fixtures.py
```

普通构建不依赖原始库、Python、Ghidra 或模拟器；只有上述取证步骤会读取原始 `libSrc.so`，并使用 `tools/python_libs` 中的 Unicorn、Capstone 与 pyelftools。证据在 `../native_analysis/core_round12/engine_registry/`。

`StoreView`、`RegistryView` 和树节点采用宿主视图。第十二轮只恢复读取逻辑；第十四轮补齐描述符树，第十五轮补齐驻留池，第十六轮补齐名称树写入和对象库创建调度，第十七轮加入对象库元数据构造及清理。第十八轮补齐包名/路径变化和非空包注销；RTTI 和资源加载仍未补齐。原函数 `011e6890` 在描述符索引含失效句柄时会无检查地解引用空地址；恢复接口明确要求索引有效，宿主实现以 `std::logic_error` 报告违反前提，不宣称此异常与原游戏行为等价。现有检查限于稳定的树和槽位，不覆盖并发/回调扩容。新模块尚未接入 ProfileStore 或 APK。

第十三轮新增 `include/engine_slots.hpp`、`src/engine_slots.cpp`：`SlotPool` 恢复槽位增长、分配、回收、创建、引用释放、延迟销毁和标志访问等 16 个原函数的行为。其中默认描述符函数 `011f173c` 的已确认行为内联于创建路径。`SlotServices` 保留描述符索引、外部事件回调和对象虚表销毁边界。当前五个程序共通过 880 项行为/状态检查：原有 240 项、本轮 632 个 ARM/C++ 差分状态检查点，以及 8 项模块连接检查。

第十三轮曾使用 `src/engine_slot_index.cpp` 的 `HostDescriptorIndex/std::map` 宿主适配器连接创建/释放与描述符读取；它已在第十四轮替换为 `DescriptorIndex`，不再以 `std::map` 或重建平衡树实现描述符索引。通过 `index.attach(pool.view())` 获取当前视图；槽位扩容后必须重新获取，索引修改后需重新 attach，不能保留失效视图。

`SlotPool` 的链表采用槽位索引及四个哨兵值 `0xfffffffc..0xffffffff`，避免把 ARM32 指针强转为宿主指针；因此 `unknown00` 的内部链接值不具有原游戏地址含义。原始增长函数会复制槽位数组、重定位槽位和四组链表头尾指针；差分检查先把原地址规范化为同样的索引，再核对全部槽位的状态指纹。业务载荷的原有偏移不变，宿主对象地址仍作为 32 位令牌由调用方解释。

本轮原 ARM 验证包含 85 个多步场景，实际执行原始描述符树的插入、删除与平衡操作；仅分配器、libc 内存函数、注册表单例和外部回调/销毁函数采用受控实现。每步记录返回值、回调观察、四组链表、计数、全部槽位和排序后的索引内容。大索引的初始状态通过批量构造准备，C++ 通过重复 `take_slot()` 达到同一状态；该准备过程不计入原 ARM 恢复证据。

重新取证与导出本轮参考数据：

```powershell
python scripts/recover_engine_slots.py
python scripts/export_engine_slot_fixtures.py
```

普通构建仍直接使用已导出的参考数据，不读取原库。本轮新增程序为 `build/engine_slot_tests.exe`，证据位于 `../native_analysis/core_round13/engine_slots/`。接口要求增长不缩容、分配成功、类型编号有效，并要求回调不移动当前槽位、不重入释放或抛出异常；未覆盖原分配失败语义、并发、实际游戏对象类、RTTI、完整资源加载和 Android 接入。

第十四轮的 `src/engine_slot_index.cpp` 已实现原来的 lower-bound、普通/提示插入位置、前驱/后继、左右旋转、插入平衡、双子节点删除移植及删除平衡。节点采用原始红=0、黑=1 和红色头节点规则；`attach` 仅将真实树的连接映射到读取视图，不改变拓扑。宿主 `new/delete`、指针宽度、递归析构和视图映射属于移植边界，不宣称与 ARM32 二进制 ABI 兼容。

新增 `build/descriptor_index_tests.exe` 对照 270 个原 ARM/Thumb 场景、3,995 个操作后完整状态，包括根/极值、每个节点的父子关系、颜色、三字键、两字句柄和计数。这里逐个整数比较，不使用状态哈希。原 ARM 和 C++ 都检查红黑性质及存活节点地址稳定；原有 632 个槽位状态检查点和 8 项模块连接检查已经使用新索引重新通过。六个程序共 4,875 项通过，CMake 目标同步但未实际执行。

本轮取证只替换 `operator new/delete` 的分配边界，所有查找、提示处理、旋转及平衡都执行原始指令。固定种子的混合操作及多种插入/删除排列覆盖高位无符号键、重复键、缺失删除、提示回退、根/叶/单子/双子节点删除。入口计数与删除指令执行记录保存在 `../native_analysis/core_round14/descriptor_index/validation.json`，并非完整分支覆盖声明。

```powershell
python scripts/recover_descriptor_index.py
python scripts/export_descriptor_index_fixtures.py
```

上述步骤重新产生第十四轮取证参考数据；普通构建直接使用导出的 `tests/descriptor_index_fixtures.inc`。尚未覆盖分配失败、无效提示、迭代器越界、并发和重入。ProfileStore 自身仍保留独立的宿主档案后端；第十四轮结束时字符串驻留表仍未补齐，第十五轮进展见下文。

第十五轮新增 `include/engine_intern.hpp`、`src/engine_intern.cpp`。`InternPool` 实现 `InternStrings`，可直接传给 `assign_handle`、`canonical_handle` 和 `resolve_registered_object`；它包含真实驻留计数、文本到条目的红黑树、编号指针表增长和空闲/活动链表。`intern` 只取得编号而不增加引用；`acquire` 才增加引用并产生 `InternValue`。编号从 1 开始，0 为空文本；归零条目进入空闲队尾，下次从该尾复用，所以编号不包含槽位句柄那样的代数保护。

新 `include/recovered_rb_tree.hpp` 提供从第十四轮源码抽出的六个共用前驱/后继/旋转/平衡辅助函数。描述符树和驻留树都直接使用它；描述符的全部 3,995 项精确树状态检查在抽取后重新通过。驻留专用的字符串比较、插入位置和链表管理另按原函数恢复，没有改用 `std::map`。

本轮 35 个原 ARM 场景共 1,240 个完整状态检查点，逐项比较编号容量、全部条目/文本/计数、空闲与活动链表、索引颜色和父子关系。名称句柄场景直接执行原驻留函数和解析链；原 Android 宽字符串赋值也实际执行了 460 次。受控边界是成功分配的分配器、libc 内存/宽字符原语及单线程 ARM kuser 比较交换辅助入口，未将这些边界实现误记为已恢复的游戏代码。

普通驻留值赋值 `assign_value` 按 `00158a20` 先 release 旧编号，再 retain 新编号，即使二者相同；这与两字名称句柄的先 retain 后 release 顺序不同。单引用的同编号赋值会先清掉该条目的文本/索引，再把已空闲条目的计数增回 1，本轮保留并对照了这一原始行为。`release_value` 也保留原函数不清除输入值字段的行为。

`std::u32string` 替换了 Android COW 宽字符串的存储 ABI，`text_address` 返回可传给 `text` 读取的编号令牌，不能当成宿主或原 ARM 地址解引用。对象池移植为显式实例：初始化布局有原指令依据，但全局单例发布、销毁及线程语义未恢复。分配失败、无效编号、重入和并发仍在验证范围外。

```powershell
python scripts/recover_engine_intern.py
python scripts/export_engine_intern_fixtures.py
```

新增程序为 `build/engine_intern_tests.exe`；普通构建使用已导出的参考数据，无需原库。取证记录在 `../native_analysis/core_round15/engine_intern/`。目前七个程序共通过 6,115 项检查，标准 CMake 目标已加入但未实际运行。类型名称/对象名称索引的完整写入、类型注册与 RTTI、真实对象类、资源和关卡运行时仍未补齐，整个游戏尚不能从源码生成可运行 APK。

第十六轮新增 `include/engine_name_index.hpp`、`src/engine_name_index.cpp`。`TypeNameIndex` 使用无符号驻留编号映射对象库类型；`ObjectNameIndex` 使用同类编号映射三字描述符。两者使用已恢复的红黑树插入位置、提示、旋转、平衡和删除行为；对象名称节点 retain/read 名称并在删除时 release，类型名称树节点本身不增加引用。调用方须让驻留池先于对象名称索引建立、晚于索引销毁。

`bind_object_name` 对应 `011ee270`：先删除旧映射，再检查新句柄。空句柄删除后返回成功；失效、越界或类型不符句柄删除旧映射后返回失败；有效句柄复制槽位的三字描述符进入名称节点。该行为不同于“失败时保留旧映射”，本轮按原 ARM 结果保留。

`RegistryBanks::ensure` 对应 `011eefb0` 的调度流程：按 `0x2000` 位选择双表，缺少目标槽位时增长到 `index + 16` 并填零，调用构造服务，先发布槽位，再依次安装面向注册表 `0x34/0x44/0x54/0x64` 的四个转发器。已存在对象库时直接复用，不重建或重复安装。完整 `011ec764` 构造器和转发器函数体仍通过 `StoreFactory` 提供，本轮未声称完成类型构造/RTTI；逻辑容量与原数值核对，宿主分配器地址/容量 ABI 不在等价范围内。

新增 `build/name_index_tests.exe`：180 个名称树场景（2,862 点）核对完整树状态和驻留调用顺序，15 个真实驻留池名称绑定场景（1,032 点）核对树/池及对象解析，5 个对象库调度场景（336 点）核对双表、复用、发布及转发安装次序。原始树与扩容指令实际执行；原始对象库构造函数体在调度取证中采用受控实现。合计 4,230 个 ARM 对照点通过。

另有 12 项动态模块连接检查，从实际源码 `SlotPool` 创建对象后写入名称索引，使用真实驻留池形成名称句柄，确认扩容后仍可解析、释放后目标失效、别名保留到显式删除、最终名称引用归零。本轮八个程序累计 10,357 项检查通过，CMake 目标同步但未实际执行。

```powershell
python scripts/recover_name_indices.py
python scripts/export_name_index_fixtures.py
```

证据位于 `../native_analysis/core_round16/name_indices/`，普通构建直接使用导出输入，无需原始库。已覆盖的名称树写入不等于完整类型注册：`$` 前缀/数字默认名称、包别名规范化、构造器其他字段、RTTI、真实对象类与资源运行时仍未补齐。原 APK、安装内容、存档在本轮未修改。

第十七轮新增 `include/engine_store.hpp`、`src/engine_store.cpp`。`OwnedRegistry` 为前一轮的 `StoreFactory` 提供具体实现，拥有 `OwnedStore`、双表和类型名称索引；`OwnedStore` 接通真实 `InternPool`、`SlotPool`、描述符/对象名称索引。未给名称时先生成类型编号的十进制文本，再统一加 `$` 前缀；给定名称也再次加前缀，不自行去重。相同类型再次 ensure 会复用原对象库并忽略新配置。

`OwnedStore::reset(false)` 按活动链表尾反复释放引用，清名称索引，保留容量和延期销毁对象；`reset(true)` 先清延期对象，再逆序处理活动对象，清槽位存储/索引，并按保留容量重建代数为 1 的空闲槽位。两者先后触发面向注册表 `0x34/0x44` 的转发回调。注销先把保留容量置零并硬重置，再删除类型名称映射、清双表槽位、释放名称引用。当前 owner 不提供非空包修改，注销等价范围限于包 ID 保持零的路径。

名称冲突保留原行为：后创建的对象库覆盖同名称的类型映射，但先创建者注销时仍按名称直接删除该映射，不检查它是否已指向另一对象库。该顺序和回调观察状态都进入原始指令对照。

默认三字描述符的第三字来自注册表 `+0x18`，不是对象库名称编号。早期 `SlotPool` 接口的 `current_package` 参数名已改为中性的 `descriptor_seed`；`OwnedRegistry` 显式接收此种子，普通类型使用种子，高字 `0x40000000` 置位时仍用 `0xffffffff`。原注册表初始化器以时间生成此字段；该全局时钟初始化未纳入本 owner，对照检查显式使用 `0x87654321`。

新增 `build/owned_store_tests.exe` 实际执行原始 `011ec764`、`011ec274`、`011ea17c` 和转发函数；构造、重置、注销均未替换为桩。32 个场景、359 个检查点逐项核对对象库元数据、双表/类型索引、真实驻留池、所有槽位/链表、描述符/名称树及销毁/回调观察值。范围包括数字默认名、中文/非 BMP 名称、UTF-8 显示文本、标志字节、配置复用、名称冲突、软/硬重置、延迟/不拥有对象、注销再创建和两张表的默认描述符。旧有检查也全部通过，九个程序累计 10,716 项。

```powershell
python scripts/recover_owned_stores.py
python scripts/export_owned_store_fixtures.py
```

证据在 `../native_analysis/core_round17/owned_stores/`。普通构建不需要原始 `.so`；只有取证脚本需要原库。外部注册表回调和对象销毁体、成功分配的分配器、libc/kuser 原语仍是受控边界。宿主所有权、COW/指针 ABI、非空包修改、实际对象虚表/RTTI、回调重入或移动槽位、分配失败和并发不在等价范围内。软重置要求活动槽位引用为正；原代码可能在违反此前提时循环，宿主改为显式报错。CMake 目标同步但未实际运行。

## 来源与边界

`include/profile_lifecycle.hpp` 的五项操作来自第八轮语义恢复：按名称切换、按名称改名、昵称过滤、选择首个剩余档案、删除档案。地址、原始指令和 13 项有界 ARM 检查记录在 `../native_analysis/core_round8/profile_lifecycle`。前三项经过原始指令分支检查，后两项的原函数尚未纳入该 ARM 检查。

`src/profile_store.cpp` 是为独立运行新写的内存后端，实现名称查询、句柄解析、字符串搜索和对象移除；它不是反编译出的原始注册表实现。同步接口只记录请求事件，不连接云端或写盘。新建操作只提供该模块所需的最小初始化，并未恢复原游戏完整 PlayerInfo 默认值和事件体系。

`007be820` 的创建路径调用 `time()`，经 `00721ce4` 写入 PlayerInfo `+0x1ec`，随后复制到 ProfileMgr `+0x74`。工程采用显式传入的时间值保持测试可重现。该字段不等同于存档外层 UID，本后端句柄键也不冒充原游戏句柄编码。

ProfileStore 删除后的对象保留为失效记录以便检查旧句柄，枚举顺序由该宿主后端维护。它尚未改用恢复出的槽位引用计数和描述符索引，完整注册表排序、重入及线程规则仍未确认。项目内使用 `std::u32string` 表达 Android ARM32 的四字节宽字符，宿主容器与原游戏二进制 ABI 不兼容。

行为检查覆盖 18 项创建、选择、中文改名、事件顺序、过滤及删除场景。它们证明当前源码工程能编译和执行这些行为，不证明完整引擎等价或完整游戏可由源码构建。原 APK、用户存档和 WSA 安装内容不会由此工程修改。

第十八轮新增 `engine_package_paths` 与 `OwnedStore::set_package`，恢复字节路径及共用类型名称树的包别名管理。`store_package_tests.exe` 对照 92 个原始场景、462 个检查点，十个程序累计 11,178 项通过。重新取证使用 `scripts/recover_store_packages.py` 和 `scripts/export_store_package_fixtures.py`；证据在 `native_analysis/core_round18/store_packages/`。见根目录第十八轮报告。

第十九轮新增 `engine_rton_writer`，从对象库 owner 写出实际元数据 RTON 字节，保留整数编码选择、窄字符串缓存、逻辑零字节和原宽字符编码规则。`rton_metadata_tests.exe` 逐步对照 23 个原始场景、480 个字节/缓存状态；十一个程序累计 11,658 项通过。这里只写字段，未生成完整文档/对象载荷，也未补齐读取端。取证和导出使用 `scripts/recover_rton_metadata.py`、`scripts/export_rton_metadata_fixtures.py`；证据在 `native_analysis/core_round19/rton_metadata/`。缓存采用宿主逻辑映射，原流扩容、指针/COW/树 ABI、文件 I/O 仍未恢复。见根目录第十九轮报告。

第二十轮新增 `engine_rton_input`，恢复字节、32/64 位 varint/ZigZag、逻辑窄/原始宽字符串、原 UTF-8 解码和内部格式头检查。`rton_input_tests.exe` 对照 466 个原 ARM 场景、2,140 个返回值/位置检查点；包含上一轮原写入器输出与新读取器衔接。十二个程序累计 13,798 项通过。原始 RTON 到内部索引格式的转换、字段导航和对象载荷仍未恢复；越界裸读在宿主抛出异常，不宣称与原无检查访问等价。重新取证和导出使用 `scripts/recover_rton_input.py`、`scripts/export_rton_input_fixtures.py`，证据在 `native_analysis/core_round20/rton_input/`，详见根目录第二十轮报告。

第二十一轮新增 `engine_rton_normalizer` 和独立 `rton_normalize.exe`，恢复原始 RTON 到内部索引格式的数值/字符串/缓存/容器/引用/二进制转换。原 ARM 466 个输出/逻辑表场景全部一致，含 4 份现有资源明文；独立工具另行转换这 4 份文件，与 ARM 输出逐字节一致。十三个检查程序累计 14,264 项通过。工具只处理明文，解密沿用既有 Python 准备流程，未计为原生解密恢复。原树/COW/流 ABI、全局驻留副作用及字段导航/对象创建仍不属于本轮实现。参考数据由 `scripts/recover_rton_normalizer.py` 和 `scripts/export_rton_normalizer_fixtures.py` 生成；证据在 `native_analysis/core_round21/rton_normalizer/`，见根目录第二十一轮报告。

第二十二轮新增 `engine_rton_reader` 与 `rton_inspect.exe`，把原始明文规范化接到内部字段迭代、按名称查找、数组下标及窄文本视图。44 个原 ARM 场景、19,396 个返回值/位置检查点通过；受控 seek 准备不计入该数量。十四个程序累计 33,660 项通过，独立工具另对 4 份关卡、23 个对象声明摘要核对原 ARM 结果一致。这里只读类型/别名声明，未创建真实对象；通用标量转换、反射和完整资源运行时仍未恢复。取证与导出使用 `scripts/recover_rton_reader.py`、`scripts/export_rton_reader_fixtures.py`，证据在 `native_analysis/core_round22/rton_reader/`，见根目录第二十二轮报告。

第二十三轮新增 `engine_rton_scalars`，覆盖布尔/int32/uint32 入口的非 RTID 分支；7542 个原 ARM 位模式/位置检查点通过，十五个程序累计 41,202 项。参考数据由 `scripts/recover_rton_scalars.py`、`scripts/export_rton_scalar_fixtures.py` 生成。RTID 与十进制溢出边界仍显式缺失，本轮不增加完整语义操作计数。检查工具新增版本号字段，4 份关卡 version=1 与 ARM 结果一致。实际 APK 依赖核查脚本为 `scripts/audit_source_build_progress.py`；仍保留 8 个原库，当前仅 Windows 独立 C++ 模块可从源码构建。完整目标进度见根目录 `完全从源码编译进度.md`。

第二十四轮新增 `engine_reflection` 与 `engine_reference_reader`，用真实 EntityComponent_GroundEffect 的工厂/字段回调为依据，打通数据实例创建、枚举填充及二进制弱引用读取与解析。32 个连续操作、54 个完整状态检查点通过，16 个程序累计 41,256 项。原 ARM 运行真实注册管理器、工厂和属性分派；源码仅实现本类数据模式，不冒充通用 schema 构建或游戏行为恢复。`normalize_rton` 新增可选共享驻留池，修复跨加载的 RTID 临时编号副作用。`rton_load_objects.exe` 对聚焦场景生成与原 ARM 一致的循环引用图。证据在 `native_analysis/core_round24/reflection_chain/`；取证/导出为 `scripts/recover_reflection_chain.py`、`scripts/export_reflection_chain_fixtures.py`，单线程边界在 `scripts/reflection_emulation_support.py`。详见根目录第二十四轮报告。
