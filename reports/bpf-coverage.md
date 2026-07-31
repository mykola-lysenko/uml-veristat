# BPF subsystem coverage under the UML selftests

Read the gaps with three filters in mind before calling something an upstream test gap:

1. **Harness scope** — this sweep runs `test_progs` only; suites living in standalone binaries (`test_maps`, `test_verifier`) do not contribute, so e.g. classic map-op paths may be covered upstream but not here.
2. **Environment** — tests that FAIL or SKIP on UML leave their kernel paths unexercised (e.g. stackmap ↔ the failing stacktrace family, priv-stack ↔ JIT features disabled on UML).
3. **Dead-by-design** — some never-executed functions are unreachable error stubs (e.g. map ops that return -EOPNOTSUPP by contract).

What survives all three filters is upstream-test material.

Overall line coverage: **43197/54713 (79.0%)** across 86 instrumented sources.

| file | line coverage | uncovered functions |
|---|---|---|
| kernel/bpf/rqspinlock.h | 0/7 (0.0%) | 0/0 |
| net/xdp/xsk_diag.c | 2/116 (1.7%) | 9/10 |
| kernel/bpf/prog_iter.c | 3/36 (8.3%) | 6/7 |
| kernel/bpf/../locking/qspinlock.h | 2/21 (9.5%) | 1/1 |
| kernel/bpf/lpm_trie.c | 38/303 (12.5%) | 9/12 |
| kernel/bpf/rqspinlock.c | 34/195 (17.4%) | 8/12 |
| kernel/bpf/bpf_inode_storage.c | 17/75 (22.7%) | 9/12 |
| kernel/bpf/offload.c | 154/460 (33.5%) | 27/43 |
| kernel/bpf/stackmap.c | 151/448 (33.7%) | 20/32 |
| net/xdp/xsk_buff_pool.c | 188/417 (45.1%) | 17/37 |
| kernel/bpf/bpf_lsm.c | 43/88 (48.9%) | 4/12 |
| net/core/xdp.c | 246/461 (53.4%) | 15/48 |
| kernel/bpf/core.c | 874/1533 (57.0%) | 79/171 |
| kernel/bpf/../../tools/lib/bpf/relo_core.c | 431/738 (58.4%) | 7/24 |
| kernel/trace/bpf_trace.h | 7/11 (63.6%) | 4/11 |
| kernel/bpf/cpumap.c | 257/384 (66.9%) | 5/23 |
| kernel/bpf/inode.c | 427/638 (66.9%) | 11/51 |
| net/xdp/xdp_umem.c | 93/138 (67.4%) | 1/12 |
| kernel/bpf/crypto.c | 98/145 (67.6%) | 2/12 |
| net/xdp/xsk.c | 757/1104 (68.6%) | 13/73 |
| kernel/bpf/trampoline.c | 452/655 (69.0%) | 15/64 |
| kernel/bpf/bpf_struct_ops.c | 528/764 (69.1%) | 14/47 |
| net/xdp/xsk_queue.h | 130/188 (69.1%) | 5/30 |
| kernel/bpf/reuseport_array.c | 96/138 (69.6%) | 3/11 |
| kernel/bpf/bpf_lru_list.c | 254/353 (72.0%) | 4/27 |
| net/core/filter.c | 3744/5099 (73.4%) | 63/348 |
| net/core/skmsg.c | 568/762 (74.5%) | 8/50 |
| net/xdp/xskmap.c | 116/155 (74.8%) | 5/16 |
| kernel/bpf/fixups.c | 1082/1417 (76.4%) | 6/39 |
| kernel/bpf/token.c | 101/132 (76.5%) | 2/14 |
| kernel/bpf/bloom_filter.c | 57/74 (77.0%) | 6/13 |
| kernel/bpf/devmap.c | 426/549 (77.6%) | 6/42 |
| kernel/bpf/cgroup.c | 973/1248 (78.0%) | 14/82 |
| net/bpf/bpf_dummy_struct_ops.c | 111/142 (78.2%) | 6/18 |
| kernel/bpf/cgroup_iter.c | 114/145 (78.6%) | 3/16 |
| kernel/bpf/hashtab.c | 1323/1675 (79.0%) | 19/133 |
| kernel/bpf/helpers.c | 1465/1850 (79.2%) | 44/201 |
| kernel/bpf/mmap_unlock_work.h | 27/34 (79.4%) | 0/4 |
| kernel/bpf/check_btf.c | 192/240 (80.0%) | 0/7 |
| net/core/sock_map.c | 816/1016 (80.3%) | 12/84 |
| kernel/bpf/arena.c | 424/526 (80.6%) | 17/46 |
| kernel/bpf/bpf_iter.c | 336/414 (81.2%) | 3/27 |
| kernel/bpf/../../tools/lib/bpf/btf_relocate.c | 195/240 (81.2%) | 0/8 |
| kernel/bpf/queue_stack_maps.c | 91/111 (82.0%) | 6/16 |
| net/bpf/test_run.c | 829/1008 (82.2%) | 10/56 |
| kernel/bpf/memalloc.c | 397/482 (82.4%) | 3/41 |
| kernel/bpf/percpu_freelist.c | 66/79 (83.5%) | 0/9 |
| kernel/trace/bpf_trace.c | 734/877 (83.7%) | 30/115 |
| kernel/bpf/syscall.c | 2674/3194 (83.7%) | 20/215 |
| kernel/bpf/local_storage.c | 253/300 (84.3%) | 3/22 |
| kernel/bpf/task_iter.c | 404/475 (85.1%) | 6/41 |
| kernel/bpf/tcx.c | 207/243 (85.2%) | 1/13 |
| net/xdp/xsk_queue.c | 24/28 (85.7%) | 0/3 |
| kernel/bpf/bpf_local_storage.c | 342/397 (86.1%) | 1/29 |
| arch/x86/net/bpf_jit_comp.c | 1611/1864 (86.4%) | 10/105 |
| kernel/bpf/btf.c | 3878/4464 (86.9%) | 13/276 |
| kernel/bpf/backtrack.c | 344/395 (87.1%) | 1/20 |
| kernel/bpf/verifier.c | 8326/9517 (87.5%) | 13/522 |
| kernel/bpf/bpf_task_storage.c | 93/106 (87.7%) | 1/12 |
| kernel/bpf/arraymap.c | 621/701 (88.6%) | 6/67 |
| kernel/bpf/map_iter.c | 80/90 (88.9%) | 4/14 |
| kernel/bpf/stream.c | 187/210 (89.0%) | 1/20 |
| kernel/bpf/tnum.c | 109/122 (89.3%) | 1/27 |
| kernel/bpf/cfg.c | 371/415 (89.4%) | 0/20 |
| kernel/bpf/ringbuf.c | 291/325 (89.5%) | 5/32 |
| kernel/bpf/kmem_cache_iter.c | 84/93 (90.3%) | 2/10 |
| kernel/bpf/../../tools/lib/bpf/btf_iter.c | 61/67 (91.0%) | 0/2 |
| kernel/bpf/net_namespace.c | 272/298 (91.3%) | 1/23 |
| kernel/bpf/dispatcher.c | 72/78 (92.3%) | 1/8 |
| kernel/bpf/disasm.c | 167/180 (92.8%) | 0/8 |
| kernel/bpf/states.c | 557/600 (92.8%) | 0/33 |
| kernel/bpf/cpumask.c | 82/88 (93.2%) | 2/28 |
| kernel/bpf/cnum.c | 29/31 (93.5%) | 0/2 |
| kernel/bpf/liveness.c | 1129/1206 (93.6%) | 1/59 |
| kernel/bpf/bpf_insn_array.c | 118/126 (93.7%) | 3/17 |
| kernel/bpf/bpf_cgrp_storage.c | 74/79 (93.7%) | 1/12 |
| kernel/bpf/log.c | 399/424 (94.1%) | 0/29 |
| kernel/bpf/const_fold.c | 229/243 (94.2%) | 0/5 |
| kernel/bpf/link_iter.c | 34/36 (94.4%) | 1/7 |
| kernel/bpf/mprog.c | 239/252 (94.8%) | 0/14 |
| kernel/bpf/map_in_map.c | 62/65 (95.4%) | 0/6 |
| kernel/bpf/cnum_defs.h | 156/160 (97.5%) | 0/36 |
| kernel/bpf/range_tree.c | 124/125 (99.2%) | 0/18 |
| kernel/bpf/bpf_lsm_proto.c | 2/2 (100.0%) | 0/1 |
| kernel/bpf/bpf_lru_list.h | 4/4 (100.0%) | 0/1 |
| kernel/bpf/sysfs_btf.c | 19/19 (100.0%) | 0/2 |

