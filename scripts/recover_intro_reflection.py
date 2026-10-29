"""Rounds 25..29: selected real inherited factories, fields and references.

Selected original factories, schema callbacks and both object load passes
execute in ARM. Flags select saved historical class profiles. Controlled
libc/allocator/single-thread boundaries only; game behavior is not ported.
"""
import hashlib,json,math,shutil,struct,sys
from reflection_emulation_support import h,seed
from unicorn import UC_HOOK_MEM_UNMAPPED,UC_HOOK_MEM_WRITE
from capstone import Cs,CS_ARCH_ARM,CS_MODE_ARM
LEVEL='--level' in sys.argv
WAVE='--wave' in sys.argv or LEVEL
SEED='--seedbank' in sys.argv or WAVE
RAIL='--railcart' in sys.argv or SEED
base=h.base;OUT=base/('native_analysis/core_round29/level_reflection' if LEVEL else 'native_analysis/core_round28/wave_reflection' if WAVE else 'native_analysis/core_round27/seedbank_reflection' if SEED else 'native_analysis/core_round26/railcart_reflection' if RAIL else 'native_analysis/core_round25/intro_reflection');OUT.mkdir(parents=True,exist_ok=True)
FUNCTIONS=dict(register=0x11f761c,lookup=0x11f6120,ancestry=0x11f595c,
 ground_factory=0x254bf8,game_factory=0x357a58,sheet_factory=0x7d27e0,module_factory=0x4496b8,
 intro_factory=0x3e0aa4,standard_factory=0x90cad4,danger_factory=0x2cb63c,
 create_pass=0x11ed5fc,fill_pass=0x11ead94,properties=0x11b9bb0,custom_property=0x11b7180,
 float_read=0x11f9ae8,int_read=0x11f8d6c,reference_read=0x11f4c90,resolve=0x1ea034,game_serialize=0x357cf4)
h.FUNCTIONS.update(FUNCTIONS)
if RAIL:FUNCTIONS.update(railcart_factory=0x89fd34,rail_resize=0x8a297c,cart_resize=0x8a1e30);h.FUNCTIONS.update(FUNCTIONS)
if SEED:FUNCTIONS.update(seedbank_factory=0x8a82a8,enum_read=0x11b1de0,boolean_read=0x11f8a24);h.FUNCTIONS.update(FUNCTIONS)
if WAVE:FUNCTIONS.update(wave_factory=0x9c4c70,wave_destroy=0x9c7a18,wave_record_destroy=0x9c7710);h.FUNCTIONS.update(FUNCTIONS)
if LEVEL:FUNCTIONS.update(level_factory=0x442f3c,level_destroy=0x44401c,feature_declined_read=0x11ab2bc);h.FUNCTIONS.update(FUNCTIONS)
for n in FUNCTIONS:h.hits.setdefault(n,0)
def unmapped(uc,access,address,size,value,unused):
 print('Unmapped',hex(address),'PC',hex(uc.reg_read(h.UC_ARM_REG_PC)),'LR',hex(uc.reg_read(h.UC_ARM_REG_LR)),'r6',hex(uc.reg_read(h.UC_ARM_REG_R6)),flush=True)
 return False
h.u.hook_add(UC_HOOK_MEM_UNMAPPED,unmapped)
ST,V,SER,SC=0x600c000,0x600c100,0x600c200,0x600d000
def vi(n):
 r=[]
 while n>=128:r.append((n&127)|128);n>>=7
 return bytes(r+[n])
def text(s):b=s.encode();return b'\x81'+vi(len(b))+b
def wide(s):b=s.encode();return vi(len(s))+vi(len(b))+b
def obj(pairs):return b''.join(text(k)+v for k,v in pairs)+b'\xff'
def array(values):return b'\x86\xfd'+vi(len(values))+b''.join(values)+b'\xfe'
def ref(name,pkg='.'):return b'\x83\x03'+wide(pkg)+wide(name)
def integer(n):return b'\x20'+struct.pack('<i',n)
def f32(n):return b'\x22'+struct.pack('<f',n)
def f64(n):return b'\x42'+struct.pack('<d',n)
def declaration(cls='DangerRoomLevelIntroProperties',aliases=(),props=(),data_mode=1):
 p=[('objclass',text(cls)),('aliases',array([text(x) for x in aliases]))]
 if data_mode:p.append(('objdata',b'\x85'+obj(props) if data_mode==1 else integer(7)))
 return b'\x85'+obj(p)
def document(values,version=1):return b'RTON\x01\0\0\0'+obj([('version',integer(version)),('objects',array(values))])+b'DONE'
operations=[]
def add(op,type=2,name='',data=b'',label=''):operations.append(dict(op=op,type=type,name=[ord(c) for c in name],data=list(data),label=label))
add('ensure',2,'local');add('ensure',3,'remote');add('package',2,'packages/CurrentLevel.rton' if LEVEL else 'packages/local.rton');add('package',3,'packages/remote.rton')
names=['RtObject','EntityComponent_GroundEffect','GameObject','PropertySheetBase','LevelModuleProperties','IntroModuleProperties','StandardLevelIntroProperties','DangerRoomLevelIntroProperties']
if RAIL:names.append('RailcartProperties')
if SEED:names.append('SeedBankProperties')
if WAVE:names.append('WaveGeneratorProperties')
if LEVEL:names.append('LevelDefinition')
add('load',data=document([declaration(cls=name,aliases=[name]) for name in names[1:]]),label='all-eleven-real-constructors' if LEVEL else 'all-ten-real-constructors' if WAVE else 'all-nine-real-constructors' if SEED else 'all-eight-real-constructors' if RAIL else 'all-seven-real-constructors')
rich=document([declaration(aliases=['Intro'],props=[('m_thisPtr',ref('Effect')),('ResourceGroupNames',array([text(x) for x in ['West','DangerRoom','West','', 'quoted"\\\n']])),('PanStartOffset',f32(-12.5)),('PanEndOffset',f64(900.125)),('PanRightDuration',integer(3)),('PanLeftDuration',text('2.75')),('NarrationID',integer(-7)),('SubsequentPlayNarrationID',text('123'))]),declaration(cls=names[1],aliases=['Effect'],props=[('m_type',text('surf')),('m_effect',ref('Intro'))])])
add('load',data=rich,label='inherited-fields-and-mixed-class-cycle')
add('populate',data=document([declaration(props=[('ResourceGroupNames',array([text('Replacement')]))]),declaration(cls=names[1])]),label='replace-list-preserve-absent-fields')
add('populate',data=document([declaration(props=[('ResourceGroupNames',integer(9)),('m_thisPtr',b'\x83\0'),('PanStartOffset',b'\x85\xff'),('NarrationID',b'\x85\xff')]),declaration(cls=names[1])]),label='nonarray-clears-list-unsupported-numeric-fallback')
add('populate',data=document([declaration(props=[('ResourceGroupNames',array([]))]),declaration(cls=names[1])]),label='empty-list')
add('load',data=document([declaration(aliases=['RemoteIntro'],props=[('m_thisPtr',ref('RemoteEffect','remote'))])]),label='forward-cross-package-inherited-reference')
add('load',3,data=document([declaration(cls=names[1],aliases=['RemoteEffect'],props=[('m_effect',ref('RemoteIntro','local'))])]),label='cross-package-target-appears')
for index,name in enumerate(names[2:]):
 props=[('m_thisPtr',ref('Self'))]
 if index>=2:props.append(('ResourceGroupNames',array([text('Shared'),text('Shared'),text('')])) )
 if index>=4:props.extend([('PanStartOffset',integer(-2147483648)),('PanEndOffset',b'\x26'+struct.pack('<I',0xffffffff)),('PanRightDuration',f64(1e-45)),('PanLeftDuration',f64(float('nan'))),('NarrationID',integer(2147483647)),('SubsequentPlayNarrationID',integer(-2147483648))])
 add('load',data=document([declaration(cls=name,aliases=['Self'],props=props)]),label='concrete-base-'+name)
