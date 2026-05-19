# TPS Build Notes For This Mac

This note records what it took to build `tps` on this macOS machine without touching any conda HDF5 environments.

## Constraints

- Keep all added dependencies outside conda.
- Use Homebrew for common system libraries.
- Use a separate local MFEM install with `gslib` enabled, because TPS tests depend on it.
- Run TPS tests serially on this machine, because the Automake tests share output filenames and race under parallel `make check`.

## Paths Used

- MFEM source: `/Users/victorzendejaslopez/Documents/MFEM/mfem`
- TPS source: `/Users/victorzendejaslopez/Documents/MFEM/tps`
- Local workspace: `/Users/victorzendejaslopez/Documents/MFEM/local`
- GRVY install prefix: `/Users/victorzendejaslopez/Documents/MFEM/local/grvy-install`
- MFEM install prefix with `gslib`: `/Users/victorzendejaslopez/Documents/MFEM/local/mfem-install-gslib`
- TPS build dir: `/Users/victorzendejaslopez/Documents/MFEM/tps/build-macos`

## Homebrew Dependencies

Installed with Homebrew:

```bash
brew install autoconf automake libtool boost hdf5 gsl git-lfs
```

Notes:

- `libtool` is needed for `glibtoolize` on macOS.
- `git-lfs` is needed because TPS test meshes and reference solutions are stored in LFS.

## Git LFS

Inside the TPS checkout:

```bash
git lfs install --local
git lfs pull
```

This converts test assets from LFS pointer files into real meshes and `.h5` reference files.

## GRVY Build

TPS needs GRVY. I built a local GRVY install from source into `local/grvy-install`.

### GRVY source patches used on this Mac

`local/src/grvy-0.37.0/src/grvy_int.h`

- Updated timer comparator signatures to use `const std::vector<double> &` and `const` member functions.

`local/src/grvy-0.37.0/src/grvy_timer.cpp`

- Added `static_cast<hsize_t>(...)` for HDF5 dimension values.

`local/src/grvy-0.37.0/src/grvy_hdf5.cpp`

- Updated `H5Oget_info_by_name(...)` to the newer HDF5 signature:

```cpp
H5Oget_info_by_name(loc_id, name, &infobuf, H5O_INFO_BASIC, H5P_DEFAULT);
```

### GRVY configure/build

```bash
cd /Users/victorzendejaslopez/Documents/MFEM/local/src/grvy-0.37.0

./configure \
  --prefix=/Users/victorzendejaslopez/Documents/MFEM/local/grvy-install \
  --enable-boost-headers-only \
  CPPFLAGS='-I/usr/local/opt/boost/include -I/usr/local/opt/hdf5/include' \
  CXXFLAGS='-std=c++14' \
  LDFLAGS='-L/usr/local/opt/boost/lib -Wl,-rpath,/usr/local/opt/boost/lib -L/usr/local/opt/hdf5/lib -Wl,-rpath,/usr/local/opt/hdf5/lib'

make -j8
make install
```

## MFEM Rebuild With `gslib`

The original MFEM build on this machine had:

```make
MFEM_USE_GSLIB = NO
```

TPS test coverage is better with `gslib` enabled, so I created a separate out-of-tree MFEM build instead of overwriting the original one.

### Confirm local `gslib`

This machine already had a local `gslib` checkout at:

`/Users/victorzendejaslopez/Documents/MFEM/gslib`

It already had a usable static library in:

`/Users/victorzendejaslopez/Documents/MFEM/gslib/build/lib/libgs.a`

### Configure MFEM out of tree

```bash
cd /Users/victorzendejaslopez/Documents/MFEM/mfem

make config BUILD_DIR=build-gslib \
  MFEM_USE_MPI=YES \
  MFEM_USE_METIS=YES \
  MFEM_USE_METIS_5=YES \
  MFEM_USE_GSLIB=YES
```

### Build and install MFEM

```bash
cd /Users/victorzendejaslopez/Documents/MFEM/mfem/build-gslib

make -j8
make install PREFIX=/Users/victorzendejaslopez/Documents/MFEM/local/mfem-install-gslib -j8
```

After install, the MFEM config file should report:

```make
MFEM_USE_GSLIB = YES
```

in:

`/Users/victorzendejaslopez/Documents/MFEM/local/mfem-install-gslib/share/mfem/config.mk`

## TPS Source Change For macOS Test Execution

On this machine, Automake was trying to execute Bats `.test` files directly, and several were being interpreted by plain shell instead of Bats.

I changed:

[`test/Makefile.am`](/Users/victorzendejaslopez/Documents/MFEM/tps/test/Makefile.am)

to make Automake run `.test` files through `./bats` explicitly:

```make
TEST_EXTENSIONS = .test
TEST_LOG_COMPILER = ./bats
```

Then I regenerated autotools files with:

```bash
cd /Users/victorzendejaslopez/Documents/MFEM/tps
PATH="/usr/local/opt/libtool/libexec/gnubin:/usr/local/bin:$PATH" ./bootstrap
```

## Hydro Test Adjustments On This Mac

After the build succeeded, the remaining hydro regressions on this Mac were not all the same type of problem.