## Never-executed functions (missing-test candidates)

### arch/x86/net/bpf_jit_comp.c

- `clear_bhb_loop` (line 75)
- `smp_text_poke_single` (line 99)
- `push_r9` (line 426)
- `pop_r9` (line 434)
- `emit_st_index` (line 1434)
- `emit_st_r12` (line 1461)
- `emit_priv_frame_ptr` (line 1752)
- `priv_stack_init_guard` (line 4001)
- `priv_stack_check_guard` (line 4013)
- `bpf_jit_supports_stack_args` (line 4246)

### kernel/bpf/../../tools/lib/bpf/relo_core.c

- `bpf_core_calc_enumval_relo` (line 864)
- `insn_bpf_size_to_bytes` (line 1002)
- `insn_bytes_to_bpf_size` (line 1013)
- `bpf_core_names_match` (line 1451)
- `bpf_core_enums_match` (line 1469)
- `bpf_core_composites_match` (line 1508)
- `__bpf_core_types_match` (line 1573)

### kernel/bpf/../locking/qspinlock.h

- `decode_tail` (line 62)

### kernel/bpf/arena.c

- `bpf_arena_map_kern_vm_start` (line 95)
- `bpf_prog_arena` (line 108)
- `arena_map_peek_elem` (line 115)
- `arena_map_push_elem` (line 120)
- `arena_map_pop_elem` (line 125)
- `arena_map_delete_elem` (line 130)
- `arena_map_get_next_key` (line 135)
- `apply_range_set_scratch_cb` (line 237)
- `arena_map_lookup_elem` (line 397)
- `arena_map_update_elem` (line 402)
- `arena_map_check_btf` (line 408)
- `arena_map_mem_usage` (line 414)
- `arena_vm_open` (line 441)
- `arena_vm_may_split` (line 448)
- `arena_vm_mremap` (line 453)
- `bpf_arena_alloc_pages_sleepable` (line 1062)
- `bpf_arena_handle_page_fault` (line 1145)

### kernel/bpf/arraymap.c

- `fd_array_map_lookup_elem` (line 872)
- `prog_array_map_seq_show_elem` (line 1022)
- `bpf_arch_poke_desc_update` (line 1101)
- `cgroup_fd_array_get_ptr` (line 1339)
- `cgroup_fd_array_put_ptr` (line 1346)
- `array_of_map_lookup_elem` (line 1403)

### kernel/bpf/backtrack.c

- `bt_clear_frame_stack_arg_slot` (line 137)

### kernel/bpf/bloom_filter.c

- `bloom_map_pop_elem` (line 68)
- `bloom_map_delete_elem` (line 73)
- `bloom_map_get_next_key` (line 78)
- `bloom_map_lookup_elem` (line 170)
- `bloom_map_update_elem` (line 176)
- `bloom_map_mem_usage` (line 192)

### kernel/bpf/bpf_cgrp_storage.c

- `notsupp_get_next_key` (line 110)

### kernel/bpf/bpf_inode_storage.c

