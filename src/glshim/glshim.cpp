#include <android/log.h>
#include <dlfcn.h>
#include <link.h>
#include <elf.h>
#include <sys/mman.h>
#include <unistd.h>
#include <stdint.h>
#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <GLES2/gl2.h>
#include <astc-codec/astc-codec.h>

#define TAG "GLShim"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, TAG, __VA_ARGS__)

typedef void (*PFN_glTexImage2D)(GLenum, GLint, GLint, GLsizei, GLsizei, GLint, GLenum, GLenum, const void *);
typedef void (*PFN_glTexSubImage2D)(GLenum, GLint, GLint, GLint, GLsizei, GLsizei, GLenum, GLenum, const void *);
typedef void (*PFN_glCompressedTexImage2D)(GLenum, GLint, GLenum, GLsizei, GLsizei, GLint, GLsizei, const void *);

static PFN_glTexImage2D real_tex = nullptr;
static PFN_glTexSubImage2D real_sub = nullptr;
static PFN_glCompressedTexImage2D real_ctex = nullptr;
typedef void (*PFN_etc1_decode)(const uint8_t *, uint8_t *, int, int);
static PFN_etc1_decode etc1_decode = nullptr;
static int tex_logs = 0;
static int ctex_logs = 0;

struct ModInfo {
    uintptr_t base = 0;
    const Elf32_Phdr *phdr = nullptr;
    int phnum = 0;
    const char *name = nullptr;
};

static int find_cb(struct dl_phdr_info *info, size_t, void *data) {
    ModInfo *out = (ModInfo *)data;
    if (info->dlpi_name && strstr(info->dlpi_name, out->name)) {
        out->base = (uintptr_t)info->dlpi_addr;
        out->phdr = (const Elf32_Phdr *)info->dlpi_phdr;
        out->phnum = info->dlpi_phnum;
        return 1;
    }
    return 0;
}

static void patch_got(ModInfo &m, const char *symname, void *replacement) {
    const Elf32_Dyn *dyn = nullptr;
    for (int i = 0; i < m.phnum; i++) {
        if (m.phdr[i].p_type == PT_DYNAMIC) {
            dyn = (const Elf32_Dyn *)(m.base + m.phdr[i].p_vaddr);
        }
    }
    if (!dyn) { LOGI("no PT_DYNAMIC"); return; }

    uintptr_t symtab = 0, strtab = 0, jmprel = 0, rel = 0;
    size_t pltrelsz = 0, relsz = 0;
    for (const Elf32_Dyn *d = dyn; d->d_tag != DT_NULL; d++) {
        switch (d->d_tag) {
            case DT_SYMTAB: symtab = d->d_un.d_ptr; break;
            case DT_STRTAB: strtab = d->d_un.d_ptr; break;
            case DT_JMPREL: jmprel = d->d_un.d_ptr; break;
            case DT_PLTRELSZ: pltrelsz = d->d_un.d_val; break;
            case DT_REL: rel = d->d_un.d_ptr; break;
            case DT_RELSZ: relsz = d->d_un.d_val; break;
        }
    }
    if (symtab < m.base) symtab += m.base;
    if (strtab < m.base) strtab += m.base;
    if (jmprel && jmprel < m.base) jmprel += m.base;
    if (rel && rel < m.base) rel += m.base;

    const Elf32_Sym *syms = (const Elf32_Sym *)symtab;
    const char *strs = (const char *)strtab;

    auto process = [&](uintptr_t addr, size_t bytes) {
        if (!addr) return;
        for (size_t off = 0; off + sizeof(Elf32_Rel) <= bytes; off += sizeof(Elf32_Rel)) {
            const Elf32_Rel *r = (const Elf32_Rel *)(addr + off);
            unsigned type = ELF32_R_TYPE(r->r_info);
            unsigned sym = ELF32_R_SYM(r->r_info);
            if (type != R_ARM_JUMP_SLOT && type != R_ARM_GLOB_DAT) continue;
            const char *n = strs + syms[sym].st_name;
            if (strcmp(n, symname) != 0) continue;
            uintptr_t *slot = (uintptr_t *)(m.base + r->r_offset);
            uintptr_t page = (uintptr_t)slot & ~(uintptr_t)(getpagesize() - 1);
            if (mprotect((void *)page, getpagesize(), PROT_READ | PROT_WRITE) != 0) {
                LOGI("mprotect failed for %s", symname);
                continue;
            }
            uintptr_t old = *slot;
            *slot = (uintptr_t)replacement;
            __builtin___clear_cache((char *)slot, (char *)slot + sizeof(*slot));
            mprotect((void *)page, getpagesize(), PROT_READ);
            LOGI("patched %s at %p: %p -> %p", symname, slot, (void *)old, replacement);
        }
    };
    process(jmprel, pltrelsz);
    process(rel, relsz);
}

