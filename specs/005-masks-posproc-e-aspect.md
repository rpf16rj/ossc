# Spec 005 — Máscaras, pós-processamento e aspect ratio

## Contexto

Máscara atual é uma janela retangular única (`scanconverter.v` ~545-553 via
`x_offset/x_size/y_offset/y_size`) — não há como ter larguras diferentes
esquerda/direita ou bordas 4:3 arbitrárias (#95 duas máscaras H, #133 bordas
em 480p 4:3). Pipeline de pós-processamento (`PP_*`, regs `R_pp/G_pp/B_pp` ~566+)
é o ponto natural para filtros novos: composite blending (#103), bit-depth
reduction + dither (#42). `misc_config` tem ~7 bits livres; `hv_out_config3[31:24]`
livre; `sl_config3[31:30]` livre.

## Requisitos

- `[RTL+FW]` Máscara H assimétrica: campos `mask_l`/`mask_r` (ou janela
  `x_start`/`x_end` absoluta). `mask_h = (xpos < MASK_L) | (xpos >= H_ACTIVE-MASK_R)`,
  OR no `mask_enable_pp[PP_MASK_END]`. Zero = comportamento atual. Resolve #95 e
  ajuda #133 (combinado com `o480p_pbox` já existente).
- `[RTL]` Composite blend / "cofi" (MiSTer-like): FIR horizontal 2-3 taps sobre
  RGB pipelined em estágio PP novo antes do SLGEN; strength em bit de
  `misc_config`/`sl_config3`. marqs reconheceu que não precisa de block RAM.
  Eficaz em modos otimizados (sample rate travado com dither da fonte).
- `[RTL]` Reduced bit depth: truncar LSBs de RGB + dither Bayer 2x2 opcional
  (paridade `xpos_pp`/`ypos_pp`); enable em bit livre. Menor que #103 no mesmo
  ponto de inserção.
- `[FW]` `pm_288p` separado de `pm_240p` (#85): split de `GROUP_288P` no
  `group_ptr[]` (`video_modes.c` ~149) + `pmcfg_ptr[]` (`controls.c` ~176) +
  campo em `avconfig_t` + menu + UDE. marqs: "como no OSSC Pro, posso
  considerar".
- `[FW]` Square PAR para 384/512-col (#37): estender `ar_256col` (hoje só 256-col)
  para `MODE_L*_384_COL`/`MODE_L*_512_COL` onde `x_rpt` resulta em fator inteiro.
- `[FW]` (explorar) Paleta PC Engine (#90): LUT 9bit→24bit; reusar caminho
  `lumacode_pal_ram` ou LUT dedicada — prior art: hitmanmcc experimental FW,
  Kitrinx/pce-devel palette math.

## Abordagem técnica

- Mudanças RTL aditivas; default = caminho atual.
- Ordem sugerida: pm_288p (FW puro, quick win) → square PAR (FW puro) →
  máscaras (RTL+FW) → blend/bitdepth (RTL).
- Cada recurso novo de perfil = campo `avconfig_t` + UDE ver 123 + item de menu.

## Critérios de aceite

- Regressão zero com novos campos em default.
- Mask_L/R independentes visíveis e simétricos quando iguais.
- pm_288p: perfil pode ter 288p em Line3x enquanto 240p fica Passthru.

## Referências

- `rtl/scanconverter.v` (~184, ~442-553, ~566-634), `sc_config_regs.h` (~115
  bits livres), `video_modes.c` (~149 group map, ~432 ar_256col, ~459-465
  x_offset), `controls.c` (~176 pmcfg_ptr), issues #37 #42 #85 #90 #95 #103 #133
