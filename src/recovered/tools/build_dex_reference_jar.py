"""Extract JVM compile-only declarations from original DEX files. No game implementation is emitted."""
from pathlib import Path
import struct,zipfile,json,hashlib
base=Path(__file__).resolve().parents[1];project=base/'rebuild_project'
be2=lambda n:struct.pack('>H',n)
be4=lambda n:struct.pack('>I',n)

class Dex:
    def __init__(self,data):
        self.b=data;self.strings=[]
        for i in range(self.u32(56)):
            off=self.u32(self.u32(60)+4*i);_,off=self.leb(off)
            self.strings.append(data[off:data.index(0,off)].replace(b'\xc0\x80',b'\0').decode('utf-8','surrogatepass'))
        self.types=[self.strings[self.u32(self.u32(68)+4*i)] for i in range(self.u32(64))]
        self.protos=[]
        for i in range(self.u32(72)):
            off=self.u32(76)+12*i
            self.protos.append('('+''.join(self.typelist(self.u32(off+8)))+')'+self.types[self.u32(off+4)])
        self.fields=[];self.methods=[]
        for i in range(self.u32(80)):
            owner,typ,name=struct.unpack_from('<HHI',data,self.u32(84)+8*i)
            self.fields.append((self.types[owner],self.strings[name],self.types[typ]))
        for i in range(self.u32(88)):
            owner,proto,name=struct.unpack_from('<HHI',data,self.u32(92)+8*i)
            self.methods.append((self.types[owner],self.strings[name],self.protos[proto]))
    def u32(self,p):return struct.unpack_from('<I',self.b,p)[0]
    def leb(self,p):
        n=shift=0
        while True:
            v=self.b[p];p+=1;n|=(v&127)<<shift
            if v<128:return n,p
            shift+=7
    def typelist(self,p):
        return [] if not p else [self.types[struct.unpack_from('<H',self.b,p+4+2*i)[0]] for i in range(self.u32(p))]
    def annotation(self,p):
        typ,p=self.leb(p);count,p=self.leb(p);values={}
        for _ in range(count):
            name,p=self.leb(p);value,p=self.value(p);values[self.strings[name]]=value
        return (self.types[typ],values),p
    def value(self,p):
        h=self.b[p];p+=1;kind=h&31;arg=h>>5
        if kind==0x1c:
            count,p=self.leb(p);result=[]
            for _ in range(count):v,p=self.value(p);result.append(v)
            return result,p
        if kind==0x1d:return self.annotation(p)
        if kind==0x1e:return None,p
        if kind==0x1f:return bool(arg),p
        raw=self.b[p:p+arg+1];p+=arg+1
        n=int.from_bytes(raw,'little',signed=kind in (0,2,4,6))
        if kind==0x17:return self.strings[n],p
        if kind==0x18:return self.types[n],p
        if kind==0x1a:return ('method',n),p
        if kind in (0x10,0x11):
            size=4 if kind==0x10 else 8
            return ('floatbits' if size==4 else 'doublebits',int.from_bytes(b'\0'*(size-len(raw))+raw,'little')),p
        return n,p
    def annotations(self,p):
        if not p:return {}
        result={}
        for i in range(self.u32(p)):
            (name,values),_=self.annotation(self.u32(p+4+4*i)+1);result[name]=values
        return result
    def classes(self):
        for i in range(self.u32(96)):
            typ,flags,sup,interfaces,source,ann,data,static=struct.unpack_from('<8I',self.b,self.u32(100)+32*i)
            result={'name':self.types[typ],'flags':flags,'super':None if sup==0xffffffff else self.types[sup],
                    'interfaces':self.typelist(interfaces),'fields':[],'methods':[],'annotations':{},'field_ann':{},'method_ann':{}}
            if ann:
                a,nf,nm,np=struct.unpack_from('<4I',self.b,ann)
                result['annotations']=self.annotations(a);p=ann+16
                for target,count in [('field_ann',nf),('method_ann',nm)]:
                    for _ in range(count):idx,loc=struct.unpack_from('<2I',self.b,p);p+=8;result[target][idx]=self.annotations(loc)
            values=[]
            if static:
                count,p=self.leb(static)
                for _ in range(count):v,p=self.value(p);values.append(v)
            if data:
                counts=[];p=data
                for _ in range(4):n,p=self.leb(p);counts.append(n)
                for group,count in enumerate(counts):
                    index=0
                    for j in range(count):
                        delta,p=self.leb(p);index+=delta;access,p=self.leb(p)
                        if group<2:
                            result['fields'].append((self.fields[index],access,values[j] if group==0 and j<len(values) else None,result['field_ann'].get(index,{})))
                        else:
                            code,p=self.leb(p);result['methods'].append((self.methods[index],access,result['method_ann'].get(index,{})))
            yield result

