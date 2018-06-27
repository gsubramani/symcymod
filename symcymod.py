from sympy.utilities.codegen import codegen,CCodeGen,make_routine
from sympy.utilities.autowrap import CythonCodeWrapper
import sympy as sym
import os
from subprocess import STDOUT, CalledProcessError, check_output
import sys

class CodeWrapError(Exception):
    pass

class create_setup:
    setup_template = """\
try:
    from setuptools import setup
    from setuptools import Extension
except ImportError:
    from distutils.core import setup
    from distutils.extension import Extension
from Cython.Build import cythonize
cy_opts = {cythonize_options}
{np_import}
ext_mods = [Extension(
    {ext_args},
    include_dirs={include_dirs},
    library_dirs={library_dirs},
    libraries={libraries},
    extra_compile_args={extra_compile_args},
    extra_link_args={extra_link_args}
)]
setup(ext_modules=cythonize(ext_mods, **cy_opts))
    """

    pyx_imports = (
        "import numpy as np\n"
        "cimport numpy as np\n\n")

    pyx_header = (
        "cdef extern from '{header_file}.h':\n"
        "    {prototype}\n\n")

    pyx_func = (
        "def {name}_c({arg_string}):\n"
        "\n"
        "{declarations}"
        "{body}")

    std_compile_flag = '-std=c99'


    def __init__(self,pyxfilename,codefilename,build_dir,module_name,**kwargs):
        self._include_dirs = kwargs.pop('include_dirs', [])
        self._library_dirs = kwargs.pop('library_dirs', [])
        self._libraries = kwargs.pop('libraries', [])
        self._extra_compile_args = kwargs.pop('extra_compile_args', [])
        self._extra_compile_args.append(self.std_compile_flag)
        self._extra_link_args = kwargs.pop('extra_link_args', [])
        self._cythonize_options = kwargs.pop('cythonize_options', {})
        self._need_numpy = False
        self.module_name = module_name

        ext_args = [repr(self.module_name), repr([pyxfilename, codefilename])]
        if self._need_numpy:
            np_import = 'import numpy as np\n'
            self._include_dirs.append('np.get_include()')
        else:
            np_import = ''

        with open(os.path.join(build_dir, 'setup.py'), 'w') as f:
            includes = str(self._include_dirs).replace("'np.get_include()'",
                                                       'np.get_include()')
            f.write(self.setup_template.format(
                ext_args=", ".join(ext_args),
                np_import=np_import,
                include_dirs=includes,
                library_dirs=self._library_dirs,
                libraries=self._libraries,
                extra_compile_args=self._extra_compile_args,
                extra_link_args=self._extra_link_args,
                cythonize_options=self._cythonize_options
            ))



def create_module(module_name,expression_name_tuples,directory):
    """Generates a cython module that can be imported."""
    routines = [make_routine(name,[expression],args) for name,expression,args in expression_name_tuples]

    if not os.path.exists(directory):
        os.makedirs(directory)



    cg = CCodeGen()

    [(cf, cs), (hf, hs)] = cg.write(routines,module_name+'_code')

    with open(directory + '/' + cf, "w") as text_file:
        text_file.write(cs)

    with open(directory + '/' + hf, "w") as text_file:
        text_file.write(hs)


    ccw = CythonCodeWrapper(cg)

    with open(directory + '/' + module_name + '.pyx', "w") as text_file:
        ccw.dump_pyx(routines,text_file,module_name + '_code')

    create_setup(module_name + '.pyx',module_name + '_code.c',directory,module_name)

    open(directory+'/__init__.py', 'a').close()

    oldwork = os.getcwd()
    os.chdir(directory)
    workdir = os.getcwd()
    command = [sys.executable, "setup.py", "build_ext", "--inplace"]
    try:
        sys.path.append(workdir)
        retoutput = check_output(command, stderr=STDOUT)
    except CalledProcessError as e:
        raise CodeWrapError(
            "Error while executing command: %s. Command output is:\n%s" % (
                " ".join(command), e.output.decode()))

    finally:
        sys.path.remove(workdir)
        os.chdir(oldwork)


if __name__ == "__main__":
    a,b,c,d = sym.symbols('a b c d')

    fun = a*b*c*d
    anotherfun = a*b*c + d


    expression_name_tuples = [('fun',fun,[a,c,d,b]),('anotherfun',anotherfun,[a,b,d,c])]

    # dump_pyx

    directory = "./temp/"
    module_name = 'temp'

    create_module(module_name,expression_name_tuples,directory)

"""
Use generated module this way!
>>> from temp.temp import fun_c, anotherfun_c
>>> print fun_c(1,2,3,4)
>>> # print anotherfun_c(1,2,3,4)

"""