add('load',data=document([declaration(aliases=['Ghost'],cls='UnknownClass'),declaration(cls='RtObject'),declaration(aliases=['Good'],props=[('m_thisPtr',ref('Ghost'))])]),label='unknown-and-abstract-holes')
add('load',data=document([declaration(aliases=['Same'],props=[('m_thisPtr',ref('Same'))]),declaration(cls=names[1],aliases=['Same'],props=[('m_effect',ref('Same'))])]),label='first-alias-wins-across-classes')
add('load',data=document([declaration(data_mode=0),declaration(data_mode=2)]),label='missing-and-nonobject-data')
add('load',data=document([declaration()],version=2),label='wrong-version-preserves-store')
add('load',data=document([]),label='clear-all')
add('load',data=rich,label='rebuild-after-clear')
sample=base/'native_analysis/core_round21/rton_normalizer/resources/resource-1.raw.rton'
prior=json.loads((base/'native_analysis/core_round21/rton_normalizer/native-cli-validation.json').read_text(encoding='utf-8'))
resource_origin=next(x['source'] for x in prior['resources'] if x['label']=='resource-1')
assert hashlib.sha256(sample.read_bytes()).hexdigest()==resource_origin['plaintext_sha256']
add('load',data=sample.read_bytes(),label='actual-cowboy-dangerroom-partial-load')
for name in names+['dangerroomlevelintroproperties','UnknownClass']:add('lookup',name=name,label='lookup-'+name)
if RAIL:
 def record(**fields):return b'\x85'+obj([(k,integer(v) if isinstance(v,int) else v) for k,v in fields.items()])
 def rail_decl(props):return declaration(cls='RailcartProperties',aliases=['Rails'],props=props)
 add('load',data=document([declaration(props=[('PanStartOffset',f32(99)),('NarrationID',integer(8))])]),label='prepare-inherited-scope-fallback')
 add('populate',data=document([declaration(props=[('ResourceGroupNames',integer(0)),('PanStartOffset',f32(123)),('NarrationID',integer(45))])]),label='nonarray-inherited-vector-changes-following-scope')
 full_props=[('m_thisPtr',ref('Intro')),('ResourceGroupNames',array([text('Railcart'),text('West')])),('RailcartType',text('railcart_cowboy')),('Rails',array([record(Column=0,RowStart=0,RowEnd=4),record(Column=3,RowStart=1,RowEnd=3)])),('Railcarts',array([record(Column=0,Row=0),record(Column=3,Row=2)]))]
 rail_cycle=document([rail_decl(full_props),declaration(aliases=['Intro'],props=[('m_thisPtr',ref('Rails'))])])
 add('load',data=rail_cycle,label='railcart-nested-records-and-cycle')
 add('populate',data=document([rail_decl([('ResourceGroupNames',integer(0)),('RailcartType',text('ignored-from-wrong-scope'))]),declaration()]),label='nonarray-inherited-vector-clears-following-string')
 add('populate',data=document([rail_decl([('Rails',array([record(Column=7),record(RowEnd=9)])),('Railcarts',array([record(Row=4),record(Column=-2)]))]),declaration()]),label='nested-resize-preserves-existing-missing-fields')
 add('populate',data=document([rail_decl([('Rails',array([record(RowStart=-3)])),('Railcarts',array([record(Column=1)]))]),declaration()]),label='nested-shrink')
 add('populate',data=document([rail_decl([('Rails',array([record(RowEnd=12),record(),record(Column=8)])),('Railcarts',array([record(Row=2),record(),record(Row=3)]))]),declaration()]),label='nested-regrow-default-minus-one')
 add('populate',data=document([rail_decl([('Rails',array([integer(7),record(RowEnd=99),b'\x85\xff'])),('Railcarts',array([integer(0),record(Row=6),record()]))]),declaration()]),label='nonobject-records-preserve-existing-elements')
 add('populate',data=document([rail_decl([('Rails',integer(0)),('Railcarts',array([record(Column=4,Row=3)]))]),declaration()]),label='nonarray-rails-clear-and-following-cart')
 add('populate',data=document([rail_decl([('Rails',array([record()])),('Railcarts',b'\x85\xff')]),declaration()]),label='nonarray-carts-clear')
 add('populate',data=document([rail_decl([('RailcartType',text('changed\0ignored')),('Rails',array([])),('Railcarts',array([]))]),declaration()]),label='empty-arrays-and-c-string-type')
 cache='railcart_cached';encoded=cache.encode()
 add('load',data=document([rail_decl([('_cached',b'\x90'+vi(len(encoded))+encoded),('RailcartType',b'\x91\0'),('Rails',array([record(Column=text('-12junk'),RowStart=f32(2.9),RowEnd=b'\x26'+struct.pack('<I',0xffffffff))])),('Railcarts',array([record(Column=integer(-2147483648),Row=integer(2147483647))]))])]),label='cached-type-and-nested-scalar-coercion')
 add('load',data=document([rail_decl([('RailcartType',text('矿车')),('Rails',array([record() for _ in range(24)])),('Railcarts',array([record(Column=i,Row=i%5) for i in range(32)]))])]),label='large-nested-lists-defaults')
 add('load',3,data=document([declaration(aliases=['RemoteIntro'],props=[('m_thisPtr',ref('Rails','local'))])]),label='remote-intro-before-railcart')
 add('load',data=document([rail_decl([('m_thisPtr',ref('RemoteIntro','remote'))])]),label='cross-package-railcart-reference')
 add('load',data=document([]),label='clear-railcart-lists-and-reference')
 add('load',data=rail_cycle,label='rebuild-railcart-after-clear')
 add('load',data=sample.read_bytes(),label='actual-cowboy-dangerroom-partial-load')
