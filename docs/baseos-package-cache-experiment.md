# BaseOS compiled-package cache experiment

This experiment is isolated on `build/baseos-package-cache`; it is not enabled
on `next`. It reuses compiled package staging directories, build stamps, and the
populated toolchain/sysroot. The standard image builder still assembles a fresh
image. `scripts/clean baseos` always discards/rebuilds the launcher/config leaf
package before image assembly. Checks compare the installed launcher and config
to the current checkout, verify the image's commit identity and checksum, and
check the expected startup files.

The key hashes the complete image dependency plan using the existing toolchain
key helper. Only BaseOS `scripts/` and `config/` files are omitted; its recipe,
service files and all other dependencies remain fingerprinted. There are no
fallback restore keys. Dependency edits discard the entire compiled-package
layer, rather than attempting selective invalidation of dependents. This is a
conservative first experiment, not a general incremental build system.

The benchmark uses a single build job. Disk cleanup runs only on package-cache
misses. It does not publish images, Docker containers, or release compiler
caches. Its image and logs are downloadable Actions artifacts. Hardware boot
validation is not performed automatically.

## Procedure and decision

1. Populate the cache with a successful build and verify archive size.
2. Run the same commit with `CACHE_PACKAGES=false` for a matched baseline using
   the populated toolchain cache. Run with `CACHE_PACKAGES=true` for warm timing.
3. Commit a harmless launcher/config comment on the experiment branch and run
   again. Require an exact cache hit and comparison checks proving the new file
   reaches the newly assembled image with the current build identity.
4. Run the local invalidation checks for unchanged inputs, runtime edits,
   dependency recipe changes, application recipe changes, nested unpack
   dependencies, compiler/environment inputs, and malformed graphs.
5. Compare wall-clock time, setup, restoration, image build, compression/cache
   upload, and archive size. Report a go/no-go recommendation. A sub-10-minute
   warm build is the stretch target, not a preset conclusion. Do not merge this
   experiment into `next` without a separate user instruction.

Run the local checks:

```sh
python3 .github/scripts/test-toolchain-cache.py
```

Dispatch the isolated experiment (switch `CACHE_PACKAGES` for the baseline):

```sh
gh workflow run build-nightly.yml \
  --repo philbudiman/rocknix-rgds-plus --ref build/baseos-package-cache \
  -f BASEOS=true -f BENCHMARK=true -f PACKAGE_CACHE_EXPERIMENT=true \
  -f CACHE_PACKAGES=true
```

## State

- Worktree: `/private/tmp/rgds-package-cache`.
- Initial implementation: `2bdd135bd2f9787f32bc8f6fccc5b54769872b1f`.
- Cache population run: [37097762068](https://github.com/philbudiman/rocknix-rgds-plus/actions/runs/37097762068).
- Awaiting population result. Fix genuine failures on this branch and retry.
- Baseline, warm run, and changed-launcher run have not been dispatched yet.
- Local invalidation checks and workflow validation passed before dispatch.