class Pool:
    def __init__(self):self.entries=[];self.lookup={}
    def item(self,tag,payload,key=None,wide=False):
        key=(tag,payload) if key is None else (tag,key)
        if key in self.lookup:return self.lookup[key]
        i=len(self.entries)+1;self.lookup[key]=i;self.entries.append(bytes([tag])+payload)
        if wide:self.entries.append(b'')
        return i
    def utf(self,s):
        raw=s.encode('utf-16be','surrogatepass');v=''.join(chr(int.from_bytes(raw[i:i+2],'big')) for i in range(0,len(raw),2))
        b=v.encode('utf-8','surrogatepass').replace(b'\0',b'\xc0\x80')
        return self.item(1,be2(len(b))+b)
    def cls(self,s):return self.item(7,be2(self.utf(s[1:-1] if s.startswith('L') else s)))
    def constant(self,typ,v):
        if typ=='Ljava/lang/String;':return self.item(8,be2(self.utf(v)))
        if typ=='J':return self.item(5,struct.pack('>q',v),wide=True)
        if typ in ('F','D'):
            tag=4 if typ=='F' else 6;bits=v[1] if isinstance(v,tuple) else 0
            return self.item(tag,bits.to_bytes(4 if tag==4 else 8,'big'),wide=tag==6)
        return self.item(3,struct.pack('>i',int(v)))

def locals_count(desc,static):
    args=desc[1:desc.index(')')];count=0 if static else 1;i=0
    while i<len(args):
        c=args[i];i+=1
        if c=='[':
            while args[i]=='[':i+=1
            c=args[i];i+=1
            if c=='L':i=args.index(';',i)+1
            count+=1
        elif c=='L':i=args.index(';',i)+1;count+=1
        else:count+=2 if c in 'JD' else 1
    return count

def make_class(c,inners):
    cp=Pool()
    def attr(name,value):return be2(cp.utf(name))+be4(len(value))+value
    def signature(a):
        value=a.get('Ldalvik/annotation/Signature;',{}).get('value')
        return [attr('Signature',be2(cp.utf(''.join(value))))] if value else []
    fields=[];methods=[]
    for (_,name,typ),flags,value,annotations in c['fields']:
        attrs=signature(annotations)
        if flags&0x18==0x18 and value is not None and typ in ('Z','B','C','S','I','J','F','D','Ljava/lang/String;'):
            attrs.append(attr('ConstantValue',be2(cp.constant(typ,value))))
        fields.append(be2(flags&0x50df)+be2(cp.utf(name))+be2(cp.utf(typ))+be2(len(attrs))+b''.join(attrs))
    for (_,name,desc),flags,annotations in c['methods']:
        if name=='<clinit>':continue
        access=flags&0x1dff;attrs=signature(annotations)
        throws=annotations.get('Ldalvik/annotation/Throws;',{}).get('value',[])
        if throws:attrs.append(attr('Exceptions',be2(len(throws))+b''.join(be2(cp.cls(v)) for v in throws)))
        if not access&(0x100|0x400):
            attrs.append(attr('Code',be2(1)+be2(locals_count(desc,bool(flags&8)))+be4(2)+b'\x01\xbf'+be2(0)+be2(0)))
        methods.append(be2(access)+be2(cp.utf(name))+be2(cp.utf(desc))+be2(len(attrs))+b''.join(attrs))
    attrs=signature(c['annotations'])
    inner=inners.get(c['name'],[])
    if inner:
        rows=[]
        for name,outer,short,flags in inner:
            rows.append(be2(cp.cls(name))+be2(cp.cls(outer))+be2(cp.utf(short) if short else 0)+be2(flags&0x761f))
        attrs.append(attr('InnerClasses',be2(len(rows))+b''.join(rows)))
    access=(c['flags']&0x7631)|0x20
    body=be2(access)+be2(cp.cls(c['name']))+be2(cp.cls(c['super']) if c['super'] else 0)
    body+=be2(len(c['interfaces']))+b''.join(be2(cp.cls(v)) for v in c['interfaces'])
    body+=be2(len(fields))+b''.join(fields)+be2(len(methods))+b''.join(methods)+be2(len(attrs))+b''.join(attrs)
    return b'\xca\xfe\xba\xbe'+be2(0)+be2(52)+be2(len(cp.entries)+1)+b''.join(cp.entries)+body

