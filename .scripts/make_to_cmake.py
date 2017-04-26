#!/grid/common/pkgs/python/v3.4.0/bin/python3.4 -B
"""
 CLion project generator.
 The scripts runs dry run in one or more directories and builds CLion project out of log.
 Run build for every directory, find all targets and then run build again for every target
 to make target options more personalized.
 Limitations due to cmake limitations:
 - compiler is the same for the whole project
 - C++ options are the same for the whole project, includes, defines and options common for C/C++ can be target-specific
 (C) Yevgen Ryazanov @ Cadence, 2016
"""

# references:
#    https://cmake.org/cmake/help/v3.5/manual/cmake-properties.7.html

import argparse
import glob
from enum import Enum
import os
import re
import shutil
import subprocess
import sys

gcc_path = "/grid/common/pkgs/gcc/v4.8.3/bin/g++"


def main():
    parser = argparse.ArgumentParser(description="Create clion project")
    parser.add_argument("--base", required=False, help="base dir to store sub-projects")
    parser.add_argument("--ignore_error", action="store_true", help="do not fail on build error")
    parser.add_argument("--one", action="store_true", help="generate one file")
    parser.add_argument("--project_dir", help="dir to store CMakeLists.txt")
    parser.add_argument("--verbose", action="store_true", help="show debug messages")
    parser.add_argument("dirs", nargs="*", help="source dir(s)")

    options = parser.parse_args()

    options.base = os.path.normpath(options.base) if options.base else os.getcwd()
    if not options.project_dir:
        options.project_dir = options.base

    if not options.dirs:
        dirs = [os.getcwd()]
        options.one = True
    else:
        dirs = [os.path.abspath(d) for d in options.dirs]

    if not options.base:
        options.base = os.getcwd()
    else:
        options.base = os.path.abspath(options.base)
        if not os.path.exists(options.base):
            os.mkdir(options.base)

    for d in dirs:
        if not os.path.exists(d):
            raise Exception("{} does not exists".format(d))
        makefile = os.path.join(d, "Makefile")
        if not os.path.exists(makefile):
            raise Exception("{} does not exists".format(makefile))

    idea = options.base + "/.idea"
    if os.path.exists(idea):
        print("removing {}...".format(idea))
        shutil.rmtree(idea)

    new_dirs = []
    for d in dirs:
        d = os.path.abspath(d)
        if is_hsv_build(d) and not os.path.exists(os.path.join(d, "Makefile.cust")):
            new_dirs.extend(find_subdirs(d))
        else:
            new_dirs.append(d)

    project = Project(options, new_dirs)
    project.generate()

    project_root = calculate_project_root(dirs)
    # print(project_root)
    source_roots = []
    exclude_roots = []
    calculate_paths(project_root, dirs, source_roots, exclude_roots)
    # print(exclude_roots)
    bin_dir = os.path.dirname(sys.argv[0])
    generate_misc(bin_dir + "/misc_templ.xml", options.base + "/.idea/misc.xml", project_root, source_roots,
                  exclude_roots)


def is_hsv_build(d):
    if os.path.exists(os.path.join(d, "Makefile.cust")):
        return True
    try:
        makefile = os.path.join(d, "Makefile")
        grep_cmd = ["grep", "QT_ROOT", makefile]
        subprocess.check_call(grep_cmd)
    except subprocess.CalledProcessError:
        return False
    return True


# get list of buildable dirs recursively
def find_subdirs(d):
    assert is_hsv_build(d)
    saved_dir = os.getcwd()
    os.chdir(d)
    try:
        grep_cmd = ["grep", "QT_ROOT", "Makefile"]
        subprocess.check_call(grep_cmd)
    except subprocess.CalledProcessError:
        return [d]
    # HSV specific
    make_cmd = ["gmake", "-j", "8", "-s", "SYSTRG=64bit", "dirlist"]
    out = subprocess.check_output(make_cmd, stderr=subprocess.DEVNULL).decode().strip().splitlines()
    dirs = [x for x in out if re.match("/vobs/", x)]
    os.chdir(saved_dir)
    return sorted(dirs)


# dry build command
def get_build_command(is_hsv):
    if is_hsv:
        return ["clearmake", "-nu", "-C", "gnu", "SYSTRG=64bit"]
    return ["gmake", "-nB"]


