import jadx.api.*;
import java.nio.file.*;
import java.nio.charset.StandardCharsets;
import java.io.File;
import java.util.*;

public class RecoveryBatch {
    public static void main(String[] input) throws Exception {
        Set<String> wanted=new LinkedHashSet<>(Files.readAllLines(Path.of(input[1]),StandardCharsets.UTF_8));
        Path output=Path.of(input[2]).toAbsolutePath().normalize();
        JadxArgs args=new JadxArgs();
        args.setInputFile(new File(input[0]));
        args.setSkipResources(true);
        args.setThreadsCount(1);
        args.setDecompilationMode(input.length>3?DecompilationMode.valueOf(input[3]):DecompilationMode.SIMPLE);
        args.setShowInconsistentCode(true);
        args.setInlineAnonymousClasses(false);
        args.setMoveInnerClasses(false);
        int count=0;
        try(JadxDecompiler decompiler=new JadxDecompiler(args)) {
            decompiler.load();
            for(JavaClass cls:decompiler.getClassesWithInners()) {
                boolean selected=wanted.contains(cls.getFullName())||wanted.contains(cls.getRawName());
                JavaClass originalTop=cls.getOriginalTopParentClass();
                if(originalTop!=null)selected|=wanted.contains(originalTop.getFullName())||wanted.contains(originalTop.getRawName());
                if(!selected)for(String target:wanted) {
                    if(cls.getFullName().startsWith(target+"$")||cls.getRawName().startsWith(target+"$")||cls.getFullName().startsWith(target+".")) {
                        selected=true;break;
                    }
                }
                if(!selected)continue;
                try {
                    String code=cls.getCode();
                    Path file=output.resolve(cls.getFullName().replace('.','/')+".java").normalize();
                    if(!file.startsWith(output))throw new IllegalArgumentException("Invalid class path");
                    Files.createDirectories(file.getParent());
                    Files.writeString(file,code,StandardCharsets.UTF_8);
                    count++;
                    System.out.println("RECOVERED\t"+cls.getFullName()+"\t"+file);
                }catch(Exception error){System.out.println("RECOVERY_FAILED\t"+cls.getFullName()+"\t"+error);}
            }
        }
        System.out.println("RECOVERY_TOTAL\t"+count+"\t"+wanted.size());
    }
}
