# BaseOS build speed comparison

See [the cache setup document](../docs/baseos-toolchain-cache.md) for retention,
invalidation rules, operating procedures, and measured benchmark results.

The built-toolchain cache applies only to RK3566 BaseOS. It reuses the existing
compressed archive on an exact input match; other profiles keep their existing
build path. Compiler versions/binaries, installed container package versions,
build configuration, dependency recipes/patches (including unpack dependencies),
and the absolute workspace path participate in the key. There is no fallback to
an older toolchain. Application-only changes can reuse the archive.

Benchmark mode uses the existing build container and skips Docker pushes,
release publishing, and updates to the release-based compiler caches. Image
artifacts, startup-file checks, and successful build logs remain available.

Run these **sequentially on the same branch commit**, waiting for each to finish:

1. Baseline, with built-toolchain reuse disabled:

   ```sh
   gh workflow run build-nightly.yml --ref build/baseos-toolchain-cache \
     -f BASEOS=true -f BENCHMARK=true -f CACHE_TOOLCHAIN=false
   ```

2. Populate the toolchain cache:

   ```sh
   gh workflow run build-nightly.yml --ref build/baseos-toolchain-cache \
     -f BASEOS=true -f BENCHMARK=true -f CACHE_TOOLCHAIN=true
   ```

3. Repeat step 2 for the warm measurement. Confirm `Built toolchain cache hit:
   true` in the toolchain job summary and that compilation was skipped. If the
   cache already existed in step 2, that run is also a warm measurement.

Compare total elapsed time and the toolchain/image Build steps. The observed
pre-change toolchain Build took approximately 39 minutes; a warm run should
replace it with cache restoration and the existing artifact upload. Image
compilation should remain similar. Repeat a warm run if runner variability is
large. Keep the existing container tag and release compiler-cache assets stable
between measurements; container version changes cause a toolchain cache miss.

Download the image/checksum artifacts, check the checksum, and boot the warm
image on the RG DS Plus before merging. Build timestamps can differ, so binary
identity is not the acceptance criterion. Keep both baseline and warm run links.

Local checks:

```sh
python3 .github/scripts/test-toolchain-cache.py
actionlint -shellcheck='' .github/workflows/build-nightly.yml \
  .github/workflows/build-device.yml .github/workflows/build-aarch64-toolchain.yml \
  .github/workflows/build-aarch64.yml .github/workflows/build-docker-image.yml
```

Runner cleanup and early host compiler caching are deferred so the first
comparison measures toolchain reuse alone.