def calculate_project_root(dirs):
    dir_lens = [len(d.split("/")) for d in dirs]
    target_len = min(dir_lens)
    target_dirs = dirs[:]
    while True:
        target_dirs = ["/".join(d.split("/")[0:target_len]) for d in target_dirs]
        root = target_dirs[0]
        if all(t == root for t in target_dirs):
            return root if root else "/"
        target_len -= 1


def is_subdirectory(child, parent):
    return child[0:len(parent)] == parent


def calculate_paths(root, dirs, sources, excludes):
    sub_dirs = glob.glob(root + "/" + "*")
    for s in sub_dirs:
        if s in dirs or not os.path.isdir(s):
            continue
        if os.path.basename(s) == "include":
            sources.append(s)
        # elif os.path.islink(s):
        #     excludes.append(s)
        elif all(not is_subdirectory(d, s) for d in dirs):
            excludes.append(s)
        else:
            calculate_paths(s, dirs, sources, excludes)
    pass


def generate_misc(frm, to, root, sources, excludes):
    to_dir = os.path.dirname(to)
    os.mkdir(to_dir)
    with open(frm, "r") as fin, open(to, "w") as fout:
        for line in fin.readlines():
            if re.match(".*%project_root%", line):
                line = line.replace("%project_root%", root)
                fout.write(line)
            elif re.match(".*%exclude_root%", line):
                for p in sorted(excludes):
                    line2 = line.replace("%exclude_root%", p)
                    fout.write(line2)
            elif re.match(".*%source_root%", line):
                for p in sources:
                    line2 = line.replace("%source_root%", p)
                    fout.write(line2)
            else:
                fout.write(line)


# multi-directory project
class Project:
    def __init__(self, options, dirs):
        self.options = options
        self.dirs = dirs

    def generate(self):
        cmake_file = os.path.join(self.options.project_dir, "CMakeLists.txt")
        failed_dirs = []
        with open(cmake_file, "w") as f:
            f.write("# generated with {}\n".format(" ".join(sys.argv)))
            f.write("cmake_minimum_required(VERSION 3.5)\n\n")
            # do not write compiler, no effect: https://cmake.org/Wiki/CMake_FAQ#How_do_I_use_a_different_compiler.3F
            # f.write("set(CMAKE_CXX_COMPILER /grid/common/pkgs/gcc/v4.8.3/bin/g++)\n\n")
            f.write("set(HAVE_CXX $ENV{CXX})\n")
            f.write("set(NEED_CXX \"{}\")\n".format(gcc_path))
            f.write("if(NOT HAVE_CXX STREQUAL NEED_CXX)\n")
            f.write("\tmessage(FATAL_ERROR \"wrong compiler, ${HAVE_CXX}, must be ${NEED_CXX}\")\n")
            f.write("endif()\n\n")
            f.write("set(CMAKE_VERBOSE_MAKEFILE ON)\n\n")
            for d in self.dirs:
                directory = Dir(self, d)
                try:
                    filename = directory.generate(f if self.options.one else None)
                    if filename:
                        f.write("include(\"{}\")\n".format(filename))
                except subprocess.CalledProcessError:
                    if self.options.ignore_error:
                        failed_dirs.append(d)
                    else:
                        break
        for d in failed_dirs:
            print("buid failed @ " + d)

    @classmethod
    def get_build_log(cls, command, target):
        for key in ["ENABLE_RND_PBUILD", "CCASE_CONC"]:
            if key in os.environ:
                del os.environ[key]
        dry_build_cmd = command
        if target:
            dry_build_cmd.append(target)
        build_log = subprocess.check_output(dry_build_cmd, stderr=subprocess.STDOUT).decode().strip()
        build_log = build_log.replace(r"\n", "").replace("\t", " ").replace("  ", " ")  # '\\n' is in progVersion
        lines = build_log.split("\n")
        lines2 = []
        for l in lines:
            l = l.strip()
            if not l:
                continue
            if re.match(".*is up to date", l):
                continue
            lines2.extend(cls.split_shell_command(l, [';']))
        lines3 = []
        for l in lines2:
            if re.match("test ", l) or re.match("if ", l) or re.match("then ", l) or re.match("fi ?", l):
                print("  ignoring " + l)
                continue
            if re.match("clearmake", l) or re.match("\"clearmake", l):
                continue
            if re.match("/bin/true ", l):
                continue
            if re.match("cd ", l):  # cd can be special
                continue
            lines3.append(l)
        return lines3

    # separate multiple statements separate by non-escaped ; into lines
    # split a command into items using several separators
    @staticmethod
    def split_shell_command(line, separators, keep_separators=None):
        lines = []
        pos = 0
        statement_pos = 0
        while pos < len(line):
            c = line[pos]
            if c == '\\':
                pos += 2
                continue
            if c == '"' or c == '\'' or c == '`':
                cc = '\'' if c == '`' else c  # invert c if needed
                pos += 1
                while pos < len(line) and (line[pos - 1] == '\\' or (line[pos] != c and line[pos] != cc)):
                    pos += 1
                if pos == len(line):
                    break
                pos += 1
                continue
            found = False
            for s in separators:
                if line[pos:pos + len(s)] == s:
                    statement = line[statement_pos:pos].strip()
                    if statement:
                        lines.append(statement)
                    pos += len(s)
                    statement_pos = pos
                    found = True
                    break
            if found:
                continue
            if keep_separators:
                for s in keep_separators:
                    if line[pos:pos + len(s)] == s:
                        statement = line[statement_pos:pos].strip()
                        if statement:
                            lines.append(statement)
                        lines.append(line[pos:pos + len(s)])
                        pos += len(s)
                        statement_pos = pos
                        found = True
                        break
            if found:
                continue
            pos += 1
        statement = line[statement_pos:].strip()
        if statement:
            lines.append(statement)
        return lines

    @staticmethod
    def project_from_path(path):
        # os.path.split splits only one level
        dirs = path.strip("/").split("/")
        dirs = [d.lower() for d in dirs]
        if len(dirs) > 4:
            return "{}_{}_{}".format(dirs[-3], dirs[-2], dirs[-1])
        if len(dirs) > 3:
            return "{}_{}".format(dirs[-2], dirs[-1])
        return "{}".format(dirs[-1])