- `inode_storage_ptr` (line 24)
- `inode_storage_lookup` (line 35)
- `bpf_fd_inode_storage_lookup_elem` (line 76)
- `bpf_fd_inode_storage_update_elem` (line 88)
- `inode_storage_delete` (line 105)
- `bpf_fd_inode_storage_delete_elem` (line 116)
- `bpf_inode_storage_get` (line 125)
- `bpf_inode_storage_delete` (line 160)
- `notsupp_get_next_key` (line 173)

### kernel/bpf/bpf_insn_array.c

- `insn_array_delete_elem` (line 96)
- `insn_array_check_btf` (line 101)
- `insn_array_mem_usage` (line 115)

### kernel/bpf/bpf_iter.c

- `bpf_iter_dec_seq_num` (line 52)
- `bpf_iter_unreg_target` (line 312)
- `bpf_iter_link_show_fdinfo` (line 435)

### kernel/bpf/bpf_local_storage.c

- `bpf_local_storage_map_mem_usage` (line 762)

### kernel/bpf/bpf_lru_list.c

- `bpf_lru_list_push_free` (line 296)
- `__local_list_pop_pending` (line 379)
- `bpf_percpu_lru_pop_free` (line 403)
- `bpf_percpu_lru_push_free` (line 565)

### kernel/bpf/bpf_lsm.c

- `bpf_lsm_find_cgroup_shim` (line 94)
- `bpf_ima_inode_hash` (line 169)
- `bpf_ima_file_hash` (line 193)
- `bpf_lsm_hook_returns_errno` (line 443)

### kernel/bpf/bpf_struct_ops.c

- `is_module_member` (line 310)
- `bpf_struct_ops_map_get_next_key` (line 471)
- `bpf_struct_ops_map_sys_lookup_elem` (line 481)
- `bpf_struct_ops_map_lookup_elem` (line 518)
- `bpf_struct_ops_map_seq_show_elem` (line 950)
- `bpf_struct_ops_map_mem_usage` (line 1137)
- `bpf_struct_ops_id` (line 1196)
- `bpf_struct_ops_for_each_prog` (line 1221)
- `bpf_struct_ops_map_link_show_fdinfo` (line 1269)
- `bpf_struct_ops_map_link_fill_link_info` (line 1283)
- `bpf_struct_ops_map_link_detach` (line 1348)
- `bpf_struct_ops_map_link_poll` (line 1378)
- `bpf_prog_get_assoc_struct_ops` (line 1509)
- `bpf_map_struct_ops_info_fill` (line 1524)

### kernel/bpf/bpf_task_storage.c

- `notsupp_get_next_key` (line 207)

### kernel/bpf/btf.c

- `btf_get_name` (line 1891)
- `btf_df_check_member` (line 2221)
- `btf_df_check_kflag_member` (line 2231)
- `btf_df_resolve` (line 2263)
- `btf_df_show` (line 2270)
- `btf_var_show` (line 2918)
- `btf_enum64_show` (line 4657)
- `btf_datasec_show` (line 5019)
- `bpf_btf_show_fdinfo` (line 8301)
- `check_btf_kconfigs` (line 8668)
- `bpf_core_types_match` (line 9350)
- `__print_cand_cache` (line 9397)
- `print_cand_cache` (line 9418)

### kernel/bpf/cgroup.c

- `__cgroup_bpf_run_lsm_sock` (line 118)
- `__cgroup_bpf_run_lsm_socket` (line 140)
- `__cgroup_bpf_run_lsm_current` (line 162)
- `bpf_cgroup_atype_get` (line 204)
- `bpf_cgroup_atype_put` (line 220)
- `purge_effective_progs` (line 1131)
- `bpf_cgroup_link_show_fdinfo` (line 1463)
- `__cgroup_bpf_run_filter_sysctl` (line 1927)
- `sysctl_cpy_dir` (line 2250)
- `bpf_sysctl_get_name` (line 2281)
- `copy_sysctl_value` (line 2312)
- `bpf_sysctl_get_current_value` (line 2338)
- `bpf_sysctl_get_new_value` (line 2353)
- `bpf_sysctl_set_new_value` (line 2373)

### kernel/bpf/cgroup_iter.c

- `bpf_iter_cgroup_show_fdinfo` (line 242)
- `bpf_iter_cgroup_fill_link_info` (line 276)
- `bpf_iter_cgroup` (line 284)

### kernel/bpf/core.c

