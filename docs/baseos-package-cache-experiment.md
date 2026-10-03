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
- Population succeeded: toolchain build/archive 39m34s, image build 35m26s,
  package archive creation 1m07s, cache upload 9s. Package archive: 1.6 GiB.
- Exact package key: `baseos-packages-v1-Linux-X64-3b487567a02c5729d914f272fe9874d8131873e7501e6ef19c83e906c627c262`.
- Matched pair uses commit `260edb5694c54f7f3a761b7f6efeeab69b41c9c8`
  (only documentation differs from population):
  - No-package-reuse baseline: [37102231938](https://github.com/philbudiman/rocknix-rgds-plus/actions/runs/37102231938).
  - Warm package reuse: [37102237403](https://github.com/philbudiman/rocknix-rgds-plus/actions/runs/37102237403).
- Both dispatched at 06:11 UTC on October 3. Baseline is still running.
- Warm run succeeded in **4m48s** (06:11:32 to 06:16:20 UTC): cache restore
  15s, extraction 38s, fresh image build 2m19s, key calculation 41s, checkout
  23s. Cleanup, toolchain compilation, compiler-cache download and archive
  creation/upload were skipped. File comparisons, build identity and SHA256
  verification passed.
- Changed-launcher validation: [37102810042](https://github.com/philbudiman/rocknix-rgds-plus/actions/runs/37102810042),
  commit `edeb142ea90ae32e7a9a74b30c69641704f44bba`, dispatched 06:21:58 UTC.
  It adds a harmless launcher comment. **Succeeded in 4m24s**, restoring the
  identical package key. Fresh image build took 2m02s; restore 15s, extraction
  33s. Installed-file comparisons, current build identity and checksum passed.
- Independently downloaded the changed-launcher `.img.gz`, verified SHA256
  `a823e003775acec861f5fe561729d4629819cdc06d69ace70fd43b26da608ad2`,
  extracted the GPT boot partition and its SquashFS SYSTEM, and compared the
  actual image's launcher, Sway config and logind power config to source.
  The launcher contains the new comment and `/etc/os-release` has the changed
  source commit, not the cache population commit.
- Verified artifact and extracted files:
  `/private/tmp/rgds-package-benchmark-results/changed-image/`.
- The matched baseline is still compiling. Await it before reporting the final
  savings/recommendation; no further warm runs are necessary unless a concern
  appears. Local key invalidation checks and workflow validation passed again.
- Raw population logs: `/private/tmp/rgds-package-population.log`; use
  `gh api repos/philbudiman/rocknix-rgds-plus/actions/jobs/JOB_ID/logs` for logs
  (`gh run view --log` returned an empty file).
- Local invalidation checks and workflow validation passed before dispatch.