class Dir:
    def __init__(self, parent, directory):
        self.parent = parent  # multi-dir project
        self.options = parent.options
        self.directory = directory
        self.hsv = is_hsv_build(directory)
        self.stages = {}
        self.generated = []  # generated source file and static libs

    def generate(self, f):
        print("dir: {}".format(self.directory))
        saved_dir = os.getcwd()
        os.chdir(self.directory)
        if self.options.verbose:
            print("locating targets")
        target = "install" if self.hsv else None
        build_log = Project.get_build_log(get_build_command(self.hsv), target)
        targets = self.find_targets(build_log)
        if not targets:
            print("  ignoring dir " + self.directory)
            os.chdir(saved_dir)
            return None
        self.stages = self.find_stages(build_log)
        project = Project.project_from_path(self.directory)  # for cmake project command
        gen_dir = os.path.join(self.directory, "x86-lx2-64") if self.hsv else self.directory
        if f:
            self.generate_file(f, project, targets, gen_dir)
            os.chdir(saved_dir)
            return None
        else:
            # creating a project dir does not help with a flat list of files in project view
            # project_dir = os.path.join(self.options.base, project)
            # if not os.path.exists(project_dir):
            #     os.mkdir(project_dir)
            project_dir = self.options.base
            outfile = os.path.join(project_dir, project) + ".cmake"
            if os.path.exists(outfile):
                #os.rename(outfile, outfile + ".bak")
                os.unlink(outfile)
            with open(outfile, "w") as f:
                self.generate_file(f, project, targets, gen_dir)
            os.chdir(saved_dir)
            return outfile

    # generate a sub-project for one directory
    def generate_file(self, f, project, targets, gen_dir):
        if not self.options.one:
            f.write("cmake_minimum_required(VERSION 3.5)\n\n")
        f.write("project({})\n\n".format(project))
        f.write("set(CMAKE_CXX_FLAGS \"-std=c++11\")\n\n")
        f.write("set(SRC_DIR {})\n".format(self.directory))
        # f.write("set(GEN_DIR ${CMAKE_CURRENT_BINARY_DIR})\n\n")
        f.write("set(GEN_DIR {})\n\n".format(gen_dir))
        f.write("add_custom_target({}\n".format(self.full_target_name("mkdir_gen")))
        f.write("    COMMAND mkdir -p ${GEN_DIR}\n")
        f.write(")\n\n")
        for target in targets:
            t = Target(self, target, self.directory, gen_dir)
            t.generate(f)

    def full_target_name(self, name):
        project = Project.project_from_path(self.directory)
        # normalize target name
        full_name = ""
        for c in "{}_{}".format(project, name):
            if not c.isalnum() and c not in "_+-.":  # CMP0002
                c = '-'
            full_name += c
        return full_name

    # scan build log for targets: shared/static lib or binary
    # the target can be multiple times because bin target can include lib target
    # make list of unique targets preserving order
    @staticmethod
    def find_targets(build_log):
        targets = []
        for line in build_log:
            tokens = Project.split_shell_command(line, [' '], [">>", ">"])
            name = None
            if Target.is_tool("gcc", tokens[0]) or Target.is_tool("g++", tokens[0]):
                if any(tok == "-c" for tok in tokens):
                    continue
                i = tokens.index("-o")
                name = tokens[i + 1]
            elif Target.is_tool("ar", tokens[0]):
                i = tokens.index("-r")
                name = tokens[i + 1]
            if name and name not in targets:
                targets.append(name)
        return targets

    # find staging commands: which binary deliver to which place
    @staticmethod
    def find_stages(build_log):
        stages = {}
        for line in build_log:
            tokens = Project.split_shell_command(line, [' '])
            if re.match("/.*/stage", tokens[0]):
                what = tokens[1]
                where = tokens[2]
                stages[what] = where
        return stages