extern "C" void glTexImage2D(GLenum target, GLint level, GLint internalformat, GLsizei width,
                             GLsizei height, GLint border, GLenum format, GLenum type,
                             const void *pixels) {
    if (tex_logs < 300) {
        tex_logs++;
        if (internalformat == 0x8033 || internalformat == 0x8045 ||
            internalformat == 0x8D64 || internalformat == 0x8D65 ||
            internalformat == 0x8D66 || internalformat == 0x8C00 ||
            tex_logs <= 20) {
            LOGI("glTexImage2D internal=0x%x format=0x%x type=0x%x %dx%d border=%d",
                 internalformat, format, type, width, height, border);
        }
    }
    // GL_UNSIGNED_SHORT_4_4_4_4 (0x8033) used as internalformat: expand to RGBA8888
    if (internalformat == 0x8033 && type == 0x8033 && format == GL_RGBA) {
        if (!pixels) {
            if (real_tex) real_tex(target, level, GL_RGBA, width, height, border, GL_RGBA, GL_UNSIGNED_BYTE, nullptr);
            return;
        }
        if (width > 0 && height > 0) {
            size_t n = (size_t)width * (size_t)height;
            uint8_t *out = (uint8_t *)malloc(n * 4);
            if (out) {
                const uint16_t *src = (const uint16_t *)pixels;
                for (size_t i = 0; i < n; i++) {
                    uint16_t p = src[i];
                    out[i*4+0] = (uint8_t)(((p >> 12) & 0xF) * 17);
                    out[i*4+1] = (uint8_t)(((p >> 8) & 0xF) * 17);
                    out[i*4+2] = (uint8_t)(((p >> 4) & 0xF) * 17);
                    out[i*4+3] = (uint8_t)((p & 0xF) * 17);
                }
                if (real_tex) real_tex(target, level, GL_RGBA, width, height, border, GL_RGBA, GL_UNSIGNED_BYTE, out);
                free(out);
                return;
            }
        }
    }
    if (real_tex) real_tex(target, level, internalformat, width, height, border, format, type, pixels);
}

extern "C" void glTexSubImage2D(GLenum target, GLint level, GLint xoffset, GLint yoffset,
                                GLsizei width, GLsizei height, GLenum format, GLenum type,
                                const void *pixels) {
    if (format == GL_RGBA && type == 0x8033 && pixels && width > 0 && height > 0) {
        size_t n = (size_t)width * (size_t)height;
        uint8_t *out = (uint8_t *)malloc(n * 4);
        if (out) {
            const uint16_t *src = (const uint16_t *)pixels;
            for (size_t i = 0; i < n; i++) {
                uint16_t p = src[i];
                out[i*4+0] = (uint8_t)(((p >> 12) & 0xF) * 17);
                out[i*4+1] = (uint8_t)(((p >> 8) & 0xF) * 17);
                out[i*4+2] = (uint8_t)(((p >> 4) & 0xF) * 17);
                out[i*4+3] = (uint8_t)((p & 0xF) * 17);
            }
            if (real_sub) real_sub(target, level, xoffset, yoffset, width, height, GL_RGBA, GL_UNSIGNED_BYTE, out);
            free(out);
            return;
        }
    }
    if (real_sub) real_sub(target, level, xoffset, yoffset, width, height, format, type, pixels);
}

static inline uint8_t clamp8(int v) {
    return v < 0 ? 0 : (v > 255 ? 255 : (uint8_t)v);
}

