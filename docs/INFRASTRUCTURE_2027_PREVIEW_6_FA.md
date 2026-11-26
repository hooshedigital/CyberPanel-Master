# Infrastructure 2027 — Preview 6

Valkey 8.1.12 standalone runtime installed, 2026-11-26.

- GitHub Actions run 45855263310 completed successfully (source build, isolated socket smoke, package, upload). Artifact 15135681771 SHA256 3599d89eb08fb57d9b55ba01ec0d5ed7c096d1373df859a033ab72358a14d764. Official source commit 38316e6c481cc6d265ab52482223c68f63f0ac30.
- ZIP digest, nested archive digest, allowed regular-file members, source commit and binary checksums checked before execution. Server SHA256 9d25c8343fcc1b890802857a54c8f1bf4f2b32a549bea0a4647890adde29699a; CLI SHA256 df1cd6e6c819aa3b3e8b87f702ed58d3134f9c7b7df7b95b97a98fe8abee0dfc.
- Runtime smoke with nonroot user, private network, no TCP listener, Unix socket 0700, Redis data directory inaccessible, 32MiB maxmemory, 96MiB cgroup cap: PING/SET/GET successful, used_memory 972624 bytes, RSS 9617408 bytes. Not production benchmark.
- Installed under /opt/hoosh-runtimes/valkey/8.1.12; no persistent daemon or data migration. Redis production remains unchanged and active. To uninstall unused candidate remove only versioned directory after dependency check.
- GitHub safety, UI/WHMCS and storefront contract workflows for commit 42ac40825af9ebabfbd2a53dcea9075a2d757fda completed successfully. This does not prove production provisioning safety.
- Inventory adds versioned runtime versions and available zswap debug counters. Missing counters are null. Run as ordinary user.
- Post-install RAM available 1961MiB, Swap free 1487MiB, disk about 11GiB free; main services active. HWE 6.8 is still not booted. No reboot, zswap allocator or compressor changes. Independent provider console still unverified. No changes to entitlement, site creation or production cache.
- Remaining: select real target workload, service-specific Valkey configuration/migration/rollback; operational web-engine provisioning; planned kernel activation and memory tuning; full integration and performance tests.