- `bpf_internal_load_pointer_neg_helper` (line 78)
- `bpf_has_frame_pointer` (line 768)
- `bpf_jit_fill_hole_with_zero` (line 884)
- `bpf_jit_binary_alloc` (line 1130)
- `bpf_jit_binary_free` (line 1168)
- `bpf_jit_free` (line 1291)
- `bpf_jit_get_prog_name` (line 1343)
- `___bpf_prog_run` (line 1853)
- `__bpf_prog_run128` (line 2438)
- `__bpf_prog_run160` (line 2438)
- `__bpf_prog_run192` (line 2438)
- `__bpf_prog_run32` (line 2438)
- `__bpf_prog_run64` (line 2438)
- `__bpf_prog_run96` (line 2438)
- `__bpf_prog_run224` (line 2439)
- `__bpf_prog_run256` (line 2439)
- `__bpf_prog_run288` (line 2439)
- `__bpf_prog_run320` (line 2439)
- `__bpf_prog_run352` (line 2439)
- `__bpf_prog_run384` (line 2439)
- `__bpf_prog_run416` (line 2440)
- `__bpf_prog_run448` (line 2440)
- `__bpf_prog_run480` (line 2440)
- `__bpf_prog_run512` (line 2440)
- `__bpf_prog_run_args128` (line 2442)
- `__bpf_prog_run_args160` (line 2442)
- `__bpf_prog_run_args192` (line 2442)
- `__bpf_prog_run_args32` (line 2442)
- `__bpf_prog_run_args64` (line 2442)
- `__bpf_prog_run_args96` (line 2442)
- `__bpf_prog_run_args224` (line 2443)
- `__bpf_prog_run_args256` (line 2443)
- `__bpf_prog_run_args288` (line 2443)
- `__bpf_prog_run_args320` (line 2443)
- `__bpf_prog_run_args352` (line 2443)
- `__bpf_prog_run_args384` (line 2443)
- `__bpf_prog_run_args416` (line 2444)
- `__bpf_prog_run_args448` (line 2444)
- `__bpf_prog_run_args480` (line 2444)
- `__bpf_prog_run_args512` (line 2444)
- `bpf_patch_call_args` (line 2466)
- `bpf_call_args_imm` (line 2477)
- `__bpf_prog_ret0_warn` (line 2486)
- `__bpf_prog_ret1` (line 2737)
- `bpf_prog_array_is_empty` (line 2807)
- `bpf_prog_array_delete_safe` (line 2863)
- `bpf_prog_array_delete_safe_at` (line 2890)
- `bpf_get_raw_cpu_id` (line 3145)
- `bpf_get_trace_printk_proto` (line 3182)
- `bpf_get_trace_vprintk_proto` (line 3187)
- `bpf_get_perf_event_read_value_proto` (line 3192)
- `bpf_event_output` (line 3198)
- `bpf_int_jit_compile` (line 3222)
- `bpf_helper_changes_pkt_data` (line 3234)
- `bpf_jit_supports_subprog_tailcalls` (line 3279)
- `bpf_jit_supports_percpu_insn` (line 3284)
- `bpf_jit_supports_kfunc_call` (line 3289)
- `bpf_jit_supports_stack_args` (line 3294)
- `bpf_jit_supports_far_kfunc_call` (line 3299)
- `bpf_jit_supports_arena` (line 3304)
- `bpf_jit_supports_insn` (line 3309)
- `bpf_jit_supports_fsession` (line 3314)
- `bpf_arch_uaddress_limit` (line 3319)
- `bpf_jit_supports_ptr_xchg` (line 3333)
- `skb_copy_bits` (line 3341)
- `bpf_arch_text_poke` (line 3347)
- `bpf_arch_text_copy` (line 3354)
- `bpf_arch_text_invalidate` (line 3359)
- `bpf_jit_supports_exceptions` (line 3364)
- `bpf_jit_supports_private_stack` (line 3369)
- `arch_bpf_stack_walk` (line 3374)
- `bpf_jit_supports_timed_may_goto` (line 3378)
- `arch_bpf_timed_may_goto` (line 3383)
- `bpf_arena_get_user_vm_start` (line 3424)
- `bpf_arena_get_kern_vm_start` (line 3428)
- `bpf_arena_handle_page_fault` (line 3434)
- `bpf_get_linfo_file_line` (line 3463)
- `bpf_prog_get_file_line` (line 3520)
- `find_from_stack_cb` (line 3562)

### kernel/bpf/cpumap.c

- `cpu_map_bpf_prog_run_skb` (line 139)
- `cpu_map_delete_elem` (line 568)
- `cpu_map_get_next_key` (line 676)
- `cpu_map_mem_usage` (line 699)
- `cpu_map_generic_redirect` (line 803)

### kernel/bpf/cpumask.c

- `bpf_cpumask_acquire` (line 83)
- `bpf_cpumask_xor` (line 298)

### kernel/bpf/crypto.c

- `bpf_crypto_unregister_type` (line 87)
- `bpf_crypto_ctx_acquire` (line 243)

### kernel/bpf/devmap.c

- `dev_map_get_next_key` (line 256)
- `dev_map_hash_get_next_key` (line 291)
- `dev_map_hash_lookup_elem` (line 844)
- `dev_map_delete_elem` (line 862)
- `dev_map_hash_delete_elem` (line 879)
- `dev_map_mem_usage` (line 1072)

### kernel/bpf/dispatcher.c

- `arch_prepare_bpf_dispatcher` (line 89)

### kernel/bpf/fixups.c

- `bpf_jit_find_kfunc_model` (line 71)
- `get_callee_stack_depth` (line 143)
- `bpf_dup_subprog_starts` (line 988)
- `bpf_restore_subprog_starts` (line 1000)
- `bpf_restore_insn_aux_data` (line 1020)
- `add_hidden_subprog` (line 1451)

### kernel/bpf/hashtab.c

- `htab_percpu_map_lookup_and_delete_batch` (line 2022)
- `htab_lru_percpu_map_lookup_and_delete_batch` (line 2057)
- `htab_lru_map_lookup_batch` (line 2066)
- `htab_lru_map_lookup_and_delete_batch` (line 2074)
- `htab_map_mem_usage` (line 2319)
- `htab_of_map_lookup_elem` (line 2695)
- `rhtab_key_cmp_long` (line 2771)
- `rhtab_hashfn_long` (line 2780)
- `rhtab_mem_dtor` (line 2878)
- `rhtab_map_lookup_elem` (line 2921)
- `rhtab_read_elem_value` (line 2929)
- `rhtab_map_lookup_and_delete_elem` (line 2988)
- `rhtab_map_get_next_key` (line 3159)
- `rhtab_map_seq_show_elem` (line 3180)
- `bpf_each_rhash_elem` (line 3197)
- `rhtab_map_mem_usage` (line 3235)
- `__rhtab_map_lookup_and_delete_batch` (line 3245)
- `rhtab_map_lookup_batch` (line 3381)
- `rhtab_map_lookup_and_delete_batch` (line 3387)

### kernel/bpf/helpers.c

