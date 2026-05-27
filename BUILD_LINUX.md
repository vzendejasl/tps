# TPS Build Notes For This Linux Machine

This note records the steps taken to build `tps` on this Ubuntu 22.04 LTS machine using an existing MFEM and HDF5 setup, along with newly built GSL and GRVY dependencies.

## Constraints

- Use an existing MFEM build located in the parent directory.
- Build missing dependencies (GSL, GRVY) from source into a local `tpls` directory.
- Build TPS as a static library to avoid PIC (Position Independent Code) issues with the pre-existing MFEM build.

## Paths Used

- MFEM directory: `/home/vzendejasl/Documents/mfem_build/mfem`
- HDF5 directory: `/home/vzendejasl/Documents/mfem_build/hdf5-mpich-install`
- TPS directory: `/home/vzendejasl/Documents/mfem_build/tps`
- TPLS directory (GSL/GRVY): `/home/vzendejasl/Documents/mfem_build/tpls`
- GSL install prefix: `/home/vzendejasl/Documents/mfem_build/tpls/gsl-install`
- GRVY install prefix: `/home/vzendejasl/Documents/mfem_build/tpls/grvy-install`

## Dependencies

### System Packages (Ubuntu 22.04)

```bash
sudo apt update
sudo apt install autoconf automake libtool pkg-config g++ libboost-all-dev
```

Note: MPI (MPICH 4.2.3) was already installed and available in `/opt/mpich/bin`.

### GSL (GNU Scientific Library)

Built from source into a local prefix:

```bash
cd /home/vzendejasl/Documents/mfem_build/tpls
wget https://ftp.gnu.org/gnu/gsl/gsl-2.7.tar.gz
tar -xzf gsl-2.7.tar.gz
cd gsl-2.7
./configure --prefix=/home/vzendejasl/Documents/mfem_build/tpls/gsl-install
make -j8
make install
```

### GRVY

Built from source with a patch for C++11/17 compatibility.

#### Patch for `src/grvy_int.h`
The comparator signatures were updated to use `const` and pass by reference to avoid compilation errors on newer `g++` versions:

```bash
sed -i 's/operator()(const std::vector <double> v1, const std::vector <double> v2 )/operator()(const std::vector <double> \&v1, const std::vector <double> \&v2 ) const/g' src/grvy_int.h
```

#### Build GRVY
```bash
cd /home/vzendejasl/Documents/mfem_build/tpls/grvy-0.37.0
./configure --prefix=/home/vzendejasl/Documents/mfem_build/tpls/grvy-install \
  --enable-boost-headers-only \
  --with-hdf5=/home/vzendejasl/Documents/mfem_build/hdf5-mpich-install \
  CPPFLAGS='-I/usr/include' \
  LDFLAGS='-L/home/vzendejasl/Documents/mfem_build/hdf5-mpich-install/lib'
make -j8
make install
```

## MFEM Preparation

The existing MFEM build was in-source. TPS expects a standard structure (or at least certain paths). I created symlinks to satisfy the TPS build system:

```bash
cd /home/vzendejasl/Documents/mfem_build/mfem
mkdir -p include/mfem lib share/mfem

# Link config
ln -sf $(pwd)/config/config.mk share/mfem/config.mk
ln -sf $(pwd)/config include/mfem/config

# Link headers and library
ln -sf $(pwd)/mfem.hpp include/mfem/mfem.hpp
ln -sf $(pwd)/libmfem.a lib/libmfem.a

# Link other source directories into include/mfem
for d in general linalg mesh fem data miniapps tests; do 
  ln -sf $(pwd)/$d include/mfem/$d
done
```

## TPS Source Patches

### 1. `m4/snarf_mfem.py`
Updated to handle `$(MFEM_DIR)` variable which is common in MFEM config files but wasn't being expanded by the script.

### 2. `utils/compute_rhs.cpp`
Fixed a type conversion error where a `DataCollection*` was being assigned to a `ParaViewDataCollection*`.

## TPS Build

### Bootstrap
```bash
cd /home/vzendejasl/Documents/mfem_build/tps
./bootstrap
```

### Configure
Built as a static library to be compatible with the existing MFEM build (not built with `-fPIC`).

```bash
mkdir -p build && cd build
export PATH=/home/vzendejasl/Documents/mfem_build/tpls/gsl-install/bin:$PATH

../configure --disable-shared --enable-static \
  MFEM_DIR=/home/vzendejasl/Documents/mfem_build/mfem \
  GRVY_DIR=/home/vzendejasl/Documents/mfem_build/tpls/grvy-install \
  HDF5_DIR=/home/vzendejasl/Documents/mfem_build/hdf5-mpich-install \
  GSL_DIR=/home/vzendejasl/Documents/mfem_build/tpls/gsl-install \
  CXXFLAGS='-O3 -std=c++17' \
  LDFLAGS='-L/home/vzendejasl/Documents/mfem_build/tpls/grvy-install/lib -Wl,-rpath,/home/vzendejasl/Documents/mfem_build/tpls/grvy-install/lib -L/home/vzendejasl/Documents/mfem_build/hdf5-mpich-install/lib -Wl,-rpath,/home/vzendejasl/Documents/mfem_build/hdf5-mpich-install/lib -L/home/vzendejasl/Documents/mfem_build/tpls/gsl-install/lib -Wl,-rpath,/home/vzendejasl/Documents/mfem_build/tpls/gsl-install/lib'
```

### Build
```bash
make -j8
```

## Verification

Run a basic Taylor-Green Vortex example:

```bash
cd /home/vzendejasl/Documents/mfem_build/tps
./build/src/tps --runFile examples/input.compressible_tgv_m05.ini
```