def main():
    classes={};dex_hashes={}
    for path in sorted((base/'raw').glob('classes*.dex')):
        data=path.read_bytes();dex_hashes[path.name]=hashlib.sha256(data).hexdigest()
        for c in Dex(data).classes():assert c['name'] not in classes;classes[c['name']]=c
    inners={}
    for c in classes.values():
        a=c['annotations'];inner=a.get('Ldalvik/annotation/InnerClass;');outer=a.get('Ldalvik/annotation/EnclosingClass;',{}).get('value')
        if inner and outer:
            row=(c['name'],outer,inner.get('name'),inner['accessFlags'])
            inners.setdefault(c['name'],[]).append(row);inners.setdefault(outer,[]).append(row)
    # The input APK itself references these absent legacy support helpers inside a catch(Throwable).
    # Declare them only for compilation; the original runtime classes are not changed.
    unresolved=[('Landroid/support/v4/content/ContextCompat;','checkSelfPermission','(Landroid/content/Context;Ljava/lang/String;)I'),
                ('Landroid/support/v4/app/ActivityCompat;','requestPermissions','(Landroid/app/Activity;[Ljava/lang/String;I)V')]
    for owner,name,desc in unresolved:
        assert not any(m[0][1:]==(name,desc) for m in classes[owner]['methods'])
        classes[owner]['methods'].append(((owner,name,desc),9,{}))
    # Java cannot name a default-package class from a named package. Compile under an alias,
    # then map only this owner descriptor back to LDreamRootPath; in generated Smali.
    alias=dict(classes['LDreamRootPath;']);alias['name']='Lcom/popcap/SexyAppFramework/DreamRootPath;'
    alias['methods']=[(method,flags,dict(annotations,**{'Ldalvik/annotation/Throws;':{'value':['Lcom/popcap/SexyAppFramework/AndroidGameApp$GeminiMethodNotFoundException;']}})
                       if method[1]=='getIMSIBySlot' else annotations) for method,flags,annotations in alias['methods']]
    out=project/'tools/original-dex-api.jar'
    with zipfile.ZipFile(out,'w',compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr('META-INF/COMPILE-ONLY.txt','Original DEX declarations. All non-native bodies throw null. NEVER package as application code.')
        for name,c in sorted(classes.items()):z.writestr(name[1:-1]+'.class',make_class(c,inners))
        z.writestr(alias['name'][1:-1]+'.class',make_class(alias,{}))
    record={'classes':len(classes),'total_compile_only_classfiles_including_alias':len(classes)+1,'original_dex_sha256':dex_hashes,'jar_sha256':hashlib.file_digest(out.open('rb'),'sha256').hexdigest(),
            'compile_only':True,'runtime_implementation':False,'contains_original_method_bodies':False,'generic_signatures_throws_and_inner_declarations':True,
            'default_package_compile_alias':alias['name'],'unresolved_original_calls_declared_compile_only':unresolved}
    (project/'tools/original-dex-api.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
    print(json.dumps(record,indent=2))
if __name__=='__main__':main()