- `bpf_map_push_elem` (line 92)
- `bpf_map_pop_elem` (line 107)
- `bpf_map_peek_elem` (line 120)
- `bpf_get_numa_node_id` (line 167)
- `bpf_ktime_get_coarse_ns` (line 202)
- `bpf_jiffies64` (line 394)
- `bpf_get_current_ancestor_cgroup_id` (line 425)
- `__bpf_strtoll` (line 501)
- `bpf_strtol` (line 523)
- `bpf_event_output_data` (line 639)
- `bpf_kptr_xchg` (line 1731)
- `bpf_obj_drop_impl` (line 2431)
- `bpf_percpu_obj_drop_impl` (line 2449)
- `bpf_refcount_acquire_impl` (line 2481)
- `bpf_list_push_front_impl` (line 2550)
- `bpf_list_push_back_impl` (line 2580)
- `bpf_rbtree_add_impl` (line 2783)
- `bpf_current_task_under_cgroup` (line 2940)
- `bpf_cast_to_kern_ctx` (line 3337)
- `bpf_rdonly_cast` (line 3342)
- `bpf_stack_walker` (line 3364)
- `bpf_throw` (line 3388)
- `bpf_copy_from_user_str` (line 3633)
- `bpf_local_irq_save` (line 3708)
- `bpf_local_irq_restore` (line 3713)
- `__bpf_trap` (line 3718)
- `__bpf_strncasecmp` (line 3730)
- `bpf_strcmp` (line 3773)
- `bpf_strcasecmp` (line 3791)
- `bpf_strncasecmp` (line 3810)
- `bpf_strnchr` (line 3831)
- `bpf_strchr` (line 3868)
- `bpf_strchrnul` (line 3885)
- `bpf_strrchr` (line 3917)
- `bpf_strnlen` (line 3950)
- `bpf_strlen` (line 3980)
- `bpf_strspn` (line 3998)
- `bpf_strcspn` (line 4042)
- `__bpf_strnstr` (line 4073)
- `bpf_strstr` (line 4133)
- `bpf_strcasestr` (line 4152)
- `bpf_strnstr` (line 4171)
- `bpf_strncasestr` (line 4192)
- `bpf_task_work_schedule_resume` (line 4669)

### kernel/bpf/inode.c

- `bpffs_obj_open` (line 354)
- `bpf_iter_link_pin_kernel` (line 475)
- `__get_prog_inode` (line 611)
- `bpf_prog_get_type_path` (line 638)
- `seq_print_delegate_opts` (line 726)
- `bpf_show_options` (line 778)
- `bpf_fs_xattr_get` (line 859)
- `bpf_fs_xattr_set` (line 876)
- `bpf_fs_listxattr` (line 927)
- `bpf_fs_initxattrs` (line 934)
- `bpf_preload_mod_put` (line 1144)

### kernel/bpf/kmem_cache_iter.c

- `bpf_iter_kmem_cache_show_fdinfo` (line 211)
- `bpf_iter_kmem_cache` (line 217)

### kernel/bpf/link_iter.c

- `bpf_iter_bpf_link` (line 42)

### kernel/bpf/liveness.c

- `stack_arg_off_to_slot` (line 619)

### kernel/bpf/local_storage.c

- `cgroup_storage_delete_elem` (line 362)
- `cgroup_storage_seq_show_elem` (line 418)
- `cgroup_storage_map_usage` (line 453)

### kernel/bpf/lpm_trie.c

- `extract_bit` (line 154)
- `longest_prefix_match` (line 230)
- `trie_lookup_elem` (line 238)
- `lpm_trie_node_alloc` (line 292)
- `trie_check_add_elem` (line 311)
- `trie_update_elem` (line 322)
- `trie_delete_elem` (line 457)
- `trie_get_next_key` (line 656)
- `trie_mem_usage` (line 764)

### kernel/bpf/map_iter.c

- `bpf_iter_bpf_map` (line 42)
- `bpf_iter_map_show_fdinfo` (line 156)
- `bpf_iter_map_fill_link_info` (line 162)
- `bpf_iter_bpf_map_elem` (line 169)

### kernel/bpf/memalloc.c

- `free_bulk` (line 326)
- `bpf_mem_cache_raw_free` (line 967)
- `bpf_mem_cache_alloc_flags` (line 979)

### kernel/bpf/net_namespace.c

- `bpf_netns_link_show_fdinfo` (line 222)

### kernel/bpf/offload.c

- `bpf_map_offload_ndo` (line 111)
- `__bpf_map_offload_destroy` (line 127)
- `bpf_prog_offload_verifier_prep` (line 287)
- `bpf_prog_offload_verify_insn` (line 303)
- `bpf_prog_offload_finalize` (line 319)
- `bpf_prog_offload_replace_insn` (line 338)
- `bpf_prog_offload_remove_insns` (line 357)
- `bpf_prog_offload_translate` (line 393)
- `bpf_prog_warn_on_exec` (line 407)
- `bpf_prog_offload_compile` (line 414)
- `bpf_prog_offload_info_fill_ns` (line 426)
- `bpf_prog_offload_info_fill` (line 451)
- `bpf_map_offload_map_alloc` (line 503)
- `bpf_map_offload_map_free` (line 556)
- `bpf_map_offload_map_mem_usage` (line 570)
- `bpf_map_offload_lookup_elem` (line 576)
- `bpf_map_offload_update_elem` (line 589)
- `bpf_map_offload_delete_elem` (line 607)
- `bpf_map_offload_get_next_key` (line 620)
- `bpf_map_offload_info_fill_ns` (line 638)
- `bpf_map_offload_info_fill` (line 662)
- `bpf_offload_prog_map_match` (line 736)
- `bpf_offload_dev_netdev_register` (line 752)
- `bpf_offload_dev_netdev_unregister` (line 764)
- `bpf_offload_dev_create` (line 774)
- `bpf_offload_dev_destroy` (line 790)
- `bpf_offload_dev_priv` (line 797)

### kernel/bpf/prog_iter.c

