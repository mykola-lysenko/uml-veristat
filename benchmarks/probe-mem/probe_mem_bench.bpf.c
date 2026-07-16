// SPDX-License-Identifier: GPL-2.0
/* Guard-dense probe-memory microbenchmark.
 *
 * Every load below goes through a bpf_rdonly_cast()'d pointer, which the
 * verifier types PTR_TO_BTF_ID | MEM_RDONLY | PTR_UNTRUSTED — so the x86
 * JIT emits the inline probe-memory guard in front of each one. The casts
 * target our own array-map value, so every access lands in valid mapped
 * kernel memory: the guards always pass and no load ever takes the
 * exception-fixup path. What the loop measures is therefore the guard
 * arithmetic itself, which is exactly what the probe-mem guard fold
 * (patch 0009c / docs/jit-probe-mem-guard-optimizations.md opt #1)
 * shrinks.
 *
 * struct sysinfo is used as the cast target purely because its leading
 * fields are a run of word-sized members present in every kernel's BTF:
 * uptime (off 0), loads[3] (8/16/24), totalram (32), freeram (40).
 * 32 casts x 6 loads = 192 guard sites, one third at off==0.
 *
 * Driven via BPF_PROG_TEST_RUN (bpftool prog run ... repeat N), same
 * mechanism as the xdp_lb (katran) benchmark.
 */
#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_core_read.h>

char LICENSE[] SEC("license") = "GPL";

#define STRIDE 64
#define CASTS 32

struct {
	__uint(type, BPF_MAP_TYPE_ARRAY);
	__uint(max_entries, 1);
	__type(key, __u32);
	__uint(value_size, CASTS * STRIDE);
} bench_data SEC(".maps");

__u64 sink;

SEC("xdp")
int guard_bench(struct xdp_md *ctx)
{
	__u64 acc = 0;
	__u32 zero = 0;
	char *base;
	int i;

	base = bpf_map_lookup_elem(&bench_data, &zero);
	if (!base)
		return XDP_DROP;

#pragma unroll
	for (i = 0; i < CASTS; i++) {
		struct sysinfo *s = bpf_core_cast(base + i * STRIDE, struct sysinfo);

		acc += s->uptime + s->loads[0] + s->loads[1] + s->loads[2] +
		       s->totalram + s->freeram;
	}
	sink = acc;
	return XDP_PASS;
}

/* Control program: identical loop shape and load count, but through the
 * trusted map-value pointer — no guards. The A/B delta of guard_bench
 * minus the delta of this program isolates guard cost from everything
 * else (test_run harness, UML noise floor).
 */
SEC("xdp")
int plain_bench(struct xdp_md *ctx)
{
	__u64 acc = 0;
	__u32 zero = 0;
	__u64 *base;
	int i;

	base = bpf_map_lookup_elem(&bench_data, &zero);
	if (!base)
		return XDP_DROP;

#pragma unroll
	for (i = 0; i < CASTS; i++) {
		volatile __u64 *s = base + i * (STRIDE / 8);

		acc += s[0] + s[1] + s[2] + s[3] + s[4] + s[5];
	}
	sink = acc;
	return XDP_PASS;
}