static void etc1_decode_cpu(const uint8_t *data, uint8_t *out, int w, int h) {
    static const int mods[8][4] = {
        {2, 8, -2, -8}, {5, 17, -5, -17}, {9, 29, -9, -29}, {13, 42, -13, -42},
        {18, 60, -18, -60}, {24, 80, -24, -80}, {33, 106, -33, -106}, {47, 183, -47, -183}
    };
    int bw = (w + 3) / 4, bh = (h + 3) / 4;
    for (int by = 0; by < bh; by++) {
        for (int bx = 0; bx < bw; bx++) {
            const uint8_t *p = data + ((size_t)by * bw + bx) * 8;
            uint32_t hi = ((uint32_t)p[0] << 24) | ((uint32_t)p[1] << 16) | ((uint32_t)p[2] << 8) | p[3];
            uint32_t lo = ((uint32_t)p[4] << 24) | ((uint32_t)p[5] << 16) | ((uint32_t)p[6] << 8) | p[7];
            int R1 = (hi >> 28) & 15, R2 = (hi >> 24) & 15;
            int G1 = (hi >> 20) & 15, G2 = (hi >> 16) & 15;
            int B1 = (hi >> 12) & 15, B2 = (hi >> 8) & 15;
            int t1 = (hi >> 5) & 7, t2 = (hi >> 2) & 7;
            bool diff = (hi >> 1) & 1, flip = hi & 1;
            int r1, g1, b1, r2, g2, b2;
            if (diff) {
                int r5 = (R1 << 1) | (R1 >> 3), g5 = (G1 << 1) | (G1 >> 3), b5 = (B1 << 1) | (B1 >> 3);
                int dr = (R2 << 29) >> 29, dg = (G2 << 29) >> 29, db = (B2 << 29) >> 29;
                int r5b = r5 + dr, g5b = g5 + dg, b5b = b5 + db;
                r5b = r5b < 0 ? 0 : (r5b > 31 ? 31 : r5b);
                g5b = g5b < 0 ? 0 : (g5b > 31 ? 31 : g5b);
                b5b = b5b < 0 ? 0 : (b5b > 31 ? 31 : b5b);
                r1 = (r5 << 3) | (r5 >> 2); r2 = (r5b << 3) | (r5b >> 2);
                g1 = (g5 << 3) | (g5 >> 2); g2 = (g5b << 3) | (g5b >> 2);
                b1 = (b5 << 3) | (b5 >> 2); b2 = (b5b << 3) | (b5b >> 2);
            } else {
                r1 = R1 * 17; g1 = G1 * 17; b1 = B1 * 17;
                r2 = R2 * 17; g2 = G2 * 17; b2 = B2 * 17;
            }
            for (int y = 0; y < 4; y++) {
                for (int x = 0; x < 4; x++) {
                    int x2 = flip ? y : x, y2 = flip ? x : y;
                    int i = x2 * 4 + y2;
                    int msb = (lo >> (i + 16)) & 1, lsb = (lo >> i) & 1;
                    int idx = (msb << 1) | lsb;
                    int sub = (x2 >= 2) ? 1 : 0;
                    int m = mods[sub ? t2 : t1][idx];
                    int px = bx * 4 + x, py = by * 4 + y;
                    if (px < w && py < h) {
                        size_t o = ((size_t)py * w + px) * 4;
                        out[o + 0] = clamp8((sub ? r2 : r1) + m);
                        out[o + 1] = clamp8((sub ? g2 : g1) + m);
                        out[o + 2] = clamp8((sub ? b2 : b1) + m);
                        out[o + 3] = 255;
                    }
                }
            }
        }
    }
}