- `bpf_prog_seq_start` (line 13)
- `bpf_prog_seq_next` (line 27)
- `bpf_iter_bpf_prog` (line 42)
- `__bpf_prog_seq_show` (line 44)
- `bpf_prog_seq_show` (line 61)
- `bpf_prog_seq_stop` (line 66)

### kernel/bpf/queue_stack_maps.c

- `queue_map_peek_elem` (line 158)
- `queue_stack_map_lookup_elem` (line 224)
- `queue_stack_map_update_elem` (line 230)
- `queue_stack_map_delete_elem` (line 237)
- `queue_stack_map_get_next_key` (line 243)
- `queue_stack_map_mem_usage` (line 249)

### kernel/bpf/reuseport_array.c

- `reuseport_array_delete_elem` (line 62)
- `reuseport_array_get_next_key` (line 316)
- `reuseport_array_mem_usage` (line 335)

### kernel/bpf/ringbuf.c

- `ringbuf_map_lookup_elem` (line 253)
- `ringbuf_map_update_elem` (line 258)
- `ringbuf_map_delete_elem` (line 264)
- `ringbuf_map_get_next_key` (line 269)
- `ringbuf_map_mem_usage` (line 362)

### kernel/bpf/rqspinlock.c

- `is_lock_released` (line 92)
- `check_deadlock_ABBA` (line 120)
- `resilient_tas_spin_lock` (line 261)
- `bpf_prog_report_rqspinlock_violation` (line 672)
- `bpf_res_spin_lock` (line 693)
- `bpf_res_spin_unlock` (line 709)
- `bpf_res_spin_lock_irqsave` (line 715)
- `bpf_res_spin_unlock_irqrestore` (line 734)

### kernel/bpf/stackmap.c

- `fetch_build_id` (line 150)
- `stack_map_build_id_set_ip` (line 156)
- `stack_map_build_id_set_valid` (line 168)
- `stack_map_build_id_set_from_cache` (line 209)
- `stack_map_build_id_cache_set_unresolved` (line 257)
- `stack_map_lock_vma` (line 286)
- `stack_map_unlock_vma` (line 323)
- `stack_map_get_build_id_offset_sleepable` (line 333)
- `count_kernel_ip` (line 614)
- `bpf_get_stackid_pe` (line 626)
- `bpf_get_stack_sleepable` (line 788)
- `bpf_get_task_stack_sleepable` (line 838)
- `bpf_get_stack_pe` (line 855)
- `stack_map_lookup_elem` (line 919)
- `stack_map_lookup_and_delete_elem` (line 925)
- `bpf_stackmap_extract` (line 932)
- `stack_map_get_next_key` (line 959)
- `stack_map_update_elem` (line 988)
- `stack_map_delete_elem` (line 995)
- `stack_map_mem_usage` (line 1024)

### kernel/bpf/stream.c

- `dump_stack_cb` (line 362)

### kernel/bpf/syscall.c

- `bpf_dummy_read` (line 1044)
- `bpf_dummy_write` (line 1053)
- `map_check_no_btf` (line 1235)
- `bpf_stackmap_extract` (line 1743)
- `generic_map_delete_batch` (line 1998)
- `bpf_prog_add` (line 2602)
- `bpf_prog_sub` (line 2608)
- `bpf_multi_func` (line 2899)
- `bpf_link_show_fdinfo` (line 3392)
- `bpf_link_poll` (line 3427)
- `bpf_tracing_link_show_fdinfo` (line 3569)
- `bpf_raw_tp_link_show_fdinfo` (line 3846)
- `bpf_perf_event_link_show_fdinfo` (line 4146)
- `bpf_tracepoint_link_show_fdinfo` (line 4158)
- `bpf_perf_link_show_fdinfo` (line 4191)
- `bpf_prog_get_curr_or_next` (line 4833)
- `prog_assoc_struct_ops` (line 6234)
- `kern_sys_bpf` (line 6499)
- `tracing_prog_func_proto` (line 6551)
- `bpf_stats_handler` (line 6628)

### kernel/bpf/task_iter.c

- `bpf_iter_task` (line 175)
- `bpf_iter_task_file` (line 341)
- `bpf_iter_task_vma` (line 605)
- `bpf_iter_task_show_fdinfo` (line 684)
- `bpf_iter_task_vma_find_next` (line 944)
- `bpf_iter_task_vma_snapshot_reset` (line 980)

### kernel/bpf/tcx.c

- `tcx_link_fdinfo` (line 251)

### kernel/bpf/tnum.c

- `tnum_sbin` (line 218)

### kernel/bpf/token.c

- `bpf_token_inc` (line 30)
- `bpf_token_show_fdinfo` (line 69)

### kernel/bpf/trampoline.c

- `bpf_tramp_ftrace_ops_func` (line 98)
- `bpf_shim_tramp_link_release` (line 996)
- `bpf_shim_tramp_link_dealloc` (line 1009)
- `cgroup_shim_alloc` (line 1022)
- `cgroup_shim_find` (line 1058)
- `bpf_trampoline_link_cgroup_shim` (line 1076)
- `bpf_trampoline_unlink_cgroup_shim` (line 1141)
- `__update_prog_stats` (line 1257)
- `__bpf_prog_enter_lsm_cgroup` (line 1296)
- `__bpf_prog_exit_lsm_cgroup` (line 1310)
- `arch_prepare_bpf_trampoline` (line 1432)
- `arch_alloc_bpf_trampoline` (line 1440)
- `arch_free_bpf_trampoline` (line 1452)
- `arch_protect_bpf_trampoline` (line 1461)
- `arch_bpf_trampoline_size` (line 1467)

### kernel/bpf/verifier.c

