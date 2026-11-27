# Infrastructure 2027 — Preview 4

FrankenPHP 1.14.0 installed as an independent versioned runtime, not a default PHP engine.

- Official GitHub release: https://github.com/php/frankenphp/releases/tag/v1.14.0
- Verified SHA256: 2069f4c6c799707cd5133ea10c46ccd0224aa482eeb6254f5dbf3bbd7dc7f02c
- Runtime reported PHP 8.6.0 and Caddy 2.11.9. This is the observed binary version, not a compatibility recommendation.
- Private-network, non-root systemd HTTP smoke test passed with a synthetic PHP page. cgroup memory snapshot 45,518,848 bytes (~43.4 MiB) with the simple fixture, not a workload benchmark.
- Binary installed root-owned at /opt/hoosh-runtimes/frankenphp/1.14.0/frankenphp. No daemon, public port, production site migration or default PHP changes.
- The panel status detects the presence of the root-owned executable with non-writable parent paths; this is not a fresh runtime or integrity attestation. Provisioning still pending.
- Docker Hub returned HTTP 403 for official FrankenPHP/Valkey images. Valkey 8.1.12 has not been installed. Redis remains untouched; no third-party mirror used.
- HWE 6.8 remains installed but not booted; no reboot was performed. Disk warning remains. Keep recovery kernels until new kernel boot is verified.
- Existing Apache hybrid, active LSCache, provisioning transaction, compatibility and security gates remain open. This is a development release, not final production certification.