class TargetKind(Enum):
    shared = 1
    static = 2
    binary = 3


# One target: static or shared library or binary
class Target:
    def __init__(self, parent, file, src_dir, gen_dir):
        print("* target: {}".format(file))
        self.parent = parent
        self.options = parent.options
        self.file = file
        self.src_dir = src_dir
        self.gen_dir = gen_dir
        self.hsv = parent.hsv
        self.build_command = get_build_command(self.hsv)
        self.cflags = []
        self.cxxflags = []
        self.includes = []
        self.defines = []
        self.lflags = []
        self.libs = []
        self.srcs = []  # existing C files
        self.processed = []  # already generated C files
        self.hdrs = []  # generated headers
        self.generated = []
        self.commands = {}  # file -> commands dict
        self.unassigned_commands = []
        self.customs = []  # custom targets like locally modified static libs
        self.file_hint = None
        self.output = None  # current > file
        if re.match("lib.*.so", self.file) or re.match("lib.*.a", self.file):
            self.name = os.path.splitext(self.file)[0]
        else:
            self.name = self.file

    def reset(self):
        self.commands = {}
        self.unassigned_commands = []
        self.file_hint = None
        self.output = None

    # generate target
    def generate(self, f):
        target = "debug-" + self.file if self.hsv else self.file
        build_log = Project.get_build_log(self.build_command, target)
        for line in build_log:
            tokens = Project.split_shell_command(line, [' '], ["<", ">>", ">"])
            assert len(tokens) != 0
            if self.options.verbose:
                # print("  tokens: " + str(tokens))
                # print("  tokens: " + " ".join(tokens))
                pass
            if self.is_tool("gcc", tokens[0]) or self.is_tool("g++", tokens[0]):
                # compilation or linking, no mix yet
                if "-c" in tokens:
                    self.process_gcc(tokens)
                else:
                    self.process_ld(f, tokens)
                self.output = None
                self.file_hint = None
            elif self.is_tool("ar", tokens[0]):
                # making archive, static lib
                self.process_ar(f, tokens)
            elif tokens[0] == "rm":
                # rm is a hint which file is generated next, last resort
                file = tokens[-1]
                if not self.is_obj_file(file) and '*' not in file and '?' not in file:
                    self.file_hint = file
                    self.commands[file] = []
            elif re.match("/.*/stage", tokens[0]):
                pass
            elif re.match("/.*/ss_strip", tokens[0]):
                pass
            else:
                (in_file, out_files) = self.find_input_output(tokens)
                if out_files:
                    if not isinstance(out_files, list):
                        out_files = [out_files]
                    self.generated.extend(out_files)
                    self.output = out_files[0]
                    self.file_hint = None
                    if out_files[0] not in self.commands:
                        self.commands[out_files[0]] = self.unassigned_commands
                        self.unassigned_commands = []
                    if in_file:
                        if in_file in list(self.commands):
                            self.commands[out_files].extend(self.commands[in_file])
                            del self.commands[in_file]
                if self.options.verbose:
                    pass  # print("    input: {}, output: {}, hint: {}".format(in_file, self.output, self.file_hint))
                if tokens[0] == "echo" and not out_files:
                    pass
                elif self.output:
                    self.commands[self.output].append(tokens)
                elif self.file_hint:
                    self.commands[self.file_hint].append(tokens)
                else:
                    print("warning: unknown output for command: " + str(tokens))
                    self.unassigned_commands.append(tokens)

    # source file compilation
    def process_gcc(self, tokens):
        file = None
        flags = []
        includes = []
        defines = []
        i = 1
        while i < len(tokens):
            tok = tokens[i]
            # print("tok: /{}/".format(tok))
            if tok == "-o":
                i += 1
            elif tok == "-c":
                pass
            elif tok[0:2] == "-I":
                includes.append(tok[2:])
            elif tok[0:2] == "-D":
                defines.append(self.normalize_define(tok[2:]))
            elif self.is_c_file(tok) or self.is_cxx_file(tok):
                file = tok
                if self.is_generated(tok):
                    self.processed.append(tok)
                else:
                    tok = tok.replace("../", "", 1)
                    self.srcs.append(tok)
            else:
                if not re.match("-std=", tok):
                    flags.append(tok)
            i += 1
        assert file is not None
        if self.is_c_file(file):
            self.cflags.extend([f for f in flags if f not in self.cflags])
        else:
            self.cxxflags.extend([f for f in flags if f not in self.cxxflags])
        self.includes.extend([i for i in includes if i not in self.includes])
        self.defines.extend([d for d in defines if d not in self.defines])

    # linking shared lib or binary
    def process_ld(self, f, tokens):
        target = None
        shared = False
        obj_files = []
        lib_path = []
        libs = []
        lflags = []
        short_libs = []
        i = 1
        while i < len(tokens):
            tok = tokens[i]
            if tok == "-o":
                i += 1
                target = tokens[i]
            elif tok == "-shared":
                shared = True
            elif tok[0:2] == "-I" or tok[0:2] == "-D":
                pass
            elif tok[0:2] == "-l":
                libs.append(tok[2:])
            elif tok[0] == '-':
                lflags.append(tok)
                if tok[0:2] == "-L":
                    lib_path.append(tok[2:])
            elif self.is_c_file(tok):
                # ? mix of .o and .cpp, can work ?
                if self.is_generated(tok):
                    self.processed.append(tok)
                else:
                    tok = tok.replace("../", "", 1)
                    self.srcs.append(tok)
            elif self.is_obj_file(tok):
                obj_files.append(tok)
            elif self.is_static_lib(tok):
                # not -l, somewhat a hack: see qt/src for ss_strip
                if os.path.isabs(tok):
                    libs.append(tok)
                else:
                    libs.append("${GEN_DIR}/" + tok)
            else:
                print("    short lib: " + tok)  # HSV specific
                short_libs.append(tok)
            i += 1

        if self.options.verbose:
            print("  --file: {}, target: {}".format(self.file, target))
        if target != self.file:
            # library will be built again if it used locally
            print("    ignoring sub-target " + target)
            self.reset()
            return

        for lib in short_libs:
            libs.append(self.find_short_lib(lib_path, lib))
        self.libs = libs
        self.lflags = lflags

        self.flush_commands(f)

        if self.options.verbose:
            print(" objs: {}".format(sorted(obj_files)))

        for file in sorted(obj_files):
            src = self.find_src(self.processed, file)
            if src and src not in self.parent.generated:
                self.generate_derived(f, src)

        kind = TargetKind.shared if shared else TargetKind.binary
        self.add_target(f, kind, obj_files)

    def process_ar(self, f, tokens):
        target = None
        obj_files = []
        i = 1
        while i < len(tokens):
            tok = tokens[i]
            if tok == "-r":
                i += 1
                target = tokens[i]
            elif tok[0] == '-':
                self.lflags.append(tok)
            elif self.is_obj_file(tok):
                obj_files.append(tok)
            else:
                print("ERROR: unknown object: " + tok)
            i += 1

        if self.options.verbose:
            print("  --file: {}, target: {}".format(self.file, target))
        if target != self.file:
            # library will be built again if it used locally
            print("    ignoring sub-target " + target)
            self.reset()
            return

        self.flush_commands(f)

        for file in sorted(obj_files):
            src = self.find_src(self.processed, file)
            if src and src not in self.parent.generated:
                self.generate_derived(f, src)

        if self.lflags:
            print("  ar flags are ignored: " + str(self.lflags))

        self.add_target(f, TargetKind.static, obj_files)

    def add_target(self, f, kind, obj_files):
        # collect sources
        src_sources = []
        gen_sources = []
        objects = []
        for file in sorted(obj_files):
            src = self.find_src(self.srcs, file)
            if src:
                src_sources.append(src)
                continue
            src = self.find_src(self.processed, file)
            if src:
                gen_sources.append(src)
                continue
            print("    cannot find source of {}, using as is".format(file))
            objects.append(file)
        # generate target
        target_name = self.full_target_name(self.name)
        if kind == TargetKind.shared:
            f.write("add_library({} SHARED\n".format(target_name))
        elif kind == TargetKind.static:
            f.write("add_library({} STATIC\n".format(target_name))
        else:
            f.write("add_executable({}\n".format(target_name))
        for s in src_sources:
            f.write("\t${{SRC_DIR}}/{}\n".format(s))
        # add all existing headers unconditionally -- does not help yet to see in project
        for h in glob.glob("*.h") + glob.glob("*.hpp"):
            f.write("\t${{SRC_DIR}}/{}\n".format(h))
        for s in gen_sources:
            f.write("\t${{GEN_DIR}}/{}\n".format(s))
        # add generated headers to force custom commands to run
        for s in self.hdrs:
            f.write("\t${{GEN_DIR}}/{}\n".format(s))
        for o in objects:
            f.write("\t{}\n".format(o))
        f.write(")\n\n")
        if gen_sources:
            self.add_dependencies(f, target_name, gen_sources)
        self.generate_target_properties(f, kind)
        # generate stages
        if self.file not in self.parent.stages:
            print("    {} is not staged".format(self.file))
        else:
            stage = "/home/eugene/cmake/bin/stage3"
            file = "${{CMAKE_CURRENT_BINARY_DIR}}/{}".format(self.file)
            location = self.parent.stages[self.file]
            f.write("add_custom_command(TARGET {} POST_BUILD\n".format(target_name))
            # f.write("\tCOMMAND ${{CMAKE_COMMAND}} -E echo {} {} {}\n".format(stage, self.file, location))
            f.write("\tCOMMAND {} {} {}\n".format(stage, file, location))
            f.write(")\n\n")

    def add_dependencies(self, f, target_name, files):
        f.write("add_dependencies({}".format(target_name))
        for s in files:
            f.write(" {}".format(self.full_target_name(s)))
        f.write(")\n")

    def generate_target_properties(self, f, kind):
        target_name = self.full_target_name(self.name)
        f.write("target_compile_options({} PUBLIC".format(target_name))
        for flag in self.cflags:
            if flag in self.cxxflags:  # common fo C/C++
                f.write(" {}".format(flag))
            else:  # unique for C
                f.write(" $<$<COMPILE_LANGUAGE:C>:{}>".format(flag))
        for flag in self.cxxflags:
            if flag not in self.cflags:  # unique for C++
                f.write(" $<$<COMPILE_LANGUAGE:CXX>:{}>".format(flag))
        f.write(")\n")
        f.write("target_include_directories({} PUBLIC".format(target_name))
        for inc in self.includes:
            if inc == ".":
                inc = "${GEN_DIR}"
            elif inc == "..":
                inc = "${SRC_DIR}"
            elif not os.path.isabs(inc):
                inc = os.path.normpath(os.path.join(self.gen_dir, inc))
            f.write(" {}".format(inc))
        f.write(")\n")
        f.write("target_compile_definitions({} PUBLIC".format(target_name))
        for df in self.defines:
            f.write(" {}".format(df))
        f.write(")\n")
        if kind != TargetKind.static:
            f.write("target_link_libraries({} PUBLIC".format(target_name))
            for lib in self.libs:
                f.write(" {}".format(lib))
            f.write(")\n")
            lflags = " ".join(self.lflags)
            f.write("set_target_properties({} PROPERTIES\n".format(target_name))
            f.write("\tLINKER_LANGUAGE CXX\n")
            f.write("\tLINK_FLAGS \"{}\"\n".format(lflags))
            f.write(")\n\n")
        f.write("set_target_properties({} PROPERTIES\n".format(target_name))
        f.write("\tOUTPUT_NAME \"{}\"\n".format(self.name))
        f.write("\tPREFIX \"\"\n")
        f.write("\tSUFFIX \"{}\"\n".format(os.path.splitext(self.file)[1]))
        f.write(")\n\n")
        for lib in self.libs:
            base = os.path.basename(lib)
            if base in self.customs:
                lib_name = self.full_target_name(base)
                f.write("add_dependencies({} {})\n\n".format(target_name, lib_name))

    def flush_commands(self, f):
        print(" flush: files in commands: {}".format(list(self.commands)))
        for file in self.commands:
            if self.commands[file]:
                if self.options.verbose:
                    print("    flush_commands: target: {}, file: {}, commands: {}".format(self.name, file,
                                                                                          self.commands[file]))
                # print("file: {}, generated: {}".format(file, self.parent.generated))
                if file in self.parent.generated:
                    print("  dup of " + file)
                    continue
                if self.is_static_lib(file):
                    base = os.path.basename(file)
                    self.customs.append(base)
                    f.write("add_custom_target(${{PROJECT_NAME}}_{}\n".format(base))
                    f.write("\tBYPRODUCTS ${{GEN_DIR}}/{}\n".format(file))
                else:
                    if self.is_h_file(file):
                        self.hdrs.append(file)
                    f.write("add_custom_command(\n")
                    f.write("\tOUTPUT ${{GEN_DIR}}/{}\n".format(file))
                for tokens in self.commands[file]:
                    s = self.escape_string(" ".join(tokens))
                    f.write("\tCOMMAND {}\n".format(s))
                f.write("\tDEPENDS {}\n".format(self.full_target_name("mkdir_gen")))
                f.write("\tWORKING_DIRECTORY ${GEN_DIR}\n")
                f.write(")\n")
                if not self.is_static_lib(file):
                    self.add_generated_target(f, file)
                else:
                    f.write("\n")
                self.parent.generated.append(file)
        self.reset()

    # add top level target in case multiple binaries use generated file
    def add_generated_target(self, f, file):
        f.write("add_custom_target({}\n".format(self.full_target_name(file)))
        f.write("\tDEPENDS ${{GEN_DIR}}/{}\n".format(file))
        f.write(")\n\n")

    def generate_derived(self, f, file):
        if self.options.verbose:
            print(" generate_derived: " + file)
        lines = Project.get_build_log(self.build_command, file)
        f.write("add_custom_command(\n")
        f.write("\tOUTPUT ${{GEN_DIR}}/{}\n".format(file))
        for line in lines:
            line = self.escape_string(line)
            f.write("\tCOMMAND {}\n".format(line))
        f.write("\tDEPENDS {}\n".format(self.full_target_name("mkdir_gen")))
        f.write("\tWORKING_DIRECTORY ${GEN_DIR}\n")
        f.write(")\n")
        self.add_generated_target(f, file)
        self.parent.generated.append(file)

    def full_target_name(self, name):
        return self.parent.full_target_name(name)

    @staticmethod
    def find_index(arr, values):
        if isinstance(values, str):
            values = [values]
        for (i, el) in enumerate(arr):
            for value in values:
                if re.match(value + "$", el):
                    return i
        return -1

    @classmethod
    def find_input_output(cls, tokens):
        if tokens[0] == "cp" or tokens[0] == "/bin/cp":
            # simple version
            if tokens[-1] == ".":
                return None, os.path.basename(tokens[-2])
            return None, tokens[-1]
        elif tokens[0] == "mv" or tokens[0] == "/bin/mv":
            # simple version
            in_file = tokens[1]
            out_files = tokens[-1]
        else:
            in_pos = cls.find_index(tokens, "<")
            in_file = None if in_pos == -1 else tokens[in_pos + 1]
            out_pos = cls.find_index(tokens, [">", ">>", ">&", ">>&"])
            out_files = [tokens[out_pos + 1]] if out_pos != -1 else cls.find_output_files(tokens)
        return in_file, out_files

    # guess what output files are for known utilities
    @classmethod
    def find_output_files(cls, tokens):
        try:
            if tokens[0] == "echo" or tokens[0] == "/bin/echo":
                return None
            if cls.is_tool("bison", tokens[0]):
                i = cls.find_index(tokens, "-o")
                if i != -1:
                    return tokens[i + 1]
                i = cls.find_index(tokens, "--output=")
                if i != -1:
                    return tokens[i][9:]
                i = cls.find_index(tokens, [r".*\.y", r".*\.Y"])
                if i != -1:
                    base = os.path.splitext(os.path.basename(tokens[i]))[0]
                    return base + ".tab.C"
                return None
            if cls.is_tool("flex", tokens[0]):
                i = cls.find_index(tokens, "-o")
                if i != -1:
                    return tokens[i + 1]
                i = cls.find_index(tokens, "-P.*")
                if i != -1:
                    return "lex." + tokens[i][2:] + ".c"
                return None
            if cls.is_tool("rpcgen", tokens[0]):
                if "-o" in tokens:
                    i = tokens.index("-o")
                    return tokens[i + 1]
                i = cls.find_index(tokens, r".*\.x")
                if i != -1:
                    xfile = os.path.splitext(tokens[i])[0]
                    return [xfile + ".h", xfile + "_clnt.c", xfile + "_svc.c", xfile + "_xdr.c"]
                return None
            if tokens[0] in ["chmod", "/bin/chmod"]:
                return None
            if tokens[0] in ["touch", "/bin/touch"]:
                return None  # ?
            # HSV specific
            if re.match("/.*/emsMkError", tokens[0]):
                i = tokens.index("-b")
                return tokens[i + 1] + ".c"
            if cls.is_tool("swig", tokens[0]):
                i = cls.find_index(tokens, "-o")
                if i != -1:
                    return tokens[i + 1]
                return None
            assert False, "unknown tool: '{}'".format(tokens)
        except ValueError:
            pass
        return None

    def is_generated(self, filename):
        if self.hsv:
            return filename[0:3] != "../"  # TODO: implement
        return filename in self.generated

    @staticmethod
    def is_tool(tool, name):
        reg_tool = ".*/" + tool.replace("+", "\\+")
        return name == tool or re.match(reg_tool, name)

    # obj name to source name
    @staticmethod
    def find_src(collection, obj_name):
        bare_name = os.path.splitext(obj_name)[0]
        for f in collection:
            if bare_name == os.path.splitext(os.path.basename(f))[0]:
                return f
        return None

    # find full path to a lib without 'lib' prefix
    @staticmethod
    def find_short_lib(lib_path, file):
        for path in lib_path:
            full_name = os.path.join(path, file)
            if os.path.exists(full_name):
                return full_name
        print("cannot find lib {} in path {}".format(file, lib_path))
        return file

    @staticmethod
    def is_h_file(filename):
        ext = os.path.splitext(filename)[1][1:]
        return ext in ["h", "hpp"]

    @staticmethod
    def is_c_file(filename):
        ext = os.path.splitext(filename)[1][1:]
        return ext in ["c"]

    @staticmethod
    def is_cxx_file(filename):
        ext = os.path.splitext(filename)[1][1:]
        return ext in ["C", "cpp", "cxx"]

    @staticmethod
    def is_obj_file(filename):
        ext = os.path.splitext(filename)[1][1:]
        return ext in ["o"]

    @staticmethod
    def is_static_lib(filename):
        ext = os.path.splitext(filename)[1][1:]
        return ext in ["a"]

    # protect cmake's special characters
    @staticmethod
    def escape_string(s):
        out = ""
        for c in s:
            if c in "\"\\#();":
                out += "\\"
            out += c
        return out

    @staticmethod
    def normalize_define(define):
        m = re.match("(.*?)=(.*)", define)
        if m:
            name = m.group(1)
            value = m.group(2)
            if value[0] == '"':
                value = value[1:-1]
            value = value.replace("\\", "")
            define = name + "=" + value
        return define


if __name__ == "__main__":
    # line = "a>>b"
    # tokens = MakeProject.split_shell_command(line, [' '], [">>", ">"])
    # print(tokens)
    main()

# TODO: debug/release build
# TODO: mv in /vobs/rcc/lib/featurefile