- `grow_stack_arg_slots` (line 1394)
- `fd_slot_btf` (line 2515)
- `fd_array_get_btf_continuous` (line 2523)
- `check_stack_arg_write` (line 4104)
- `check_stack_arg_read` (line 4144)
- `mark_stack_arg_precision` (line 4172)
- `retrieve_ptr_limit` (line 13437)
- `update_alu_sanitation_state` (line 13474)
- `sanitize_speculative_path` (line 13512)
- `sanitize_err` (line 13641)
- `check_stack_access_for_ptr_arithmetic` (line 13686)
- `sanitize_dead_code` (line 18423)
- `bpf_check_attach_btf_id_multi` (line 19519)

### kernel/trace/bpf_trace.c

- `bpf_probe_write_user` (line 355)
- `bpf_perf_event_read` (line 589)
- `bpf_perf_event_output` (line 687)
- `bpf_get_func_ip_tracing` (line 1062)
- `bpf_get_func_ip_kprobe` (line 1084)
- `bpf_get_func_ip_kprobe_multi` (line 1110)
- `bpf_get_attach_cookie_kprobe_multi` (line 1122)
- `bpf_get_func_ip_uprobe_multi` (line 1134)
- `bpf_get_attach_cookie_uprobe_multi` (line 1146)
- `bpf_get_branch_snapshot` (line 1200)
- `get_func_arg` (line 1224)
- `get_func_ret` (line 1244)
- `get_func_arg_cnt` (line 1261)
- `bpf_get_stack_tp` (line 1450)
- `bpf_perf_prog_read_value` (line 1509)
- `bpf_prog_test_run_tracing` (line 1816)
- `bpf_trace_run5` (line 2177)
- `bpf_trace_run6` (line 2178)
- `bpf_trace_run7` (line 2179)
- `bpf_trace_run8` (line 2180)
- `bpf_trace_run9` (line 2181)
- `bpf_trace_run10` (line 2182)
- `bpf_trace_run11` (line 2183)
- `bpf_trace_run12` (line 2184)
- `bpf_kprobe_multi_cookie` (line 2940)
- `bpf_kprobe_multi_entry_ip` (line 2944)
- `bpf_uprobe_multi_cookie` (line 3407)
- `bpf_uprobe_multi_entry_ip` (line 3411)
- `bpf_session_is_return` (line 3419)
- `bpf_session_cookie` (line 3427)

### kernel/trace/bpf_trace.h

- `__bpf_trace_bpf_trace_printk` (line 11)
- `__probestub_bpf_trace_printk` (line 11)
- `do_perf_trace_bpf_trace_printk` (line 11)
- `perf_trace_bpf_trace_printk` (line 11)

### net/bpf/bpf_dummy_struct_ops.c

- `dummy_ops_test_ret_function` (line 15)
- `bpf_dummy_reg` (line 276)
- `bpf_dummy_unreg` (line 281)
- `bpf_dummy_ops__test_1` (line 285)
- `bpf_dummy_test_2` (line 290)
- `bpf_dummy_test_sleepable` (line 296)

### net/bpf/test_run.c

- `bpf_fentry_test_sinfo` (line 561)
- `bpf_fentry_test_ppvoid` (line 565)
- `bpf_fentry_test_pppvoid` (line 569)
- `bpf_fentry_test_ppfile` (line 573)
- `bpf_fexit_test_ret_ppfile` (line 577)
- `bpf_modify_return_test_tp` (line 595)
- `bpf_fentry_shadow_test` (line 602)
- `bpf_kfunc_call_memb_release` (line 635)
- `bpf_kfunc_call_memb_release_dtor` (line 639)
- `verify_and_copy_hook_state` (line 1721)

### net/core/filter.c

- `bpf_skb_get_pay_offset` (line 179)
- `bpf_skb_get_nlattr` (line 184)
- `bpf_skb_get_nlattr_nest` (line 204)
- `bpf_skb_load_helper_8` (line 242)
- `bpf_skb_load_helper_16` (line 267)
- `bpf_skb_load_helper_32` (line 292)
- `convert_skb_access` (line 317)
- `sk_filter_charge` (line 1253)
- `bpf_prog_create_from_user` (line 1429)
- `bpf_prog_destroy` (line 1472)
- `sk_reuseport_attach_filter` (line 1569)
- `__get_bpf` (line 1589)
- `sk_attach_bpf` (line 1597)
- `sk_reuseport_prog_free_rcu` (line 1660)
- `bpf_l4_csum_replace` (line 1980)
- `bpf_msg_apply_bytes` (line 2628)
- `bpf_msg_cork_bytes` (line 2642)
- `sk_msg_reset_curr` (line 2648)
- `sk_msg_elem_is_copy` (line 2662)
- `sk_msg_clear_elem_copy` (line 2667)
- `sk_msg_set_elem_copy` (line 2672)
- `sk_msg_clear_copy_range` (line 2677)
- `sk_msg_sg_move` (line 2685)
- `bpf_msg_pull_data` (line 2701)
- `bpf_msg_push_data` (line 2838)
- `sk_msg_shift_left` (line 3003)
- `sk_msg_shift_right` (line 3019)
- `bpf_get_cgroup_classid_curr` (line 3188)
- `bpf_skb_cgroup_classid` (line 3199)
- `bpf_get_cgroup_classid` (line 3217)
- `bpf_get_route_realm` (line 3229)
- `bpf_set_hash_invalid` (line 3258)
- `bpf_set_hash` (line 3274)
- `sk_skb_adjust_room` (line 3748)
- `sk_skb_change_head` (line 4024)
- `bpf_xdp_shrink_data_zc` (line 4262)
- `bpf_xdp_redirect_map` (line 4742)
- `bpf_skb_under_cgroup` (line 5062)
- `bpf_get_socket_cookie` (line 5223)
- `bpf_get_socket_cookie_sock` (line 5247)
- `bpf_get_netns_cookie_sock` (line 5301)
- `bpf_get_netns_cookie_sock_addr` (line 5313)
- `bpf_get_socket_uid` (line 5349)
- `bpf_sol_tcp_getsockopt` (line 5427)
- `sk_allows_sol_ip_sockopt` (line 5621)
- `sol_ip_sockopt` (line 5634)
- `bpf_unlocked_sk_setsockopt` (line 5811)
- `bpf_unlocked_sk_getsockopt` (line 5828)
- `bpf_skb_get_xfrm_state` (line 6163)
- `bpf_update_srh_state` (line 6844)
- `bpf_skc_lookup_tcp` (line 7157)
- `bpf_sk_lookup_udp` (line 7195)
- `bpf_xdp_sk_lookup_udp` (line 7300)
- `bpf_xdp_skc_lookup_tcp` (line 7324)
- `bpf_sock_addr_skc_lookup_tcp` (line 7372)
- `bpf_get_listener_sock` (line 7587)
- `bpf_tcp_raw_gen_syncookie_ipv6` (line 8146)
- `bpf_tcp_raw_check_syncookie_ipv6` (line 8198)
- `bpf_warn_invalid_xdp_action` (line 9398)
- `sk_detach_filter` (line 11477)
- `sk_get_filter` (line 11497)
- `bpf_skc_to_tcp_timewait_sock` (line 12076)
- `bpf_skc_to_udp6_sock` (line 12128)