static bool astc_decode_scaled(const uint8_t *data, size_t imageSize,
                               int w, int h, int bx, int by, int step,
                               astc_codec::FootprintType fp,
                               uint8_t **out, int *ow, int *oh) {
    int bw = (w + bx - 1) / bx;
    int bh = (h + by - 1) / by;
    int nw = (bw + step - 1) / step;
    int nh = (bh + step - 1) / step;
    size_t dstBlocks = (size_t)nw * (size_t)nh;
    uint8_t *tmp = (uint8_t *)calloc(dstBlocks, 16);
    if (!tmp) return false;
    for (int j = 0; j < nh; j++) {
        for (int i = 0; i < nw; i++) {
            int si = i * step, sj = j * step;
            size_t off = (size_t)(sj * bw + si) * 16;
            if (si < bw && sj < bh && off + 16 <= imageSize) {
                memcpy(tmp + ((size_t)j * nw + i) * 16, data + off, 16);
            }
        }
    }
    *ow = nw * bx;
    *oh = nh * by;
    size_t outsz = (size_t)(*ow) * (size_t)(*oh) * 4;
    uint8_t *rgba = (uint8_t *)malloc(outsz);
    bool ok = rgba &&
              astc_codec::ASTCDecompressToRGBA(tmp, dstBlocks * 16,
                                               (size_t)(*ow), (size_t)(*oh), fp,
                                               rgba, outsz, (size_t)(*ow) * 4);
    free(tmp);
    if (!ok) {
        free(rgba);
        return false;
    }
    *out = rgba;
    return true;
}

extern "C" void glCompressedTexImage2D(GLenum target, GLint level, GLenum internalformat,
                                       GLsizei width, GLsizei height, GLint border,
                                       GLsizei imageSize, const void *data) {
    if (ctex_logs < 500) {
        ctex_logs++;
        LOGI("glCompressedTexImage2D internal=0x%x %dx%d size=%d border=%d",
             internalformat, width, height, imageSize, border);
    }
    // ETC1 (0x8D64): decode to RGBA8888
    if (internalformat == 0x8D64 && data && width > 0 && height > 0 && real_tex) {
        uint8_t *out = (uint8_t *)malloc((size_t)width * (size_t)height * 4);
        if (out) {
            etc1_decode_cpu((const uint8_t *)data, out, width, height);
            real_tex(target, level, GL_RGBA, width, height, border, GL_RGBA, GL_UNSIGNED_BYTE, out);
            free(out);
            return;
        }
    }
    // ASTC (0x93B0..0x93BD): decode to RGBA8888 in horizontal strips to limit memory
    if (data && width > 0 && height > 0 && real_tex) {
        astc_codec::FootprintType fp;
        int bx = 4, by = 4;
        bool is_astc = true;
        switch (internalformat) {
            case 0x93B0: fp = astc_codec::FootprintType::k4x4; bx = 4; by = 4; break;
            case 0x93B1: fp = astc_codec::FootprintType::k5x4; bx = 5; by = 4; break;
            case 0x93B2: fp = astc_codec::FootprintType::k5x5; bx = 5; by = 5; break;
            case 0x93B3: fp = astc_codec::FootprintType::k6x5; bx = 6; by = 5; break;
            case 0x93B4: fp = astc_codec::FootprintType::k6x6; bx = 6; by = 6; break;
            case 0x93B5: fp = astc_codec::FootprintType::k8x5; bx = 8; by = 5; break;
            case 0x93B6: fp = astc_codec::FootprintType::k8x6; bx = 8; by = 6; break;
            case 0x93B7: fp = astc_codec::FootprintType::k8x8; bx = 8; by = 8; break;
            case 0x93B8: fp = astc_codec::FootprintType::k10x5; bx = 10; by = 5; break;
            case 0x93B9: fp = astc_codec::FootprintType::k10x6; bx = 10; by = 6; break;
            case 0x93BA: fp = astc_codec::FootprintType::k10x8; bx = 10; by = 8; break;
            case 0x93BB: fp = astc_codec::FootprintType::k10x10; bx = 10; by = 10; break;
            case 0x93BC: fp = astc_codec::FootprintType::k12x10; bx = 12; by = 10; break;
            case 0x93BD: fp = astc_codec::FootprintType::k12x12; bx = 12; by = 12; break;
            default: is_astc = false; break;
        }
        if (is_astc) {
            int step = 1;
            if (width >= 2048 || height >= 2048) step = 2;
            
            if (step > 1) {
                uint8_t *scaled = nullptr;
                int ow = 0, oh = 0;
                if (astc_decode_scaled((const uint8_t *)data, (size_t)imageSize,
                                       width, height, bx, by, step, fp,
                                       &scaled, &ow, &oh) && real_tex) {
                    LOGI("ASTC scale step=%d %dx%d -> %dx%d", step, width, height, ow, oh);
                    real_tex(target, level, GL_RGBA, ow, oh, border, GL_RGBA, GL_UNSIGNED_BYTE, scaled);
                    free(scaled);
                    return;
                }
                free(scaled);
            }
            int blocksPerRow = (width + bx - 1) / bx;
            int blockRows = (height + by - 1) / by;
            // allocate the RGBA texture once; feed it strip by strip
            real_tex(target, level, GL_RGBA, width, height, border, GL_RGBA, GL_UNSIGNED_BYTE, nullptr);
            int stripBlocks = 256 / by;
            if (stripBlocks < 1) stripBlocks = 1;
            bool ok = true;
            for (int r = 0; r < blockRows; r += stripBlocks) {
                int rows = blockRows - r; if (rows > stripBlocks) rows = stripBlocks;
                int sh = rows * by; if (sh > height - r * by) sh = height - r * by;
                size_t srcOff = (size_t)r * blocksPerRow * 16;
                size_t srcSize = (size_t)rows * blocksPerRow * 16;
                if (srcOff + srcSize > (size_t)imageSize) srcSize = (size_t)imageSize - srcOff;
                size_t outsz = (size_t)width * (size_t)sh * 4;
                uint8_t *out = (uint8_t *)malloc(outsz);
                if (!out) { ok = false; break; }
                if (!astc_codec::ASTCDecompressToRGBA((const uint8_t *)data + srcOff, srcSize,
                                                      (size_t)width, (size_t)sh, fp,
                                                      out, outsz, (size_t)width * 4)) {
                    ok = false;
                    free(out);
                    break;
                }
                if (real_sub) real_sub(target, level, 0, r * by, width, sh, GL_RGBA, GL_UNSIGNED_BYTE, out);
                free(out);
            }
            if (ok) return;
            LOGI("ASTC decode failed internal=0x%x %dx%d size=%d", internalformat, width, height, imageSize);
        }
    }
    if (real_ctex) real_ctex(target, level, internalformat, width, height, border, imageSize, data);
}

