# BaseOS toolchain cache

This document describes the toolchain cache added on
`build/baseos-toolchain-cache`, its retention policy, invalidation rules, and
operating procedures. The measured benchmark results below are from October 2,
2026.

## Scope

Reuse is enabled when `CACHE_TOOLCHAIN=true`, `BASEOS=true`, and `DEVICE=RK3566`.
`CACHE_TOOLCHAIN` defaults to true. Other build profiles keep their existing
build path.

The cache stores `build.aarch64-toolchain.tar.zst`, the existing archive of the
built toolchain, retained build directories, package installation directories,
and build stamps. The archive is approximately 1.1 GB.

The OS image still builds normally. This does not enable general incremental
reuse of completed OS packages.

Three different storage mechanisms participate in the workflow:

| Storage | Purpose | Retention |
| --- | --- | --- |
| GitHub Actions built-toolchain cache | Reuse completed toolchain work across runs | GitHub cache eviction policy; no workflow-defined maximum age |
| Existing release-based `ccache` archives | Reuse individual compiler outputs when compilation runs | Release assets; separate from GitHub Actions cache retention |
| Workflow artifacts | Transfer the toolchain between jobs and retain images/checksums/logs | Artifact retention settings; separate from cache retention |

## Build flow

1. Checkout the source and apply the selected suspend variant.
2. Calculate the current toolchain input fingerprint inside the build container.
3. Attempt to restore the archive using that fingerprint as the cache key.
4. On an exact hit, skip toolchain compilation, compiler-cache maintenance, and
   archive creation. Upload the restored archive for the image job.
5. On a miss, use the existing compiler cache and build the toolchain normally.
   Create and save the completed archive, then upload it for the image job.
6. The image job downloads and extracts the archive, builds BaseOS, verifies
   startup files, and uploads the image and checksum.

Cache-key generation errors fail the job rather than silently trusting an older
archive. A missing or evicted archive takes the normal rebuild path.

## Cache key and invalidation

The key has this form:

```text
toolchain-v1-<runner OS>-<runner architecture>-<SHA-256 input fingerprint>
```

The [key helper](../.github/scripts/toolchain-cache-key.sh) derives dependencies
from the existing `pkgjson` and `genbuildplan.py` tools for
`toolchain alsa-lib llvm:host`. It also follows recursive unpack dependencies.
Package contents are fingerprinted with ROCKNIX's existing `calculate_stamp`
function, including global recipes inherited by project overrides.

| Input group | What participates in the fingerprint |
| --- | --- |
| Build identity | Absolute workspace path, project, device, architecture, BaseOS/base-only/DS-only profile, and suspend setting |
| Container environment | Installed package names and versions, plus local C and C++ compiler binary contents |
| Build infrastructure | Tracked Dockerfile, Makefile, `config/`, `scripts/`, `tools/`, key helper, and toolchain workflow |
| Distribution/device configuration | Active distribution files; project/device options, patch directories, and Linux configuration directories |
| Toolchain dependencies | Selected package recipes and files, native package-stamp inputs, patches, and unpack dependencies |

Changed tracked inputs produce a new key and require a new toolchain build.
Unrelated application-only changes can keep the same key. Broad configuration
inputs intentionally make some changes invalidate more than strictly necessary.

There are no configured `restore-keys`. More importantly, **only
`cache-hit == 'true'` permits compilation to be skipped**; a partial match is
not sufficient to reuse the completed toolchain without rebuilding it.

GitHub caches are scoped by branch/ref. A cache populated on this feature branch
is not available to its parent/default branch merely because the key matches.
Expect a cache-populating build after merging into that branch.

## TTL and storage eviction

The workflow does **not** implement a fixed time-to-live or a maximum cache age.
A regularly accessed entry can remain available for much longer than a week.