if SEED:
 def seed_decl(props=(),aliases=('SeedBank',)):return declaration(cls='SeedBankProperties',aliases=aliases,props=props)
 seed_cycle=document([seed_decl([('m_thisPtr',ref('Intro')),('ResourceGroupNames',array([text('SeedBank'),text('West')])),('SelectionMethod',text(' preset ')),('AlwaysUseChooser',b'\x01'),('ZombieMode',b'\x00'),('GridItemMode',integer(7)),('PlantWhiteList',array([text(x) for x in ['sunflower','peashooter','sunflower','']])),('PlantBlackList',array([text('wallnut')])),('BlackListLiftedBy',text('upgrade')),('PresetPlantList',array([text('sunflower'),text('peashooter')]))]),declaration(aliases=['Intro'],props=[('m_thisPtr',ref('SeedBank'))])])
 add('load',data=seed_cycle,label='seedbank-all-fields-and-cycle')
 add('populate',data=document([seed_decl([('PlantWhiteList',array([text('changed')])),('ZombieMode',b'\x01')]),declaration()]),label='replace-one-plant-list-preserve-missing')
 add('populate',data=document([seed_decl([('PlantBlackList',array([])),('PresetPlantList',array([])),('BlackListLiftedBy',text(''))]),declaration()]),label='clear-two-plant-lists-and-text')
 for name in ['preset','chooser',' chooser\t','CHOOSER','unknown','-1','7','preset|chooser','']:
  add('load',data=document([seed_decl([('SelectionMethod',text(name))])]),label='seed-enum-'+repr(name))
 for label,values in [('json-bools',[b'\x00',b'\x01',b'\x00']),('integer-coercion',[integer(0),integer(-1),integer(2147483647)]),('float-coercion',[f32(-0.0),f64(float('nan')),f32(1.25)]),('string-coercion',[text('false'),text('0'),text('')]),('string-prefix-coercion',[text('0abc'),text('-1'),text('true')])]:
  add('load',data=document([seed_decl(list(zip(['AlwaysUseChooser','ZombieMode','GridItemMode'],values)))]),label='seed-bool-'+label)
 encoded=b'cachedplant'
 add('load',data=document([seed_decl([('_cache',b'\x90'+vi(len(encoded))+encoded),('PlantWhiteList',array([b'\x91\0',text('plant\0tail'),text('植物')])),('PlantBlackList',array([b'\x91\0'])),('PresetPlantList',array([b'\x91\0'])),('BlackListLiftedBy',b'\x91\0')])]),label='seed-cached-nul-and-utf8-text')
 add('populate',data=document([seed_decl([('PlantWhiteList',array([text('n'+str(i)) for i in range(32)])),('PlantBlackList',array([text('x')]*24)),('PresetPlantList',array([text('y')]*16))])]),label='seed-large-string-lists')
 add('populate',data=document([seed_decl([('PlantWhiteList',integer(0)),('PlantBlackList',array([text('ignored')])),('BlackListLiftedBy',text('ignored')),('PresetPlantList',array([text('ignored')]))])]),label='seed-nonarray-list-following-scope')
 add('load',data=document([seed_decl([('ResourceGroupNames',integer(0)),('SelectionMethod',text('chooser')),('AlwaysUseChooser',b'\x01')])]),label='seed-inherited-nonarray-scope-fallback')
 add('load',data=document([seed_decl([],aliases=['Same']),declaration(aliases=['Same'],props=[('m_thisPtr',ref('Same'))])]),label='seed-first-alias-wins-across-types')
 add('load',3,data=document([seed_decl([('m_thisPtr',ref('SeedBank','local'))],aliases=['RemoteSeed'])]),label='seed-cross-package-before-local')
 add('load',data=document([seed_decl([('m_thisPtr',ref('RemoteSeed','remote'))])]),label='seed-cross-package-local-target')
 add('load',data=document([]),label='seed-clear-with-owned-reference')
 add('load',data=seed_cycle,label='seed-rebuild-after-clear')
 for number in [2,3,4]:
  p=base/f'native_analysis/core_round21/rton_normalizer/resources/resource-{number}.raw.rton'
  origin=next(x['source'] for x in prior['resources'] if x['label']==f'resource-{number}')
  assert hashlib.sha256(p.read_bytes()).hexdigest()==origin['plaintext_sha256']
  add('load',data=p.read_bytes(),label=f'actual-resource-{number}-partial-load')
 add('load',data=sample.read_bytes(),label='actual-cowboy-dangerroom-partial-load')

if WAVE:
 def wave_decl(props=(),aliases=('WaveGen',)):return declaration(cls='WaveGeneratorProperties',aliases=aliases,props=props)
 def pool_record(name='Target',pkg='.',**fields):return record(**fields,Type=ref(name,pkg))
 one_wave=record(DisableRandomSpawns=b'\x01',WaitUntilAllZombiesDie=b'\x01',ColNumPlantIsDragged=4,SpawnColStart=2,SpawnColEnd=8,SpawnPlantFoodCount=1,WavePointStart=7,WavePointIncrement=3,WavePointOverride=b'\x01',Event=record(Enabled=b'\x01',Count=2,TimeSpread=5,Waves=4),WaveSpawnTime=f64(3.75),Zombies=array([record(Row=text('2'),HasPlantFood=b'\x01',Loot=5,Level=3,Type=ref('Target'),Rise_GridX=2,Rise_GridY=4,SunDrop=25,BesiegeHit=2,ZombieRate=f32(1.25),ZombieScale=f32(0.75),TargetValidTime=f32(9.0))]),AddToZombiePool=array([pool_record(Cost=7,Weight=10,Overridden=b'\x01')]),RemoveFromZombiePool=array([pool_record('Missing',Cost=9)]),AddToSeedPool=array([pool_record(Weight=1500,MaxCount=3,MaxCountIncludesPlanted=b'\x01')]),RemoveFromSeedPool=array([pool_record('RemovedSeed')]))
 wave_cycle=document([wave_decl([('HeroProps',ref('Target')),('Waves',array([one_wave,record()])),('ZombiePool',array([pool_record(Cost=3,Weight=8),pool_record('Missing',Weight=2)])),('FlagWaveInterval',integer(5)),('WaveCount',integer(10)),('WaveSpendingPointIncrement',integer(2)),('WaveSpendingPoints',integer(15)),('SpawnColStart',integer(1)),('SpawnColEnd',integer(9)),('SpawnCount',integer(4)),('IgnoreFlagCarriers',b'\x01'),('IsRiseFromGroundMode',b'\x01')]),declaration(aliases=['Target'],props=[('m_thisPtr',ref('WaveGen'))])])
 add('load',data=wave_cycle,label='wave-all-nested-fields-and-cycle')
 add('populate',data=document([wave_decl([('Waves',array([record(Zombies=array([record(Level=8)])),record(SpawnPlantFoodCount=5)])),('ZombiePool',array([record(Weight=99),record()]))]),declaration()]),label='wave-partial-record-update-preserves-references')
 add('populate',data=document([wave_decl([('Waves',array([record(Zombies=array([]),AddToZombiePool=array([]),RemoveFromSeedPool=array([]))])),('ZombiePool',array([record()]))]),declaration()]),label='wave-shrink-clears-owned-nested-references')
 add('populate',data=document([wave_decl([('Waves',array([record(),record(Zombies=array([record(),record(Type=ref('Target'))]),AddToSeedPool=array([record()]))])),('ZombiePool',array([record(),record()]))]),declaration()]),label='wave-regrow-resets-record-defaults')
 add('populate',data=document([wave_decl([('Waves',array([integer(0),record(Zombies=array([integer(7),record(Row=text('prev'))]))]))]),declaration()]),label='wave-nonobject-elements-preserve-records')
 for row in ['1','2','3','4','5','6','?','prev',' prev\t','unknown','-1','99']:
  add('load',data=document([wave_decl([('Waves',array([record(Zombies=array([record(Row=text(row))]))]))])]),label='wave-row-enum-'+repr(row))
 add('load',data=document([wave_decl([('Waves',array([record(Event=record(Enabled=text('false'),Count=text('-3')),WaveSpawnTime=f64(1e-45),Zombies=array([record(ZombieRate=f64(float('nan')),ZombieScale=f64(-0.0))]))])),('IgnoreFlagCarriers',text('0')),('IsRiseFromGroundMode',integer(-1)),('SpawnCount',text('-1'))])]),label='wave-scalar-coercion-and-defined-spawn-count')
 add('populate',data=document([wave_decl()]),label='wave-missing-spawn-count-preserves-defined-value')
 add('load',data=document([wave_decl()]),label='wave-fresh-spawn-count-is-uninitialized')
 add('load',data=document([wave_decl([('HeroProps',b'\x83\0'),('ZombiePool',array([pool_record('first'),pool_record('second'),pool_record('third')]))])]),label='wave-three-distinct-owned-pool-references')
 add('populate',data=document([wave_decl([('ZombiePool',array([]))])]),label='wave-pool-clears-in-original-forward-order')
 add('load',data=document([wave_decl([('Waves',array([record(Zombies=array([pool_record('a'),pool_record('b')]),AddToZombiePool=array([pool_record('c')]),RemoveFromZombiePool=array([pool_record('d')]),AddToSeedPool=array([pool_record('e')]),RemoveFromSeedPool=array([pool_record('f')]))]))])]),label='wave-own-all-five-nested-reference-lists')
 add('load',data=document([]),label='wave-destroy-releases-in-original-field-order')
 add('load',data=document([wave_decl([('ZombiePool',array([pool_record('Target','remote')]))])]),label='wave-cross-package-before-target')
 add('load',3,data=document([declaration(aliases=['Target'],props=[('m_thisPtr',ref('WaveGen','local'))])]),label='wave-cross-package-target-appears')
 add('package',3,'packages/HeroTypes.rton',label='wave-default-hero-package-registered')
 add('load',3,data=document([declaration(aliases=['DefaultHeroLevelProps'])]),label='wave-default-hero-target-created')
 add('load',data=document([wave_decl()]),label='wave-default-hero-reference-resolves')
 add('load',data=wave_cycle,label='wave-rebuild-complex-after-clears')
 add('load',data=sample.read_bytes(),label='actual-cowboy-dangerroom-partial-load')