__attribute__((constructor)) static void init_shim() {
    void *gles = dlopen("libGLESv2.so", RTLD_NOW | RTLD_GLOBAL);
    if (!gles) { LOGI("dlopen libGLESv2 failed: %s", dlerror()); }
    real_tex = (PFN_glTexImage2D)dlsym(RTLD_NEXT, "glTexImage2D");
    if (!real_tex) real_tex = (PFN_glTexImage2D)dlsym(gles, "glTexImage2D");
    real_sub = (PFN_glTexSubImage2D)dlsym(RTLD_NEXT, "glTexSubImage2D");
    if (!real_sub) real_sub = (PFN_glTexSubImage2D)dlsym(gles, "glTexSubImage2D");
    real_ctex = (PFN_glCompressedTexImage2D)dlsym(RTLD_NEXT, "glCompressedTexImage2D");
    if (!real_ctex) real_ctex = (PFN_glCompressedTexImage2D)dlsym(gles, "glCompressedTexImage2D");
    void *etc1 = dlopen("/system/lib/libETC1.so", RTLD_NOW | RTLD_GLOBAL);
    if (!etc1) etc1 = dlopen("libETC1.so", RTLD_NOW | RTLD_GLOBAL);
    if (etc1) etc1_decode = (PFN_etc1_decode)dlsym(etc1, "etc1_decode_image");
    LOGI("init: real tex=%p sub=%p ctex=%p etc1h=%p etc1=%p err=%s",
         real_tex, real_sub, real_ctex, etc1, etc1_decode, etc1 ? "" : dlerror());

    ModInfo mi;
    mi.name = "libSrc.so";
    dl_iterate_phdr(find_cb, &mi);
    if (!mi.base) { LOGI("libSrc not found"); return; }
    LOGI("libSrc base=%p", (void *)mi.base);
    patch_got(mi, "glTexImage2D", (void *)glTexImage2D);
    patch_got(mi, "glTexSubImage2D", (void *)glTexSubImage2D);
    patch_got(mi, "glCompressedTexImage2D", (void *)glCompressedTexImage2D);
    LOGI("done patching");
}