GitHub removes cache entries that have not been accessed in over seven days.
Storage pressure can also evict entries, starting with the least recently
accessed. The default repository cache-storage limit is 10 GB; repository
settings can change it. See GitHub's
[cache retention and eviction policy](https://docs.github.com/en/actions/reference/workflows-and-actions/dependency-caching#usage-limits-and-eviction-policy).

Eviction affects speed: the next matching run rebuilds and repopulates the
cache. Retention controls storage; the input fingerprint controls whether reuse
is compatible with the current build.

## Stale-cache risks and limits

The checks cover recorded source/configuration changes and compiler/package
version changes. For example, updating the GCC recipe or a toolchain dependency
patch invalidates the archive, while changing a launcher asset need not.

They do not prove that every possible external input is immutable:

- An unpinned remote source could change behind the same URL or branch without
  changing a recipe. Prefer pinned commits/versions and source checksums.
- The key fingerprints compiler binaries and installed package versions, not
  the entire container image digest. Custom container file changes with the
  same package versions may be missed.
- Custom environment overrides or files outside the fingerprinted paths need
  explicit consideration before they are introduced.

A short TTL would not reliably address these gaps. Track or pin the changed
input, or bypass reuse while investigating. Full OS-package reuse needs its own
invalidation review and is not part of this setup.

## Inspect, bypass, or replace the cache

The toolchain job summary reports `Built toolchain cache hit` and the cache key.
An exact hit also skips the toolchain `Build` step.

List the built-toolchain entries:

```sh
gh cache list --repo philbudiman/rocknix-rgds-plus \
  --key toolchain-v1- --ref refs/heads/build/baseos-toolchain-cache
```

To bypass built-toolchain reuse for one benchmark:

```sh
gh workflow run build-nightly.yml --repo philbudiman/rocknix-rgds-plus \
  --ref build/baseos-toolchain-cache \
  -f BASEOS=true -f BENCHMARK=true -f CACHE_TOOLCHAIN=false
```

This still permits the existing compiler-object cache. It is a rebuild of the
toolchain packages, not a completely cache-free build, and does not replace an
existing built-toolchain cache entry.

To replace an entry, delete its specific ID from the list above, then run with
`CACHE_TOOLCHAIN=true` to rebuild and save it:

```sh
gh cache delete <cache-id> --repo philbudiman/rocknix-rgds-plus
```

Alternatively, change the key namespace when deliberately invalidating every
entry. GitHub cache entries are immutable: an existing exact key is not
refreshed in place. See
[GitHub's cache-key behavior](https://docs.github.com/en/actions/reference/workflows-and-actions/dependency-caching#cache-action-usage).

## Benchmark results and validation

Both successful runs used commit `488da6f2d7149c82c0a444e02b2310d03c05b531`
and the same benchmark inputs. The first populated the built-toolchain cache;
both runs could use the existing compiler-object caches.

| Measurement | [Cache population run](https://github.com/philbudiman/rocknix-rgds-plus/actions/runs/37045119027) | [Warm run](https://github.com/philbudiman/rocknix-rgds-plus/actions/runs/37058235688) |
| --- | --- | --- |
| Total elapsed time | 81m 08s | 46m 57s |
| Toolchain job | 42m 14s | 4m 41s |
| Image compilation | 33m 57s | 35m 03s |

The warm run restored the archive in seven seconds and skipped toolchain
compilation. Total elapsed time fell by **34m 11s (42%)**. Both runs passed the
BaseOS startup-file checks. These are two observations, not a guarantee of every
run's duration; image compilation, cleanup, and runner performance vary.

Benchmark mode skips release publishing, Docker pushes, and updates to the
release-based compiler caches. It retains image/checksum artifacts and build
logs. See the [benchmark procedure](../rocknix/toolchain-cache.md) for sequential
baseline, cache-population, and warm runs, plus local regression checks.

Hardware boot validation of the warm image remains outstanding. Verify the
image checksum and boot it on the RG DS Plus before merging. Runner cleanup and
early host compiler caching have not been changed by this optimization.

## Implementation references

- [Toolchain workflow](../.github/workflows/build-aarch64-toolchain.yml)
- [Image workflow](../.github/workflows/build-aarch64.yml)
- [Cache-key helper](../.github/scripts/toolchain-cache-key.sh)
- [Cache regression checks](../.github/scripts/test-toolchain-cache.py)