if LEVEL:
 def level_decl(props=(),aliases=('Root',)):return declaration(cls='LevelDefinition',aliases=aliases,props=props)
 level_texts=['Name','Description','MainObjective','challengeDropGroupId','NormalPresentTable','ShinyPresentTable','FirstRewardParam','ReplayRewardParam','FirstIntroNarrative','ReplayIntroNarrative','FirstOutroNarrative','ReplayOutroNarrative','ForceNextLevel','CompletionAchievement','MusicType']
 level_flags=['SuppressVictoryScreen','GameOverDialogShowBrain','GameOverDialogTaskFailed','ForceWarpTunnel','IsDangerRoom','IsBossFight','IsArenaBattle','IsArenaEdit','IsLevelOfTheDay']
 full_level=[(n,text('value-'+str(i))) for i,n in enumerate(level_texts)]+[(n,b'\x01' if i%2==0 else b'\x00') for i,n in enumerate(level_flags)]+[('m_thisPtr',ref('Target')),('StartingSun',integer(125)),('LevelNumber',integer(7)),('LevelIndex',integer(311)),('ZombieMaxLevel',integer(8)),('StageModule',ref('Target')),('VictoryModule',ref('Root')),('Loot',ref('MissingLoot')),('Modules',array([ref('Root'),ref('Target'),b'\x83\0',ref('MissingModule')])),('FirstRewardType',text('present')),('ReplayRewardType',text('powerup')),('GameFeaturesToUnlock',array([text('unknown-feature'),integer(9)])),('ZombieWarningInfos',array([record(Type=ref('Target'),Text=text('warning'),Level=3),record(Type=ref('UnknownZombie'),Text=text('other'))]))]
 level_cycle=document([level_decl(full_level),declaration(aliases=['Target'],props=[('m_thisPtr',ref('Root'))])])
 add('load',data=level_cycle,label='level-all-fields-modules-and-cycle')
 add('populate',data=document([level_decl([('Name',text('changed')),('Modules',array([ref('Target')])),('ZombieWarningInfos',array([record(Level=9)]))]),declaration()]),label='level-shrink-modules-and-partial-warning')
 add('populate',data=document([level_decl([('Modules',array([ref('Target'),ref('Root'),ref('Third')])),('ZombieWarningInfos',array([record(Text=text('updated')),record(),integer(0)])),('GameFeaturesToUnlock',array([integer(1)]))]),declaration()]),label='level-regrow-warning-defaults-and-feature-slots')
 add('populate',data=document([level_decl([('Modules',array([])),('ZombieWarningInfos',array([])),('GameFeaturesToUnlock',array([]))]),declaration()]),label='level-clear-owned-reference-lists')
 for number in [-2147483648,-1,0,32767,32768,65535,65536,2147483647]:
  add('load',data=document([level_decl([('StartingSun',integer(number))])]),label='level-starting-sun-truncate-'+str(number))
 for name in ['none','present','collectable','seed_packet','powerup','upgrade','bonus','mapgadget','powerupgadget','firstkey','note','worldtrophy','starkey','piece_firegourd','piece_gravebuster',' collectable\t','UNKNOWN','-1','99','']:
  add('load',data=document([level_decl([('FirstRewardType',text(name)),('ReplayRewardType',text(name))])]),label='level-reward-enum-'+repr(name))
 add('load',data=document([level_decl([('Name',text('关卡\0tail')),('Description',text('quoted"\\\n')),('StartingSun',f64(65537.75)),('IsDangerRoom',text('false')),('GameOverDialogShowBrain',text('0'))])]),label='level-text-and-scalar-coercion')
 add('load',data=document([level_decl([('Modules',array([ref('first'),ref('second'),ref('third')])),('StageModule',ref('stage')),('VictoryModule',ref('victory')),('Loot',ref('loot')),('ZombieWarningInfos',array([record(Type=ref('warn1')),record(Type=ref('warn2'))]))])]),label='level-distinct-owned-reference-teardown-order')
 add('load',data=document([]),label='level-destroy-all-owned-references')
 add('load',data=document([level_decl([('Modules',array([ref('Target','remote')]))])]),label='level-forward-cross-package-module')
 add('package',3,'packages/remote.rton',label='level-restore-remote-package')
 add('load',3,data=document([declaration(aliases=['Target'],props=[('m_thisPtr',ref('Root','CurrentLevel'))])]),label='level-cross-package-module-target-appears')
 add('load',data=level_cycle,label='level-rebuild-after-clears')
 for number in [2,3,4]:
  add('load',data=(base/f'native_analysis/core_round21/rton_normalizer/resources/resource-{number}.raw.rton').read_bytes(),label=f'actual-resource-{number}-partial-load')
 add('load',data=sample.read_bytes(),label='actual-cowboy-dangerroom-partial-load')