### net/core/skmsg.c

- `sk_msg_clone` (line 87)
- `sk_msg_return_zero` (line 138)
- `sk_msg_return` (line 162)
- `sk_msg_free_nocharge` (line 212)
- `__sk_msg_free_partial` (line 224)
- `sk_msg_free_partial` (line 252)
- `sk_msg_free_partial_nocharge` (line 258)
- `sk_msg_trim` (line 264)

### net/core/sock_map.c

- `sock_map_get_next_key` (line 455)
- `bpf_iter_sockmap` (line 717)
- `sock_map_mem_usage` (line 813)
- `sock_hash_get_next_key` (line 1056)
- `bpf_sock_hash_update` (line 1229)
- `sock_hash_mem_usage` (line 1427)
- `sock_map_unhash` (line 1643)
- `sock_map_destroy` (line 1670)
- `sock_map_link_detach` (line 1757)
- `sock_map_link_get_map_id` (line 1832)
- `sock_map_link_fill_info` (line 1843)
- `sock_map_link_show_fdinfo` (line 1854)

### net/core/xdp.c

- `xdp_rxq_info_unused` (line 197)
- `xdp_unreg_page_pool` (line 396)
- `xdp_rxq_info_attach_page_pool` (line 415)
- `xdp_return_frame_bulk` (line 510)
- `xdp_return_frag` (line 543)
- `xdp_attachment_setup` (line 566)
- `xdp_convert_zc_to_xdp_frame` (line 576)
- `xdp_warn` (line 616)
- `xdp_build_skb_from_buff` (line 633)
- `xdp_copy_frags_from_zc` (line 687)
- `xdp_build_skb_from_zc` (line 739)
- `xdp_build_skb_from_frame` (line 849)
- `bpf_xdp_metadata_rx_timestamp` (line 903)
- `bpf_xdp_metadata_rx_hash` (line 925)
- `bpf_xdp_metadata_rx_vlan_tag` (line 958)

### net/xdp/xdp_umem.c

- `xdp_umem_release_deferred` (line 67)

### net/xdp/xsk.c

- `xsk_set_rx_need_wakeup` (line 51)
- `xsk_set_tx_need_wakeup` (line 61)
- `xsk_clear_rx_need_wakeup` (line 78)
- `xsk_clear_tx_need_wakeup` (line 88)
- `xsk_uses_need_wakeup` (line 105)
- `xsk_rcv_zc` (line 219)
- `xsk_tx_completed` (line 500)
- `xsk_tx_release` (line 506)
- `xsk_tx_peek_desc` (line 517)
- `xsk_tx_peek_release_fallback` (line 565)
- `xsk_tx_peek_release_desc_batch` (line 577)
- `xsk_wakeup` (line 622)
- `xsk_build_skb_zerocopy` (line 843)

### net/xdp/xsk_buff_pool.c

- `xp_set_rxq_info` (line 119)
- `xp_fill_cb` (line 128)
- `xp_assign_dev_shared` (line 268)
- `xp_find_dma_map` (line 342)
- `xp_create_dma_map` (line 354)
- `xp_destroy_dma_map` (line 377)
- `__xp_dma_unmap` (line 384)
- `xp_dma_unmap` (line 402)
- `xp_check_dma_contiguity` (line 425)
- `xp_init_dma_info` (line 437)
- `xp_dma_map` (line 464)
- `xp_alloc_new_from_fq` (line 604)
- `xp_alloc_reused` (line 640)
- `xp_alloc_batch` (line 678)
- `__xp_raw_get_dma` (line 744)
- `xp_raw_get_dma` (line 751)
- `xp_raw_get_ctx` (line 769)

### net/xdp/xsk_diag.c

- `xsk_diag_put_info` (line 17)
- `xsk_diag_put_ring` (line 26)
- `xsk_diag_put_rings_cfg` (line 35)
- `xsk_diag_put_umem` (line 47)
- `xsk_diag_put_stats` (line 79)
- `xsk_diag_fill` (line 92)
- `xsk_diag_dump` (line 151)
- `xsk_diag_handler_dump` (line 181)
- `xsk_diag_exit` (line 207)

### net/xdp/xsk_queue.h

- `parse_desc` (line 259)
- `xskq_cons_read_desc_batch` (line 267)
- `xskq_cons_nb_entries` (line 326)
- `xskq_prod_reserve_addr` (line 416)
- `xskq_prod_write_addr_batch` (line 435)

### net/xdp/xskmap.c

- `xsk_map_mem_usage` (line 88)
- `xsk_map_get_next_key` (line 104)
- `xsk_map_lookup_elem` (line 151)
- `xsk_map_lookup_elem_sys_only` (line 156)
- `xsk_map_meta_equal` (line 263)

