# Spec 002 — REA sweep do TVP7002 + THS7353 (analog frontend)

## Contexto

Sweep estilo REA nos drivers do AFE: o driver `tvp7002.c` expõe bem o básico
(sog_thold, coast, filtros, ganho fino/offset, CSC), mas vários blocos documentados
no datasheet estão intocados — inclusive um `//TODO: TVP_ADCSETUP` pendurado em
`tvp_source_sel` (`tvp7002.c` ~461). THS7353 usa só `AC_BIAS`/`AVMUTE`; o modo
`STC` (sync-tip clamp mid-bias, feito exatamente para sinais com sync-on-video)
nunca é usado.

## Requisitos (ordem de valor)

1. `[FW]` Escrever `TVP_ADCSETUP` (0x2C) — resolver o TODO. Avaliar default vs
   recomendado do datasheet.
2. `[FW]` Expor coarse offset (`TVP_B/G/R_COFFSET` 0x1E-0x20, `TVP_FOFFSET_LSB`
   0x1D) como range estendido de black level — resolve fontes com DC fora do
   range do fine offset (queixa conhecida de placas arcade).
3. `[FW]` Clamp coarse (`TVP_FCLAMPCTRL` 0x2A, `TVP_CCLAMPCTRL` 0x2D,
   `TVP_SOGCLAMP` 0x2E, `TVP_RGBCCLAMPCTRL` 0x2F, `TVP_SOGCCLAMPCTRL` 0x30) —
   tunável "coarse clamp" para fontes washed-out/crushed.
4. `[FW]` Toggle de ALC (`TVP_ALCEN` 0x26): hoje `tvp_set_clamp_alc(...,1)`
   hardcoded; permitir desligar p/ testar gain staging manual.
5. `[FW]` Telemetria TVP: `TVP_LINECNT1/2`, `TVP_CLKCNT1/2`, `TVP_HSINWIDTH`,
   `TVP_VSINWIDTH`, `TVP_*_ALCOUT_*` + `TVP_SYNCSTAT` (0x14, helper
   `tvp_check_sync` já existe, morto) → alimentar página de status/INFO do OSD
   (cross-check com `fe_status` do FPGA). Habilita #110 (auto 400p por
   polaridade de vsync).
6. `[FW]` `MVSWIDTH` (0x34) e `OUTFORMAT` (0x15) — experimentos comentados no
   código; expor como opções de debug.
7. `[FW]` THS7353 `THS_MODE_STC` no canal que carrega sync (SOG/YPbPr-Y); avaliar
   vs AC_BIAS por formato. `ths_source_sel(input, lpf)` já honra `lpf` (fix P0).
8. `[FW]` Registradores de saída `TVP_HSOUTWIDTH`/`HSOUTSTART` — ajuste fino de
   HSYNC para sinks estritos.

## Abordagem técnica

- Novos campos em `avconfig_t` + itens `ude_profile_items` (IDs 70+, ver 123) —
  formato itemizado torna retrocompatível automaticamente.
- Entradas de menu em `menu_vinput_opt`/`menu_sync`; defaults = comportamento
  atual (valores de reset do chip) → zero risco para perfis existentes.
- Telemetria: estender `print_vm_stats()` ou nova página OSD (infra existe).
- Para clamp/coarse: consultar datasheet TVP7002 (SLAS) para mapear campos; marcar
  limites nos `*_MAX` de `avconfig.h`.

## Critérios de aceite

- Defaults == comportamento atual bit-a-bit (verificar com diff do dump de regs
  esperado).
- Menu expõe novos itens com ranges corretos; perfis antigos carregam sem erro.
- Telemetria visível no OSD confere com `fe_status` em fonte estável.

## Referências

- `ic_drivers/tvp7002/tvp7002_regs.h` (endereços), `tvp7002.c` (~44-87 clamp,
  ~212/237/240/247 experimentos comentados, ~396 ALC, ~461 TODO, ~467
  `tvp_check_sync`)
- `ic_drivers/ths7353/ths7353.h:54` (`THS_MODE_STC=6`), `ths7353.c`
- Datasheet TVP7002 (TI SLAS), issue #90 (paleta PCE pode reusar caminho de
  `lumacode_pal_ram`)