seed()
# Exact empty event-bus state written by _INIT_134, excluding process atexit
# registration. GameObject's real post-deserialize notification still executes;
# the selected data test owner has no game subscribers.
h.u.mem_write(0x1843830,bytes(0x74));h.put(0x1843838,0x7fffffff,0x7fffffff);h.put(0x1843848,0x17a06a0)
for a in [0x1843850,0x1843890]:h.put(a+8,a,a)
manager=h.call(0x11b10ec,[]);ground=h.call(0x255520,[]);danger=h.call(0x2cb9b8,[])
if RAIL:h.call(0x8a0610,[])
if SEED:h.call(0x8ab974,[])
if WAVE:h.call(0x9c6944,[])
if LEVEL:h.call(0x444b2c,[])
h.call(0x11b15b4,[manager])
b,e=h.words(0x18cbfa4,2);types=h.words(b,(e-b)//4)
assert [h.narrow(h.words(t+4)[0]).decode() for t in types]==names
schemas={}
for meta,name in zip(types,names):
 schema=h.words(meta+0x24)[0];fields=[]
 if schema:
  b,e=h.words(schema+0x134,2)
  for p in h.words(b,(e-b)//4):fields.append(dict(name=h.narrow(h.words(p+0x38)[0]).decode(),offset=h.words(p+0x48)[0]))
 schemas[name]=fields
assert schemas[names[7]]==[dict(name=n,offset=o) for n,o in [('m_thisPtr',8),('ResourceGroupNames',16),('PanStartOffset',28),('PanEndOffset',32),('PanRightDuration',36),('PanLeftDuration',40),('NarrationID',44),('SubsequentPlayNarrationID',48)]]
if RAIL:assert schemas['RailcartProperties']==[dict(name=n,offset=o) for n,o in [('m_thisPtr',8),('ResourceGroupNames',16),('RailcartType',28),('Rails',32),('Railcarts',44)]]
seed_enum=None
if SEED:
 assert schemas['SeedBankProperties']==[dict(name=n,offset=o) for n,o in [('m_thisPtr',8),('ResourceGroupNames',16),('SelectionMethod',28),('AlwaysUseChooser',32),('ZombieMode',33),('GridItemMode',34),('PlantWhiteList',48),('PlantBlackList',60),('BlackListLiftedBy',72),('PresetPlantList',36)]]
 meta=types[9];schema=h.words(meta+0x24)[0];b,e=h.words(schema+0x134,2);field=h.words(b+8)[0]
 enum=h.words(h.words(field+0x4c)[0]+0x4c)[0];entries=[]
 def enum_walk(n):
  if n:enum_walk(h.words(n+8)[0]);entries.append([h.narrow(h.words(n+16)[0]).decode(),h.words(h.words(n+20)[0]+0x3c)[0]]);enum_walk(h.words(n+12)[0])
 enum_walk(h.words(enum+0x6c)[0]);seed_enum=dict(flags=h.words(enum+0x54)[0],entries=entries)
 assert seed_enum['flags']&1==0 and entries==[['chooser',1],['preset',0]],seed_enum
wave_schemas={};row_enum=None
if WAVE:
 assert schemas['WaveGeneratorProperties']==[dict(name=n,offset=o) for n,o in [('m_thisPtr',8),('ResourceGroupNames',16),('HeroProps',32),('Waves',40),('ZombiePool',52),('FlagWaveInterval',64),('WaveCount',68),('WaveSpendingPointIncrement',72),('WaveSpendingPoints',76),('SpawnColStart',80),('SpawnColEnd',84),('SpawnCount',88),('IgnoreFlagCarriers',92),('IsRiseFromGroundMode',93)]]
 def members(schema):
  b,e=h.words(schema+0x134,2);return {h.narrow(h.words(p+0x38)[0]).decode():p for p in h.words(b,(e-b)//4)}
 def vector_schema(field):
  typ=h.words(field+0x4c)[0];inner=h.words(typ+0x4c)[0];return h.words(inner+0x4c)[0]
 top=members(h.words(types[10]+0x24)[0]);ws=vector_schema(top['Waves']);wfields=members(ws)
 for name,schema in [('Wave',ws),('Event',h.words(h.words(wfields['Event']+0x4c)[0]+0x4c)[0]),('ZombieSpawn',vector_schema(wfields['Zombies'])),('ZombiePool',vector_schema(top['ZombiePool'])),('SeedPool',vector_schema(wfields['AddToSeedPool']))]:
  wave_schemas[name]=[dict(name=n,offset=h.words(p+0x48)[0]) for n,p in members(schema).items()]
 row=members(vector_schema(wfields['Zombies']))['Row'];enum=h.words(h.words(row+0x4c)[0]+0x4c)[0];entries=[]
 def row_walk(n):
  if n:row_walk(h.words(n+8)[0]);entries.append([h.narrow(h.words(n+16)[0]).decode(),h.words(h.words(n+20)[0]+0x3c)[0]]);row_walk(h.words(n+12)[0])
 row_walk(h.words(enum+0x6c)[0]);row_enum=dict(flags=h.words(enum+0x54)[0],entries=entries)
 assert entries==[[str(i+1),i] for i in range(6)]+[['?',6],['prev',7]],entries
addresses=[];object_types={};vectors={};checks=0
level_reward_enum=None;level_warning_schema=[];level_feature_codec=None
level_text_offsets=[16,20,24,80,84,88,100,108,116,120,124,128,132,144,160]
level_flag_offsets=[92,112,113,136,137,138,139,140,180]
if LEVEL:
 fields=members(h.words(types[11]+0x24)[0])
 assert len(fields)==37 and h.words(h.words(fields['StartingSun']+0x4c)[0]+0x40)[0]==2
 enum=h.words(h.words(fields['FirstRewardType']+0x4c)[0]+0x4c)[0];entries=[]
 def reward_walk(n):
  if n:reward_walk(h.words(n+8)[0]);entries.append([h.narrow(h.words(n+16)[0]).decode(),h.words(h.words(n+20)[0]+0x3c)[0]]);reward_walk(h.words(n+12)[0])
 reward_walk(h.words(enum+0x6c)[0]);level_reward_enum=dict(flags=h.words(enum+0x54)[0],entries=entries)
 schema=vector_schema(fields['ZombieWarningInfos']);level_warning_schema=[dict(name=n,offset=h.words(p+0x48)[0]) for n,p in members(schema).items()]
 typ=h.words(h.words(fields['GameFeaturesToUnlock']+0x4c)[0]+0x4c)[0]
 h.put(SER,0,0,1);h.put(h.VALUE,0x12345678);result=h.call(0x11ab2bc,[typ,h.VALUE,SER,h.REF])
 level_feature_codec=dict(type_name=h.narrow(h.words(typ+0x48)[0]).decode(),read_address='011ab2bc',read_result=result,output_word=h.words(h.VALUE)[0])
 assert result==0 and h.words(h.VALUE)[0]==0x12345678,level_feature_codec
spawn_written={}
def track_spawn_write(uc,access,address,size,value,unused):
 if address in spawn_written:spawn_written[address]=True
def serial(p):return addresses.index(p)+1 if p else 0
def object_type(p):
 if p not in object_types:object_types[p]=h.call(h.words(h.words(p)[0])[0],[p])
 return object_types[p]
def handle_state(p):
 bits=h.words(p,2);h.put(h.HANDLE,*bits);resolved=h.call(FUNCTIONS['resolve'],[h.REG,h.HANDLE]);return [*bits,serial(resolved)]
def rows(p,offset,size):
 b,e=h.words(p+offset,2);return range(b,e,size)
def byte(p):return bytes(h.u.mem_read(p,1))[0]
def pool_state_at(p,seed_pool=False):return [*h.words(p,2),byte(p+8),*handle_state(p+(24 if seed_pool else 16))]
def wave_state_at(p):
 out=[byte(p),byte(p+1),byte(p+28),*h.words(p+4,6),byte(p+36),*h.words(p+40,3),h.words(p+32)[0]]
 zs=rows(p,52,56);out.append(len(zs))
 for q in zs:out.extend([h.words(q)[0],byte(q+4),*h.words(q+8,2),*h.words(q+24,4),*handle_state(q+16),*h.words(q+40,3)])
 for offset,size in [(64,24),(76,24),(88,32),(100,32)]:
  items=rows(p,offset,size);out.append(len(items))
  for q in items:out.extend(pool_state_at(q,size==32))
 return out
def snapshot():
 out=[len(types)]
 for index,p in enumerate(types):
  n=h.narrow(h.words(p+4)[0]);parent=h.words(p+8)[0]
  out.extend([len(n),*n,types.index(parent)+1 if parent else 0,int(index!=0)])
 for a in [0,*types]:
  for b in [0,*types]:out.append(h.call(FUNCTIONS['ancestry'],[a,b]))
 h.append(out,h.pool_state());alive=set()
 for type in [2,3]:
  store=h.store_for(type);out.append(int(bool(store)))
  if not store:continue
  out.extend([h.words(store+0xc4)[0],h.words(store+0xd4)[0]]);slots=h.slot_state(store)
  for i in range(slots[0]):
   offset=13+i*8+2;p=slots[offset]
   if p:alive.add(p);slots[offset]=serial(p)
  h.append(out,slots);h.append(out,h.tree_state(store+0xe4,'descriptor'));h.append(out,h.tree_state(store+0xfc,'object'))
 out.append(len(addresses))
 for p in addresses:
  out.append(int(p in alive))
  if p not in alive:continue
  index=types.index(object_type(p));out.append(index+1)
  if index==1:out.extend([bytes(h.u.mem_read(p+4,1))[0],h.words(p+8)[0],*handle_state(p+16)])
  else:
   out.extend(handle_state(p+8))
   if 4<=index<=10:
    b,e=h.words(p+16,2);out.append((e-b)//4)
    for q in range(b,e,4):s=h.narrow(h.words(q)[0]);out.extend([len(s),*s])
   if index in [6,7]:out.extend(h.words(p+28,6))
   if index==8:
    name=h.narrow(h.words(p+28)[0]);out.extend([len(name),*name])
    for offset,size in [(32,12),(44,8)]:
     b,e=h.words(p+offset,2);out.extend([(e-b)//size,*h.words(b,(e-b)//4)])
   if index==9:
    out.extend([h.words(p+28)[0],*bytes(h.u.mem_read(p+32,3))])
    for offset in [48,60,36]:
     b,e=h.words(p+offset,2);out.append((e-b)//4)
     for q in range(b,e,4):s=h.narrow(h.words(q)[0]);out.extend([len(s),*s])
    s=h.narrow(h.words(p+72)[0]);out.extend([len(s),*s])
   if index==10:
    out.extend(handle_state(p+32));items=rows(p,40,112);out.append(len(items))
    for q in items:out.extend(wave_state_at(q))
    items=rows(p,52,24);out.append(len(items))
    for q in items:out.extend(pool_state_at(q))
    out.extend(h.words(p+64,6));defined=spawn_written[p+88];out.append(int(defined))
    if defined:out.append(h.words(p+88)[0])
    out.extend([byte(p+92),byte(p+93)])
   if index==11:
    for offset in level_text_offsets:
     text=h.narrow(h.words(p+offset)[0]);out.extend([len(text),*text])
    out.extend([h.words(p+28)[0]&0xffff,h.words(p+36)[0],h.words(p+32)[0],h.words(p+176)[0]])
    for offset in [40,48,72]:out.extend(handle_state(p+offset))
    items=rows(p,56,8);out.append(len(items))
    for q in items:out.extend(handle_state(q))
    out.extend([h.words(p+96)[0],h.words(p+104)[0],*[byte(p+offset) for offset in level_flag_offsets]])
    items=rows(p,148,4);out.extend([len(items),*[h.words(q)[0] for q in items]])
    items=rows(p,164,16);out.append(len(items))
    for q in items:
     out.extend(handle_state(q));text=h.narrow(h.words(q+8)[0]);out.extend([len(text),*text,h.words(q+12)[0]])
 return out
def read_document(data):
 src=h.alloc(len(data));h.u.mem_write(src,data);dst=h.alloc(0x20000);h.u.mem_write(ST,bytes(0x100));h.put(ST,dst,0x20000,0,0,0,0,0x100)
 for off in [0x1c,0x34]:h.put(ST+off+4,0,0,ST+off+4,ST+off+4,0)
 assert h.call(0x1202a74,[ST,src,len(data)])==1
 h.call(0x11f8818,[V,ST]);h.put(V+12,SC,SC,SC+0x1000);h.put(SER,V,0,1)
def graph(type):
 vector=vectors[type];b,e=h.words(vector,2);items=h.words(b,(e-b)//4);result_rows=[]
 for i,p in enumerate(items):
  if not p:result_rows.append(None);continue
  index=types.index(object_type(p));row=dict(index=i,objclass=names[index])
  def target(offset):
   h.put(h.HANDLE,*h.words(p+offset,2));resolved=h.call(FUNCTIONS['resolve'],[h.REG,h.HANDLE]);return items.index(resolved) if resolved in items and resolved else None
  def ref_json(address):
   lo,hi=h.words(address,2);package=name=None
   if hi&0x80000000:
    package=''.join(chr(c) for c in h.wide(h.call(0x11f14cc,[h.pool,(lo>>31)|((hi&0x3fffffff)<<1)])))
    name=''.join(chr(c) for c in h.wide(h.call(0x11f14cc,[h.pool,lo&0x7fffffff])))
   h.put(h.HANDLE,lo,hi);resolved=h.call(FUNCTIONS['resolve'],[h.REG,h.HANDLE])
   return dict(package=package,name=name,target=items.index(resolved) if resolved in items and resolved else None)
  def i32(address):return struct.unpack('<i',bytes(h.u.mem_read(address,4)))[0]
  def float_json(result,name,address):
   bits=h.words(address)[0];number=struct.unpack('<f',struct.pack('<I',bits))[0];result[name]=number if math.isfinite(number) else None;result[name+'_bits']=bits
  def pool_json(address,seed_pool=False):
   result=dict(Weight=i32(address),MaxCount=i32(address+4),MaxCountIncludesPlanted=bool(byte(address+8))) if seed_pool else dict(Cost=i32(address),Weight=i32(address+4),Overridden=bool(byte(address+8)))
   result['Type']=ref_json(address+(24 if seed_pool else 16));return result
  def zombie_json(address):
   result=dict(Row=h.words(address)[0],HasPlantFood=bool(byte(address+4)),Loot=i32(address+8),Level=i32(address+12),Type=ref_json(address+16))
   for n,offset in [('Rise_GridX',24),('Rise_GridY',28),('SunDrop',32),('BesiegeHit',36)]:result[n]=i32(address+offset)
   for n,offset in [('ZombieRate',40),('ZombieScale',44),('TargetValidTime',48)]:float_json(result,n,address+offset)
   return result
  def wave_json(address):
   result=dict(DisableRandomSpawns=bool(byte(address)),WaitUntilAllZombiesDie=bool(byte(address+1)))
   for n,offset in [('ColNumPlantIsDragged',4),('SpawnColStart',8),('SpawnColEnd',12),('SpawnPlantFoodCount',16),('WavePointStart',20),('WavePointIncrement',24)]:result[n]=i32(address+offset)
   result['WavePointOverride']=bool(byte(address+28));result['Event']=dict(Enabled=bool(byte(address+36)),Count=i32(address+40),TimeSpread=i32(address+44),Waves=i32(address+48))
   float_json(result,'WaveSpawnTime',address+32);result['Zombies']=[zombie_json(q) for q in rows(address,52,56)]
   for n,offset,size in [('AddToZombiePool',64,24),('RemoveFromZombiePool',76,24),('AddToSeedPool',88,32),('RemoveFromSeedPool',100,32)]:result[n]=[pool_json(q,size==32) for q in rows(address,offset,size)]
   return result
  if index==1:row.update(m_type=h.words(p+8)[0],m_effect_target=target(16))
  else:
   row['m_thisPtr_target']=target(8)
   if 4<=index<=10:
    b,e=h.words(p+16,2);row['ResourceGroupNames']=[h.narrow(h.words(q)[0]).decode() for q in range(b,e,4)]
   if index in [6,7]:
    bits=h.words(p+28,4);row['float32_bits']=bits
    for n,bit in zip(['PanStartOffset','PanEndOffset','PanRightDuration','PanLeftDuration'],bits):
     number=struct.unpack('<f',struct.pack('<I',bit))[0];row[n]=number if math.isfinite(number) else None
    for n,offset in [('NarrationID',44),('SubsequentPlayNarrationID',48)]:row[n]=struct.unpack('<i',bytes(h.u.mem_read(p+offset,4)))[0]
   if index==8:
    row['RailcartType']=h.narrow(h.words(p+28)[0]).decode()
    for name,offset,fields in [('Rails',32,['Column','RowStart','RowEnd']),('Railcarts',44,['Column','Row'])]:
     b,e=h.words(p+offset,2);size=len(fields)*4
     row[name]=[dict(zip(fields,struct.unpack('<'+'i'*len(fields),bytes(h.u.mem_read(q,size))))) for q in range(b,e,size)]
   if index==9:
    row['SelectionMethod']=h.words(p+28)[0]
    for name,offset in [('AlwaysUseChooser',32),('ZombieMode',33),('GridItemMode',34)]:row[name]=bool(bytes(h.u.mem_read(p+offset,1))[0])
    for name,offset in [('PlantWhiteList',48),('PlantBlackList',60),('PresetPlantList',36)]:
     b,e=h.words(p+offset,2);row[name]=[h.narrow(h.words(q)[0]).decode() for q in range(b,e,4)]
    row['BlackListLiftedBy']=h.narrow(h.words(p+72)[0]).decode()
   if index==10:
    row['HeroProps']=ref_json(p+32);row['Waves']=[wave_json(q) for q in rows(p,40,112)];row['ZombiePool']=[pool_json(q) for q in rows(p,52,24)]
    for n,offset in [('FlagWaveInterval',64),('WaveCount',68),('WaveSpendingPointIncrement',72),('WaveSpendingPoints',76),('SpawnColStart',80),('SpawnColEnd',84)]:row[n]=i32(p+offset)
    row['SpawnCount_defined']=spawn_written[p+88];row['SpawnCount']=i32(p+88) if spawn_written[p+88] else None
    row['IgnoreFlagCarriers']=bool(byte(p+92));row['IsRiseFromGroundMode']=bool(byte(p+93))
   if index==11:
    row.update({name:h.narrow(h.words(p+offset)[0]).decode() for name,offset in zip(level_texts,level_text_offsets)})
    row['StartingSun']=struct.unpack('<h',bytes(h.u.mem_read(p+28,2)))[0];row['StartingSun_bits']=h.words(p+28)[0]&0xffff
    for name,offset in [('LevelNumber',36),('LevelIndex',32),('ZombieMaxLevel',176)]:row[name]=i32(p+offset)
    for name,offset in [('StageModule',40),('VictoryModule',48),('Loot',72)]:row[name]=ref_json(p+offset)
    row['Modules']=[ref_json(q) for q in rows(p,56,8)]
    row['FirstRewardType']=h.words(p+96)[0];row['ReplayRewardType']=h.words(p+104)[0]
    row.update({name:bool(byte(p+offset)) for name,offset in zip(level_flags,level_flag_offsets)})
    row['GameFeaturesToUnlock']=[h.words(q)[0] for q in rows(p,148,4)];row['GameFeaturesToUnlock_values_read']=False
    row['ZombieWarningInfos']=[dict(Type=ref_json(q),Text=h.narrow(h.words(q+8)[0]).decode(),Level=i32(q+12)) for q in rows(p,164,16)]
  result_rows.append(row)
 return dict(data_only=True,success=True,objects=result_rows)
initial=snapshot()
for s in operations:
 op,type=s['op'],s['type'];results=[];states=[];store=h.store_for(type)
 if op=='ensure':
  p=h.PARAM;h.put(p,0,0,0x16c5e40,0x194a588,0);h.put(h.QUERY,*s['name'],0);h.put(h.REF,h.QUERY);h.call(0x594184,[p+4,h.REF]);name=h.words(p+4)[0]
  h.call(0x11eefb0,[h.REG,type,p]);h.call(0x11f1f08,[h.pool,name]);results.append([]);states.append(snapshot())
 elif op=='package':
  h.put(h.QUERY,*s['name'],0);h.put(h.REF,h.QUERY);h.call(0x594184,[h.VALUE,h.REF]);name=h.words(h.VALUE)[0]
  h.put(h.REF,name);h.call(0x11ebe2c,[store,h.REF]);h.call(0x11f1f08,[h.pool,name]);results.append([]);states.append(snapshot())
 elif op=='lookup':
  h.u.mem_write(h.QUERY,''.join(chr(c) for c in s['name']).encode()+b'\0');p=h.call(FUNCTIONS['lookup'],[h.QUERY]);results.append([types.index(p)+1 if p else 0]);states.append(snapshot())
 else:
  read_document(bytes(s['data']))
  if op=='load':
   vector=h.alloc(12);h.put(vector,0,0,0);created=h.call(FUNCTIONS['create_pass'],[store,SER,vector]);vectors[type]=vector
   b,e=h.words(vector,2);items=h.words(b,(e-b)//4)
   for p in items:
    if p and p not in addresses:
     addresses.append(p)
     if WAVE and object_type(p)==types[10]:
      spawn_written[p+88]=False;h.u.hook_add(UC_HOOK_MEM_WRITE,track_spawn_write,begin=p+88,end=p+91)
   results.append([created,*[serial(p) for p in items]]);states.append(snapshot())
   if created:results.append([h.call(FUNCTIONS['fill_pass'],[store,SER,vector])]);states.append(snapshot())
  else:results.append([h.call(FUNCTIONS['fill_pass'],[store,SER,vectors[type]])]);states.append(snapshot())
 s['results']=results;s['states']=states;checks+=len(states)
 if s['label'] in ['inherited-fields-and-mixed-class-cycle','actual-cowboy-dangerroom-partial-load','railcart-nested-records-and-cycle','seedbank-all-fields-and-cycle','wave-all-nested-fields-and-cycle','level-all-fields-modules-and-cycle'] or s['label'].startswith('actual-resource-'):
  folder=OUT/'example';folder.mkdir(exist_ok=True);name='mixed-cycle' if s['label'].startswith('inherited') else 'railcart-cycle' if s['label'].startswith('railcart-nested') else 'seedbank-cycle' if s['label'].startswith('seedbank-all') else 'wave-cycle' if s['label'].startswith('wave-all') else 'level-cycle' if s['label'].startswith('level-all') else '-'.join(s['label'].split('-')[1:3]) if s['label'].startswith('actual-resource-') else 'cowboy-dangerroom'
  (folder/(name+'.raw.rton')).write_bytes(bytes(s['data']));(folder/(name+'.arm.objects.json')).write_text(json.dumps(graph(type),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print('Captured',s['label'] or op,flush=True)
assert all(h.hits[n] for n in FUNCTIONS),h.hits
folder=OUT/'pseudocode';folder.mkdir(exist_ok=True)
for a in [*FUNCTIONS.values(),0x2cb9b8,0x2cba38,0x90d0b4,0x90d134,0x3e1140,0x3e11c0,0x4499c4,0x449a44,0x358354,0x3583d4,0x163660,*([0x8a0610,0x8a0690,0x8a04ac,0x89f928,0x89faf8] if RAIL else [])]:
 for p in (base/'native_analysis/core_round3/full_library/functions').glob(f'{a:08x}_*.c'):shutil.copy2(p,folder/p.name)
md=Cs(CS_ARCH_ARM,CS_MODE_ARM)
(OUT/'game_object_serialize.asm').write_text('\n'.join(f'{i.address:08x}: {i.mnemonic:8} {i.op_str}' for i in md.disasm(bytes(h.u.mem_read(0x357cf4,0x200)),0x357cf4))+'\n',encoding='utf-8')
record=dict(original_sha256=hashlib.sha256((base/'raw/lib/armeabi/libSrc.so').read_bytes()).hexdigest(),operations=len(operations),checkpoints=checks,function_entry_hits={n:h.hits[n] for n in FUNCTIONS},schemas=schemas,initial=initial,steps=operations,scope='Real manager/schema callbacks, all seven selected original constructors, both original load passes and property/ref dispatch execute; compare class order/all ancestry pairs, whole intern state, both game-store slot/index trees, live/dead object tokens, all initialized reflected fields and resolved references. String vectors compare logical contents, not allocator capacity/COW identity. Original padding, vtable ABI and physical global metadata/schema symbol table excluded. GameObject Serialize executes its real post-read event path against an empty bus seeded from _INIT_134; no game subscribers. The host data adapter does not implement the event bus, callbacks or game behavior, and event-bus state is excluded. ASCII alias/narrow string list, no explicit UID/text RTID; float decimal C-library boundary controlled, wide/special text excluded. Real resource1 loads 1/5 objects because four game classes remain unsupported; this is not a whole-level/gameplay run.')
if RAIL:
 record['scope']=record['scope'].replace('all seven','all eight').replace('1/5','2/5').replace('four game classes','three game classes')+' RailcartType narrow/C-string text plus nested Rails/Railcarts int records; resize preserves existing fields, new entries initialize to -1, nonobjects preserve resized entries. Vector capacities excluded. Selected nonarray-vector following-field scope fallbacks compared; host does not implement the whole original serializer scope stack or arbitrary malformed-context propagation.'
 for name,a,b in [('rail_resize',0x8a279c,0x8a29dc),('cart_resize',0x8a1cc8,0x8a1e78)]:
  (OUT/(name+'.asm')).write_text('\n'.join(f'{i.address:08x}: {i.mnemonic:8} {i.op_str}' for i in md.disasm(bytes(h.u.mem_read(a,b-a)),a))+'\n',encoding='utf-8')
record['real_resource_source']=resource_origin
if SEED:
 record['scope']=record['scope'].replace('all eight','all nine').replace('2/5','3/5').replace('three game classes','two game classes')+' SeedBank data: narrow SelectionMethod enum (preset=0/chooser=1), three boolean read properties, three narrow-string plant lists and BlackListLiftedBy; fields follow actual registration order. Non-reference bool coercion only; numeric/wide enum and arbitrary string conversions remain excluded.'
 record['seedbank_selection_enum']=seed_enum
 record['real_resource_sources']={x['label']:x['source'] for x in prior['resources']}
 for name,a,b in [('seedbank_metadata',0x8ab974,0x8ab9d4),('seedbank_schema',0x8ab9f4,0x8abeec)]:
  (OUT/(name+'.asm')).write_text('\n'.join(f'{i.address:08x}: {i.mnemonic:8} {i.op_str}' for i in md.disasm(bytes(h.u.mem_read(a,b-a)),a))+'\n',encoding='utf-8')
if WAVE:
 record['scope']=record['scope'].replace('all nine','all ten').replace('3/5','4/5').replace('two game classes','one game class')+' WaveGeneratorProperties: default owned HeroTypes/DefaultHeroLevelProps symbolic reference, nonempty nested waves/event/zombie/seed pool records, Row narrow enum and all registered scalar fields. Original factory leaves SpawnCount uninitialized: CPU property writes track definedness; compare its value only once written. Nested vector inputs require arrays; arbitrary malformed nested-context propagation excluded. Private non-reflected record words/padding excluded; pool ownership and original forward element/reverse field teardown order are compared.'
 record['wave_nested_schemas']=wave_schemas;record['wave_row_enum']=row_enum
 for a in [0x9c6944,0x9c4c70,0x9c78b4,0x9c7710]:
  for p in (base/'native_analysis/core_round3/full_library/functions').glob(f'{a:08x}_*.c'):shutil.copy2(p,folder/p.name)
if LEVEL:
 record['scope']=record['scope'].replace('all ten','all eleven').replace('4/5','5/5').replace('because one game class remain unsupported','with all five declarations supported in this selected profile')+' LevelDefinition inherits PropertySheetBase, not LevelModuleProperties; 37 registered fields including owned module/warning refs, narrow texts/reward enum, signed short bit truncation and flags. CurrentLevel is the primary package alias for this profile, enabling four local module links. GameFeature remains an unresolved read-declining placeholder in original selected registration: compare resize/default slots only, no unlock-value semantics. External game modules/types and gameplay remain incomplete; 5/5 is declaration construction only.'
 record['level_reward_enum']=level_reward_enum;record['level_warning_schema']=level_warning_schema;record['level_feature_codec']=level_feature_codec
 for a in [0x444b2c,0x442f3c,0x44401c]:
  for p in (base/'native_analysis/core_round3/full_library/functions').glob(f'{a:08x}_*.c'):shutil.copy2(p,folder/p.name)
 (OUT/'game_feature_declined_read.asm').write_text('\n'.join(f'{i.address:08x}: {i.mnemonic:8} {i.op_str}' for i in md.disasm(bytes(h.u.mem_read(0x11ab2bc,0x11ab35c-0x11ab2bc)),0x11ab2bc))+'\n',encoding='utf-8')
(OUT/'validation.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
def arr(v):return '{'+','.join(str(x)+'U' for x in v)+'}'
lines=['// Original ARM inherited factory/property/list/reference full states.','const std::vector<std::uint32_t> initial_state = '+arr(initial)+';','const Step steps[] = {']
for s in operations:
 nested=lambda v:'{'+','.join(arr(x) for x in v)+'}'
 lines.append('{'+','.join(['Operation::'+s['op'],str(s['type'])+'U',arr(s['name']),arr(s['data']),json.dumps(s['label']),nested(s['results']),nested(s['states'])])+'},')
lines.append('};');(base/('native_recovered/tests/level_reflection_fixtures.inc' if LEVEL else 'native_recovered/tests/wave_reflection_fixtures.inc' if WAVE else 'native_recovered/tests/seedbank_reflection_fixtures.inc' if SEED else 'native_recovered/tests/railcart_reflection_fixtures.inc' if RAIL else 'native_recovered/tests/intro_reflection_fixtures.inc')).write_text('\n'.join(lines)+'\n',encoding='utf-8')
print('PASS',checks,'real inherited reflection full-state checkpoints',flush=True)