- The base `cyl3d`, `cyl3d.dtconst`, and `cyl3d.mflow` reference files in TPS did not match the local `MFEM 4.9.1` build.
- Two `cyl3d` restart tests used GNU `sed -i`, which fails on BSD `sed` on macOS.
- Some serialized MPI restart tests were hitting HDF5 file locking when multiple ranks wrote one restart file.

Source changes made for that:

- [`test/cyl3d.test`](/Users/victorzendejaslopez/Documents/MFEM/tps/test/cyl3d.test)
  - Added MFEM-version-based hydro reference selection for `4.9+`
  - Replaced GNU-only `sed -i` usage with a portable temp-file rewrite
  - Wrapped serialized MPI restart checks with `HDF5_USE_FILE_LOCKING=FALSE`
- [`test/cyl3d.dtconst.test`](/Users/victorzendejaslopez/Documents/MFEM/tps/test/cyl3d.dtconst.test)
  - Added MFEM-version-based hydro reference selection for `4.9+`
- [`test/cyl3d.mflow.test`](/Users/victorzendejaslopez/Documents/MFEM/tps/test/cyl3d.mflow.test)
  - Added MFEM-version-based hydro reference selection for `4.9+`
- [`test/cyl3d.python.test`](/Users/victorzendejaslopez/Documents/MFEM/tps/test/cyl3d.python.test)
  - Added MFEM-version-based hydro reference selection for `4.9+`
- [`test/cyl3d.python.splitcomm.test`](/Users/victorzendejaslopez/Documents/MFEM/tps/test/cyl3d.python.splitcomm.test)
  - Added MFEM-version-based hydro reference selection for `4.9+`
- [`test/soln_differ`](/Users/victorzendejaslopez/Documents/MFEM/tps/test/soln_differ)
  - Fixed the shell check so it does not warn when species comparison is not requested

New hydro reference files created for this Mac:

- `test/ref_solns/cyl3d_coarse.4iters.v49.h5`
- `test/ref_solns/cyl3d_coarse.8iters.varp.v49.h5`
- `test/ref_solns/cyl3d.dtconst.cpu.v49.h5`
- `test/ref_solns/cyl3d.dtconst.heatSource.cpu.v49.h5`
- `test/ref_solns/cyl3d.mflow.2iters.v49.h5`
- `test/ref_solns/cyl3d.mflow.2iters.bulkVisc.dtconst.v49.h5`

## TPS Configure

```bash
cd /Users/victorzendejaslopez/Documents/MFEM/tps
mkdir -p build-macos
cd build-macos

PATH="/usr/local/opt/libtool/libexec/gnubin:/usr/local/bin:$PATH" \
MFEM_DIR=/Users/victorzendejaslopez/Documents/MFEM/local/mfem-install-gslib \
GRVY_DIR=/Users/victorzendejaslopez/Documents/MFEM/local/grvy-install \
HDF5_DIR=/usr/local/opt/hdf5 \
GSL_DIR=/usr/local/opt/gsl \
HDF5_CFLAGS='-I/usr/local/opt/hdf5/include' \
HDF5_LIBS='-L/usr/local/opt/hdf5/lib -lhdf5_hl -lhdf5' \
../configure \
  CXXFLAGS='-g -O2 -std=c++17' \
  LDFLAGS='-L/Users/victorzendejaslopez/Documents/MFEM/local/grvy-install/lib -Wl,-rpath,/Users/victorzendejaslopez/Documents/MFEM/local/grvy-install/lib -L/usr/local/opt/hdf5/lib -Wl,-rpath,/usr/local/opt/hdf5/lib -L/usr/local/opt/gsl/lib -Wl,-rpath,/usr/local/opt/gsl/lib'
```

Expected configure result:

- `GRVY` detected
- `MFEM` detected
- `GSLIB is available in mfem... yes`
- `HDF5` include/lib flags populated

## TPS Build

```bash
cd /Users/victorzendejaslopez/Documents/MFEM/tps/build-macos
PATH="/usr/local/opt/libtool/libexec/gnubin:/usr/local/bin:$PATH" make -j8
```

## Tests

Use:

```bash
cd /Users/victorzendejaslopez/Documents/MFEM/tps/build-macos
PATH="/usr/local/opt/libtool/libexec/gnubin:/usr/local/bin:$PATH" make -j1 AM_COLOR_TESTS=yes check
```

Important:

- Do not use parallel `make check` here.
- Several TPS tests write shared filenames like `restart_output.sol.h5`, so parallel test execution causes false failures.
- For serialized MPI hydro restart tests on this Mac, use `HDF5_USE_FILE_LOCKING=FALSE` if multiple ranks need to write one HDF5 restart file.

Example:

```bash
cd /Users/victorzendejaslopez/Documents/MFEM/tps/build-macos/test
export HDF5_USE_FILE_LOCKING=FALSE
mpirun -n 2 ../src/tps --runFile inputs/input.4iters.cyl.ini.part
```

Hydro-only regression status after the above changes:

- `cyl3d.test`: pass
- `cyl3d.mflow.test`: pass
- `cyl3d.dtconst.test`: pass

## What I Did Not Touch

- I did not modify any conda environment.
- I did not install HDF5 into conda.
- I kept the original MFEM build intact and installed the `gslib`-enabled MFEM into a separate local prefix.
